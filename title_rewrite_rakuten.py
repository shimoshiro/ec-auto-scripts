#!/usr/bin/env python
# coding: utf-8

# 楽天の商品名書き換え
# 商品情報書き換え 1時間毎の定期実行(9時と15時以外）　毎時間の20分
# 商品情報書き換え 14時50分

print("\n\n\n")
print("-" * 80)
print("-" * 80)

# 処理開始時間
from datetime import datetime

# 現在の日付と時間を取得
now = datetime.now()
print()
formatted_date = now.strftime("%m/%d")
formatted_time = now.strftime("%H:%M")
print("ここから書換えスタート:", formatted_date, formatted_time)
print()
print()

#----------------------------------------------　

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
from selenium.common.exceptions import NoSuchWindowException, WebDriverException
from os.path import expanduser

#----------------------------------------------　

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

USER1 = "your_user_id_1"
PASS1 = "your_password_1"
USER2 = "your_user_id_2"
PASS2 = "your_password_2"

url_login = "https://order.goqsystem.com/goq21/form/goqsystem_new/systemlogin.php?type=&shop="
browser.get(url_login)
time.sleep(1)

# login with user1
element = browser.find_element(By.ID, "login_id")
element.clear()
element.send_keys(USER1)
element = browser.find_element(By.ID, "login_pw")
element.clear()
element.send_keys(PASS1)
browser_from = browser.find_element(By.ID, "loginbtn1")
browser_from.click()
time.sleep(2)

# login with user2
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

#------------------------------------------------------------------

# 受注管理にアクセス
url_login = "https://order.goqsystem.com/goq21/index.php"
browser.get(url_login)
time.sleep(1)

checkboxes = browser.find_elements(By.CLASS_NAME, "info-check-box")
for checkbox in checkboxes:
    checkbox.click()
    print("チェックを入れました")
    time.sleep(2)

# チェックボックスを検索してクリックする
try:
    checkbox = browser.find_element(By.ID, 'manage_puw_close')
    checkbox.click()
except NoSuchElementException:
    pass
    print("チェック項目はありませんでした")

time.sleep(2)

browser_from = browser.find_element(By.XPATH, '//*[@id="collapseExamplexxx2"]/div/table/tbody/tr/td[3]/table[1]/tbody/tr/td/table/tbody/tr[3]/td[2]/span/a[4]')
browser_from.click()
print("表示件数を500件に変更")
time.sleep(2)

#-----------------------------変更箇所

browser_from = browser.find_element(By.XPATH, '//*[@id="goq_index"]/ul[3]/li[15]/a')
browser_from.click()
print("書き換え処理BOXをクリック")
time.sleep(2)

browser_from = browser.find_element(By.XPATH, '//*[@id="pro_form"]/table/tbody/tr/td/ul/li[2]/a')
browser_from.click()
print("楽天ボタンをクリック")
time.sleep(2)

print()
print("-" * 8)
print()

# urlリスト
urls = []

html_content = browser.page_source
soup = BeautifulSoup(html_content, 'html.parser')

tr_tags = soup.find_all('tr', align='center', bgcolor=True)

for tr_tag in tr_tags:
    review_tag = tr_tag.find(text=re.compile("※済み"))
    if review_tag:
        link_tag = tr_tag.find('a')
        if link_tag is not None:
            link = link_tag['href']
            yurl = f"https://order.goqsystem.com/goq21/{link}"
            urls.append(yurl)
            print("URLを追加しました:", yurl)
                        
            browser.get(yurl)
            time.sleep(2)

            # 以下のコードを追加して修正します
            browser_from = browser.find_element(By.XPATH, '//*[@id="a6"]')
            browser_from.click()
            print("※ 受注ステータスを押しました")
            time.sleep(1)

#---------------------------------------------------------------------------------------
# ステータス変更箇所　

            try:                        
                browser_from = browser.find_element(By.XPATH, '//*[@id="a6"]/option[15]')
                browser_from.click()
                print("書き換え完了BOXを押しました")
                time.sleep(1)
            except:
                print("※※※ 書き換え完了BOXを押せませんでした")


            try:
                browser_from = browser.find_element(By.XPATH, '//*[@id="order_from"]/table[8]/tbody/tr/td/input[1]')
                browser_from.click()
                print("※ 入力内容を反映するを押しました")
                time.sleep(2)
                print()
                print()
            except:
                print("※※※ 入力内容を反映するを押せませんでした")
                print()
                print()     

print()
print("-" * 8)
print()

# 受注管理にアクセス
url_login = "https://order.goqsystem.com/goq21/index.php"
browser.get(url_login)
time.sleep(3)

checkboxes = browser.find_elements(By.CLASS_NAME, "info-check-box")
for checkbox in checkboxes:
    checkbox.click()
    print("チェックを入れました")
    time.sleep(2)

# チェックボックスを検索してクリックする
try:
    checkbox = browser.find_element(By.ID, 'manage_puw_close')
    checkbox.click()
except NoSuchElementException:
    pass
    print("チェック項目はありませんでした")

time.sleep(8)

#------------------------------------------------

try:
    browser_from = browser.find_element(By.XPATH, '//*[@id="collapseExamplexxx2"]/div/table/tbody/tr/td[3]/table[1]/tbody/tr/td/table/tbody/tr[3]/td[2]/span/a[4]')
    browser_from.click()
    print("表示件数を500件に変更")
    time.sleep(1)
except:
    print("表示件数を500件に変更できませんでした")
    print()
    print()
    
#-----------------------------変更箇所

try:
    browser_from = browser.find_element(By.XPATH, '//*[@id="goq_index"]/ul[3]/li[15]/a')
    browser_from.click()
    print("書き換え処理BOXをクリック")
    time.sleep(1)
except:
    print("表示件数を500件に変更できませんでした")
    print()
    print()

try:
    browser_from = browser.find_element(By.XPATH, '//*[@id="pro_form"]/table/tbody/tr/td/ul/li[2]/a')
    browser_from.click()
    print("楽天ボタンをクリック")
    time.sleep(1)
except:
    print("表示件数を500件に変更できませんでした")
    print()
    print()

# urlリスト
urls = []

html_content = browser.page_source
soup = BeautifulSoup(html_content, 'html.parser')

tr_tags = soup.find_all('tr', align='center', bgcolor=True)

for tr_tag in tr_tags:
    review_tag = tr_tag.find(text=re.compile("※済み"))
    if review_tag is None:
        link_tag = tr_tag.find('a')
        if link_tag is not None:
            link = link_tag['href']
            yurl = f"https://order.goqsystem.com/goq21/{link}"
            urls.append(yurl)
            print()
            print()
            print("-" * 24)
            print("URLを追加しました:", yurl)
            
            ex_texts = []
            text_list = []
            
            browser.get(yurl)
            time.sleep(2)
        
# -----------------------------------------------------------------------
#受注番号を取得

            # 受注番号を取得
            html_content = browser.page_source
            soup = BeautifulSoup(html_content, 'html.parser')

            table_tags = soup.find_all('table')

            # 重複を防ぐためのセット
            extracted_texts = set()

            # tableタグが見つかった場合、それぞれのtableタグ内のtrタグの中のtdタグを検索
            for table_tag in table_tags:
                tr_tags = table_tag.find_all('tr')
                for tr_tag in tr_tags:
                    try:
                        # クラス名ordermanegebg4 を指定して、'受注番号'が含まれるspanタグを検索
                        span_tag = tr_tag.find('span', class_='fontsz12', string=lambda text: text and '受注番号' in text)
                        if span_tag:
                            # spanタグの親であるtdタグを取得
                            order_number_td = span_tag.find_parent('td', class_='ordermanegebg4')
                            if order_number_td:
                                # '受注番号'が含まれるtdタグと同じ階層のもう一つのtdタグを検索
                                additional_td = order_number_td.find_next('td', bgcolor='#ffffff')
                                if additional_td:
                                    # additional_td内のspanタグのテキストを取得
                                    additional_span_tag = additional_td.find('span', class_='fontsz12')
                                    if additional_span_tag:
                                        # 重複を避けるために、一度だけ抽出するための処理
                                        additional_span_text = additional_span_tag.get_text(strip=True)
                                        # 重複していない場合のみ表示
                                        if additional_span_text not in extracted_texts:
                                            print('受注番号：',additional_span_text)
                                            print()
                                            extracted_texts.add(additional_span_text)
                                    else:
                                        print("1 受注番号が取得できませんでした")
                                else:
                                    print("2 受注番号が取得できませんでした")
                            else:
                                print("3 受注番号が取得できませんでした")
                    except Exception as e:
                        print(f"An error occurred: {e}")

# -----------------------------------------------------------------------
#注文数を取得して同一商品が複数ある場合にメモに書き込む

            # ページソースを取得
            html_content = browser.page_source  # ページソースを取得
            soup = BeautifulSoup(html_content, 'html.parser')

            # 対象のテーブルを特定
            target_table = soup.find('table', style=re.compile(r'border:.*rgba\(196,196,196,1\.00\).*background-color:.*rgba\(213,203,203,1\.00\)'))

            if target_table:
                # テーブル内のすべての<tr>を取得
                rows = target_table.find_all('tr', style=re.compile(r'color:#000000'))

                # 各行を処理
                for idx, row in enumerate(rows):
                    cells = row.find_all('td')
                    if len(cells) >= 9:  # 必要な列数があるか確認
                        target_value = cells[9].text.strip()  # 9番目の<td>を取得（インデックスは0始まりなので実質10番目）

                        # 値を数値に変換してチェック
                        try:
                            numeric_value = int(target_value.replace(",", "").replace("円", "").strip())  # 数値に変換（整数に変換）
                            if numeric_value > 1:  # 値が1以上かを判定
                                print(f"\n注文 {idx + 1} の数量: {numeric_value}")
                                print(f"※※※　同一商品が複数です。")

                                try:
                                    zaiko_zero = "数量注意  "
                                    # 発送日情報をひとことメモに記載
                                    element = browser.find_element(By.XPATH, '//*[@id="a9"]')
                                    # 改行
                                    newline = "\n"
                                    element.send_keys('  ※')
                                    element.send_keys(zaiko_zero)
                                    element.send_keys(newline)
                                    print("※※※　数量注意を書き込みました")

                                    # 入力内容を反映するをクリック　
                                    update_button = browser.find_element(By.XPATH, '//*[@id="order_from"]/table[8]/tbody/tr/td/input[1]')
                                    update_button.click()
                                    print("入力内容を反映するをクリック\n")

                                except:
                                    print("※※※　数量情報を入力できませんでした\n")

                            else:
                                print(f"注文 {idx + 1} の数量: {numeric_value} ")
                        except ValueError:
                            print(f"注文 {idx + 1} の数量: '{target_value}' は数値ではありません。")
                    else:
                        print(f"注文 {idx + 1} の行に9個以上の<td>タグがありません。")
            else:
                print("指定されたstyleの<table>タグが見つかりません。")

# -----------------------------------------------------------------------
#複数在庫と包装紙以外のURLを取得して在庫の情報を取得

            print("-" * 8)
            print()

            print("※個別ページの商品内訳を取得して、複数連携・ラッピングがないかチェック")
            print()

            html_content = browser.page_source
            soup = BeautifulSoup(html_content, 'html.parser')

            # -----------------------------------------------------------------------

            otori_match = None
            shipping_match = None

            # 新しい処理が始まる前にリストをリセット
            extracted_data_list = []

            # 商品リストの tr タグを取得してループ処理
            tr_tags = soup.find_all('tr', style=re.compile(r'color:#000000'))

            url_list = []

            for tr_tag in tr_tags:
                # td タグを抽出
                td_tags = tr_tag.find_all('td', valign='top', bgcolor='#ffffff')

                if len(td_tags) >= 1:
                    # 2つ目の td タグを取得
                    second_td_tag = td_tags[0]

                    # div タグを取得
                    div_tags = second_td_tag.find_all('div', align='right')

                    if len(div_tags) >= 1:
                        # 2つ目の div タグを取得
                        second_div_tag = div_tags[-1]

                        # テキストだけを抽出
                        div_text_content = second_div_tag.get_text(strip=True)
                        print("テキスト抽出1:\n", div_text_content)
                        print()

                        # span タグを取得
                        span_tag = second_td_tag.find('span')

                        if span_tag:
                            # span タグ内のテキストを抽出
                            span_text_content = span_tag.get_text(strip=True)
                            print("テキスト抽出2:\n", span_text_content)

                            # スペース、全角スペース、改行、タブ、特殊文字を削除
                            clean_text = span_text_content.replace('\u3000', ' ').replace('\n', '').replace('\r', '').replace('\t', '').strip()

                            # 正規表現のマッチングを試みる
                            shipping_match = None
                            
                            # 「お取り寄せのため」の部分だけをマッチさせて確認
                            otori_match = re.search(r'お取り寄せの[為ため].*?(\d+[\s\-〜～−－‐]*\d+).*?(営業日|日)以内で発送', clean_text, re.DOTALL)

                            if otori_match:
                                shipping_match = otori_match.group()
                                print("パターン: 取り寄せ情報（完全マッチ）:", shipping_match)

                            # パターン2: お取り寄せのため5〜10営業日以内で発送できます（別パターン）
                            elif (otori_match := re.search(r'お取り寄せの為\s*[\d〜-]+\s*営業日以内で発送', clean_text, re.DOTALL)):
                                shipping_match = otori_match.group()
                                print("パターン2: 取り寄せ情報（発送できます）:", shipping_match)

                            # 即日発送（定休日を除く）を取得する正規表現
                            elif (otori_match := re.search(r'即日発送（定休日を除く）', clean_text, re.DOTALL)):
                                shipping_match = otori_match.group()
                                print("パターン3: 発送情報:", shipping_match)

                            # 在庫切れ対応
                            elif (otori_match := re.search(r'在庫切れのため、[\d〜-]+日以内に発送となります。', clean_text, re.DOTALL)):
                                shipping_match = otori_match.group()
                                print("パターン4: 在庫切れ情報:", shipping_match)

                            # 営業日または営業以内で発送のパターンを取得する正規表現
                            elif (otori_match := re.search(r'[\d〜-]+営業日以内で発送(できます|予定です)。', clean_text, re.DOTALL)):
                                shipping_match = otori_match.group()
                                print("パターン5: 営業日以内で発送情報:", shipping_match)

                            # 再入荷対応
                            elif (otori_match := re.search(r'【再入荷】\s*(.*?)\s*発送予定', clean_text, re.DOTALL)):
                                shipping_match = otori_match.group()
                                print("パターン6: 再入荷情報:", shipping_match)

                            else:
                                print("パターンマッチなし。")
                                shipping_match = None  # 発送情報が見つからない場合は None にする

                            # (数字やテキスト-数字-数字)のパターンを抽出する正規表現 (SKU形式)
                            custom_pattern = re.compile(r'\(([\w-]+-\d+-\d+)\)')
                            custom_match = custom_pattern.findall(clean_text)  # clean_textを使用

                            if custom_match:
                                # 最後のマッチしたSKUを変数に格納
                                custom_extracted_text = custom_match[-1]
                                print(f"抽出されたSKU: {custom_extracted_text}")
                                print()
                            else:
                                # 2つ目の()内のテキストを条件なしで抽出する正規表現
                                fallback_pattern = re.compile(r'\(([^)]+)\)')
                                fallback_match = fallback_pattern.findall(clean_text)
                                if len(fallback_match) >= 2:
                                    custom_extracted_text = fallback_match[1]  # 2つ目の括弧内のテキストを取得
                                    print(f"括弧内の2つ目のテキスト: {custom_extracted_text}")
                                else:
                                    custom_extracted_text = None
                                    print("SKUが見つかりませんでした。")

                            # 抽出したテキストと配送情報をセットにしてリストに追加
                            if custom_extracted_text:
                                extracted_data_list.append({
                                    'custom_extracted_text': custom_extracted_text,
                                    'shipping_info': shipping_match
                                })
                                
                            print()
                            print('shipping_match1:',shipping_match)
                            print()
                            print()
                            print(extracted_data_list)
                            print()

                            # -----------------------------------------------------------------------
                            #下記条件にヒットした場合にTrureになりトリガーが発動して、修正内容の一番上（下記の場合は包装紙）の記入をスキップされるため、編集時は注意

                            #前の処理で i+1　の処理がされているかもしれないので一度リセット
                            giftwrap = None

                            # div_text_contentとspan_text_contentの中に指定のテキストが格納されていない場合に処理を行う
                            if "複数登録あり" not in div_text_content and "ギフト袋" not in span_text_content and "包装紙" not in span_text_content and "追加情報" not in span_text_content:

                                # aタグの要素を取得
                                elements = tr_tag.find_all('a', string=re.compile('【在庫数更新】'))

                                for element in elements:
                                    # 修正: 'a'タグが見つからない場合をチェック
                                    onclick = element.get('onclick')
                                    if onclick:
                                        start_index = onclick.index("'/goq21/auth/stock2_auth2.php?") + len("'/goq21/auth/stock2_auth2.php?")
                                        end_index = onclick.index("'", start_index)
                                        result = onclick[start_index:end_index]

                                        url = "http://stock2.goqsystem.com/?" + result
                                        url_list.append(url)
                                        print(url)
                                        print()

                            # ギフト袋がある場合は giftwrapにtrueをつけて書き換えの時にエックスパスの変数に1を足して、ギフト欄に代入しないようにする
                            else:
                                print('※※※ 複数登録・包装紙・ギフト袋のどれかの表記があるので、URLを取得しませんでした。')
                                print()

                                if "ギフト袋" in span_text_content:
                                    giftwrap = True
                                    print("giftwrapにTrueを代入")
                                    print()

                                else:
                                    print("※※※ ギフト袋 ではないのでTrueを代入しませんでした")

            # extracted_data_list の内容を出力
            if extracted_data_list:
                for data in extracted_data_list:
                    print(f"抽出テキスト: {data['custom_extracted_text']}, 配送情報: {data['shipping_info']}")
            else:
                print("extracted_data_list にデータが追加されていません。")
                print()

            print()

            print()
            print("-" * 80)
            otori_match = re.search(r'お取り寄せの[為ため]\s*[\d〜\-]+(?:営業日|日)以内で発送', span_text_content.replace('\u3000', ' '), re.DOTALL)
            print()

            # 最終的なurl_listを表示
            print(url_list)

            #-----------------------------------------------

            # 受注管理にアクセス
            url_login = url
            browser.get(url_login)
            time.sleep(2)

            # login with user1
            try:
                element = browser.find_element(By.ID, "login_id")
                element.clear()
                element.send_keys(USER1)
                element = browser.find_element(By.ID, "login_pw")
                element.clear()
                element.send_keys(PASS1)
                browser_form = browser.find_element(By.XPATH, '//*[@id="loginform"]/div/div/div[1]/input')
                browser_form.click()
                time.sleep(2)
            except NoSuchElementException:
                time.sleep(2)
                pass

            # login with user2
            try:
                element = browser.find_element(By.ID, "seq_id")
                element.clear()
                element.send_keys(USER2)
                element = browser.find_element(By.ID, "seq_pw")
                element.clear()
                element.send_keys(PASS2)
                browser_from = browser.find_element(By.XPATH, '//*[@id="loginform"]/div/div/div[2]/input')
                browser_from.click()
                time.sleep(2)
            except NoSuchElementException:
                time.sleep(2)
                pass
                print()

            #-----------------------------------------------
            # 取得した在庫連携のURLを使用して処理を繰り返す

            collations = []
            order_list = []

            for j, url in enumerate(url_list):
                time.sleep(2)
                url_login = url
                browser.get(url_login)
                time.sleep(5)

                shop_sku = None

                try:
                    # ページが完全に読み込まれるのを待つ
                    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
                    
                    # ページのHTMLコンテンツを取得
                    html = browser.page_source
                    # BeautifulSoupを使用してHTMLを解析
                    soup = BeautifulSoup(html, 'html.parser')
                    # <td>タグを検索して目的の要素を取得
                    td_element = soup.find('td', class_='shop-sku-red sku')
                    
                    time.sleep(3)

                    # <span>タグを検索してテキストを取得
                    if td_element:
                        span_element = td_element.find('span')
                        if span_element:
                            shop_sku = span_element.get_text()
                            print(shop_sku)
                        else:
                            print("shop_skuが見つかりませんでした。")
                    else:
                        print("商品情報が見つかりませんでした。")
                    
                    if td_element is None:
                        # 目的の要素が見つからない場合はスキップする
                        print("※ 情報がなかったので処理をスキップします")

                        browser.get(yurl)
                        time.sleep(1)

                        # 以下のコードを追加して修正します
                        browser_from = browser.find_element(By.XPATH, '//*[@id="a6"]')
                        browser_from.click()
                        print("※1 受注ステータスを押しました")

    #---------------------------------------------------------------------------------------
    # ステータス変更箇所　1

                        try:                        
                            browser_from = browser.find_element(By.XPATH, '//*[@id="a6"]/option[15]')
                            browser_from.click()
                            print("書き換え完了BOXを押しました")
                        except:
                            print("※※※ 書き換え完了BOXを押せませんでした")

                        try:
                            browser_from = browser.find_element(By.XPATH, '//*[@id="order_from"]/table[8]/tbody/tr/td/input[1]')
                            browser_from.click()
                            print("※ 入力内容を反映するを押しました")
                        except:
                            print("※※※ 入力内容を反映するを押せませんでした")
                            
                        print()
                        print()
                        print()
                        print()
                        print()
                        print("-" * 8)
                        print()
                        data_content = None

                        continue  # 処理をスキップして次のループに進む

                    else:
                        # <span>タグのdata-content属性を取得
                        data_content = td_element.find('span')['data-content']

                        # 商品管理番号(商品URL)：から<br>までの行を省く
                        start_index = data_content.find('商品管理番号（商品URL）：')
                        end_index = data_content.find('<br>', start_index)
                        data_content = data_content[:start_index] + data_content[end_index + len('<br>'):]

                        # バリエーション項目選択肢3からバリエーション項目選択肢6までの行を省く
                        variation_start = data_content.find('バリエーション項目選択肢3')
                        variation_end = data_content.find('バリエーション項目選択肢6：', variation_start)
                        data_content = data_content[:variation_start] + data_content[variation_end + len('バリエーション項目選択肢6：'):]
                        data_content = "\n".join(line for line in data_content.splitlines() if line.strip())

                        # テキスト情報を表示
                        print(data_content)
                        print()
  
                        #---------------------------------------------------------------------------------------
                        # ここから管理番号で検索して商品管理の方のタイトルを取得

                        pattern = r"商品番号：(.*?)<br>"
                        match = re.search(pattern, data_content)

                        if match:
                            product_number = match.group(1)
                            print("商品番号:", product_number)
                        else:
                            print("商品番号が見つかりませんでした")
                            print()
                            
                        #-----------------------
                        
                        pattern = r"SKU管理番号：(.*?)<br>"
                        match = re.search(pattern, data_content)

                        if match:
                            sku_number = match.group(1)
                            print("SKU管理番号:", sku_number)
                            print()
                        else:
                            print("SKU管理番号が見つかりませんでした")
                            print()
                            
                        #-----------------------
                        product_sku = None
                        
                        # sku管理番号が-から始まる場合だけ実行    
                        if sku_number.startswith('-'):
                            if product_number:
                                product_sku = product_number + sku_number
                                print("照合用ナンバー1: ", product_sku)
                                print()

                        elif not product_sku:
                            product_sku = product_number
                            print("照合用ナンバー2: ", product_sku)
                            print()

                        else:
                            product_sku = shop_sku
                            print("照合用ナンバー3: ", product_sku)
                            print()

                        #--------------------------------------

                        # 受注管理にアクセス
                        url_login = "https://item6.goqsystem.com/goqsku/product/main"
                        browser.get(url_login)
                        time.sleep(2)

                        try:
                            element = browser.find_element(By.NAME, "userid")
                            element.clear()
                            element.send_keys(USER2)
                            element = browser.find_element(By.NAME, "passwd")
                            element.clear()
                            element.send_keys(PASS2)

                            browser_from = browser.find_element(By.NAME, 'login')
                            browser_from.click()
                            time.sleep(2)

                        except NoSuchElementException:
                            print("ログイン済みでスキップ")
                            time.sleep(2)

                        #--------------------------------------                            

                        try:
                            # 商品コードを入力
                            element = browser.find_element(By.NAME,"f_prodcode")
                            element.clear()
                            element.send_keys(product_number)
                            time.sleep(1)

                            browser_from = browser.find_element(By.NAME, 'find')
                            browser_from.click()
                            print("商品コードを入力して検索")
                            time.sleep(3)
                        except:
                            print("※※※ 商品コードを入力できませんでした")
                            print()
                            time.sleep(2)

                        #--------------------------------------        

                        # 商品一覧から商品コードが一致しているURLを抽出
                        html_content = browser.page_source
                        soup = BeautifulSoup(html_content, 'html.parser')

                        tabletags = soup.find_all('table', id='table-02')

                        for tabletag in tabletags:
                            tr_tags = tabletag.find_all('tr')
                            for tr_tag in tr_tags:
                                td_tags = tr_tag.find_all('td')
                                for td_tag in td_tags:
                                    td_text = td_tag.get_text().strip()
                                    if product_number == td_text:  # 先頭のゼロを取り除いて比較
                                        print(f"製品番号 {product_number} が一致しました")

                                        # 下記2のようにURLを取得
                                        link_tag = tr_tag.find('a')
                                        if link_tag is not None:
                                            link = link_tag['href']
                                            print("URLを追加しました:", link)

                                            browser.get(link)
                                            time.sleep(2)
                                              
                        #-------------------------------------------
                        
                        # 商品一覧から商品コードが一致しているURLを抽出
                        try:
                            # ウィンドウが閉じられていないかを確認
                            if len(browser.window_handles) == 0:
                                print("エラー: ウィンドウが閉じられています。処理を中断します。")
                                browser.quit()
                            else:
                                html_content = browser.page_source
                                soup = BeautifulSoup(html_content, 'html.parser')

                                tabletags = soup.find_all('table', id='table-02')

                                for tabletag in tabletags:
                                    tr_tags = tabletag.find_all('tr')
                                    for tr_tag in tr_tags:
                                        td_tags = tr_tag.find_all('td')
                                        for td_tag in td_tags:
                                            td_text = td_tag.get_text().strip()
                                            if product_number == td_text:  # 先頭のゼロを取り除いて比較
                                                print(f"製品番号 {product_number} が一致しました")

                                                # 下記2のようにURLを取得
                                                link_tag = tr_tag.find('a')
                                                if link_tag is not None:
                                                    link = link_tag['href']
                                                    print("URLを追加しました:", link)

                                                    # ウィンドウがまだ有効か確認
                                                    if len(browser.window_handles) > 0:
                                                        browser.get(link)
                                                        time.sleep(2)
                                                    else:
                                                        print("エラー: ブラウザウィンドウが閉じられています。")
                        except NoSuchWindowException:
                            print("エラー: ターゲットウィンドウがすでに閉じられています。")
                            browser.quit()
                        except WebDriverException as e:
                            print(f"エラー: {e}")
                            browser.quit()
                              
                        #----------------------------------------------------------------------------
                        # 商品管理にアクセスして商品名の修正  

                        if browser.find_element(By.ID,"swname").get_attribute("src") == "https://item6.goqsystem.com/goqsku/img/main/btn_sin.jpg":
                            browser_from = browser.find_element(By.ID,"swname")
                            time.sleep(1)
                            browser_from.click()
                            print("個別に設定するを押しました\n")
                        else:
                            print("個別設定になっています\n")

                        # 商品名を取得
                        value_content = None
                        replaced_text = None

                        html_content = browser.page_source
                        soup = BeautifulSoup(html_content, 'html.parser')

                        table_tags = soup.find_all('table', id='table-01')

                        for table_tag in table_tags:
                            tr_tags = table_tag.find_all('tr')
                            for tr_tag in tr_tags:
                                div_tags = tr_tag.find('div')
                                if div_tags:
                                    input_tag = div_tags.find('input', {'name': 'name'})
                                    if input_tag:
                                        value_content = input_tag.get('value', '')
                                        print(f"商品管理のタイトル: {value_content}")
                                        print()

                                        #---------------------------------------------------------------------------------------

                                        # 商品名の置換
                                        replaced_text = re.sub(r"商品名：.*?<br>", f"商品名：{value_content}<br>", data_content)
                                        # バリエーション部分の削除（項目選択肢は残す）
                                        replaced_text = re.sub(r"バリエーション.*?", "", replaced_text)

                                        print(replaced_text)
                                        print()

                        #---------------------------------------------------------------------------------------

                        # 再度個別ページにアクセス
                        re_url = yurl
                        browser.get(re_url)
                        time.sleep(1)

                        # 既存の出荷処理中のエックスパスとは一文字違うので注意
                        try:
                            browser_from = browser.find_element(By.XPATH, '//*[@id="order_from"]/table[4]/tbody/tr/td/table/tbody/tr/td[3]/table/tbody/tr/td[3]/span/a')
                            browser_from.click()
                            time.sleep(1)
                            print("1 注文内容修正ボタンを押しました")

                        except:
                            print("1 ※※※ 注文内容修正ボタンが押せませんでした")

                        #-----------------------------------------------

                        try:
                            element = browser.find_element(By.NAME, "B003")
                            element.click()
                            time.sleep(3)
                            print("2 修正ボタンを押しました")
                        except:
                            print("2 ※※※ 修正ボタンが押せませんでした")

                        #-----------------------------------------------                     

                        # product_sku に格納されている SKU と extracted_data_list の一致する項目を検索
                        extracted_text = None
                        shipping_info = None
                            
                        # extracted_data_list から一致する項目を探す
                        for data in extracted_data_list:
                            # extracted_text と product_sku をゼロパディングを考慮して比較
                            if data['custom_extracted_text'].lstrip("0") == product_sku.lstrip("0"):  # 先頭のゼロを削除して比較
                                custom_extracted_text = data['custom_extracted_text']  # 一致する SKU を extracted_text に格納
                                shipping_info = data['shipping_info']  # その SKU に対応する配送情報を格納
                                print(f"一致する SKU が見つかりました: {custom_extracted_text}")
                                print(f"配送情報: {shipping_info}")
                                print()
                                break

                        #----------------------------------------------------------

                        sku_found = False  # 一致するSKUが見つかったかどうかを示すフラグ
                        sku_match1 = False
                        sku_match2 = False

                        html_content = browser.page_source
                        soup = BeautifulSoup(html_content, 'html.parser')

                        tr_tags = soup.find_all('tr')

                        for tr_tag in tr_tags:
                            if sku_found:  # 一致するSKUが見つかったらループを終了する
                                break
                            td_tags = tr_tag.find_all('td', bgcolor='#ffffff')
                            for td_tag in td_tags:
                                span_tags = td_tag.find_all('span')
                                for span_tag in span_tags:
                                    input_tags = span_tag.find_all('input')
                                    for input_tag in input_tags:
                                        # value 属性の取得
                                        input_value = input_tag.get('value', '')

                                        # 部分一致の比較処理
                                        if custom_extracted_text == input_value:  # 完全一致を確認

                                            print("※一致しました")
                                            # 一致した場合の処理
                                            sku_match1 = True

                                            # 最初のinputタグのidを取得する
                                            first_input_tag = input_tags[0]
                                            first_input_id = first_input_tag.get('id')
                                            print("Input Tag ID:---------------------------", first_input_id)

                                            sku_found = True  # 一致するSKUが見つかったことを示すフラグを設定
                                            break  # 一致したら内側のループを終了
                                            
                                    if sku_found:
                                        #print("sku_foundあり1")
                                        break  # 一致するSKUが見つかったら外側のループを終了
                                if sku_found:
                                    #print("sku_foundあり2")
                                    break

                        #----------------------------------------------------------

                        disable = False
                            
                        # extracted_data_list から一致する項目を探す
                        for data in extracted_data_list:
                            # extracted_text と product_sku をゼロパディングを考慮して比較
                            if data['custom_extracted_text'].lstrip("0") == product_sku.lstrip("0"):  # 先頭のゼロを削除して比較
                                custom_extracted_text = data['custom_extracted_text']  # 一致する SKU を extracted_text に格納
                                shipping_info = data['shipping_info']  # その SKU に対応する配送情報を格納
                                #print(f"一致する SKU が見つかりました: {custom_extracted_text}")
                                #print(f"配送情報: {shipping_info}")
                                break

                        # 一致する SKU が見つからなかった場合の処理
                        if custom_extracted_text is None:
                            print("一致する SKU が見つかりませんでした。")
                            print(f"extracted_text: {custom_extracted_text}")
                            print()
                        else:
                            # sku_found フラグの初期化
                            sku_found = False  # 一致するSKUが見つかったかどうかを示すフラグ

                            # HTMLコンテンツを解析
                            html_content = browser.page_source
                            soup = BeautifulSoup(html_content, 'html.parser')

                            # 商品リストの tr タグを取得してループ処理
                            tr_tags = soup.find_all('tr')

                            # ループ処理して SKU を探す
                            for tr_tag in tr_tags:
                                if sku_found:  # 一致するSKUが見つかったらループを終了する
                                    break

                                # td タグを取得
                                td_tags = tr_tag.find_all('td', bgcolor='#ffffff')

                                for td_tag in td_tags:
                                    # span タグを取得
                                    span_tags = td_tag.find_all('span')

                                    for span_tag in span_tags:
                                        # input タグを取得 (SKU 管理番号が格納されている)
                                        input_tags = span_tag.find_all('input')

                                        for input_tag in input_tags:
                                            input_value = input_tag.get('value', '')

                                            # extracted_text と一致するか確認
                                            if input_value == custom_extracted_text:
                                                print(f"※一致しました: {input_value}")

                                                # 一致したSKUの span_tag 内の textarea を処理
                                                textarea_tag = span_tag.find('textarea')
                                                if textarea_tag:
                                                    textarea_id = textarea_tag.get('id')
                                                    print(f"Textarea ID:--------------------------- {textarea_id}")

                                                    # 'disabled' 属性があるか確認
                                                    if 'disabled' in textarea_tag.attrs:
                                                        print("※※※ この textarea は disabled です")
                                                        
                                                        # 同じ階層で "rakuten_selected_choice" が含まれる textarea を探す
                                                        sibling_textareas = span_tag.find_all('textarea')  # 同じ span タグ内のすべての textarea を取得
                                                        for sibling_textarea in sibling_textareas:
                                                            sibling_id = sibling_textarea.get('id')
                                                            sibling_name = sibling_textarea.get('name')

                                                            # "rakuten_selected_choice" を含む name 属性を持つ textarea を探す
                                                            if sibling_name and "rakuten_selected_choice" in sibling_name:
                                                                textarea_id = sibling_id  # textarea_id を更新
                                                                print(f"次に使用する Textarea ID: {textarea_id}")
                                                                break
                                                        else:
                                                            print("※※※ 'rakuten_selected_choice' に対応する textarea が見つかりませんでした")
                                                            
                                                #---------------------------------------------------------------------------------------------
                                                        
                                                else:
                                                    print("※※※ textareaがありません")

                                                sku_found = True  # 一致したSKUが見つかったフラグを設定
                                                break  # 一致したSKUが見つかったら内側のループを終了する

                                        if sku_found:
                                            break  # 一致するSKUが見つかったら外側のループを終了する

                                    if sku_found:
                                        break  # さらに外側のループも終了する

                        #----------------------------------------------------------
                        
                        print()
                        print('shipping_info:',shipping_info)
                        print()

                        if sku_match1:
                            textarea_xpath = f'//*[@id="{first_input_id}"]'
                            #textarea_xpath = f'//*[@id="ia6[0][{i}]"]'
                            element = browser.find_element(By.XPATH, textarea_xpath)

                            # 要素からテキストを取得
                            value_attribute = element.get_attribute("value")
                            #print(value_attribute)

                            # ※※※ 本来は包装紙の場合はtrureが代入されて、iに1が代入されるので、このコードが使われることはないが一応記述
                            if value_attribute == "包装紙":
                                print("※※※ valueの値が\"包装紙\"です。以降の処理をスキップするので確認してください")

                            else:
                                # iの部分は、変数giftwrapがTrureの場合は1スタートでギフト項目を省き、通常は0スタート
                                try:
                                    #textarea_xpath = f'//*[@id="ia6[0][{i}]"]'
                                    textarea_xpath = f'//*[@id="{first_input_id}"]'
                                    element = browser.find_element(By.XPATH, textarea_xpath)

                                    current_text1 = element.get_attribute("value")
                                    print()
                                    print("3 変更前情報を取得")
                                    print()
                                    print(current_text1)

                                    element.clear()
                                    time.sleep(1)
                                    #print(f"3 商品名を削除しました")
                                except:
                                    print("3 ※※※ 商品名を削除できませんでした")
                                    print("\n\n")

                                #----------------------------------------------------------
                                
                                sku_nashi = True
                                
                                try:
                                    # テキストエリアを検索して内容を更新します
                                    textarea_xpath = f'//*[@id="{textarea_id}"]'  # XPathの生成を修正

                                    # 在庫連携されていない場合もあるため、照合用にエックスパスを取得して最後の照合で使用
                                    order_list.append(textarea_xpath)

                                    element = browser.find_element(By.XPATH, textarea_xpath)

                                    # テキストエリアから現在のテキストを取得
                                    current_text2 = element.text

                                    print()
                                    print(current_text2)
                                    print()
                                    
                                    #------------------------------------------------
                                    
                                    # 重複チェック
                                    # "項目選択肢"が含まれているかチェック
                                    if re.search(r"項目選択肢", current_text2):
                                        sku_nashi = False
                                        print("すでに書き換え済みの可能性があるので真偽値をFalseにします")
                                        print()
                                    else:
                                        sku_nashi = True

                                    #------------------------------------------------ 

                                    # 最初の'<br>'以降のテキストを残して、それ以前のテキストを削除
                                    match = re.search(r'<br>', current_text2)
                                    match2 = re.search(r'即日発送', current_text2)
                                    match3 = re.search(r'お取り寄せ', current_text2)

                                    if match:
                                        index = match.start()
                                        replaced_text = replaced_text + "\n" + current_text2[index + 4:]

                                        # 追記部分だけ格納して、最後の照合の時に一致している部分を削除
                                        collation = current_text2[index + 4:]
                                        print("※ 照合時の削除ワード:\n", collation)
                                        print()
                                        collations.append(collation)

                                        element.clear()
                                        element.send_keys(replaced_text)
                                            
                                        #------------------------------------------------ 

                                        print()
                                        print("整形前（入力内容）: \n", replaced_text)
                                        print()

                                        # 結果を出力します
                                        print("4_1 <br>以降のテキストを入力しました")

                                        print('\nmatch 1\n')

                                    elif match2:
                                        if match2:
                                            replaced_text = replaced_text + "<br>" + current_text2
                                            
                                            element.clear()
                                            element.send_keys(replaced_text)

                                            #------------------------------------------------ 

                                            print()
                                            print("整形前（入力内容）: \n", replaced_text)
                                            print()

                                            collation = current_text2
                                            print("※ 照合時の削除ワード:\n", collation)
                                            print()
                                            collations.append(collation)

                                            print("4_2 即日発送に<br>を追記してテキスト入力")   

                                        else:
                                            print("4_3 ※※※ 即日発送　が正常に追記できませんでした")

                                        print('\nmatch 2\n')

                                    elif match3:
                                        if match3:
                                            replaced_text = replaced_text + "<br>" + current_text2

                                            element.clear()
                                            element.send_keys(replaced_text)

                                            #------------------------------------------------ 

                                            print()
                                            print("整形前（入力内容）: \n", replaced_text)
                                            print()

                                            collation = current_text2
                                            print("※ 照合時の削除ワード:\n", collation)
                                            print()
                                            collations.append(collation)
                                            print("4_4 お取り寄せ〜に<br>を追記してテキスト入力")

                                        else:
                                            print("4_5 ※※※ お取り寄せ〜が正常に追記できませんでした")

                                        print('\nmatch 3\n')

                                    else:
                                        print("4 ※※※ 該当の項目が見つかりませんでした")
                                        element.clear()
                                        element.send_keys(replaced_text)
                                            
                                        #------------------------------------------------        

                                        print()
                                        print("整形前（入力内容）: \n", replaced_text)
                                        print()
                                        print("4_7 そのままテキストを入力しました")

                                except:
                                    print("4_8 ※※※ テキスト入力できませんでした")
                                    sku_nashi = False 

                        else:
                            print("※※※ 商品タイトルの情報を取得できませんでした")

                        #----------------------------------------------------------                    
    
                        if sku_nashi:
                            # 既存の保存ボタンのエックスパスとは一文字違うので注意
                            try:
                                browser_from = browser.find_element(By.XPATH, '//*[@id="orderform"]/div/div[2]/table[2]/tbody/tr[1]/td/input[2]')
                                browser_from.click()
                                print("5_1 この内容で保存するを押しました")
                            except:
                                browser_from = browser.find_element(By.XPATH, '//*[@id="orderform"]/table[6]/tbody/tr[1]/td/input[2]')
                                browser_from.click()
                                print("5_2 この内容で保存するを押しました")
                                
                            #----------------------------------------------
                            
                            time.sleep(2)
                            
                            try:
                                browser_from = browser.find_element(By.XPATH, '//*[@id="js-btnPageTop"]')
                                browser_from.click()
                                print("TOPボタンを押しました")
                            except:
                                print("※※※ TOPボタンボタンが押せませんでした")
                            
                            time.sleep(1)

                            #-----------------------------------------------

                            try:
                                browser_from = browser.find_element(By.XPATH, '/html/body/table[4]/tbody/tr/td/strong/a')
                                browser_from.click()
                                print("6 受注番号を押しました")
                            except:
                                print("6 ※※※ 受注番号を押せませんでした")

                            #-----------------------------------------------   

                            try:
                                text = " ※済み "
                                # ひとことメモに記載
                                element = browser.find_element(By.XPATH, '//*[@id="a9"]')
                                # 改行
                                element.send_keys(text)
                                print()
                                print("メモに ※済み を記入")
                                print()

                            except:
                                print("※※※ メモに 済み を入力できませんでした")

                            # javascriptを使ってスクロールダウン
                            browser.execute_script("window.scrollBy(0, -2400);")  # 200ピクセル下にスクロール
                            print("上にスクロール")

                            time.sleep(2)

                            #-----------------------------------------------

                            try:
                                browser_from = browser.find_element(By.XPATH, '//*[@id="a6"]')
                                browser_from.click()
                                print("7 受注ステータスを押しました")
                            except:
                                print("7 ※※※ 受注ステータスを押せませんでした")

        #---------------------------------------------------------------------------------------
        # ステータス変更箇所　2

                            try:                        
                                browser_from = browser.find_element(By.XPATH, '//*[@id="a6"]/option[15]')
                                browser_from.click()
                                print("8 書き換え完了BOXを押しました")
                            except:
                                print("8 ※※※ 書き換え完了BOXを押せませんでした")

                            try:
                                browser_from = browser.find_element(By.XPATH, '//*[@id="order_from"]/table[8]/tbody/tr/td/input[1]')
                                browser_from.click()
                                print("9 入力内容を反映するを押しました")
                                print()

                            except:
                                print("9 ※※※ 入力内容を反映を押せませんでした")
                                print()

                            print("-" * 8)
                            print()
                         
                        #-----------------------------------------------
                        
                        else:
                            print()
                            print("※※※ 真偽値がFalseで重複の可能性があるので、保存しませんでした")
                            print("※※※ チェック必要 ※※※")
                            print()
                            print()

                except TimeoutException:
                    # タイムアウト例外が発生した場合のエラーハンドリング
                    print("ページの読み込みがタイムアウトしました。")
           
            #---------------------------------------------------------------------------------------
            #在庫連携のURLがない場合、ステータスを変更
            if not url_list:
                    
                browser.get(yurl)
                time.sleep(1)

                # 以下のコードを追加して修正します
                browser_from = browser.find_element(By.XPATH, '//*[@id="a6"]')
                browser_from.click()
                print("※ 受注ステータスを押しました")

    #---------------------------------------------------------------------------------------
    # ステータス変更箇所　3

                try:                        
                    browser_from = browser.find_element(By.XPATH, '//*[@id="a6"]/option[15]')
                    browser_from.click()
                    print("書き換え完了BOXを押しました")
                except:
                    print("※※※ 書き換え完了BOXを押せませんでした")

                try:
                    browser_from = browser.find_element(By.XPATH, '//*[@id="order_from"]/table[8]/tbody/tr/td/input[1]')
                    browser_from.click()
                    print("※ 入力内容を反映するを押しました")
                except:
                    print("※※※ 入力内容を反映するを押せませんでした")
                    
                print("※※※ 在庫連携のURLがないので処理を終了")
                    
                # 処理終了時間
                # 現在の日付と時間を取得
                from datetime import datetime
                now = datetime.now()
                print()
                formatted_date = now.strftime("%m/%d")
                formatted_time = now.strftime("%H:%M")
                print("処理時刻:", formatted_date, formatted_time)
                print("-" * 24)
                print("\n\n\n")

                print()
                print()
                print()
                print()
                continue  # 処理をスキップして次のループに進む
            
            else:
                print()
            
            #---------------------------------------------------------------------------------------

            print("\n※※※\nここから商品名を再度チェック （取得してある在庫連携のURLを再表示させてリストに格納）")
            ex_texts = []
            text_list = []

            # ここから商品名などが一致するか確認　
            #---------------------------------------------------------------------------------------

            # 在庫連携にアクセス
            url_login = url
            browser.get(url_login)
            time.sleep(2)

            try:
                element = browser.find_element(By.ID, "login_id")
                element.clear()
                element.send_keys(USER1)
                element = browser.find_element(By.ID, "login_pw")
                element.clear()
                element.send_keys(PASS1)
                browser_form = browser.find_element(By.XPATH, '//*[@id="loginform"]/div/div/div[1]/input')
                browser_form.click()
                time.sleep(2)
            except NoSuchElementException:
                pass

            try:
                element = browser.find_element(By.ID, "seq_id")
                element.clear()
                element.send_keys(USER2)
                element = browser.find_element(By.ID, "seq_pw")
                element.clear()
                element.send_keys(PASS2)
                browser_from = browser.find_element(By.XPATH, '//*[@id="loginform"]/div/div/div[2]/input')
                browser_from.click()
                time.sleep(2)
            except NoSuchElementException:
                pass

            from selenium.common.exceptions import TimeoutException
            
            ex_texts = None
            ex_texts = []

            # 取得したURLを使用して処理を繰り返す
            for i, url in enumerate(url_list):
                url_login = url
                browser.get(url_login)
                time.sleep(3)

                try:
                    # ページが完全に読み込まれるのを待つ
                    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

                    # ページのHTMLコンテンツを取得
                    html = browser.page_source
                    # BeautifulSoupを使用してHTMLを解析
                    soup = BeautifulSoup(html, 'html.parser')
                    # <td>タグを検索して目的の要素を取得
                    td_element = soup.find('td', class_='shop-sku-red sku')

                    if td_element is None:
                        # 目的の要素が見つからない場合はスキップする
                        print("※ 情報がなかったので処理をスキップします")

                        browser.get(yurl)
                        time.sleep(1)

                        print()
                        print()
                        print()
                        print()
                        continue

                    else:
                        # <span>タグのdata-content属性を取得
                        data_content = td_element.find('span')['data-content']

                        # 商品管理番号(商品URL)：から<br>までの行を省く
                        start_index = data_content.find('商品管理番号（商品URL）：')
                        end_index = data_content.find('<br>', start_index)
                        data_content = data_content[:start_index] + data_content[end_index + len('<br>'):]

                        # バリエーション項目選択肢3からバリエーション項目選択肢6までの行を省く
                        variation_start = data_content.find('バリエーション項目選択肢3')
                        variation_end = data_content.find('バリエーション項目選択肢6：', variation_start)
                        data_content = data_content[:variation_start] + data_content[variation_end + len('バリエーション項目選択肢6：'):]

                        #------------------------------------------
                        
                        # 商品管理のタイトルに修正されているので、商品名から<br>までを削除
                        pattern = re.compile(r"商品名：.*?<br>")
                        # パターンに一致する部分を削除
                        result = re.sub(pattern, "", data_content)

                        #------------------------------------------

                        # バリエーション部分の削除（項目選択肢は残す）
                        data_content = re.sub(r"バリエーション.*?", "", result)

                        #------------------------------------------

                        data_content = "\n".join(line for line in data_content.splitlines() if line.strip())

                        # テキスト情報を表示
                        print(data_content)
                        print()

                        ex_texts.append(data_content)
                        time.sleep(2)

                except TimeoutException:
                    # タイムアウト例外が発生した場合のエラーハンドリング
                    print("ページの読み込みがタイムアウトしました。")

            print(ex_texts)
            print()

            # 在庫連携されている場合は以降の処理を実行
            #---------------------------------------------------------------------------------------
            # td_elementだと最後のループ処理で連携されていないと、全体の照合に入らないので、前回の処理に連携されている商品があればdata_contentに入っているので、data_contentを使う
            if data_content:

                # 再度個別ページにアクセス
                re_url = yurl
                browser.get(re_url)
                time.sleep(3)            

                try:
                    # 楽天の場合
                    browser_from = browser.find_element(By.XPATH, '//*[@id="order_from"]/table[4]/tbody/tr/td/table/tbody/tr/td[3]/table/tbody/tr/td[3]/span/a')
                    browser_from.click()
                    time.sleep(2)
                    print()
                    print("--------------------------- 注文内容修正ボタンを押しました")

                except:
                    print("--------------------------- ※※※注文内容修正ボタンが押せませんでした")

                try:
                    element = browser.find_element(By.NAME, "B003")
                    element.click()
                    time.sleep(2)
                    print("--------------------------- 修正ボタンを押しました")
                    print()
                except:
                    print("--------------------------- ※※※修正ボタンを押せませんでした")
                    print()

    # ----------------------------------------

    # 楽天対応バージョン

                print("\n※※※\n修正した注文内容を再度開いてリストに格納して照合")

                try: 
                    # テキストエリアのテキストを抽出
                    html_content = browser.page_source
                    soup = BeautifulSoup(html_content, 'html.parser')

                    # テキストを格納するための変数
                    text_list = []

                    # 全ての textarea タグを取得してテキストを変数に格納
                    textarea_tags = soup.find_all('textarea')

                    # for textarea_tag, collation in zip(textarea_tags, collations):
                    for textarea_tag in textarea_tags:
                        textarea_text = textarea_tag.get_text()
                        print()
                        print("-" * 8)
                        print()
                        print('テキストエリアの値：\n', textarea_text)
                        print()

                        # "ラッピング"のみの記述がある場合はスキップ
                        if textarea_text.strip() == "ラッピング":
                            continue

                        # 在庫連携されていない場合、書換え前の内容が照合するリストに格納されているので、条件分岐
                        if "商品名：" in textarea_text:

                            # 商品名から<br>までの部分を削除
                            pattern = re.compile(r"商品名：.*?<br>\n?")
                            textarea_text = re.sub(pattern, "", textarea_text)
                            #print('商品名を削除：\n', textarea_text)
                            #print()

                            #------------------------------------------------------
                            
                            # 正規表現でい商品名からいっきに抽出ができないので、一行ずつ抽出して変数に格納する
                            if "商品番号" in textarea_text:    
                                pattern = r'商品番号：(.*?)<br>\s*SKU管理番号：(.*?)<br>\s*項目選択肢1：(.*?)<br>\s*項目選択肢2：(.*?)<br>'
                                matches = re.search(pattern, textarea_text, re.DOTALL)

                                if matches:
                                    textarea_text = f"商品番号：{matches.group(1)}<br>\nSKU管理番号：{matches.group(2)}<br>\n項目選択肢1：{matches.group(3)}<br>\n項目選択肢2：{matches.group(4)}<br>"
                                    text_list.append(textarea_text)
                                    print("整形後: \n", textarea_text)
                                    print()

                                else:
                                    text_list.append(textarea_text)
                                    print("無整形: \n", textarea_text)
                                    print()

                            else:
                                print('商品番号の文字がないので、テキスト内容をそのまま保持')

                            #------------------------------------------------------
                
                        else:
                            print()
                            print("※※※ '商品名〜' がないので格納しませんでした")
                            print()

                    #------------------------------------------

                    # 最終的なテキストを表示
                    print(text_list)
                    print()

                    # print("除外ワードリスト:\n", collations)
                    print()
                except:
                    print("テキストを抽出できませんでした") 

                #----------------------------------------

                # あらかじめ用意されたデータとテキストエリアの内容を比較
                if ex_texts is not None and text_list is not None:
                    if ex_texts == text_list:
                        print("※※※ 内容が一致しています")

                        try:
                            browser_from = browser.find_element(By.XPATH, '/html/body/table[4]/tbody/tr/td/strong/a')
                            browser_from.click()
                            print("\n\n\n")        
                        except:
                            print("※※※ 受注番号を押せませんでした\n\n\n\n\n")

                    else:
                        print("※※※ 内容が一致しません")

                        try:
                            browser_from = browser.find_element(By.XPATH, '/html/body/table[4]/tbody/tr/td/strong/a')
                            browser_from.click()
                            print("\n\n\n\n\n")     
                        except:
                            print("※※※ 受注番号を押せませんでした\n\n\n\n\n")

                        #----------------------------------------

                        try:
                            # 発送日情報をひとことメモに記載
                            element = browser.find_element(By.XPATH, '//*[@id="a9"]')
                            # 改行
                            newline = "\n"
                            element.send_keys('※ ')
                            element.send_keys('商品名が一致していないので注文内容を確認してください')
                            element.send_keys(newline)
                            print('※※※ 商品名が一致していないので注文内容を確認してください')

                            # 入力内容を反映するをクリック　
                            update_button = browser.find_element(By.XPATH, '//*[@id="order_from"]/table[8]/tbody/tr/td/input[1]')
                            update_button.click()
                            print("入力内容を反映するをクリック")
                            print("\n\n\n\n\n")
                        except:
                            print("メモに保存できませんでした")
                            print("\n\n\n\n\n")

                #----------------------------------------

                else:
                    if ex_texts is None and text_list is not None:
                        print("※※※ ex_texts が空です")
                    elif ex_texts is not None and text_list is None:
                        print("※※※ text_list が空です")
                    else:
                        print("※※※ 変数が両方とも空です")

                    try:
                        browser_from = browser.find_element(By.XPATH, '/html/body/table[4]/tbody/tr/td/strong/a')
                        browser_from.click()
                        print("\n\n\n\n\n")

                    except:
                        print("※※※ 受注番号を押せませんでした\n\n\n\n\n")

                    #----------------------------------------

                    try:
                        # 発送日情報をひとことメモに記載
                        element = browser.find_element(By.XPATH, '//*[@id="a9"]')
                        # 改行
                        newline = "\n"
                        element.send_keys('※ ')
                        element.send_keys('表示エラー。下代に確認してください。')
                        element.send_keys(newline)
                        print('※※※ 表示エラー。')

                        # 入力内容を反映するをクリック　
                        update_button = browser.find_element(By.XPATH, '//*[@id="order_from"]/table[8]/tbody/tr/td/input[1]')
                        update_button.click()
                        print("入力内容を反映するをクリック")
                        print("\n\n\n\n\n")
                    except:
                        print("メモに保存できませんでした")
                        print("\n\n\n\n\n")

            else:
                print("在庫連携されていないので再チェックしませんでした")
                
            #----------------------------------------

            # 処理終了時間
            # 現在の日付と時間を取得
            from datetime import datetime
            now = datetime.now()
            print()
            formatted_date = now.strftime("%m/%d")
            formatted_time = now.strftime("%H:%M")
            print("処理時刻:", formatted_date, formatted_time)
            print("-" * 24)
            print("\n\n\n")
          
#----------------------------------------

# 処理終了時間
from datetime import datetime

# 現在の日付と時間を取得
now = datetime.now()
print()
formatted_date = now.strftime("%m/%d")
formatted_time = now.strftime("%H:%M")
print("処理完了:", formatted_date, formatted_time)
print("-" * 80)
print("\n\n\n")


browser.quit()




