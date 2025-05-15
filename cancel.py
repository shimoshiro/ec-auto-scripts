#!/usr/bin/env python
# coding: utf-8

# yahooメールのAmazonキャンセルメールをチェックして処理
# Amazon キャンセル処理　　毎時間の5分と35分
# Amazon キャンセル処理　　6時-10時と13時-16時まで10分おきに処理 (上記と同じ処理)

print("\n\n\n")
print("-" * 80)
print("-" * 80)

# 現在の日付と時間を取得
now = datetime.now()
print()
formatted_date = now.strftime("%m/%d")
formatted_time = now.strftime("%H:%M")
print("ここから書換えスタート:", formatted_date, formatted_time)
print()
print()

#----------------------------------------------　

from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import re
import unicodedata
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import numpy as np
from selenium.webdriver.chrome.options import Options

import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
from os.path import expanduser

# ----------------------------------------------　

# ChromeDriverのパス候補（MacやLinuxに対応）
driver_paths = [
    expanduser('~/Library/CloudStorage/Dropbox/chrome/chromedriver_mac_arm64/chromedriver'),  # macOS (M1)
    expanduser('~/Library/CloudStorage/Dropbox/chrome/chromedriver-mac-x64/chromedriver'),    # macOS (Intel)
    '/usr/bin/chromedriver'  # Linux, EC2など
]

# 使用可能なChromeDriverを探す
selected_path = next((path for path in driver_paths if os.path.exists(path)), None)

if not selected_path:
    raise FileNotFoundError("❌ ChromeDriver が見つかりません。driver_paths を確認してください。")

print(f"✅ 使用するChromeDriver: {selected_path}")

# 環境判定（ローカルかEC2かを判別）
is_ec2 = "ec2-user" in os.getenv("HOME", "")

# ローカルでもヘッドレスにするか設定
use_headless = True  # True: ヘッドレスモード, False: GUIモード（デバッグ用）

# ChromeOptionsの設定
options = Options()

# 画面表示させたい場合は下記を表示させる
#if is_ec2:

# ヘッドレスモードの設定
if is_ec2 or use_headless:
    options.add_argument("--headless")  # ヘッドレスモード
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")  # GPUを無効化
    options.add_argument("--window-size=1820,1080")  # ウィンドウサイズを指定
    options.add_argument("--disable-popup-blocking")  # ポップアップブロックを無効化
    print("ヘッドレスモードを使用します")
    print()
else:
    # ローカル環境の場合は通常のGUIモードで動作
    options.add_argument("--window-size=1320,1280")  # ウィンドウサイズを指定
    print("ローカル環境で動作中: GUIモードを使用します")

# ChromeDriverの設定
service = Service(selected_path)
browser = webdriver.Chrome(service=service, options=options)

#------------------------------------------------------------------

USER1 = "your_user_id"
PASS1 = "your_password"

# yahooのキャンセルリクエストページにアクセス
url_login = "https://mail.yahoo.co.jp/u/pc/f/list/30"
browser.get(url_login)
time.sleep(1)

element = browser.find_element(By.ID, "login_handle")
element.clear()
element.send_keys(USER1)
    
browser_from = browser.find_element(By.XPATH, '//*[@id="content"]/div[1]/div/form/div[1]/div[1]/div[2]/div/button')
browser_from.click()
time.sleep(1)

element = browser.find_element(By.XPATH, '//*[@id="password"]')
element.clear()
element.send_keys(PASS1)

browser_from = browser.find_element(By.XPATH, '//*[@id="content"]/div[1]/div/form/div[2]/div/div[1]/div[2]/div[3]/button')
browser_from.click()
time.sleep(2)
print("yahoo_proにログインしました")

# 現在の日付と時間を取得
now = datetime.now()
# フォーマットして表示
formatted_date = now.strftime("%m/%d")
formatted_time = now.strftime("%H:%M")
print("処理の開始時間:", formatted_date, formatted_time)
print()

# HTMLコンテンツを取得してBeautifulSoupオブジェクトを作成
html_content = browser.page_source
soup = BeautifulSoup(html_content, 'html.parser')

m_times = []
unread_tr_xpaths_list = []

# 抽出したtrタグの中から未読のテキストがあるかをチェック
trtag = soup.find_all('tr', class_='bifa4g-8')
for tr in trtag:
    if '未読' in tr.get_text():
        m_tdtags = tr.find('td', class_='sc-1xxpdrg-0 hvGGsk sc-1xxpdrg-12 jsvsuy')
        if m_tdtags:
            m_time_tag = m_tdtags.find('time', class_='sc-1dpypvu-20 cmNhdI')
            if m_time_tag and 'title' in m_time_tag.attrs:
                m_time = m_time_tag['title']
                # 曜日の情報を削除
                m_time = m_time.replace(' 木', '').replace('水', '').replace('火', '').replace('月', '').replace('日', '').replace('土', '').replace('金', '')
                # 現在の年を取得して、メールの受信時刻の文字列に追加
                m_time_with_year = datetime.now().strftime("%Y") + "/" + m_time
                m_times.append(m_time_with_year)

                print(m_time_with_year)

                # 抽出される時間の差分が1時間以上の場合に新たな処理を実行
                if datetime.now() - datetime.strptime(m_time_with_year, "%Y/%m/%d %H:%M") >= timedelta(minutes=10):
                    print("10分以上経過")
                    print()
                    
                    # 未読のテキストが格納されているtrタグに対応するXPathを抽出する関数
                    def get_xpath_for_tag(tag):
                        components = []
                        current = tag
                        while current.parent is not None:
                            siblings = current.parent.find_all(current.name, recursive=False)
                            index = siblings.index(current) + 1
                            components.append(f"{current.name}[{index}]")
                            current = current.parent
                        components.reverse()
                        xpath = "/".join(components)
                        return xpath

                    # 抽出した未読のtrタグに対応するXPathを取得する
                    unread_tr_xpaths = get_xpath_for_tag(tr)
                    unread_tr_xpaths_list.append(unread_tr_xpaths)
                    # print(unread_tr_xpaths_list)
                    
                else:
                    print("10分未満で処理できません")
                    print()

order_numbers = []  # 空のリストを作成

# 未読のテキストが見つかった場合、順番に繰り返し処理
if len(unread_tr_xpaths_list) > 0:
    for xpath in unread_tr_xpaths_list:
        # XPathを使ってブラウザの要素を取得し、クリック
        element = browser.find_element(By.XPATH, xpath)
        element.click()
        time.sleep(2)

        # 前のコードでsoupを取得していると仮定します
        html_content = browser.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        # divタグの中でclass名が 'sc-1gpcxcw-14' と 'dkhotT' の要素を抽出
        target_div = soup.find('div', class_='sc-1gpcxcw-17 hxTFOA')        

        # 要素が存在するかを確認してからテキストを抽出
        if target_div:
            extracted_text = target_div.get_text()

            # 正規表現で注文番号を抽出 (注文番号は()内にあります)
            order_number_pattern = r"（(\d+-\d+-\d+)）"
            matches = re.findall(order_number_pattern, extracted_text)

            if matches:
                for match in matches:
                    order_number = match
                    order_numbers.append(order_number)
            else:
                print("注文番号が見つかりませんでした。")
        else:
            print("対象の要素が見つかりませんでした。")
            
print(order_numbers)

if unread_tr_xpaths_list:
    print(unread_tr_xpaths_list)
else: 
    print('※※※エックスパスがありません※※※')
    time.sleep(2)

USER1 = "your_user_id_1"
PASS1 = "your_password_1"
USER2 = "your_user_id_2"
PASS2 = "your_password_2"

url_login = "https://order.goqsystem.com/goq21/form/goqsystem_new/systemlogin.php?type=&shop="
browser.get(url_login)
time.sleep(2)

element = browser.find_element(By.ID, "login_id")
element.clear()
element.send_keys(USER1)
element = browser.find_element(By.ID, "login_pw")
element.clear()
element.send_keys(PASS1)
browser_from = browser.find_element(By.ID, "loginbtn1")
browser_from.click()
time.sleep(2)

element = browser.find_element(By.ID, "seq_id")
element.clear()
element.send_keys(USER2)
element = browser.find_element(By.ID, "seq_pw")
element.clear()
element.send_keys(PASS2)
browser_from = browser.find_element(By.XPATH, '//*[@id="goqlogin"]/div/div[2]/button')
browser_from.click()
time.sleep(2)
browser_from = browser.find_element(By.ID, "login3")
browser_from.click()
time.sleep(2)
print()

# 受注管理にアクセス
url_login = "https://order.goqsystem.com/goq21/index.php"
browser.get(url_login)
time.sleep(1)

# チェックボックスを検索してクリックする
checkboxes = browser.find_elements(By.CLASS_NAME, "info-check-box")
for checkbox in checkboxes:
    checkbox.click()
    print("チェックを入れました")
    time.sleep(2)

try:
    checkbox = browser.find_element(By.ID, 'manage_puw_close')
    checkbox.click()
except NoSuchElementException:
    pass
    print("チェック項目はありませんでした")

time.sleep(2)

# 全てボタンをクリックする
browser_from = browser.find_element(By.XPATH, '//*[@id="goq_index"]/ul[3]/li[1]/a')
browser_from.click()
print("全てボタンをクリック")
time.sleep(2)

# urlをforループで回す
for order_number in order_numbers:
    
    # 受注管理にアクセス
    url_login = "https://order.goqsystem.com/goq21/index.php?stat=12&page=1"
    browser.get(url_login)
    time.sleep(1)
    
    element = browser.find_element(By.XPATH, '//*[@id="srh_onum"]')
    element.clear()
    element.send_keys(order_number)

    try:
        browser_from = browser.find_element(By.ID, 'search')
        browser_from.click()
        print("絞り込み検索をクリック")
        time.sleep(2)
    except:
        print("絞り込み検索を押せなかったため、スキップします")  
        
# 個別ページにアクセスするためのURLを取得        
    html_content = browser.page_source
    soup = BeautifulSoup(html_content, 'html.parser')

    # trタグの中のtdタグの中のtableタグ内にあるaタグのURLを抽出するコード
    tr_url = soup.find_all('tr', id='orderListRow_0')

    # trタグが見つかった場合、その中のtdタグからtableタグを探し、その中のaタグからURLを抽出
    if tr_url:
        td_tags = tr_url[0].find_all('td')  # 最初に見つかったtrタグ内のすべてのtdタグを取得
        for td_tag in td_tags:
            # tdタグ内にtableタグがあるかチェック
            table_tag = td_tag.find('table')
            if table_tag:
                # tableタグ内にリンク（aタグ）がある場合はURLを抽出
                link = table_tag.find('a')
                if link and link.get('href'):
                    aurl = link['href']

    else:
        print("※※※ 個別ページのURLを取得できませんでした")     
        
# ゴクーで検索できないので再度未読処理
        # ２時間以上経過している場合は未読にしない
        if datetime.now() - datetime.strptime(m_time_with_year, "%Y/%m/%d %H:%M") <= timedelta(hours=2):
            
            url_login = "https://mail.yahoo.co.jp/u/pc/f/list/30"
            browser.get(url_login)
            time.sleep(6)

            # ゴクーにまだキャンセル注文が来ていない場合に、再度未読にする
            html_content = browser.page_source
            soup = BeautifulSoup(html_content, 'html.parser')

            target_value = order_number
            final_xpath = None  # final_xpath を初期化

            tr_tags = soup.find_all('tr', class_='bifa4g-8')
            for tr in tr_tags:
                if target_value in tr.get_text():
                    div_element = tr.find('div', {'title': 'メール選択', 'role': 'checkbox', 'data-cy': 'mailListCheckBox'})

                    if div_element:
                        # 該当するdiv要素が見つかった場合、XPathを生成する
                        xpath_parts = []
                        while div_element:
                            tag_name = div_element.name
                            index = sum(1 for previous_sibling in div_element.find_previous_siblings(tag_name)) + 1
                            xpath_parts.append(f'{tag_name}[{index}]')
                            div_element = div_element.parent
                        xpath_parts.reverse()
                        final_xpath = '/'.join(xpath_parts)
                        #print("Generated XPath:", final_xpath)
                        break  # 一致した最初のtrタグに対するXPathを生成したら終了

            # final_xpath が設定されているか確認し、設定されている場合のみ要素を取得する
            if final_xpath:
                # 要素を特定するためのXPathを組み立てる
                final_xpath2 = "//" + final_xpath.replace("[document][1]/", "").replace("/", "//")

                try:
                    # ブラウザから要素を取得
                    browser_from = browser.find_element(By.XPATH, final_xpath2)
                    browser_from.click()
                    print("チェックボックスを押しました")
                except Exception as e:
                    print("チェックボックスを押せませんでした:", str(e))
            else:
                print("該当する要素が見つかりませんでした")

            try:
                browser_from = browser.find_element(By.XPATH, '//*[@id="root"]/div[1]/div[4]/div[2]/div/div[2]/div[2]/ul[1]/li[7]/button')
                browser_from.click()
                time.sleep(1)
                print("その他を押しました")

            except:
                print("その他を押せませんでした")

            try:
                browser_from = browser.find_element(By.XPATH, '/html/body/div[15]/div/div/div[2]/div[2]/span[1]')
                browser_from.click()
                time.sleep(1)
                print("未読にするを押しました")
            except:
                print("未読にするを押せませんでした")

            continue  # 処理をスキップして次のループに進む
            
        else:
            print("2時間以上経過しているため未読にしませんでした")
            
            continue  # 処理をスキップして次のループに進む
        
# ステータスの抽出       
    html_content = browser.page_source
    soup = BeautifulSoup(html_content, 'html.parser')

    # trタグの中のtdタグの中のtableタグ内にあるfontタグを探し、最初に一致したテキストを抽出するコード
    tr_url = soup.find_all('tr', id='orderListRow_0')

    # 抽出したテキストを格納する変数を初期化
    s_text = ""

    # trタグが見つかった場合、その中のtdタグからtableタグを探し、最初に一致したfontタグのテキストを抽出
    if tr_url:
        td_tags = tr_url[0].find_all('td')  # 最初に見つかったtrタグ内のすべてのtdタグを取得
        for td_tag in td_tags:
            # tdタグ内にtableタグがあるかチェック
            table_tag = td_tag.find('table')
            if table_tag:
                # tableタグ内にあるfontタグを探し、最初に見つかったもののテキストを抽出
                font_tag = table_tag.find('font')
                if font_tag:
                    # 正規表現を使ってスペースを削除
                    s_text = re.sub(r'\s+', '', font_tag.text)
                    break  # 最初に見つかったものだけを抽出するため、ループを終了

    # []を削除
    s_text = s_text.replace("[", "").replace("]", "")
    print("変更前のステータス:", s_text)

# 受注管理にアクセス
    aurl = f"https://order.goqsystem.com/goq21/{aurl}"
    browser.get(aurl)
    time.sleep(1)
    print(aurl)
            
    try:
        browser_from = browser.find_element(By.XPATH, '//*[@id="order_from"]/table[4]/tbody/tr/td/table/tbody/tr/td[3]/table/tbody/tr/td[3]/span/a')
        browser_from.click()
        print("注文のキャンセル(Amazon)をクリック")
        time.sleep(3)
    except:
        print("注文のキャンセル(Amazon)を押せなかったため、スキップします")

    try:
        browser_from = browser.find_element(By.XPATH, '//*[@id="jsCancel"]')
        browser_from.click()
        print("キャンセル処理を行うをクリック")
        time.sleep(3)
    except:
        print("キャンセル処理を行うを押せなかったため、スキップします")
        
    time.sleep(5)
        
    #　再度元の個別ページに戻る
    browser.get(aurl)
    time.sleep(60)
        
    memo = "※ 購入者によるキャンセルリクエスト"
    try:
        # 発送日情報をひとことメモに記載
        element = browser.find_element(By.XPATH, '//*[@id="a9"]')
        # 改行
        newline = "\n"
        element.send_keys(newline)
        element.send_keys(memo)
        print(memo)

        # 入力内容を反映するをクリック　
        update_button = browser.find_element(By.XPATH, '//*[@id="order_from"]/table[8]/tbody/tr/td/input[1]')
        update_button.click()
        print("入力内容を反映するをクリック")

    except:
        print("テキストを入力できませんでした")
    
# 注文数を取得
    html_content = browser.page_source
    soup = BeautifulSoup(html_content, 'html.parser')

    # trタグの中のtdタグの中にあるspanタグの値を抽出するコード
    span_values = []
    tr_tags = soup.find_all('tr')
    for tr_tag in tr_tags:
        td_tags = tr_tag.find_all('td')
        for td_tag in td_tags:
            span_tag = td_tag.find('span', class_='u-fsz-16')
            if span_tag:
                span_value1 = span_tag.text
                print(span_value1)
                span_values.append(span_tag.text)

    #---------------------------- 複数注文の繰り返し処理

    # 在庫数更新ボタンのURLを取得
    import re
    html_content = browser.page_source
    soup = BeautifulSoup(html_content, 'html.parser')

    # divタグ内にある在庫数更新というテキストを含むaタグのonclick属性を抽出するコード
    onclick_values = []
    div_tags = soup.find_all('div', align='right')
    for div_tag in div_tags:
        a_tags = div_tag.find_all('a')
        for a_tag in a_tags:
            if '在庫数更新' in a_tag.text:
                onclick_value = a_tag.get('onclick')
                if onclick_value:
                    onclick_values.append(onclick_value)

    # クエリ文字列を抽出する正規表現パターン
    pattern = r'\?[^,\'"]+'
    query_strings = []
    for onclick_value in onclick_values:
        match = re.search(pattern, onclick_value)
        if match:
            query_strings.append(match.group())

    # クエリ文字列から[ ]を取り除く
    cleaned_query_strings = [query_string.replace('[', '').replace(']', '') for query_string in query_strings]

    # URL生成とアクセス
    for query_string, span_value in zip(cleaned_query_strings, span_values):
        zurl = f"http://stock2.goqsystem.com/{query_string}"
        browser.get(zurl)
        time.sleep(1)
        print(zurl)  # 正しく生成されたURLを表示
        print("注文数:", span_value)  # 対応するspanの値を表示

        # 在庫連携にアクセスする時にログインを求められた時    
        try:
            element = browser.find_element(By.ID, "login_id")
            element.clear()
            element.send_keys(USER1)
            element = browser.find_element(By.ID, "login_pw")
            element.clear()
            element.send_keys(PASS1)
            browser_from = browser.find_element(By.XPATH, '//*[@id="loginform"]/div/div/div[1]/input')
            browser_from.click()
            time.sleep(2)
            print("ログインしました")

            element = browser.find_element(By.ID, "seq_id")
            element.clear()
            element.send_keys(USER2)
            element = browser.find_element(By.ID, "seq_pw")
            element.clear()
            element.send_keys(PASS2)
            browser_from = browser.find_element(By.XPATH, '//*[@id="loginform"]/div/div/div[2]/input')
            browser_from.click()
            time.sleep(2)

            browser.get(zurl)
        except:
            print("ログインボタンがありません")

        # 在庫連携にアクセスして、箱の番号と在庫数を取得
        html_content = browser.page_source
        soup = BeautifulSoup(html_content, 'html.parser')

        # 抽出したname属性とvalue属性の格納リスト
        input_data = []

        # trタグの中のtdタグの中にあるinput要素を抽出するコード
        tr_tags = soup.find_all('tr')
        for tr_tag in tr_tags:
            td_tags = tr_tag.find_all('td')
            for td_tag in td_tags:
                # input要素を取得
                input_tag = td_tag.find('input', {'type': 'text'})
                if input_tag:
                    # input要素のvalue属性を取得
                    input_value = input_tag['value']
                    # input要素のname属性を取得
                    input_name = input_tag['name']
                    # name属性とvalue属性をリストに追加
                    input_data.append((input_name, input_value))

                    print("在庫連携:", input_data)

        # input_dataに値がない場合の処理
        if not input_data:
            browser.get(aurl)
            time.sleep(1)

            # 受注ステータスを選択
            browser_from = browser.find_element(By.XPATH, '//*[@id="a6"]')
            browser_from.click()
            print("受注ステータスを押しました")

            # キャンセルを選択
            browser_from = browser.find_element(By.XPATH, '//*[@id="a6"]/option[11]')
            browser_from.click()
            s_text = "加藤処理BOX"
            print("加藤処理BOXを選択")

            # 入力内容を反映するを押す
            browser_from = browser.find_element(By.XPATH, '//*[@id="order_from"]/table[8]/tbody/tr/td/input[1]')
            browser_from.click()
            print("入力内容を反映するを押しました")
            time.sleep(2)

            memo_zaiko = "※ 在庫連携されていません"
            try:
                element = browser.find_element(By.XPATH, '//*[@id="a9"]')
                # 改行
                newline = "\n"
                element.send_keys(newline)
                element.send_keys(memo_zaiko)
                print(memo_zaiko)

                # 入力内容を反映するをクリック　
                update_button = browser.find_element(By.XPATH, '//*[@id="order_from"]/table[8]/tbody/tr/td/input[1]')
                update_button.click()
                print("入力内容を反映するをクリック")
                print()
                print()

            except:
                print("テキストを入力できませんでした")
                print()
                print()

            continue  # 処理をスキップして次のループに進む

        # 注文数と在庫数と合計して書き込んで保存
        input_value2 = int(input_value)
        span_value2 = int(span_value)
        total_value = input_value2 + span_value2

        print("入力数:", total_value)

        # elementを取得
        element = browser.find_element(By.NAME, input_name)
        # elementの値をクリア
        element.clear()
        # 数字の部分をname属性に代入して送信
        element.send_keys(total_value)

        # 在庫連携の全選択
        try:
            time.sleep(1)
            browser_from = browser.find_element(By.XPATH, '//*[@id="stock-main-table"]/thead/tr[1]/th[1]/label/input')
            browser_from.click()
            time.sleep(1)
        except:
            pass

        try:
            time.sleep(1)
            browser_from = browser.find_element(By.XPATH, '//*[@id="myTabContent"]/div[2]/div[2]/div/button')
            browser_from.click()
            time.sleep(3)
        except:
            pass

        # 反映押した後のアラートをクリック
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        # ページを取得
        html_content = None
        try:
            WebDriverWait(browser, 5).until(EC.alert_is_present())
            alert = browser.switch_to.alert
            alert_text = alert.text
            alert.accept()
            print("アラートが表示されました: {}".format(alert_text))
            time.sleep(2)

            # アラートが表示されたら、再度ページを取得
            html_content = browser.page_source
            time.sleep(2)
        except:
            # アラートが表示されなかった場合
            html_content = browser.page_source
            time.sleep(2)

        #---------------------------- 

        #print("注文数: ", span_values)
        print()

        # 変更前ステータスと比較してステータスの変更

        browser.get(aurl)
        time.sleep(1)

        # 条件判定と処理の分岐
        if s_text == "新規受付" or s_text == "りゅうじシステム書き換え処理BOX" or s_text == "書き換え完了BOX" or s_text == "★★処理反応しないBOX★★":
            browser_from = browser.find_element(By.XPATH, '//*[@id="a6"]')
            browser_from.click()
            print("受注ステータスを押しました")

            # キャンセルを選択
            browser_from = browser.find_element(By.XPATH, '//*[@id="a6"]/option[53]')
            browser_from.click()
            print("キャンセルを選択")

            # 入力内容を反映するを押す
            browser_from = browser.find_element(By.XPATH, '//*[@id="order_from"]/table[8]/tbody/tr/td/input[1]')
            browser_from.click()
            print("入力内容を反映するを押しました")

            print()
            print()

        else:
            browser_from = browser.find_element(By.XPATH, '//*[@id="a6"]')
            browser_from.click()
            print("受注ステータスを押しました")

            # キャンセルを選択
            browser_from = browser.find_element(By.XPATH, '//*[@id="a6"]/option[11]')
            browser_from.click()
            print("加藤処理BOXを選択")

            # 入力内容を反映するを押す
            browser_from = browser.find_element(By.XPATH, '//*[@id="order_from"]/table[8]/tbody/tr/td/input[1]')
            browser_from.click()
            print("入力内容を反映するを押しました")
            time.sleep(2)

            memo_prepare = "※ 出荷準備中か確認お願いします"
            try:
                # 発送日情報をひとことメモに記載
                element = browser.find_element(By.XPATH, '//*[@id="a9"]')
                # 改行
                newline = "\n"
                element.send_keys(newline)
                element.send_keys(memo_prepare)
                print(memo_prepare)

                # 入力内容を反映するをクリック　
                update_button = browser.find_element(By.XPATH, '//*[@id="order_from"]/table[8]/tbody/tr/td/input[1]')
                update_button.click()
                print("入力内容を反映するをクリック")

            except:
                print("テキストを入力できませんでした")

            print()
            print("-" * 8)
            print()
            print()

# 現在の日付と時間を取得
now = datetime.now()
print()
formatted_date = now.strftime("%m/%d")
formatted_time = now.strftime("%H:%M")
print("処理時刻:", formatted_date, formatted_time)
print("-" * 24)
print("\n\n\n")

browser.quit()
