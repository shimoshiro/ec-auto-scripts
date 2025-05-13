#!/usr/bin/env python
# coding: utf-8

# BUYMAの受注内容や配送情報をメモに残し、在庫数の変更
# 1時間毎の定期実行

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

from datetime import datetime
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
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import subprocess
import unicodedata
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

# **ローカルでもヘッドレスにするか設定**
use_headless = True  # **True: ヘッドレスモード, False: GUIモード（デバッグ用）**

# ChromeOptionsの設定
options = Options()

# 画面表示させたい場合は下記を表示させる
#if is_ec2:

# **ヘッドレスモードの設定**
if is_ec2 or use_headless:
    # EC2環境の場合はヘッドレスモード
    options.add_argument("--headless")  # ヘッドレスモード
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")  # 必要に応じて無効化
    print("ヘッドレスモードを使用します")
else:
    # ローカル環境の場合は通常のGUIモード
    options.add_argument("--window-size=1320,1280")  # ウィンドウサイズを指定
    print("ローカル環境で動作中: GUIモードを使用します")

# ChromeDriverの設定
service = Service(selected_path)
browser = webdriver.Chrome(service=service, options=options)

#----------------------------------------------　 

USER1 = "your_user_id_1"
PASS1 = "your_password_1"
USER2 = "your_user_id_2"
PASS2 = "your_password_2"

# 在庫管理ページへアクセス
url_login = "http://stock2.goqsystem.com/?nav_id=stockSituation"
browser.get(url_login)
time.sleep(1)

element = browser.find_element(By.ID, "login_id")
element.clear()
element.send_keys(USER1)
element = browser.find_element(By.ID, "login_pw")
element.clear()
element.send_keys(PASS1)

browser_from = browser.find_element(By.XPATH, '//*[@id="loginform"]/div/div/div[1]/input')
time.sleep(1)
browser_from.click()

element = browser.find_element(By.ID, "seq_id")
element.clear()
element.send_keys(USER2)
element = browser.find_element(By.ID, "seq_pw")
element.clear()
element.send_keys(PASS2)

browser_from = browser.find_element(By.XPATH, '//*[@id="loginform"]/div/div/div[2]/input')
time.sleep(1)
browser_from.click()

# バイマにログイン
USER1 = "your_user_address"
PASS1 = "your_password"

url_login = "https://www.buyma.com/my/orders/"
browser.get(url_login)
time.sleep(1)

element = browser.find_element(By.ID, "txtLoginId")
element.clear()
element.send_keys(USER1)
element = browser.find_element(By.ID, "txtLoginPass")
element.clear()
element.send_keys(PASS1)
browser_from = browser.find_element(By.ID, "login_do")
browser_from.click()
time.sleep(1)

try:
    time.sleep(2)
    # 詳細情報の編集ボタンをクリック
    browser_from = browser.find_element(By.ID, 'driver-highlighted-element-stage')
    browser_from.click()
    print("ポップ画面をクリック")
except:
    # ボタンが押せなかった場合の処理
    print("ポップがないのでスキップします")

try:
    time.sleep(3)
    # 詳細情報の編集ボタンをクリック
    browser_from = browser.find_element(By.CSS_SELECTOR, ".driver-close-btn")
    browser_from.click()
    print("スキップをクリック")
except:
    time.sleep(3)
    # ボタンが押せなかった場合の処理
    print("スキップボタンがありませんでした")
   
try:
    # キーワード欄を取得
    element = browser.find_element(By.XPATH, '//*[@id="js-form-highlight"]/form/div[1]/div[1]/div[2]/dl/dd/div/div[1]/input')

    # クリック対象要素が画面の上部に来るようにスクロール
    browser.execute_script("arguments[0].scrollIntoView({block: 'start'});", element)
    print("下にスクロール")
    time.sleep(3)  # スクロールが完了するのを待つ

    # クリック
    element.click()
    print("キーワード欄をクリック")
    
except:
    # ボタンが押せなかった場合の処理
    print("キーワード欄をクリックできませんでした")
    print()
    
    browser.execute_script("window.scrollBy(0, -600);")
    print("上にスクロール")
    # キーワードをクリックして件数表示欄を上にスクロールしてトップへボタンと被らないようにする
    element = browser.find_element(By.XPATH, '//*[@id="js-form-highlight"]/form/div[1]/div[1]/div[2]/dl/dd/div/div[1]/input')
    # 要素をクリック
    element.click()
    print("キーワード欄をクリック")
    print()

try:
    time.sleep(1)
    checkbox = browser.find_element(By.XPATH, '//*[@id="content"]/div/div/div[4]/div/span/div')
    checkbox.click()
    print("件数表示をクリック")
except:
    # ボタンが押せなかった場合の処理
    print("件数表示をクリックできませんでした")
    
    browser.execute_script("window.scrollBy(0, -600);")
    print("上にスクロール")
    checkbox = browser.find_element(By.XPATH, '//*[@id="content"]/div/div/div[4]/div/span/div')
    checkbox.click()
    time.sleep(2)
    print("件数表示をクリック")
    
try:
    time.sleep(1)
    # クリックする要素を表示するために要素までスクロール
    checkbox = browser.find_element(By.XPATH, '//*[@id="content"]/div/div/div[4]/div/span/div/ul/li[3]')
    actions = ActionChains(browser)
    actions.move_to_element(checkbox).perform()
    # 要素をクリック
    checkbox.click()
    print("100件表示を選択")
    time.sleep(1)
except:
    # ボタンが押せなかった場合の処理
    print("100件表示を選択できませんでした")

# 受注日を選択
datebox = browser.find_element(By.CSS_SELECTOR, ".bmm-c-text-field.sell-term.bmm-u-typo-size80")
datebox.click()

button = browser.find_element(By.XPATH, '//div[contains(@class, "react-datepicker__day--today")]')
button.click()
print("日付を選択")
time.sleep(1)

# 受注にチェック
checkbox = browser.find_element(By.NAME, "statuses.placed")
checkbox.click()
print("受注にチェック")
time.sleep(1)

# ポップが出た時のために、取引IDを一番上までスクロールしてクリック
element = browser.find_element(By.XPATH, '//*[@id="js-form-highlight"]/form/div[1]/div[1]/div[3]/dl/dd/div/textarea')
browser.execute_script("arguments[0].scrollIntoView();", element)
# 取引IDをクリック
element.click()
time.sleep(1)

browser_from = browser.find_element(By.XPATH, '//*[@id="js-form-highlight"]/form/div[2]/button')
browser_from.click()
print("検索をクリック")
time.sleep(6)

# iframeでクーポンなどのバナーが表示された場合
try:
    # iframeを見つける
    iframe = WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.TAG_NAME, 'iframe')))

    # iframeに切り替える
    browser.switch_to.frame(iframe)

    # iframe内の要素を見つけてクリック
    close_button_element = WebDriverWait(browser, 5).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, ".close_button"))
    )
    close_button_element.click()
    print("バナーをクリック")
    
except:
    print("バナーがありませんでした")
    
browser.switch_to.default_content()

while True:
    # 現在開いているページのURLを取得
    # ページが複数ある場合、遷移するために開いているページのURLを取得し、メイン処理後に次へボタンを取得
    current_url = browser.current_url

    if current_url:
        print("Current URL:", current_url)
    else:
        print("Failed to retrieve the current URL.")

# -----------------------------------------------------------------------
# ここからメイン処理
# -----------------------------------------------------------------------
    
    # メモの中に処理しないテキストがないかチェック
    html_content = browser.page_source
    soup = BeautifulSoup(html_content, 'html.parser')
    
    extracteds = []

    blocks2 = soup.find_all('tr', class_='orders-table-tr-main')
    
    # 一致するテキストがある場合、その親要素にフラれてる取引IDを取得してリストに格納
    for block in blocks2:
        element = block.find('a', class_='MyCont_PlaceholderLink')

        if element and ('※' in element.text or '入荷待ち' in element.text or '提案' in element.text or '在庫切れ' in element.text or '買付まだ' in element.text):
            parent_class = block['class']
            target_class = [c for c in parent_class if c.startswith('trade_row_dt_tr_')]
            if target_class:
                extracted_class = int(re.search(r'\d+', target_class[0]).group())
                extracteds.append(extracted_class)

    #-----------------------------------------------------------------------

    # 変数extractedsにintのリストを格納するために、appendのループの外に移動させます
    extracteds = [int(item) for item in extracteds]
    print(extracteds)

    total_value = None
    
    # 色・サイズの情報を取得
    common_parent = soup.find('table', class_='n_details_box mg_t15 orders-table')  # block.find_parentをsoup.findに変更します
    blocks = common_parent.find_all('tr', class_=['orders-table-tr-sub', 'trade_row'])
    for i in range(len(blocks)):
        block = blocks[i]
        element = block.find('strong', class_='orders-trade-msg__title')
        parent_class2 = block.get('class')
        parent_class2 = [c for c in parent_class2 if c.startswith('dt_tr_')]
        if parent_class2:
            parent_class2 = int(re.search(r'\d+', parent_class2[0]).group())
        else:
            parent_class2 = None
        if parent_class2 not in extracteds:  # extractedsリストにparent_class2の値が含まれていない場合に処理を実行します
                   
            if i < len(blocks2):
                order_number_td = blocks2[i].find('td', class_='order_number_column')
                if order_number_td:
                    order_number = order_number_td.text.strip()
                else:
                    order_number = ""
                print()
                print("-" * 24)
                print()
                print("注文数:", order_number)

                a_tag = blocks2[i].find('a', class_='js-orders-ga-click-event')
                if a_tag:
                    tid = a_tag['href'].split('=')[1]
                    print("取引ID:", tid)

                delivery_content_span = blocks[i].find('span', class_='orders-trade-msg__content-delivery')
                if delivery_content_span:
                    delivery_content = delivery_content_span.get_text(strip=True)
                    #print("配送内容:", delivery_content)

                    if "ゆうパック" in delivery_content:
                        delivery_method = "ゆうパック"
                    elif "ゆうパケット" in delivery_content:
                        delivery_method = "ゆうパケ"
                    else:
                        delivery_method = "その他"       

                print(delivery_method)
                
            #----------------------------------------------　メモに載せるため先に情報だけ取得 下で再度取得処理あり
                
            # urlリスト
            texts = []
            purchaser_item_spans = block.find_all('span', class_='orders-trade-msg__container js-purchaser-item')
            for purchaser_item_span in purchaser_item_spans:
                full_message_show = purchaser_item_span.find('span', class_='orders-trade-msg__content-shop-full')
                if full_message_show is not None:
                    p_tags = full_message_show.find_all('p')
                    if p_tags:
                        for p_tag in p_tags:
                            text2 = p_tag.text.strip()
                            texts.append(text2)
                            print('買付先 :', text2)
                    else:
                        print("買付先: No <p> tags found")
                else:
                    print("買い付け: No element found")   
            print(texts)
            
           #-----------------------------------------------------------------------
            
            text1 = ""  # text1 の初期化

            if element is not None and '[色・サイズ]' in element.text:
                next_span = element.find_next_sibling('span', class_='orders-trade-msg__content')
                if next_span is not None:
                    text1 = next_span.text.strip()

                    if '/' in text1:
                        split_texts = text1.split('/')
                        left_text = split_texts[0].strip()
                        right_text = '/'.join(split_texts[1:]).strip()
                    else:
                        left_text = text1.strip()
                        right_text = ""

                    print("色:", left_text)
                    print("サイズ:", right_text)
                    #print("親要素のクラス:", parent_class2)
            else:
                left_text = text1.strip()
                right_text = ""

                if left_text == text1.strip() and right_text == "":
                    url_login = "https://www.buyma.com/my/orders/"
                    browser.get(url_login)

                    element = browser.find_element(By.NAME, "order_id")
                    element.clear()
                    element.send_keys(tid)
                    time.sleep(1)
                    
                    # ポップが出た時のために、取引IDを一番上までスクロールしてクリック
                    element = browser.find_element(By.XPATH, '//*[@id="js-form-highlight"]/form/div[1]/div[1]/div[3]/dl/dd/div/textarea')
                    browser.execute_script("arguments[0].scrollIntoView();", element)
                    # 取引IDをクリック
                    element.click()
                    time.sleep(1)

                    # 検索ボタンをクリック
                    browser_from = browser.find_element(By.XPATH, '//*[@id="js-form-highlight"]/form/div[2]/button')
                    browser_from.click()
                    time.sleep(2)

                    # メモボタンをクリック
                    browser_from = browser.find_element(By.XPATH, '//*[@id="js-table-highlight"]/td[11]/p/a')
                    browser_from.click()
                    time.sleep(1)
                    # elementを取得
                    time.sleep(1)
                    element = browser.find_element(By.XPATH, '//*[@id="fab-dialog"]/div[2]/form/div/div[2]/textarea')
                    # 改行
                    newline = "\n"
                    time.sleep(1)

                    element.send_keys(newline)
                    element.send_keys(newline)
                    element.send_keys('※ 色・サイズの該当なし')
                    element.send_keys("\n")
                    element.send_keys(texts)
                    
                    print('色・サイズの該当なし')

                    # 保存ボタンをクリック
                    browser_from = browser.find_element(By.XPATH, '//*[@id="fab-dialog"]/div[2]/form/div/div[4]/input[2]')
                    browser_from.click()
                    
            #-----------------------------------------------------------------------        

            # ご要望・ご相談がある場合に取得
            msg_wrap = block.find('div', class_='js-massage-wrap')
            if msg_wrap:
                # 非表示メッセージ（詳細）
                hidden_msg_span = msg_wrap.find('span', class_='orders-trade-msg__content-msg-full is-hidden js-full-massage is-left')
                if hidden_msg_span:
                    hidden_msg = hidden_msg_span.get_text(strip=True)
                    print(f"ご要望・ご相談:【 {hidden_msg} 】")
                else:
                    hidden_msg = ""
                    #print("非表示メッセージが見つかりませんでした")
            else:
                print("js-massage-wrapが見つかりませんでした")

            #-----------------------------------------------------------------------        
                    
            # urlリスト
            texts = []
            purchaser_item_spans = block.find_all('span', class_='orders-trade-msg__container js-purchaser-item')
            for purchaser_item_span in purchaser_item_spans:
                full_message_show = purchaser_item_span.find('span', class_='orders-trade-msg__content-shop-full')
                if full_message_show is not None:
                    p_tags = full_message_show.find_all('p')
                    if p_tags:
                        for p_tag in p_tags:
                            text2 = p_tag.text.strip()
                            texts.append(text2)
                            #print('買付先 :', text2)
                    else:
                        print("買付先: No <p> tags found")
                else:
                    print("買い付け: No element found")   
            
            #-----------------------------------------------------------------------
            
            if not texts:
                url_login = "https://www.buyma.com/my/orders/"
                browser.get(url_login)

                element = browser.find_element(By.NAME, "order_id")
                element.clear()
                element.send_keys(tid)
                time.sleep(1)
                
                # ポップが出た時のために、取引IDを一番上までスクロールしてクリック
                element = browser.find_element(By.XPATH, '//*[@id="js-form-highlight"]/form/div[1]/div[1]/div[3]/dl/dd/div/textarea')
                browser.execute_script("arguments[0].scrollIntoView();", element)
                # 取引IDをクリック
                element.click()
                time.sleep(1)

                # 検索ボタンをクリック
                browser_from = browser.find_element(By.XPATH, '//*[@id="js-form-highlight"]/form/div[2]/button')
                browser_from.click()
                time.sleep(2)

                # メモボタンをクリック
                browser_from = browser.find_element(By.XPATH, '//*[@id="js-table-highlight"]/td[11]/p/a')
                browser_from.click()
                time.sleep(1)
                # elementを取得
                time.sleep(1)
                element = browser.find_element(By.XPATH, '//*[@id="fab-dialog"]/div[2]/form/div/div[2]/textarea')
                # 改行
                newline = "\n"
                time.sleep(1)

                element.send_keys(newline)
                element.send_keys(newline)
                element.send_keys('※ 買付先の該当なし')
                print('買付先の該当なし')

                # 保存ボタンをクリック
                browser_from = browser.find_element(By.XPATH, '//*[@id="fab-dialog"]/div[2]/form/div/div[4]/input[2]')
                browser_from.click()

            # ------------------------------------------------------------------------------ 
            # 在庫情報を取得
            # ------------------------------------------------------------------------------

            code = texts

            # リストの要素を繰り返し処理
            for code in texts:
                # 在庫管理ページへアクセス
                url_login = "http://stock2.goqsystem.com/?nav_id=stockSituation"
                browser.get(url_login)
                time.sleep(1)
                try:
                    # 店舗選択をクリック
                    browser_from = browser.find_element(By.XPATH, '//*[@id="serch_mall"]')
                    browser_from.click()
                except:
                    pass
                try:
                    # 楽天市場をクリック
                    browser_from = browser.find_element(By.XPATH, '//*[@id="serch_mall"]/option[2]')
                    browser_from.click()
                except:
                    pass
                try:
                    # 在庫コードを入力
                    element = browser.find_element(By.NAME, "serch_key")
                    element.clear()
                    element.send_keys(code)
                except:
                    pass
                try:
                    # 検索ボタンをクリック
                    browser_from = browser.find_element(By.XPATH, '//*[@id="product--search"]/div/div/div[8]/button[1]')
                    browser_from.click()
                except:
                    pass
                
                #-------------------------------------------------

                time.sleep(3)

                html = browser.page_source
                soup = BeautifulSoup(html, 'html.parser')
                tr_elements = soup.find_all('tr')

                set_input_value = None
                combined_number = None
                # 単品在庫で在庫が0以上で、注文数が在庫を超えている時用
                zaiko_change = False

                # 完全一致したSKUを格納するリスト
                matched_skus = []
                sku = None

                # 各 tr 要素をループし、完全一致する最初のSKUを取得
                for tr in tr_elements:
                    # <td> 要素を取得
                    td_elements = tr.find_all('td')

                    # 各 td 要素のテキストを取得して正規化
                    td_texts = [unicodedata.normalize('NFKC', td.get_text(strip=True)) for td in td_elements]

                    # left_text と right_text を正規化
                    left_text_no_space = unicodedata.normalize('NFKC', left_text).replace(' ', '')
                    right_text_no_space = unicodedata.normalize('NFKC', right_text).replace(' ', '')

                    # 各 td のテキストからスペースを除去
                    td_texts_no_space = [text.replace(' ', '') for text in td_texts]

                    # left_text と right_text が含まれている行を特定
                    if left_text_no_space in td_texts_no_space and right_text_no_space in td_texts_no_space:
                        # SKU 情報を取得
                        sku_element = tr.find('td', class_="shop-sku-red sku")
                        if sku_element:
                            span_element = sku_element.find('span', {'data-content': True})
                            if span_element:
                                data_content = span_element['data-content']
                                sku_full = span_element.get_text(strip=True)
                                sku = sku_full

                                # デバッグ情報を出力
                                print(f"完全一致: {sku}")
                                
                                # skuをcombined_numberに代入
                                combined_number = sku
                                print(f"skuをcombined_numberに代入_1: {combined_number}")

                                # 完全一致したSKUをリストに追加
                                matched_skus.append(sku_full)

                        # 完全一致を1回だけ取得して処理を進める
                        break

                #----------------------------------------------------------------------

                # 完全一致したSKUを出力
                if matched_skus:
                    # 完全一致したSKUの行をチェック
                    for tr in tr_elements:
                        sku_element = tr.find('td', class_="shop-sku-red sku")
                        if sku_element:
                            sku_text = sku_element.get_text(strip=True)
                            if sku_text in matched_skus:  # 完全一致SKUの行を特定

                                # 「詳細」ボタンを確認してセット商品かを判定
                                detail_button = tr.find('input', {'type': 'button'})
                                if detail_button and detail_button.get('value') == "詳細":
                                    print("セット商品です。後続のセット商品処理に進みます。")
                                    set_input_value = True  # セット商品の場合はTrueに設定

                                    # セット商品のURLを取得して処理を追加
                                    onclick_attribute = detail_button.get('onclick', '')
                                    set_url_match = re.search(r"'(.*?)'", onclick_attribute)
                                    if set_url_match:
                                        set_url = f"https://stock2.goqsystem.com{set_url_match.group(1)}"
                                        print(f"セット商品のURL: {set_url}")
                                        # ここでセット商品の処理を実行
                                        browser.get(set_url)
                                        time.sleep(1)
                                    break  # セット商品の場合はそれ以上調べる必要がないため、ループを終了
                                    
                                #----------------------------------------------------------------------
                                    
                                else:
                                    print("セット商品ではありません。")
                                    set_input_value = False  # 非セット商品の場合はFalseに設定
                                    
                                    #セットじゃないので、取得したskuで個別ページにアクセス
                                    # 在庫管理ページへアクセス
                                    url_login = "http://stock2.goqsystem.com/?nav_id=stockSituation"
                                    browser.get(url_login)
                                    time.sleep(1)
                                    try:
                                        # 店舗選択をクリック
                                        browser_from = browser.find_element(By.XPATH, '//*[@id="serch_mall"]')
                                        browser_from.click()
                                    except:
                                        pass
                                    try:
                                        # 楽天市場をクリック
                                        browser_from = browser.find_element(By.XPATH, '//*[@id="serch_mall"]/option[2]')
                                        browser_from.click()
                                    except:
                                        pass
                                    try:
                                        # 在庫コードを入力
                                        element = browser.find_element(By.NAME, "serch_key")
                                        element.clear()
                                        element.send_keys(sku)
                                    except:
                                        pass
                                    try:
                                        # 検索ボタンをクリック
                                        browser_from = browser.find_element(By.XPATH, '//*[@id="product--search"]/div/div/div[8]/button[1]')
                                        browser_from.click()
                                    except:
                                        pass
                                
                #----------------------------------------------------------------------
                                    
                else:
                    print("完全一致するSKUが見つかりませんでした。")
                    set_input_value = False  # 完全一致SKUがない場合もFalseに設定

                # ----------------------------------------------------------------------
                # ここから在庫変更処理
                # ----------------------------------------------------------------------

                # フラグを用意して初期値をFalseに設定
                processed = False
                single_item = False
                set_zaiko = False
                zaiko_zero = False

                # ページのHTMLを取得
                html = browser.page_source
                # BeautifulSoupを使ってHTMLをパース
                soup = BeautifulSoup(html, 'html.parser')
                # tr要素を取得
                tr_elements = soup.find_all('tr')  # 全てのtr要素をリストで取得

                # left_textとright_textの値が存在しない場合のみ、skuとの比較処理を実行
                if not left_text and not right_text:
                    for tr in tr_elements:  # tr_elements をループして1つずつ処理
                        
                        td_elements = tr.find_all('td')

                        # td要素のテキストを取得して正規化
                        td_texts = [unicodedata.normalize('NFKC', td.get_text(strip=True)) for td in td_elements]
                        td_texts_no_space = [text.replace(' ', '') for text in td_texts]

                        # 完全一致SKUが含まれている行を探す
                        if td_texts_no_space:
                            # input要素を取得
                            input_element = tr.find('input', {'name': True, 'type': 'text'})

                            combined_number = sku
                            print(f"skuをcombined_numberに代入_2: {combined_number}")

                            #-------------------------------------------------------------------

                            if input_element:
                                # input要素のvalue属性を取得
                                input_value = input_element['value']
                                # input要素のname属性を取得
                                input_name = input_element['name']

                                input_value2 = int(input_value)
                                order_number = int(order_number)
                                total_value = input_value2 - order_number

                                if total_value <= 0:
                                    input_value2 = max(0, order_number)
                                    total_value = 0

                                # elementを取得
                                element = browser.find_element(By.NAME, input_name)
                                # elementの値をクリア
                                element.clear()
                                # 数字の部分をname属性に代入して送信
                                element.send_keys(total_value)

                                # valueの中の値を書き出す処理
                                print()
                                print('項目名がなく基本コードで検索')
                                print('基本コード:', sku, '在庫数:', input_value)

                                # 処理が実行されたのでフラグをTrueに設定
                                processed = True
                                print()
                                print("True1")
 
                #-------------------------------------------------------------------

                # left_textとright_textの値が存在する場合、上記の処理を実行
                elif set_input_value:
                    if not sku:
                        print("完全一致SKUが定義されていません。処理をスキップします。")
                    else:
                        for tr in tr_elements:
                            td_elements = tr.find_all('td')
                            
                            if processed:
                                print("セット商品の在庫変更処理は1回のみ実行。次の注文へ進みます。")
                                continue
                                
                            #--------------------------------------------------------------
                            
                            if not zaiko_zero:

                                # td要素のテキストを取得して正規化
                                td_texts = [unicodedata.normalize('NFKC', td.get_text(strip=True)) for td in td_elements]
                                td_texts_no_space = [text.replace(' ', '') for text in td_texts]

                                # 完全一致SKUが含まれている行を探す
                                if td_texts_no_space:
                                    input_element = tr.find('input', {'name': True, 'type': 'text'})

                                    if input_element:
                                        value = input_element.get('value', '値が見つかりません')
                                        print(f"在庫数: {value}")
                                    else:
                                        print()
                                        continue

                                    # input要素の属性を取得
                                    try:
                                        input_value = input_element.get('value', '0')
                                        input_name = input_element.get('name', '')

                                        # デバッグログ
                                        print(f"Debug: Input Name: {input_name}, Input Value: {input_value}")

                                        #------------------------------------------------
                                        # ここからロット数を取得
                                        #------------------------------------------------

                                        lot_value = 1

                                        html = browser.page_source
                                        soup = BeautifulSoup(html, 'html.parser')

                                        tr_lots = soup.find_all('tr')

                                        for tr_lot in tr_lots:
                                            td_lots = tr_lot.find_all('td')
                                            if len(td_lots) >= 12:
                                                # 12個目のtdタグの中の数字を取得
                                                lot_value = td_lots[11].get_text(strip=True)

                                        #------------------------------------------------

                                        trigger = False
                                        skip_processing = False  # スキップフラグ
                                        set_zaiko = False  # 在庫更新成功フラグを追加

                                        html = browser.page_source
                                        soup = BeautifulSoup(html, 'html.parser')
                                        tr_elements = soup.find_all('tr')

                                        values = []
                                        values_total = []

                                        # どれかの在庫が0なら処理をスキップ
                                        for tr_element in tr_elements:
                                            td_tags = tr_element.find_all('td')
                                            for td_tag in td_tags:
                                                input_tags = td_tag.find_all('input', {'type': 'text'})
                                                for input_tag in input_tags:
                                                    input_name = input_tag.get('name')
                                                    input_value = input_tag.get('value')

                                                    # input_valueがNoneや空文字の場合はスキップ
                                                    if input_value is None or input_value.strip() == "":
                                                        continue 

                                                    input_value2 = int(input_value)

                                                    # どれかの在庫が0ならスキップフラグをTrueに
                                                    if input_value2 == 0:
                                                        skip_processing = True
                                                        continue  # 0の在庫はリストに含めない

                                                    values.append(input_value2)

                                        #-----------------------------------------------------------------

                                        # セット商品のどれかが在庫0なら処理をスキップ
                                        if skip_processing:
                                            print("※※※ セット商品のどれかの在庫が0のため、処理をスキップします")

                                            # 在庫切れのメモを記録
                                            try:
                                                url_login = "https://www.buyma.com/my/orders/"
                                                browser.get(url_login)

                                                element = browser.find_element(By.NAME, "order_id")
                                                element.clear()
                                                element.send_keys(tid)
                                                time.sleep(1)

                                                # ポップが出た時のために、取引IDを一番上までスクロールしてクリック
                                                element = browser.find_element(By.XPATH, '//*[@id="js-form-highlight"]/form/div[1]/div[1]/div[3]/dl/dd/div/textarea')
                                                browser.execute_script("arguments[0].scrollIntoView();", element)
                                                element.click()
                                                time.sleep(1)

                                                # 検索ボタンをクリック
                                                browser_from = browser.find_element(By.XPATH, '//*[@id="js-form-highlight"]/form/div[2]/button')
                                                browser_from.click()
                                                time.sleep(2)

                                                # メモボタンをクリック
                                                browser_from = browser.find_element(By.XPATH, '//*[@id="js-table-highlight"]/td[11]/p/a')
                                                browser_from.click()
                                                time.sleep(1)

                                                # メモ欄に「在庫切れ」を入力
                                                element = browser.find_element(By.XPATH, '//*[@id="fab-dialog"]/div[2]/form/div/div[2]/textarea')
                                                element.send_keys('※')
                                                element.send_keys("\n")
                                                element.send_keys(combined_number)
                                                element.send_keys("\n")
                                                element.send_keys('在庫切れ')

                                                # メモを保存
                                                browser_from = browser.find_element(By.XPATH, '//*[@id="fab-dialog"]/div[2]/form/div/div[4]/input[2]')
                                                browser_from.click()

                                                set_zaiko = True

                                                print("✅ 在庫切れのメモを記録しました")
                                                
                                                zaiko_zero = True #片方が0の場合、もう片方のセット在庫の処理をしないように
                                                
                                                print()
                                            except Exception as e:
                                                print(f"⚠️ 在庫切れメモの記録中にエラーが発生しました: {e}")

                                            continue

                                        #------------------------------------------------------------------------------------------

                                        # 在庫がある場合は通常通り処理を続行
                                        for tr_element in tr_elements:
                                            td_tags = tr_element.find_all('td')
                                            for td_tag in td_tags:
                                                input_tags = td_tag.find_all('input', {'type': 'text'})
                                                for input_tag in input_tags:
                                                    input_name = input_tag.get('name')
                                                    input_value = input_tag.get('value')

                                                    if input_value is None or input_value.strip() == "":
                                                        continue 

                                                    input_value2 = int(input_value)
                                                    order_number = int(order_number)
                                                    lot_value = int(lot_value)

                                                    # ロット数をかける
                                                    set_order_number = order_number * lot_value
                                                    print('ロット数: ', lot_value)
                                                    print('注文枚数: ', set_order_number)
                                                    print()

                                                    # 在庫更新処理
                                                    total_value = max(0, input_value2 - set_order_number)
                                                    element = browser.find_element(By.NAME, input_name)
                                                    element.clear()
                                                    element.send_keys(total_value)
                                                    
                                                    #----------------------------------------------------
                                                    
                                                    # 在庫連携のチェックボックスを選択
                                                    try:
                                                        time.sleep(1)
                                                        # name属性からstock番号だけを取得
                                                        numbers = ''.join(filter(str.isdigit, input_name))
                                                        #print('stock番号:', numbers)

                                                        # value属性とstock番号が共通の為、value属性からxpathでクリック
                                                        checkbox_element = browser.find_element(By.XPATH, f"//input[@value='{numbers}']")
                                                        checkbox_element.click()
                                                        time.sleep(1)
                                                    except:
                                                        pass
                                                    
                                                    #---------------------------------------------------

                                                    print('(セット) 注文前の在庫:', input_value2)
                                                    print('(セット) 残りの在庫:', total_value)
                                                    print()

                                                    values.append(input_value2)  # 元の処理に戻して在庫数をリストに追加
                                                    values_total.append(total_value)  # 更新後の在庫数もリストに追加

                                                    # 在庫更新が成功した場合
                                                    set_zaiko = True  # ここで在庫更新が成功した場合に True にする

                                        #------------------------------------------------

                                        if values:  # もしvaluesが空でない場合
                                            input_value = min(values, key=int)  # 数値比較を適用
                                            print("valuesリストに格納されたinput_valueの最小値" ,input_value)
                                        else:
                                            print("※※※ input_valueに格納できませんでした")

                                        if values_total:
                                            total_value = min(values_total, key=int)
                                            print("values_totalリストに格納されたtotal_valueの最小値" ,total_value)
                                        else:
                                            print("※※※ total_valueに格納できませんでした")

                                        if trigger:
                                            print()
                                            print("※※※ どちらかに在庫切れがあるので、在庫数の格納する値を0にします")
                                            input_value = 0
                                            total_value = 0
                                            print('(セット) 注文前の在庫（確認）:', input_value)
                                            print('(セット) 残りの在庫（確認）:', total_value)
                                            print()

                                        #---------------------------------------------------------------

                                        # values リスト内の要素を整数に変換して、0が含まれているかどうかを検索する
                                        if 0 not in map(int, values):
                                            try:
                                                time.sleep(1)
                                                link = browser.find_element(By.XPATH, '//*[@id="product--search"]/div/div/div[3]/div/input')
                                                link.click()  # 総在庫数をクリックして反映を押せるようにする
                                                time.sleep(1)
                                            except:
                                                pass      

                                            # 在庫連携画面の文字までスクロールして、反映ボタンを表示
                                            from selenium.webdriver.common.keys import Keys

                                            def scroll_to_element(element):
                                                # スクロール先の位置までスクロールするJavaScriptコード
                                                script = """
                                                    var element = arguments[0];
                                                    element.scrollIntoView({ behavior: 'auto', block: 'center', inline: 'center' });
                                                """
                                                browser.execute_script(script, element)

                                            try:
                                                button = browser.find_element(By.XPATH, '//*[@id="stockSituation"]/div[3]/div/h1')
                                                if not button.is_displayed():
                                                    actions = ActionChains(browser)
                                                    actions.move_to_element(button).perform()
                                                    time.sleep(1)
                                                button.click()
                                                time.sleep(3)
                                            except:
                                                pass

                                            #------------------------------------------------

                                            # 反映をクリック
                                            try:
                                                browser_from = browser.find_element(By.XPATH, '/html/body/div/form/div[4]/div[1]/div[2]/button[1]')
                                                browser_from.click()
                                                time.sleep(3)
                                            except:
                                                pass

                                            #------------------------------------------------

                                            # 反映押した後のアラートをクリック
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
                                                print("セットの在庫を変更しました")

                                                # 処理が実行されたのでフラグをTrueに設定
                                                processed = True
                                                print()
                                                print("True2_1")

                                            except:
                                                # アラートが表示されなかった場合
                                                html_content = browser.page_source
                                                print("※※※ アラートが表示されませんでした")
                                                time.sleep(2)

                                        else:
                                            print("※※※ 在庫数に0が含まれているので保存しませんでした")

                                            # 取引IDで個別ページにアクセス
                                            url_login = "https://www.buyma.com/my/orders/"
                                            browser.get(url_login)

                                            element = browser.find_element(By.NAME, "order_id")
                                            element.clear()
                                            element.send_keys(tid)
                                            time.sleep(1)

                                            # ポップが出た時のために、取引IDを一番上までスクロールしてクリック
                                            element = browser.find_element(By.XPATH, '//*[@id="js-form-highlight"]/form/div[1]/div[1]/div[3]/dl/dd/div/textarea')
                                            browser.execute_script("arguments[0].scrollIntoView();", element)
                                            # 取引IDをクリック
                                            element.click()
                                            time.sleep(1)

                                            # 検索ボタンをクリック
                                            browser_from = browser.find_element(By.XPATH, '//*[@id="js-form-highlight"]/form/div[2]/button')
                                            browser_from.click()
                                            time.sleep(2)

                                            # メモボタンをクリック
                                            browser_from = browser.find_element(By.XPATH, '//*[@id="js-table-highlight"]/td[11]/p/a')
                                            browser_from.click()
                                            time.sleep(1)

                                            # elementを取得
                                            time.sleep(1)
                                            element = browser.find_element(By.XPATH, '//*[@id="fab-dialog"]/div[2]/form/div/div[2]/textarea')
                                            # 改行
                                            newline = "\n"
                                            element.send_keys('※')
                                            element.send_keys(newline)
                                            element.send_keys(newline)
                                            element.send_keys(combined_number)
                                            element.send_keys("\n")
                                            element.send_keys('在庫切れ')

                                            print("在庫切れ")

                                            browser_from = browser.find_element(By.XPATH, '//*[@id="fab-dialog"]/div[2]/form/div/div[4]/input[2]')
                                            browser_from.click()

                                            print()
                                            print("True2_2")

                                            set_zaiko = True
                                            
                                    #--------------------------------------------------------------

                                    except Exception as e:
                                        print(f"エラーが発生しました: {e}")
                                        continue

                                #--------------------------------------------------------------
                                
                                else:
                                    print("次のtrタグを検索...")
                                    
                            #--------------------------------------------------------------
                            
                            else:
                                print("※※※ どちらかの在庫が0などの処理しません")
                                        
                # --------------------------------------------------------------                
                # ここまでセット処理
                # --------------------------------------------------------------

                else:
                    html = browser.page_source
                    soup = BeautifulSoup(html, 'html.parser')
                    tr_elements = soup.find_all('tr')

                    if not sku:
                        print("完全一致SKUが定義されていません。処理をスキップします。")
                        
                    else:
                        for tr in tr_elements:
                            
                            td_elements = tr.find_all('td')

                            # td要素のテキストを取得して正規化
                            td_texts = [unicodedata.normalize('NFKC', td.get_text(strip=True)) for td in td_elements]
                            td_texts_no_space = [text.replace(' ', '') for text in td_texts]

                            # 完全一致SKUが含まれている行を探す
                            if td_texts_no_space:
                                # input要素を取得
                                input_element = tr.find('input', {'name': True, 'type': 'text'})

                                # input要素が見つからない場合を処理
                                if not input_element:
                                    print("input要素が見つかりませんでした。スキップします。")
                                    
                                    continue

                                # input要素の属性を取得
                                try:
                                    input_value = input_element.get('value', '0')
                                    input_name = input_element.get('name', '')

                                    # デバッグログ
                                    print(f"Debug: Input Name: {input_name}, Input Value: {input_value}")

                                    # input_value を数値に変換
                                    input_value2 = int(input_value)
                                    order_number = int(order_number)

                                    # 注文数が在庫数を超えているかをチェック
                                    if order_number > input_value2:
                                        print("注文数が在庫数を超えています。処理を中止します。2")

                                        zaiko_change = True
                                        processed = True
                                        continue

                                    #--------------------------------------------------------------
                                    
                                    else:
                                        total_value = input_value2 - order_number

                                        if total_value <= 0:
                                            input_value2 = max(0, order_number)
                                            total_value = 0

                                        # elementを取得して値を送信
                                        element = browser.find_element(By.NAME, input_name)
                                        element.clear()
                                        element.send_keys(total_value)

                                        # 処理が実行されたのでフラグをTrueに設定
                                        processed = True
                                        single_item = True

                                except Exception as e:
                                    print(f"エラーが発生しました: {e}")
                                    continue

                            else:
                                print("次のtrタグを検索...")

                #--------------------------------------------------------------
                
                # processedフラグに基づいて、処理が実行されたかどうかを判定
                if processed:
                    print('処理が実行されました')
                    print()
                else:
                    print('処理が実行されませんでした')
                    print()

                    if set_zaiko:
                        print()
                        # 実行された場合これ以降はスキップ
                        continue
                        
                    else:
                        url_login = "https://www.buyma.com/my/orders/"
                        browser.get(url_login)

                        element = browser.find_element(By.NAME, "order_id")
                        element.clear()
                        element.send_keys(tid)
                        time.sleep(1)

                        # ポップが出た時のために、取引IDを一番上までスクロールしてクリック
                        element = browser.find_element(By.XPATH, '//*[@id="js-form-highlight"]/form/div[1]/div[1]/div[3]/dl/dd/div/textarea')
                        browser.execute_script("arguments[0].scrollIntoView();", element)
                        # 取引IDをクリック
                        element.click()
                        time.sleep(1)

                        # 検索ボタンをクリック
                        browser_from = browser.find_element(By.XPATH, '//*[@id="js-form-highlight"]/form/div[2]/button')
                        browser_from.click()
                        time.sleep(2)

                        # メモボタンをクリック
                        browser_from = browser.find_element(By.XPATH, '//*[@id="js-table-highlight"]/td[11]/p/a')
                        browser_from.click()
                        time.sleep(1)
                        # elementを取得
                        time.sleep(1)
                        element = browser.find_element(By.XPATH, '//*[@id="fab-dialog"]/div[2]/form/div/div[2]/textarea')
                        # 改行
                        newline = "\n"
                        time.sleep(1)

                        element.send_keys(newline)
                        element.send_keys(newline)
                        element.send_keys('在庫連携されていません')
                        element.send_keys("\n")
                        element.send_keys('※')
                        element.send_keys(text2)

                        print('在庫連携されていません')

                        # 保存ボタンをクリック
                        browser_from = browser.find_element(By.XPATH, '//*[@id="fab-dialog"]/div[2]/form/div/div[4]/input[2]')
                        browser_from.click()

                        # 実行された場合これ以降はスキップ
                        continue

                #--------------------------------------------------------------
                    
                if single_item:     

                    # 在庫コードを入力
                    element = browser.find_element(By.NAME, "serch_key")
                    element.clear()
                    element.send_keys(code)

                    # 在庫連携のチェックボックスを選択
                    try:
                        time.sleep(1)
                        # name属性からstock番号だけを取得
                        numbers = ''.join(filter(str.isdigit, input_name))
                        print('stock番号:', numbers)

                        # value属性とstock番号が共通の為、value属性からxpathでクリック
                        checkbox_element = browser.find_element(By.XPATH, f"//input[@value='{numbers}']")
                        checkbox_element.click()
                        time.sleep(1)
                    except:
                        pass

                    try:
                        time.sleep(1)
                        link = browser.find_element(By.XPATH, '//*[@id="product--search"]/div/div/div[3]/div/input')
                        link.click()  # 総在庫数をクリックして反映を押せるようにする
                        time.sleep(1)
                    except:
                        pass

                    #----------------------------------------------------

                    # 在庫連携画面の文字までスクロールして、反映ボタンを表示
                    def scroll_to_element(element):
                        # スクロール先の位置までスクロールするJavaScriptコード
                        script = """
                            var element = arguments[0];
                            element.scrollIntoView({ behavior: 'auto', block: 'center', inline: 'center' });
                        """
                        browser.execute_script(script, element)

                    try:
                        button = browser.find_element(By.XPATH, '//*[@id="stockSituation"]/div[3]/div/h1')
                        if not button.is_displayed():
                            actions = ActionChains(browser)
                            actions.move_to_element(button).perform()
                            time.sleep(1)
                        button.click()
                        time.sleep(3)
                    except:
                        pass

                    #----------------------------------------------------

                    # 反映をクリック
                    try:
                        browser_from = browser.find_element(By.XPATH, '//*[@id="myTabContent"]/div[2]/div[2]/div[5]/button')
                        browser_from.click()
                        time.sleep(3)
                    except:
                        pass
                    
                    #----------------------------------------------------
      
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
                        
                #--------------------------

                else:
                    print("単品用の在庫を変更しませんでした")
                    print()


                # --------------------------------------------------------------
                # 個別ページでメモに記入
                # --------------------------------------------------------------

                # 取引IDで個別ページにアクセス
                url_login = "https://www.buyma.com/my/orders/"
                browser.get(url_login)

                element = browser.find_element(By.NAME, "order_id")
                element.clear()
                element.send_keys(tid)
                time.sleep(1)
                
                # ポップが出た時のために、取引IDを一番上までスクロールしてクリック
                element = browser.find_element(By.XPATH, '//*[@id="js-form-highlight"]/form/div[1]/div[1]/div[3]/dl/dd/div/textarea')
                browser.execute_script("arguments[0].scrollIntoView();", element)
                # 取引IDをクリック
                element.click()
                time.sleep(1)

                # 検索ボタンをクリック
                browser_from = browser.find_element(By.XPATH, '//*[@id="js-form-highlight"]/form/div[2]/button')
                browser_from.click()
                time.sleep(2)

                # メモボタンをクリック
                browser_from = browser.find_element(By.XPATH, '//*[@id="js-table-highlight"]/td[11]/p/a')
                browser_from.click()
                time.sleep(1)

                if zaiko_change:
                    input_value = 0
                    print("※※※ 注文数が在庫数を超えているので、在庫を0に設定")

                # 在庫が0の場合
                input_value = int(input_value)
                if input_value == 0:

                    # elementを取得
                    time.sleep(1)
                    element = browser.find_element(By.XPATH, '//*[@id="fab-dialog"]/div[2]/form/div/div[2]/textarea')
                    # 改行
                    newline = "\n"
                    element.send_keys('※')
                    element.send_keys(newline)
                    element.send_keys(newline)
                    element.send_keys(combined_number)
                    element.send_keys("\n")
                    element.send_keys('在庫切れ')
                    
                    print("在庫が0で減らせません")

                    browser_from = browser.find_element(By.XPATH, '//*[@id="fab-dialog"]/div[2]/form/div/div[4]/input[2]')
                    browser_from.click()
                
                #--------------------------------------------------------------
                
                # 在庫が0意外の場合
                input_value = int(input_value)
                if input_value != 0:

                    # 現在の日付と時間を取得
                    now = datetime.now()

                    # フォーマットして表示
                    formatted_date = now.strftime("%m/%d")
                    formatted_time = now.strftime("%H:%M")
                    print("日付:", formatted_date)
                    #print("時間:", formatted_time)
                    print('(単品) 注文前の在庫:', input_value)
                    print('(単品) 残りの在庫:', total_value)

                    now = datetime.now()
                    formatted_time = now.strftime("%H:%M")
                    ampm = now.strftime("%p")

                    if ampm == "AM":
                        input_text = "午前"
                    else:
                        input_text = "午後"

                    # elementを取得
                    time.sleep(1)
                    element = browser.find_element(By.XPATH, '//*[@id="fab-dialog"]/div[2]/form/div/div[2]/textarea')
                    # 改行
                    newline = "\n"
                    time.sleep(1)

                    element.send_keys(newline)
                    element.send_keys(newline)
                    element.send_keys('※')
                    
                    element.send_keys(newline)
                    element.send_keys(combined_number)

                    if int(order_number) > 1:
                        element.send_keys(newline)
                        element.send_keys('数量注意')
                        print('数量注意') 
                    
                    if int(input_value) == 0:
                        print("在庫が0で減らせません")
                        element.send_keys(newline)
                        element.send_keys('在庫切れ')
                    elif int(total_value) <= 0:
                        print('ラスト')
                        element.send_keys(newline)
                        element.send_keys('ラスト')              
                    
                    element.send_keys(newline)
                    element.send_keys('当日')
                    element.send_keys(newline)
                    element.send_keys(delivery_method)

                    # 保存ボタンをクリック
                    browser_from = browser.find_element(By.XPATH, '//*[@id="fab-dialog"]/div[2]/form/div/div[4]/input[2]')
                    browser_from.click()

                # --------------------------------------------------------------
                # 受注リストの詳細にアクセスしてメール送信
                # --------------------------------------------------------------
                
                input_value = int(input_value)
                if input_value != 0:

                    # 取引IDボタンをクリック
                    try:
                        time.sleep(2)
                        browser_from = browser.find_element(By.XPATH, '//*[@id="js-table-highlight"]/td[4]/p[2]/a')
                        browser_from.click()
                        time.sleep(2)
                    except:
                        pass

                    try:
                    # ポップのログインが出た場合
                        browser_from = browser.find_element(By.XPATH, '//*[@id="fab-dialog"]/div[2]/div[2]/div[2]/a')
                        browser_from.click()
                    except:
                        pass

                    # buymaに未ログインの場合はログイン
                    buyma_code = "shoyan75294"
                    try:
                        element = browser.find_element(By.NAME, "txtLoginPass")
                        element.clear()
                        element.send_keys(buyma_code)

                        browser_from = browser.find_element(By.XPATH, '//*[@id="login_do"]')
                        browser_from.click()
                    except:
                        pass

                    try:
                        # 問い合わせボタンを待機してクリック
                        inquiry_button = WebDriverWait(browser, 5).until(
                            EC.element_to_be_clickable((By.XPATH, '//*[@id="content"]/form/div/div/div[2]/div/div/div/ul[2]/li[1]/div[1]/div/a'))
                        )
                        inquiry_button.click()
                    except Exception as e:
                        print(f"問い合わせボタンのクリックに失敗しました: {str(e)}")

                    try:
                        # テンプレートを選択してくださいを待機してクリック
                        template_select = WebDriverWait(browser, 5).until(
                            EC.element_to_be_clickable((By.XPATH, '//*[@id="fab-dialog"]/div[2]/div[2]/form/div[1]/div[1]/div/div/span[2]'))
                        )
                        template_select.click()
                    except Exception as e:
                        print(f"テンプレート選択のクリックに失敗しました: {str(e)}")
                        
                        #--------------------------------------------------------------
                        
                        # 問い合わせがきていて送れない可能性があるため、確認のメモを残す
                        url_login = "https://www.buyma.com/my/orders/"
                        browser.get(url_login)

                        element = browser.find_element(By.NAME, "order_id")
                        element.clear()
                        element.send_keys(tid)
                        time.sleep(1)
                        
                        # ポップが出た時のために、取引IDを一番上までスクロールしてクリック
                        element = browser.find_element(By.XPATH, '//*[@id="js-form-highlight"]/form/div[1]/div[1]/div[3]/dl/dd/div/textarea')
                        browser.execute_script("arguments[0].scrollIntoView();", element)
                        # 取引IDをクリック
                        element.click()
                        time.sleep(1)
                        
                        # 検索ボタンをクリック
                        browser_from = browser.find_element(By.XPATH, '//*[@id="js-form-highlight"]/form/div[2]/button')
                        browser_from.click()
                        time.sleep(2)

                        # メモボタンをクリック
                        browser_from = browser.find_element(By.XPATH, '//*[@id="js-table-highlight"]/td[11]/p/a')
                        browser_from.click()
                        time.sleep(3)

                        # メモの中の要素を取得
                        html_content = browser.page_source
                        soup = BeautifulSoup(html_content, 'html.parser')

                        memotexts = soup.find_all('div', id='fab-dialog')
                        # メモの中身を取得
                        for memotext in memotexts:
                            memo_in = memotext.find('textarea', class_='fab-dialog__textarea')
                            if memo_in:
                                memo_text = memo_in.text.strip()  # テキストだけを取得して、前後の空白を除去
                                print(memo_text)

                        # elementを取得
                        time.sleep(2)
                        element = browser.find_element(By.XPATH, '//*[@id="fab-dialog"]/div[2]/form/div/div[2]/textarea')
                        element.clear()

                        newline = "\n"
                        element.send_keys('※ メールが送れませんでした\n')
                        element.send_keys(newline)
                        element.send_keys(memo_text)
                        print('メールが送れなかったので問い合わせ確認してください')

                        # 保存ボタンをクリック
                        browser_from = browser.find_element(By.XPATH, '//*[@id="fab-dialog"]/div[2]/form/div/div[4]/input[2]')
                        browser_from.click()
                        
                    #--------------------------------------------------------------                       

                    try:
                        # 汎用を待機してクリック
                        generic_option = WebDriverWait(browser, 5).until(
                            EC.element_to_be_clickable((By.XPATH, '//span[@class="bmm-c-select-option__main"][contains(text(),"汎用")]'))
                        )
                        generic_option.click()
                    except Exception as e:
                        print(f"汎用の選択に失敗しました: {str(e)}")

                    try:
                        # その他を待機してクリック
                        other_option = WebDriverWait(browser, 5).until(
                            EC.element_to_be_clickable((By.XPATH, '//span[@class="bmm-c-select-option__main" and text()="その他"]'))
                        )
                        other_option.click()
                    except Exception as e:
                        print(f"その他の選択に失敗しました: {str(e)}")

                    try:
                        # 1.注文承諾(即日発送)を待機してクリック
                        order_accept_option = WebDriverWait(browser, 5).until(
                            EC.element_to_be_clickable((By.XPATH, '//span[@class="bmm-c-select-option__main" and text()="1.注文承諾(即日発送)"]'))
                        )
                        order_accept_option.click()
                    except Exception as e:
                        print(f"注文承諾(即日発送)の選択に失敗しました: {str(e)}")

                    try:
                        # 送信ボタンを待機してクリック
                        send_button = WebDriverWait(browser, 10).until(
                            EC.element_to_be_clickable((By.XPATH, '//*[@id="fab-dialog"]/div[2]/div[2]/form/div[4]/input'))
                       )
                        send_button.click()
                        print('送信しました')
                    except Exception as e:
                        print(f"送信ボタンのクリックに失敗しました: {str(e)}")

# --------------------------------------------------------------
# ここまでメイン処理
# --------------------------------------------------------------

    browser.get(current_url)
    
    # ページを取得
    html_content = browser.page_source
    soup = BeautifulSoup(html_content, 'html.parser')

    # 次へボタンの要素を検索
    next_button = soup.find('a', {'class': 'box', 'rel': 'next'})

    # 次へボタンが存在しない場合、ループを終了
    if not next_button:
        break

    # 次へボタンのURLを取得
    next_url = next_button['href']
    # 次のページのURLを設定
    url = next_url
    url_login = url    

    page = "https://www.buyma.com/" + url_login
    
    browser.get(page)
    time.sleep(2)
    
print()

# 処理終了時間
now = datetime.now()
print()
formatted_date = now.strftime("%m/%d")
formatted_time = now.strftime("%H:%M")
print("処理完了:", formatted_date, formatted_time)
print("-" * 80)
print("\n\n\n")

browser.quit()
