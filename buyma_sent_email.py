#!/usr/bin/env python
# coding: utf-8

# Buymで出荷完了した受注内容を取得してBuymaで発送完了メールを送信

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
import logging
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
use_headless = True  # **True: ヘッドレスモード, False: GUIモード（デバッグ用）**

# ChromeOptionsの設定
options = Options()

# 画面表示させたい場合は下記を表示させる
if is_ec2:
    
# ヘッドレスモードの設定
#if is_ec2 or use_headless:
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

browser_from = browser.find_element(By.XPATH, '//*[@id="goq_index"]/ul[3]/li[19]/a')
browser_from.click()
print("出荷完了をクリック")
time.sleep(2)

browser_from = browser.find_element(By.XPATH, '//*[@id="pro_form"]/table/tbody/tr/td/ul/li[9]/a')
browser_from.click()
print("buymaをクリック")
time.sleep(2)

# 一覧ページ読み込み
WebDriverWait(browser, 20).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "tr[id^='orderListRow_']"))
)

html_content = browser.page_source
soup = BeautifulSoup(html_content, 'html.parser')
tr_tags = soup.find_all('tr', id=re.compile(r'orderListRow_\d+'))

order_data_list = []

print(f"\n🔍 注文行数: {len(tr_tags)}")

for index, tr in enumerate(tr_tags):
    print(f"\n--- 行 {index + 1} を処理中 ---")

    # 同梱アイコン確認
    is_doukon = tr.find('img', {'src': 'img/icon/package.gif'}) is not None
    print("📦 同梱: ", "あり" if is_doukon else "なし")

    # 注文番号とURL
    order_number, order_url = None, None
    for a_tag in tr.find_all('a', href=True):
        href = a_tag['href']
        if 'order_details' in href:
            order_number = a_tag.get_text(strip=True)
            order_url = f"https://order.goqsystem.com/goq21/{href}"
            print(f"✅ 受注番号: {order_number}")
            print(f"🌐 URL: {order_url}")
            break

    # 追跡番号
    tracking_number = None
    for span in tr.find_all('span'):
        span_text = span.get_text(strip=True)
        if re.fullmatch(r'\d{8,}', span_text):
            tracking_number = span_text
            print(f"✅ 追跡番号: {tracking_number}")
            break

    # 配送種別抽出
    delivery_td_text = None
    delivery_type = None
    for td in tr.find_all('td'):
        if '日本郵便' in td.get_text():
            delivery_td_text = td.get_text(separator='\n', strip=True)
            lines = delivery_td_text.split('\n')
            try:
                jp_index = lines.index('日本郵便')
                denpyou_index = lines.index('[伝票入力済]')
                between = lines[jp_index + 1:denpyou_index]
                valid_lines = [line.strip() for line in between if line.strip() and '【住】' not in line]
                if valid_lines:
                    if 'ゆうパケ' in valid_lines[0]:
                        delivery_type = 'ゆうパケ'
                    elif 'メール便' in valid_lines[0]:
                        delivery_type = 'メール便'
                    elif '宅急便コンパクト' in valid_lines[0]:
                        delivery_type = '宅急便コンパクト'
                    else:
                        delivery_type = '不明'
                else:
                    delivery_type = '空欄'
            except ValueError:
                delivery_type = '不明'
            print(f"🚚 配送パターン: {delivery_type}")
            break

    is_teikeigai = delivery_type == "メール便"
    print(f"定形外: {'定形外です' if is_teikeigai else '定形外ではありません'}")

    # 子注文番号も含めて取得する場合（同梱）
    order_numbers_to_add = [order_number]
    if is_doukon and order_url:
        browser.get(order_url)
        time.sleep(2)
        detail_html = browser.page_source
        detail_soup = BeautifulSoup(detail_html, 'html.parser')
        detail_tr = detail_soup.find('tr', class_='ordermanegebg4')
        if detail_tr:
            tds = detail_tr.find_all('td')
            if len(tds) >= 2:
                raw_text = tds[1].get_text(separator='\n', strip=True)
                order_numbers = [
                    re.sub(r'（.*?）', '', line.strip())
                    for line in raw_text.split('\n')
                    if line.strip()
                ]
                if order_numbers:
                    order_numbers_to_add = order_numbers
                    print(f"👨‍👧‍👦 同梱注文番号取得: {order_numbers_to_add}")

    for num in order_numbers_to_add:
        order_info = {
            "order_number": num,
            "tracking_number": tracking_number,
            "is_teikeigai": is_teikeigai,
            "order_url": order_url,
            "delivery_text": delivery_td_text,
            "delivery_type": delivery_type,
            "is_doukon": is_doukon
        }
        order_data_list.append(order_info)
        print(f"✅ データを追加: {num}")

# 出力確認
print("\n=== ✅ 最終取得結果 ===")
for data in order_data_list:
    print(data)


# バイマにログイン
USER1 = "your_user_id"
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

# バイマで発送メール送信
# ログ設定（冒頭に一度だけ）
logging.basicConfig(
    filename='/Users/wills3/Documents/log/buyma_process.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

all_completion = True  # 全体の処理が成功したか（→次の処理に進めるか）
    
for index, order in enumerate(order_data_list):
    buyma_completion = False
    try:
        order_id = order["order_number"]
        tracking_number = order["tracking_number"]
        is_teikeigai = order["is_teikeigai"]
        delivery_type = order.get("delivery_type", "不明")

        print(f"\n========== 注文 {index + 1} / {len(order_data_list)} ==========\n")
        print(f"🔍 処理中の注文番号: {order_id}")
        print(f"📦 配送タイプ: {'定形外' if is_teikeigai else '通常配送'}")
        print(f"📬 追跡番号: {tracking_number}")
        print(f"🚚 配送種別: {delivery_type}")

        # バイマ注文一覧ページへ移動
        browser.get("https://www.buyma.com/my/orders/")
        time.sleep(1)

        # オーダー番号を入力
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.NAME, "order_id"))
        ).send_keys(order_id)
        print("✅ オーダーID入力完了")

        # 検索ボタンをクリック
        browser.find_element(By.XPATH, '//*[@id="js-form-highlight"]/form/div[2]/button').click()
        print("🔎 検索をクリック")
        time.sleep(2)

        #「発送した」ボタンをクリック
        xpath = f'//a[@id="{order_id}" and contains(text(), "発送した")]'
        print(f"🔎 XPath: {xpath}")

        try:
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            button = browser.find_element(By.XPATH, xpath)
            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            time.sleep(1.0)
            WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            browser.execute_script("arguments[0].click();", button)
            print("✅ 『発送した』ボタンをクリックしました")
        except Exception as e:
            print("❌ 『発送した』ボタンが押せませんでした")
            print(f"エラー: {e}")
            continue 

        time.sleep(5)

        #----------------------------------------------------------------------------

        # モーダル内の入力
        # 配送方法（selectタグ）を選択
        try:
            # 配送タイプと選択肢のマッピング
            mapping = {
                "ゆうパケ": "日本郵便 - ゆうパケット",
                "メール便": "日本郵便 - 定形郵便、定型外郵便",
                "宅急便コンパクト": "日本郵便 - ゆうパケット",
                "空欄": "日本郵便 - ゆうパック",
            }

            # 該当するラベルを取得（マッピングから）
            delivery_text = order.get("delivery_type")  # None含めてOK
            label_to_select = mapping.get(delivery_text, "日本郵便 - ゆうパック")

            # selectタグを取得
            select_element = WebDriverWait(browser, 5).until(
                EC.presence_of_element_located((By.ID, "haiso_cd"))
            )

            # 選択肢の中からラベル一致するoptionを探して選択
            for option in select_element.find_elements(By.TAG_NAME, "option"):
                if option.text.strip() == label_to_select:
                    option.click()
                    print(f"✅ 配送方法のセレクトボックスで『{label_to_select}』を選択しました")
                    break
            else:
                print(f"❌ 配送方法の選択肢に『{label_to_select}』が見つかりませんでした")

        except Exception as e:
            print("❌ 配送方法セレクトボックスの選択に失敗しました")
            print(f"エラー内容: {e}")

        print()

        #-----------------------------------------------------------------------------------------

        try:
            if is_teikeigai:
                # 定形外 → 「なし」をクリック
                element = browser.find_element(By.XPATH, '//*[@id="send_notice"]/div[1]/table/tbody/tr[5]/td/label[1]/input')
                element.click()
                print("✅ 配送方法が定形外なので『なし』をクリックしました")

                #-----------------------------------------------------------------------------------------

                try:
                    # 汎用を待機してクリック
                    generic_option = WebDriverWait(browser, 5).until(
                        EC.element_to_be_clickable((By.XPATH, '//*[@id="order-send-template-select-root"]/div'))
                    )
                    generic_option.click()
                except Exception as e:
                    print(f"※※※ テンプレートの選択に失敗しました: {str(e)}")

                time.sleep(2)

                #-----------------------------------------------------------------------------------------

                try:
                    # 汎用を待機してクリック
                    generic_option = WebDriverWait(browser, 5).until(
                        EC.element_to_be_clickable((By.XPATH, '//div[contains(@class,"Select-option") and @role="option"]//span[normalize-space(text())="汎用"]'))
                    )
                    generic_option.click()
                except Exception as e:
                    print(f"※※※ 汎用の選択に失敗しました: {str(e)}")

                time.sleep(2)

                #-----------------------------------------------------------------------------------------

                try:
                    # 汎用を待機してクリック
                    generic_option = WebDriverWait(browser, 5).until(
                        EC.element_to_be_clickable((By.XPATH, '//div[contains(@class,"Select-option") and @role="option"]//span[contains(text(), "定型文")]'))
                    )
                    generic_option.click()
                except Exception as e:
                    print(f"※※※ 定型文を選択に失敗しました: {str(e)}")

                time.sleep(2)

                #-----------------------------------------------------------------------------------------

                try:
                    # 汎用を待機してクリック
                    generic_option = WebDriverWait(browser, 5).until(
                        EC.element_to_be_clickable((By.XPATH, '//div[contains(@class,"Select-option") and @role="option"]//span[contains(text(), "商品発送メール")]'))
                    )
                    generic_option.click()
                except Exception as e:
                    print(f"※※※ 商品発送メールを選択に失敗しました: {str(e)}")

                time.sleep(2)

                #-----------------------------------------------------------------------------------------

                try:
                    # 汎用を待機してクリック
                    generic_option = WebDriverWait(browser, 5).until(
                        EC.element_to_be_clickable((By.XPATH, '//*[@id="send_notice"]/div[1]/div[5]/input[4]'))
                    )
                    generic_option.click()
                    print("入力内容を確認するを押しました")
                except Exception as e:
                    print(f"※※※ 入力内容を確認するを押せませんでした: {str(e)}")
                    print()
                    print()
                    print()

                time.sleep(2)

                #-----------------------------------------------------------------------------------------

                try:
                    # 汎用を待機してクリック
                    generic_option = WebDriverWait(browser, 5).until(
                        EC.element_to_be_clickable((By.XPATH, '//*[@id="sn_submit"]'))
                    )
                    generic_option.click()
                    print("この内容で確定するを押しました")
                except Exception as e:
                    print(f"※※※ この内容で確定するを押せませんでした: {str(e)}")
                    print()
                    print()
                    print()

                time.sleep(3)

            #--------------------------------------------------------------------------------------------------------------    

            else:
                # 定形外以外 → 「あり」をクリック
                element = browser.find_element(By.XPATH, '//*[@id="send_notice"]/div[1]/table/tbody/tr[5]/td/label[2]/input')
                element.click()
                print("✅ 配送方法が定形外以外なので『あり』をクリックしました")
                time.sleep(2)

                try:
                    # トラッキングNoの入力欄が表示されるまで待機
                    input_box = WebDriverWait(browser, 10).until(
                        EC.presence_of_element_located((By.ID, "trackingno"))
                    )
                    input_box.clear()
                    input_box.send_keys(tracking_number)
                    print(f"📮 トラッキング番号を入力しました: {tracking_number}")
                    print()

                    #-----------------------------------------------------------------------------------------

                    try:
                        # 汎用を待機してクリック
                        generic_option = WebDriverWait(browser, 5).until(
                            EC.element_to_be_clickable((By.XPATH, '//*[@id="order-send-template-select-root"]/div'))
                        )
                        generic_option.click()
                    except Exception as e:
                        print(f"※※※ テンプレートの選択に失敗しました: {str(e)}")

                    time.sleep(2)

                    #-----------------------------------------------------------------------------------------

                    try:
                        # 汎用を待機してクリック
                        generic_option = WebDriverWait(browser, 5).until(
                            EC.element_to_be_clickable((By.XPATH, '//div[contains(@class,"Select-option") and @role="option"]//span[normalize-space(text())="汎用"]'))
                        )
                        generic_option.click()
                    except Exception as e:
                        print(f"※※※ 汎用の選択に失敗しました: {str(e)}")

                    time.sleep(2)

                    #-----------------------------------------------------------------------------------------
                    try:
                        # 汎用を待機してクリック
                        generic_option = WebDriverWait(browser, 5).until(
                            EC.element_to_be_clickable((By.XPATH, '//div[contains(@class,"Select-option") and @role="option"]//span[contains(text(), "定型文")]'))
                        )
                        generic_option.click()
                    except Exception as e:
                        print(f"※※※ 定型文を選択に失敗しました: {str(e)}")

                    time.sleep(2)

                    #-----------------------------------------------------------------------------------------

                    try:
                        # 汎用を待機してクリック
                        generic_option = WebDriverWait(browser, 5).until(
                            EC.element_to_be_clickable((By.XPATH, '//div[contains(@class,"Select-option") and @role="option"]//span[contains(text(), "商品発送メール")]'))
                        )
                        generic_option.click()
                        print("商品発送メールを選択しました")
                    except Exception as e:
                        print(f"※※※ 商品発送メールを選択に失敗しました: {str(e)}")

                    time.sleep(2)

                    #-----------------------------------------------------------------------------------------

                    try:
                        # 汎用を待機してクリック
                        generic_option = WebDriverWait(browser, 5).until(
                            EC.element_to_be_clickable((By.XPATH, '//*[@id="send_notice"]/div[1]/div[5]/input[4]'))
                        )
                        generic_option.click()
                        print("入力内容を確認するを押しました")
                    except Exception as e:
                        print(f"※※※ 入力内容を確認するを押せませんでした: {str(e)}")
                        print()
                        print()
                        print()

                    time.sleep(2)

                    #-----------------------------------------------------------------------------------------

                    try:
                        # 汎用を待機してクリック
                        generic_option = WebDriverWait(browser, 5).until(
                            EC.element_to_be_clickable((By.XPATH, '//*[@id="sn_submit"]'))
                        )
                        generic_option.click()
                        print("この内容で確定するを押しました")
                        buyma_completion = True

                    except Exception as e:
                        print(f"この内容で確定するを押せませんでした: {str(e)}")
                        print()
                        print()
                        print()

                    time.sleep(3)
                    
                    if buyma_completion:
                        print(f"✅ 注文 {order_id} のBUYMA処理が成功しました")
                    else:
                        print(f"❌ 注文 {order_id} のBUYMA処理に失敗しました")

                #-----------------------------------------------------------------------------------------   

                except Exception as e:
                    print("❌ トラッキング番号の入力に失敗しました")
                    print(f"エラー内容: {e}")
                    print()
                    buyma_completion = False

        except Exception as e:
            print("❌ 配送方法のチェック切り替えに失敗しました")
            print(f"エラー内容: {e}")
            print()
            buyma_completion = False

    except Exception as e:
        print(f"❌ BUYMAの注文処理に失敗しました: {e}")
        print("全体が正常に終了しなかったので、all_completionをFalseにしました")
        print()
        buyma_completion = False
        all_completion = False
        
    #-----------------------------------------------------------------------------------------   

    # 各ループの終了後に失敗時のログを記録
    if not buyma_completion:
        logging.error(f"BUYMA処理失敗: 注文番号 {order_id} の完了フラグがFalseでした")
        print()

# 再度受注管理にアクセスしてステータス移動
if all_completion:
    print("✅ 全注文が正常に処理されたため、次の処理に進みます")
    
    # 再度受注管理にアクセスしてステータス移動
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

    #----------------------------------------------------------------------
    
    browser_from = browser.find_element(By.XPATH, '//*[@id="goq_index"]/table[1]/tbody/tr/td[1]/header/div/div[1]/ul/li[8]/a')
    browser_from.click()
    print("自動処理をクリック")
    time.sleep(2)

    browser_from = browser.find_element(By.XPATH, '//*[@id="inner"]/div/ul/li[7]/a')
    browser_from.click()
    print("出荷完了をクリック")
    time.sleep(2)

    browser_from = browser.find_element(By.XPATH, '//*[@id="updatebtm401"]')
    browser_from.click()
    print("バイマ発送完了の手動で実行するをクリック")
    time.sleep(2)

    browser_from = browser.find_element(By.XPATH, '//*[@id="btmdoautoexection"]')
    browser_from.click()
    print("自動処理を実行するをクリック")
    time.sleep(2)

    #----------------------------------------------------------------------
    
else:
    print("❌ 処理中にエラーがありました。ステータス移動を実行しませんでした")
    print()

#----------------------------------------
# 現在の日付と時間を取得
now = datetime.now()
print()
formatted_date = now.strftime("%m/%d")
formatted_time = now.strftime("%H:%M")
print("処理完了:", formatted_date, formatted_time)
print("-" * 80)
print("\n\n\n")

browser.quit()
