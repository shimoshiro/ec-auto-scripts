#!/usr/bin/env python
# coding: utf-8

# Buyの受注内容をCSVでダウンロードしてGoqに取り込む

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

#-------------------------------------------------------------------------------

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
import glob
import re
from selenium.webdriver.chrome.options import Options
from send2trash import send2trash
from os.path import expanduser

#-------------------------------------------------------------------------------

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

#-------------------------------------------------------------------------------

USER1 = "your_user_id_1"
PASS1 = "your_password_1"
USER2 = "your_user_id_2"
PASS2 = "your_password_2"

# 在庫管理ページへアクセス
url_login = "http://stock2.goqsystem.com/?nav_id=stockSituation"
browser.get(url_login)
time.sleep(1)

# テキストボックス入力　左側
element = browser.find_element(By.ID, "login_id")
element.clear()
element.send_keys(USER1)
element = browser.find_element(By.ID, "login_pw")
element.clear()
element.send_keys(PASS1)

# 入力したデータをクリック　左側
browser_from = browser.find_element(By.XPATH, '//*[@id="loginform"]/div/div/div[1]/input')
browser_from.click()
time.sleep(2)

# テキストボックス入力　右側
element = browser.find_element(By.ID, "seq_id")
element.clear()
element.send_keys(USER2)
element = browser.find_element(By.ID, "seq_pw")
element.clear()
element.send_keys(PASS2)

# 入力したデータをクリック　右側
browser_from = browser.find_element(By.XPATH, '//*[@id="loginform"]/div/div/div[2]/input')
browser_from.click()
time.sleep(2)

#-------------------------------------------------------------------------------

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
    browser_from = browser.find_element(By.ID, 'driver-highlighted-element-stage')
    browser_from.click()
    print("ポップ画面をクリック")
except:
    print("ポップがないのでスキップします")

try:
    time.sleep(3)
    browser_from = browser.find_element(By.CSS_SELECTOR, ".driver-close-btn")
    browser_from.click()
    print("スキップをクリック")
except:
    time.sleep(3)
    print("スキップボタンがありませんでした")

try:
    # キーワード欄を取得
    element = browser.find_element(By.XPATH, '//*[@id="js-form-highlight"]/form/div[1]/div[1]/div[2]/dl/dd/div/div[1]/input')

    # クリック対象要素が画面の上部に来るようにスクロール
    browser.execute_script("arguments[0].scrollIntoView({block: 'start'});", element)
    print("下にスクロール")
    time.sleep(3)

    element.click()
    print("キーワード欄をクリック")
    
except:
    print("キーワード欄をクリックできませんでした")
    print()
    
    browser.execute_script("window.scrollBy(0, -600);")
    print("上にスクロール")
    # キーワードをクリックして件数表示欄を上にスクロールしてトップへボタンと被らないようにする
    element = browser.find_element(By.XPATH, '//*[@id="js-form-highlight"]/form/div[1]/div[1]/div[2]/dl/dd/div/div[1]/input')
    element.click()
    print("キーワード欄をクリック")
    print()

try:
    time.sleep(1)
    checkbox = browser.find_element(By.XPATH, '//*[@id="content"]/div/div/div[4]/div/span/div')
    checkbox.click()
    print("件数表示をクリック")
except:
    print("件数表示をクリックできませんでした")
    
    browser.execute_script("window.scrollBy(0, -600);")
    print("上にスクロール")
    checkbox = browser.find_element(By.XPATH, '//*[@id="content"]/div/div/div[4]/div/span/div')
    checkbox.click()
    time.sleep(2)
    print("件数表示をクリック")
    
try:
    time.sleep(1)
    from selenium.webdriver.common.action_chains import ActionChains
    # クリックする要素を表示するために要素までスクロール
    checkbox = browser.find_element(By.XPATH, '//*[@id="content"]/div/div/div[4]/div/span/div/ul/li[3]')
    actions = ActionChains(browser)
    actions.move_to_element(checkbox).perform()
    checkbox.click()
    print("100件表示を選択")
    time.sleep(1)
except:
    print("100件表示を選択できませんでした")

# 受注日を選択
datebox = browser.find_element(By.CSS_SELECTOR, ".bmm-c-text-field.sell-term.bmm-u-typo-size80")
datebox.click()

button = browser.find_element(By.XPATH, '//div[contains(@class, "react-datepicker__day--today")]')
button.click()
print("日付を選択")
time.sleep(1)

checkbox = browser.find_element(By.NAME, "statuses.placed")
checkbox.click()
print("受注にチェック")
time.sleep(1)

# ポップが出た時のために、取引IDを一番上までスクロールしてクリック
element = browser.find_element(By.XPATH, '//*[@id="js-form-highlight"]/form/div[1]/div[1]/div[3]/dl/dd/div/textarea')
browser.execute_script("arguments[0].scrollIntoView();", element)
element.click()
time.sleep(1)

browser_from = browser.find_element(By.XPATH, '//*[@id="js-form-highlight"]/form/div[2]/button')
browser_from.click()
print("検索をクリック")
time.sleep(6)

#-------------------------------------------------------------------------------

# iframeでクーポンなどのバナーが表示された場合
try:
    iframe = WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.TAG_NAME, 'iframe')))
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

#-------------------------------------------------------------------------------

# 以降の処理内容の概要
# 1. メモリンクをクリックして内容を取得し、「※」が含まれ「＊」が含まれていない場合のみ対象とする
# 2. 対象メモに対して、該当行のチェックボックスを自動でONにする
# 3. 取引IDもログとして出力し、モーダルはクリック後にキャンセルして閉じます

# XPath生成関数
def get_element_xpath(element):
    xpath = []
    while element and element.name != '[document]':
        siblings = element.find_previous_siblings(element.name)
        tag = element.name
        if siblings:
            tag += f"[{len(siblings) + 1}]"
        xpath.insert(0, tag)
        element = element.parent
    return "/html/" + "/".join(xpath[1:])  # /html/body/... の形式に

# HTML取得 & パース
html_content = browser.page_source
soup = BeautifulSoup(html_content, 'html.parser')
tr_tags = soup.find_all('tr', class_='orders-table-tr-main')

# チェックボックス要素（先頭の一括チェック除外）
checkbox_inputs_all = browser.find_elements(By.CSS_SELECTOR, 'label.orders-check-box input[type="checkbox"]')
checkbox_inputs = checkbox_inputs_all[1:]

print("===== 実行ログ =====\n")

# 各行を処理
for index, tr_tag in enumerate(tr_tags):

    print("-" * 24)
    print()
    
    # 取引ID取得
    trade_id_tag = tr_tag.select_one('td.order_trade_id_column a[data-event-label="取引ID"]')
    if trade_id_tag:
        trade_id = trade_id_tag.get_text(strip=True)
        print(f"[{index}] 🔢 取引ID: {trade_id}")
    else:
        trade_id = "不明"
        print(f"[{index}] ⚠️ 取引IDが見つかりません")

    # メモリンク取得
    a_tag = tr_tag.find('a', class_='MyCont_PlaceholderLink')
    if not a_tag:
        print("メモリンクが見つかりませんでした")
        print("-" * 40)
        continue

    memo_link_text = a_tag.get_text(strip=True)
    print(f"【メモリンク検出】{memo_link_text}")

    try:
        # メモリンククリック
        xpath = get_element_xpath(a_tag)
        browser_element = browser.find_element(By.XPATH, xpath)
        browser_element.click()
        print("📝 メモをクリックしました")
        time.sleep(1)

        # メモ内容取得
        memo_element = browser.find_element(By.CSS_SELECTOR, 'textarea.fab-dialog__textarea')
        memo_text = memo_element.get_attribute("value").strip()
        print("【メモ内容】\n" + memo_text)

        # モーダル閉じる
        try:
            cancel_btn = browser.find_element(By.XPATH, '//*[@id="fab-dialog"]/div[2]/form/div/div[4]/input[1]')
            cancel_btn.click()
            time.sleep(1)
            print("キャンセルボタンをクリックしてモーダルを閉じました")
        except:
            print("⚠️ モーダルを閉じるのに失敗しました")

        # ✅ チェック条件：※を含み、＊は含まない
        if "※" in memo_text and "＊" not in memo_text:
            print("✅ チェック対象！")
            try:
                checkbox = checkbox_inputs[index]
                browser.execute_script("arguments[0].click();", checkbox)
                print(f"✔️ チェックを付けました: checkbox_inputs[{index}]")
                time.sleep(1)
            except Exception as e:
                print(f"⚠️ チェック失敗: checkbox_inputs[{index}] - {e}")
                time.sleep(1)
        else:
            print("スキップ：条件に合致せず")

    except Exception as e:
        print(f"❌ メモクリックまたは処理エラー: {e}")

    print()

print("✅ 全処理完了")
print("\n\n\n")

time.sleep(5)

#-------------------------------------------------------------------------------

try:
    # 詳細情報の編集ボタンをクリック
    browser_from = browser.find_element(By.XPATH, '//*[@id="MyContgoTop"]')
    browser_from.click()
    time.sleep(2)
    print("ページトップをクリック")
except:
    print("ページトップを押せませんでした")

try:
    # 詳細情報の編集ボタンをクリック
    browser_from = browser.find_element(By.XPATH, '//*[@id="js-actions-highlight"]')
    browser_from.click()
    time.sleep(3)
    print("一括連絡・配送先情報をクリック")
except:
    print("一括連絡・配送先情報を押せませんでした")
    
click_on = False

try:
    # 詳細情報の編集ボタンをクリック
    browser_from = browser.find_element(By.XPATH, '//*[@id="content"]/div/div/div[5]/div/div[1]/div/ul/li[6]')
    browser_from.click()
    time.sleep(5)
    print("配送先情報 CSVをクリック")
    click_on = True
    print("click_onをTrueにしました")
    print()
except:
    print("配送先情報 CSVを押せませんでした")
    print()
    
time.sleep(5)

#-------------------------------------------------------------------------------

# 以降の処理内容の概要
# メモに「※」が含まれ「＊」が未記載のものを検出し、
# メモ欄に「＊」を先頭に追加した上で保存する自動処理です。
# また、取引IDもログ出力され、処理対象外のメモはスキップされます。

def get_element_xpath(element):
    xpath = []
    while element.parent:
        siblings = element.find_previous_siblings(element.name)
        tag = element.name
        if siblings:
            tag += f"[{len(siblings) + 1}]"
        xpath.insert(0, tag)
        element = element.parent
    return "/" + "/".join(xpath)

# ページHTML取得
html = browser.page_source
soup = BeautifulSoup(html, 'html.parser')
rows = soup.select('tr.orders-table-tr-main')

if click_on:

    print("===== メモ処理開始 =====\n")
    for index, tr_tag in enumerate(rows):

        print()
        print("-" * 24)
        print()

        try:
            # 取引ID取得
            trade_id_tag = tr_tag.select_one('td.order_trade_id_column a[data-event-label="取引ID"]')
            if trade_id_tag:
                trade_id = trade_id_tag.get_text(strip=True)
                print(f"[{index}] 🔢 取引ID: {trade_id}")
            else:
                trade_id = "不明"
                print(f"[{index}] ⚠️ 取引IDが見つかりません")

            # メモリンク検出
            a_tag = tr_tag.find('a', class_='MyCont_PlaceholderLink')
            if not a_tag:
                print(f"[{index}] ❌ メモリンクが見つかりません")
                continue

            xpath = get_element_xpath(a_tag)
            memo_link = browser.find_element(By.XPATH, xpath)
            browser.execute_script("arguments[0].click();", memo_link)
            print("📝 メモをクリックしました")
            time.sleep(1.5)

            memo_area = WebDriverWait(browser, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea.fab-dialog__textarea'))
            )
            memo_text = memo_area.get_attribute("value").strip()
            print("【メモ内容】\n" + memo_text + "\n--------\n")

            if "※" in memo_text and "＊" not in memo_text:
                print("✅ ＊を追加対象！")

                # textarea をユーザー操作で更新
                memo_area.clear()
                memo_area.send_keys("＊" + memo_text)
                time.sleep(0.5)

                # 保存ボタンをクリック
                save_btn = browser.find_element(By.XPATH, '//*[@id="fab-dialog"]/div[2]/form/div/div[4]/input[2]')
                browser.execute_script("arguments[0].click();", save_btn)
                print("💾 保存ボタンをクリックしました")

                # モーダルが閉じるのを待機
                WebDriverWait(browser, 10).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, 'textarea.fab-dialog__textarea'))
                )
                print("✅ メモ保存完了を確認")
                print()
            else:
                print("スキップ：条件に合致せず")
                try:
                    cancel_btn = browser.find_element(By.XPATH, '//*[@id="fab-dialog"]/div[2]/form/div/div[4]/input[1]')
                    cancel_btn.click()
                    print("キャンセルボタンでモーダルを閉じました")
                except:
                    print("❗ キャンセルボタンが見つかりません")

        except Exception as e:
            print(f"[{index}] ❌ 処理中エラー: {e}")

    print()
    print("✅ 全処理完了")
    print("\n\n\n")
    
else:
    print("ダウンロードできなかったので実行しませんでした")
    print()
    
time.sleep(5)

#-------------------------------------------------------------------------------

# 受注管理にアクセス
url_login = "https://order.goqsystem.com/goq21/form/goqsystem_new/systemlogin.php?type=&shop="
browser.get(url_login)
time.sleep(2)

try:
    element = browser.find_element(By.ID, "login_id")
    element.clear()
    element.send_keys(USER1)
    element = browser.find_element(By.ID, "login_pw")
    element.clear()
    element.send_keys(PASS1)
    browser_form = browser.find_element(By.XPATH, '//*[@id="loginbtn1"]')
    browser_form.click()
    time.sleep(2)
except NoSuchElementException:
    time.sleep(2)
    pass

try:
    element = browser.find_element(By.ID, "seq_id")
    element.clear()
    element.send_keys(USER2)
    element = browser.find_element(By.ID, "seq_pw")
    element.clear()
    element.send_keys(PASS2)
    browser_from = browser.find_element(By.XPATH, '//*[@id="goqlogin"]/div/div[2]/button')
    browser_from.click()
    time.sleep(2)
except NoSuchElementException:
    time.sleep(2)
    pass
    print()

try:
    browser_from = browser.find_element(By.XPATH, '//*[@id="login3"]')
    browser_from.click()
    time.sleep(2)
    print("同意してをクリック")
except:
    print("同意してを押せませんでした")

# 固定URLが分かっているなら、直接アクセス
target_url = "https://order.goqsystem.com/goq21/modules/CustomImportCSV/index.php/top/"
browser.get(target_url)
print(f"🌐 カスタムCSV取込画面へ直接アクセスしました: {target_url}")

# 最新の buyerorder-*.csv を取得
download_dir = expanduser("~/Downloads")

csv_files = sorted(
    glob.glob(os.path.join(download_dir, "buyerorder-*.csv")),
    key=os.path.getmtime,
    reverse=True
)
latest_file = csv_files[0] if csv_files else None

if latest_file:
    print(f"📄 選択するファイル: {latest_file}")
    print()
    try:
        # input[type=file] が DOM に現れるのを最大10秒待つ
        file_input = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "csv_file"))
        )

        # JSでhidden解除（念のため）
        browser.execute_script("arguments[0].style.display = 'block';", file_input)

        # ファイルパスを送信（選択）
        file_input.send_keys(latest_file)

        # jQueryのonchangeを発火させて、label反映も行う
        browser.execute_script("arguments[0].dispatchEvent(new Event('change'))", file_input)

        print("✅ ファイル送信成功")

    except Exception as e:
        print(f"❌ ファイル選択に失敗しました: {e}")

else:
    print("❌ buyerorder-*.csv が見つかりません")

try:
    browser_from = browser.find_element(By.ID, 'submit_fileupload')
    browser_from.click()
    time.sleep(2)
    print("送信ボタンをクリック")
    print()
except:
    print("送信ボタンを押せませんでした")
    print()

# ボタンをクリック
browser_from = browser.find_element(By.ID, 'submit_exec')
browser_from.click()

try:
    WebDriverWait(browser, 300).until(EC.alert_is_present())
    alert = browser.switch_to.alert
    alert_text = alert.text
    print("アラートメッセージ:", alert_text)

    if "取り込み完了" in alert_text:
        alert.accept()
        print("✅ 正常アラートを閉じました")
    else:
        # アラートが取り込み完了でなかったらエラーログに記録
        error_log_path = os.path.join(expanduser("~/Documents/log"), "error_handle.log")
        with open(error_log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Unexpected alert: {alert_text}\n")

        alert.accept()
        print("⚠️ 異常アラートを閉じ、ログに記録しました")

except:
    print("300秒以内にアラートが出ませんでした")

time.sleep(3)

#-------------------------------------------------------------------------------

if latest_file and os.path.exists(latest_file):
    try:
        send2trash(latest_file)
        print(f"🗑️ ゴミ箱に移動しました: {latest_file}")
    except Exception as e:
        print(f"⚠️ ゴミ箱への移動に失敗: {e}")

#-------------------------------------------------------------------------------

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
