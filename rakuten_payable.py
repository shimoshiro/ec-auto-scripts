#!/usr/bin/env python
# coding: utf-8

# 楽天市場で仕入れた商品をスプレッドシートの買付表に記述

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
    
# **ヘッドレスモードの設定**
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

url_login = "https://grp01.id.rakuten.co.jp/rms/nid/vc?__event=login&service_id=s302&l-id=pc_header_login&return_url=import-ss-shop%2F"
browser.get(url_login)
time.sleep(2)

USER1 = "your_user_id"
PASS1 = "your_password"

try:
    # login1
    element = browser.find_element(By.ID, "loginInner_u")
    element.clear()
    element.send_keys(USER1)
    element = browser.find_element(By.ID, "loginInner_p")
    element.clear()
    element.send_keys(PASS1)
    browser_from = browser.find_element(By.NAME, "submit")
    browser_from.click()
    time.sleep(2)
except:
    print("ログインできませんでした")
    time.sleep(1)
    
try:
    browser_from = browser.find_element(By.XPATH, '//*[@id="root"]/header/div/div[2]/div/div[2]/div[5]/a')
    browser_from.click()
    time.sleep(2)
except:
    print("ボタンが押せませんでした")
    time.sleep(1)

try:
    element = browser.find_element(By.ID, "user_id")
    element.clear()
    element.send_keys(USER1)
    time.sleep(1)
except:
    pass

try:
    browser_from = browser.find_element(By.ID, 'cta001')
    browser_from.click()
    time.sleep(2)
except:
    pass

try:
    element = browser.find_element(By.ID, "password_current")
    element.clear()
    element.send_keys(PASS1)
    time.sleep(1)
except:
    pass

try:
    browser_from = browser.find_element(By.ID, 'cta011')
    browser_from.click()
    print("リダイレクトログインしました")
    time.sleep(2)
except:
    pass

# 変更適用
# 実際のページソースを取得する場合、Seleniumなどを使用してhtml_contentを取得
html_content = browser.page_source
soup = BeautifulSoup(html_content, 'html.parser')

# 注文番号を格納するリスト
order_ids = []

# 注文番号を含むdivをすべて見つける
order_divs = soup.find_all('div', class_='spacer--xFAdr full-width--2JiOP flex-row-start-wrap--1T_YI padding-top-custom-xxsmall--_xsnf')

for order_div in order_divs:
    # 「注文番号」を含むspanタグを探す（完全一致でなく部分一致に変更）
    label_span = order_div.find('span', class_='text-container--IAFCr size-body-3-low--3Tnry display-block--23DOu default-color--29EHk')
    if label_span and '注文番号' in label_span.text:
        # 次のspanタグから注文番号を取得
        order_number_span = label_span.find_next('span', class_='text-container--IAFCr size-body-3-low--3Tnry display-block--23DOu default-color--29EHk')
        if order_number_span:
            order_ids.append(order_number_span.text.strip())

print(order_ids)

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread.exceptions import APIError

# 認証情報を指定
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('/Users/wills3/Documents/python_storage/kaikake-6cc6532e286c.json', scope)

# 認証
gc = gspread.authorize(credentials)

def open_spreadsheet():
    retries = 3
    for _ in range(retries):
        try:
            # 「買掛」スプレッドシートを開く
            spreadsheet = gc.open('買掛')
            worksheet_rakuten = spreadsheet.worksheet('楽天市場')
            worksheet_dic = spreadsheet.worksheet('辞書')

            # まず「買掛」スプレッドシート内の「全部の前」シートを探す
            try:
                worksheet_all = spreadsheet.worksheet('全部の前')
                print('✔ 「買掛」スプレッドシート内の「全部の前」シートを使用します')
            except gspread.exceptions.WorksheetNotFound:
                print('⚠ 「全部の前」シートが見つかりません。次に「全部」スプレッドシートを確認します。')
                try:
                    spreadsheet_all = gc.open('全部')
                    worksheet_all = spreadsheet_all.worksheet('全部')
                    print('✔ 「全部」スプレッドシート内の「全部」シートを使用します')
                except gspread.exceptions.SpreadsheetNotFound:
                    raise Exception('「全部」スプレッドシートが見つかりません')
                except gspread.exceptions.WorksheetNotFound:
                    raise Exception('「全部」スプレッドシートに「全部」シートが見つかりません')

            return spreadsheet, worksheet_rakuten, worksheet_all, worksheet_dic

        except APIError as e:
            if e.response.status_code in [500, 503]:
                print(f"Error: {e}. Retrying in 3 seconds...")
                time.sleep(3)
            else:
                raise e

    raise Exception("Failed to open spreadsheet after multiple retries.")

spreadsheet, worksheet_rakuten, worksheet_all, worksheet_dic = open_spreadsheet()

# 楽天市場シートを検索する関数
def find_cells_with_retry(worksheet, query, retries=3, delay=5):
    attempt = 0
    while attempt < retries:
        try:
            cell_list = worksheet.findall(query)
            return cell_list
        except APIError as e:
            if e.response.status_code in [500, 503]:
                print(f"Internal server error encountered. Retrying in {delay} seconds...")
                time.sleep(delay)
                attempt += 1
            else:
                raise e
    raise Exception("Failed to find cells after multiple retries due to internal server errors.")

# 注文IDのリストをループ
for order_id in order_ids:
    time.sleep(1)
    try:
        cell_list_rakuten = find_cells_with_retry(worksheet_rakuten, order_id)
        if cell_list_rakuten:
            print()
            print("【 ※※※ 楽天市場シートに登録済み 】")
            print()
            print(order_id)
            print()
            print("-" * 80)
            print()
            continue

        else:
            time.sleep(1)
            # 楽天市場シートに該当がない場合、全部シートを検索
            cell_list_all = worksheet_all.findall(order_id)

            if cell_list_all:
                print()
                print("【 ※※※ 全部シートに登録済み 】")
                print()
                print(order_id)
                print()
                print("-" * 80)
                print()
                print()
                continue

            else:
                time.sleep(1)

                print()
                print("【 楽天市場シートおよび全部シートに未登録なので処理開始します 】")
                print()
                print("order_id: ", order_id)

                #---------------------------------------------------

                # ページソースの取得とパース
                html_content = browser.page_source
                soup = BeautifulSoup(html_content, 'html.parser')

                #---------------------------------------------------

                # `order_id` が格納されている 'div' タグを探す
                order_divs = soup.find_all('div', class_='spacer--xFAdr full-width--2JiOP flex-row-start-wrap--1T_YI padding-top-custom-xxsmall--_xsnf')

                # 一致する項目があるかどうかを確認する
                found = False

                for order_div in order_divs:
                    # '注文番号' に一致する 'span' タグを探し、その次の 'span' のテキストが `order_id` と一致するか確認
                    label_span = order_div.find('span', class_='text-container--IAFCr size-body-3-low--3Tnry display-block--23DOu default-color--29EHk')

                    if label_span and '注文番号' in label_span.text:
                        # 注文番号が含まれている `span` タグのテキストを確認
                        order_number_span = label_span.find_next('span')
                        if order_number_span and order_number_span.text.strip() == order_id:
                            print(f"一致しました: {order_number_span.text}")
                            found = True

                            # 該当の `div` タグの下にある `a` タグを探して order_number を含むリンクを取得
                            sibling_divs = soup.find_all('div', class_='spacer--xFAdr padding-right-small--2cgxR')
                            for div in sibling_divs:
                                a_tag = div.find('a', {'aria-label': '注文詳細'})
                                if a_tag and 'href' in a_tag.attrs and order_id in a_tag['href']:
                                    detail_url = a_tag['href']
                                    print("購入履歴詳細: ", detail_url)
                                    break  # 一度リンクが見つかったらループを終了

                            if detail_url:
                                # 個別ページにアクセス
                                browser.get(detail_url)
                                time.sleep(2)

#-------------------------------------------------------
#ここから個別処理
#-------------------------------------------------------

                                # 商品ごとに初期化する変数
                                shop_name = None
                                orderdate = None
                                total_td_number = 0  # 合計数を初期化
                                td_prices = []  # 価格リストをリセット
                                item_text = None  # 商品名をリセット
                                c_s_text = None  # カラー・サイズ情報をリセット

                                # 割引と合計金額の確認
                                discount_price = 0
                                postage_amount = 0
                                percent = None
                                point_amount = 0
                                discount_amount = 0
                                all_discount = 0
                                item_data = None
                                dictionary_data = None
                                not_span_data = None
                                div_number = None

                                # ショップ名（aria-label属性の値）と購入店URLを取得
                                html_content = browser.page_source
                                soup = BeautifulSoup(html_content, 'html.parser')

                                # 対象のクラスを持つ a タグを探す
                                a_tags = soup.find_all('a', class_='button--3SNaj size-l--xNF0z size-l-padding--Vs2pB border-radius--1ip29 no-padding--3mzqd type-link--8tP4V variant-gray-darker--3lUzx')

                                for a_tag in a_tags:
                                    if a_tag.has_attr('aria-label') and a_tag.has_attr('href'):
                                        shop_name = a_tag['aria-label']
                                        print('購入店舗名: ', shop_name)

                                #---------------------------------------
                                # 日時を取得
                                html_content = browser.page_source
                                soup = BeautifulSoup(html_content, 'html.parser')

                                time.sleep(1)
                                # 親のdivタグを取得
                                parent_div = soup.find('div', class_='spacer--xFAdr full-width--2JiOP flex-row-start-wrap--1T_YI padding-all-none--3xhH7')

                                if parent_div:
                                    # 全てのspanタグを取得
                                    spans = parent_div.find_all('span')
                                    if len(spans) >= 2:
                                        # 2つ目のspanタグから日付を取得
                                        orderdate = spans[1].get_text().strip()

                                        # 日付部分（YYYY/MM/DD）だけを抽出
                                        orderdate = orderdate.split('(')[0].strip()

                                        print('注文日: ', orderdate)
                                    else:
                                        print('※※※ 日付を取得できませんでした')
                                else:
                                    print('※※※ 親のdivタグが見つかりませんでした')

                                #---------------------------------------
                                # ここから割引や送料があるか確認
                                #---------------------------------------
                                #---------------------------------------
                                # クーポン利用の割引を確認
                                #---------------------------------------
                                # 全角数字を半角数字に変換する関数
                                def to_halfwidth(s):
                                    return s.translate(str.maketrans('０１２３４５６７８９', '0123456789'))

                                coupons = None
                                amount = None  # 修正: 割引額を初期化
                                percent = None  # 割引率を保持する変数

                                # HTMLから情報を取得
                                html_content = browser.page_source
                                soup = BeautifulSoup(html_content, 'html.parser')

                                # クーポンに関連するspanタグを取得
                                ttl_class = soup.find_all('span', class_='text-container--IAFCr size-body-4-low--N6wix default-color--29EHk')

                                # クーポンを検索
                                for ttl in ttl_class:
                                    text = ttl.get_text(strip=True)  # spanタグ内のテキストを取得

                                    # 通常のクーポンパターンを探す
                                    match = re.search(
                                        r'([０-９\d,]+)(円(?:OFF|オフ|クーポン)|%OFF|％OFF|%オフ)',  # 全角数字と半角数字、カンマ、「円クーポン」をサポート
                                        text
                                    )

                                    # "クーポンver" パターンを探す
                                    ver_match = re.search(r'クーポンver(\d+)', text)

                                    if match:
                                        # 抽出した金額部分を全角から半角に変換し、カンマを削除
                                        amount_str = to_halfwidth(match.group(1)).replace(',', '').strip()

                                        # 無効な`000`のようなパターンは除外
                                        if amount_str.isdigit() and int(amount_str) == 0:
                                            print("無効な金額です")
                                            continue  # 無効なクーポンはスキップ

                                        coupons = match.group(0)
                                        print("クーポン利用:", coupons)
                                        break

                                    elif ver_match:
                                        # "クーポンver" パターンが見つかった場合
                                        ver_number = int(to_halfwidth(ver_match.group(1)))
                                        percent = ver_number * 10  # 10%刻みの割引率として扱う
                                        print(f"クーポンverパターン: {percent}%OFF")
                                        coupons = f"{percent}%OFF"
                                        break

                                else:
                                    coupons = None
                                    print("クーポンなし")

                                # 追加の割引ロジック
                                discount_price = None
                                total_td_number = 0  # 合計数を保持する変数を初期化

                                # クーポン金額を抽出したら `discount_amount` に格納
                                if coupons:
                                    # クーポンのパターンを再度チェックして処理
                                    pattern = r'([０-９\d,]+)(円(?:OFF|オフ|クーポン)|%OFF|％OFF|%オフ)'  # 全角と半角の数字、カンマ、「円クーポン」に対応
                                    matches = re.findall(pattern, coupons)
                                    if matches:
                                        for match in matches:
                                            amount_str = to_halfwidth(match[0]).replace(',', '').strip()
                                            if not amount_str or int(amount_str) == 0:
                                                print("無効な金額です")
                                                continue

                                            try:
                                                amount = int(amount_str)
                                                unit = match[1]

                                                # 割引額を設定
                                                if unit in ["円OFF", "円オフ", "円クーポン"]:
                                                    discount_amount = amount
                                                    print(f"割引1: {discount_amount} 円割引")
                                                elif unit in ["%OFF", "％OFF", "%オフ"]:
                                                    discount_amount = amount  # 割引率の場合
                                                    print(f"割引: {discount_amount} %OFF")
                                            except ValueError:
                                                print("数値変換に失敗しました: ", amount_str)
                                    elif percent:
                                        # "クーポンver" パターンが見つかった場合の処理
                                        discount_amount = percent
                                        print(f"割引: {discount_amount}%OFF")
                                    else:
                                        print("クーポンが見つかりませんでした")

                                # `discount_amount` が更新されているか確認
                                if discount_amount:
                                    print("【割引金額】", discount_amount, "円または%")
                                    print()
                                else:
                                    print("※※※ 割引額がありません")

                                #---------------------------------------
                                # 商品の個数を取得して合計数を計算
                                #---------------------------------------

                                # HTMLから情報を取得
                                html_content = browser.page_source
                                soup = BeautifulSoup(html_content, 'html.parser')

                                # 個数を保持する変数を初期化
                                total_td_number = 0

                                # すべての該当するdivタグを取得
                                div_tags = soup.find_all('div', class_="text-display--1Iony type-body--1W5uC size-custom-12--18yBN align-left--1hi1x color-gray-darker--1SJFG line-height-x-medium--11iQZ layout-inline--1ajCj word-break-break-all--2ytck")

                                # 商品ごとの数量を取得してリストに追加
                                quantities = []  # 数量のリストを初期化

                                # 各divタグ内から数量を取得
                                for div_tag in div_tags:
                                    number_divs = div_tag.find_all('div', class_='text-display--1Iony type-body--1W5uC size-custom-12--18yBN align-right--2ACTn color-gray-darker--1SJFG layout-inline--1ajCj')

                                    if number_divs:
                                        for number_div in number_divs:
                                            number_text = number_div.get_text().strip()
                                            try:
                                                # 数値を取得しリストに追加
                                                number = int(number_text)
                                                print("【個数】", number)
                                                quantities.append(number)
                                            except ValueError:
                                                # 数値変換に失敗した場合のエラーメッセージ
                                                print("無効な数値:", number_text)

                                # 合計数をリセットして再計算
                                total_td_number = 0

                                # 取得した数量を合計
                                for idx, quantity in enumerate(quantities):
                                    total_td_number += quantity

                                # 合計数を表示
                                print("合計数:", total_td_number)

                                #---------------------------------------
                                # 割引と合計金額の確認
                                #---------------------------------------

                                # 割引金額と合計金額の確認
                                if coupons:
                                    time.sleep(2)

                                    # 正規表現パターンを定義
                                    pattern = r'([０-９\d,]+)(円(?:OFF|オフ)|%OFF|％OFF|%オフ)'  # 全角と半角の数字、カンマをサポート
                                    matches = re.findall(pattern, coupons)

                                    if matches:
                                        for match in matches:
                                            # 正しい金額部分を取得するための処理を改良
                                            amount_str = to_halfwidth(match[0]).replace(',', '').strip()

                                            # 金額が "000" や "0" の場合はスキップ
                                            if amount_str == '' or int(amount_str) == 0:
                                                print("無効な割引金額です")
                                                continue

                                            try:
                                                amount = int(amount_str)
                                                # ここに割引の処理を追加
                                            except ValueError:
                                                print("無効な数値形式:", amount_str)

                                            if unit in ["円OFF", "円オフ", "円クーポン"]:
                                                print(f"割引2: {amount} 円OFF")

                                                # 合計数が0以上でないと割引を適用しない
                                                if total_td_number > 0:
                                                    total_td_number = int(total_td_number)
                                                else:
                                                    print("※※※ 合計数が0または無効です")
                                                    continue

                                                # 合計金額を取得するためにHTMLから情報を取得
                                                html_content = browser.page_source
                                                soup = BeautifulSoup(html_content, 'html.parser')

                                                # '小計'が含まれているdivタグを探す
                                                spacer_divs = soup.find_all('div', class_='spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk')
                                                found = False

                                                for spacer_div in spacer_divs:
                                                    if spacer_div.find(text='小計'):
                                                        value_div = spacer_div.find('div', class_='number-display--3L2fG layout-inline--TxdJ_')
                                                        if value_div:
                                                            amount_div = value_div.find('div', class_='text-display--1Iony type-body--1W5uC size-large--3esfg align-right--2ACTn color-gray-darker--1SJFG layout-inline--1ajCj')
                                                            if amount_div:
                                                                total_amount = amount_div.text.strip().replace(',', '').replace('円', '')
                                                                try:
                                                                    total_amount = int(total_amount)
                                                                    print("【小計】 ", total_amount)
                                                                    found = True
                                                                    break
                                                                except ValueError:
                                                                    print("無効な金額形式です。")
                                                                    found = True
                                                                    break

                                                #---------------------------------------
                                                # 送料を抽出
                                                #---------------------------------------

                                                # 'spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk' クラスを持つ全てのdivを探す
                                                spacer_divs = soup.find_all('div', class_='spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk')
                                                found_postage = False

                                                # 各divの中をチェックして、'送料'が含まれているかを確認
                                                for spacer_div in spacer_divs:
                                                    if spacer_div.find(text='送料'):
                                                        # 'text-display--1Iony type-body--1W5uC size-large--3esfg align-right--2ACTn color-gray-darker--1SJFG layout-inline--1ajCj' クラスを持つdivを探す
                                                        postage_div = spacer_div.find('div', class_='text-display--1Iony type-body--1W5uC size-large--3esfg align-right--2ACTn color-gray-darker--1SJFG layout-inline--1ajCj')
                                                        if postage_div:
                                                            # 金額のテキストを取得し、コンマと円記号を取り除く
                                                            postage_amount = postage_div.text.strip().replace(',', '').replace('円', '')
                                                            try:
                                                                # 送料を整数に変換して表示
                                                                postage_amount = int(postage_amount)
                                                                print("【送料】 ", postage_amount)
                                                                found_postage = True
                                                                break
                                                            except ValueError:
                                                                print("無効な送料の形式です。")
                                                                found_postage = True
                                                                break

                                                # 送料が見つからなかった場合の処理
                                                if not found_postage:
                                                    print("※※※ 送料はかかっていません")

                                                #---------------------------------------
                                                # ポイント利用を抽出
                                                #---------------------------------------

                                                html_content = browser.page_source
                                                soup = BeautifulSoup(html_content, 'html.parser')

                                                # クーポン利用を抽出
                                                # 'spacer--xFAdr flex-row-space-between--2x2Xr padding-bottom-xxsmall--14_zk' クラスを持つ全てのdivを探す
                                                spacer_divs = soup.find_all('div', class_='spacer--xFAdr flex-row-space-between--2x2Xr padding-bottom-xxsmall--14_zk')
                                                found_coupon = False  # フラグを変更

                                                # 各divの中をチェックして、'クーポン利用'が含まれているかを確認
                                                for spacer_div in spacer_divs:
                                                    if spacer_div.find(text='クーポン利用'):
                                                        # 指定されたクラスを持つdivを探す
                                                        discount_div = spacer_div.find('div', class_='text-display--1Iony type-body--1W5uC size-large--3esfg align-right--2ACTn color-gray-darker--1SJFG layout-inline--1ajCj')
                                                        if discount_div:
                                                            # 金額のテキストを取得し、コンマと円記号を取り除く
                                                            discount_amount_str = discount_div.text.strip().replace(',', '').replace('円', '').replace('-', '')
                                                            try:
                                                                discount_amount = int(discount_amount_str)
                                                                print("【クーポン現金割引】", discount_amount)
                                                                found_coupon = True
                                                                break
                                                            except ValueError:
                                                                print("無効なクーポン割引の形式です。")
                                                                found_coupon = True
                                                                break
                                                else:
                                                    print("クーポン利用なし")

                                                #---------------------------------------
                                                # ポイント利用を抽出
                                                #---------------------------------------

                                                # 'spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk' クラスを持つ全てのdivを探す
                                                spacer_divs = soup.find_all('div', class_='spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk')
                                                found_point = False

                                                # 各divの中をチェックして、'ポイント利用'が含まれているかを確認
                                                for spacer_div in spacer_divs:
                                                    if spacer_div.find(text='ポイント利用'):
                                                        # 'text-display--1Iony type-body--1W5uC size-large--3esfg align-right--2ACTn color-gray-darker--1SJFG layout-inline--1ajCj' クラスを持つdivを探す
                                                        point_div = spacer_div.find('div', class_='text-display--1Iony type-body--1W5uC size-large--3esfg align-right--2ACTn color-gray-darker--1SJFG layout-inline--1ajCj')
                                                        if point_div:
                                                            # 金額のテキストを取得し、コンマと円記号、マイナス記号を取り除く
                                                            point_amount = point_div.text.strip().replace(',', '').replace('円', '').replace('-', '')
                                                            try:
                                                                # ポイントを整数に変換して表示
                                                                point_amount = int(point_amount)
                                                                print("【割引ポイント】 ", point_amount)
                                                                found_point = True
                                                                break
                                                            except ValueError:
                                                                print("無効なポイント利用の形式です。")
                                                                found_point = True
                                                                break

                                                # ポイントが見つからなかった場合の処理
                                                if not found_point:
                                                    print("※※※ ポイント利用はありません")

                                                #---------------------------------------
                                                # 割引金額を抽出
                                                #---------------------------------------

                                                # 'couponUse' クラスを持つtdタグを検索して、割引金額を取得
                                                discount_amount_element = soup.find('td', class_='couponUse')

                                                if discount_amount_element:
                                                    discount_amount_text = discount_amount_element.text.strip()
                                                    discount_amount_text = discount_amount_text.replace(',', '').replace('円', '').replace('-', '')
                                                    try:
                                                        discount_amount = int(discount_amount_text)
                                                        print("【割引】 ", discount_amount, "円")
                                                    except ValueError:
                                                        print("無効な割引金額形式です。")
                                                else:
                                                    if discount_amount == 0:  # すでに割引が適用されている場合、0にリセットしない
                                                        print("※※※ 割引金額はありません")

                                                #---------------------------------------
                                                # 支払い金額を抽出
                                                #---------------------------------------

                                                # 'spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk' クラスを持つ全てのdivを探す
                                                spacer_divs = soup.find_all('div', class_='spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk')
                                                found = False

                                                # 各divの中をチェックして、'支払い金額'が含まれているかを確認
                                                for spacer_div in spacer_divs:
                                                    if spacer_div.find(text='支払い金額'):
                                                        # 'value--3Z7Nj layout-inline--TxdJ_ size-custom-24--1fKI- color-gray-darker--3TKgt align-right--1LuZY' クラスを持つdivを探す
                                                        value_div = spacer_div.find('div', class_='value--3Z7Nj layout-inline--TxdJ_ size-custom-24--1fKI- color-gray-darker--3TKgt align-right--1LuZY')
                                                        if value_div:
                                                            # 金額のテキストを取得し、コンマと円記号を取り除く
                                                            payment_amount = value_div.text.strip().replace(',', '').replace('円', '')
                                                            try:
                                                                payment_amount = int(payment_amount)  # 変数名修正: `payment_amountt`を `payment_amount` に変更
                                                                print("【支払金額】 ", payment_amount, "円")
                                                                found = True
                                                                break
                                                            except ValueError:
                                                                print("無効な金額形式です。")
                                                                found = True
                                                                break

                                                print()
                                                #---------------------------------------
                                                # 割引金額とポイント利用を合算して処理
                                                #---------------------------------------

                                                if discount_amount or point_amount:
                                                    # None の場合は 0 に設定
                                                    discount_amount = discount_amount if discount_amount is not None else 0
                                                    point_amount = point_amount if point_amount is not None else 0
                                                    all_discount = discount_amount + point_amount

                                                    # 全体の割引金額と注文数を表示
                                                    print("全体の割引金額：", all_discount, "円")
                                                    print("全体の注文数:", total_td_number, "件")

                                                    # 合計数が0でなく、割引が存在する場合に1商品の割引額を計算
                                                    if total_td_number is not None and total_td_number > 0:
                                                        if all_discount > 0:
                                                            # 割引額を商品の合計数で割る。結果を小数点以下切り捨てるかは要確認
                                                            discount_price = all_discount // total_td_number
                                                            print("1商品の割引額：", discount_price, "円")
                                                        else:
                                                            print("※※※ 割引額がありません")
                                                    else:
                                                        print("※※※ 合計数が0または無効です")
                                                else:
                                                    print("※※※ 割引やポイントがありません")

                                            #---------------------------------------
                                            # %OFF 割引の処理
                                            #---------------------------------------

                                            elif unit in ["%OFF", "％OFF", "％オフ"]:
                                                print(f"※※※ 割引: {amount} %OFF")
                                                print()

                                                # スプレッドシートに入力する用に代入
                                                percent = amount

                                                # 合計金額を取得
                                                html_content = browser.page_source
                                                soup = BeautifulSoup(html_content, 'html.parser')

                                                # 'spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk' クラスを持つ全てのdivを探す
                                                spacer_divs = soup.find_all('div', class_='spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk')
                                                found = False

                                                # 各divの中をチェックして、'小計'が含まれているかを確認
                                                for spacer_div in spacer_divs:
                                                    if spacer_div.find(text='小計'):
                                                        # 'number-display--3L2fG layout-inline--TxdJ_' クラスを持つdivを探す
                                                        value_div = spacer_div.find('div', class_='number-display--3L2fG layout-inline--TxdJ_')
                                                        if value_div:
                                                            # 内部の金額を取得
                                                            amount_div = value_div.find('div', class_='text-display--1Iony type-body--1W5uC size-large--3esfg align-right--2ACTn color-gray-darker--1SJFG layout-inline--1ajCj')
                                                            if amount_div:
                                                                # 金額のテキストを取得し、コンマと円記号を取り除く
                                                                total_amount = amount_div.text.strip().replace(',', '').replace('円', '')
                                                                try:
                                                                    total_amount = int(total_amount)
                                                                    print("【小計】 ", total_amount)
                                                                    found = True
                                                                    break
                                                                except ValueError:
                                                                    print("無効な金額形式です。")
                                                                    found = True
                                                                    break

                                                #---------------------------------------
                                                # 送料を抽出
                                                #---------------------------------------

                                                # HTMLから最新の情報を取得
                                                html_content = browser.page_source
                                                soup = BeautifulSoup(html_content, 'html.parser')

                                                # 'spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk' クラスを持つすべてのdivタグを探す
                                                spacer_divs = soup.find_all('div', class_='spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk')
                                                found_postage = False

                                                # 各divの中をチェックして、'送料'というテキストが含まれているかを確認
                                                for spacer_div in spacer_divs:
                                                    if spacer_div.find(text='送料'):
                                                        # 'text-display--1Iony type-body--1W5uC size-large--3esfg align-right--2ACTn color-gray-darker--1SJFG layout-inline--1ajCj' クラスを持つdivを探す
                                                        postage_div = spacer_div.find('div', class_='text-display--1Iony type-body--1W5uC size-large--3esfg align-right--2ACTn color-gray-darker--1SJFG layout-inline--1ajCj')
                                                        if postage_div:
                                                            # 金額のテキストを取得し、コンマと円記号を取り除く
                                                            postage_amount = postage_div.text.strip().replace(',', '').replace('円', '')
                                                            try:
                                                                postage_amount = int(postage_amount)
                                                                print("【送料】 ", postage_amount)
                                                                found_postage = True
                                                                break
                                                            except ValueError:
                                                                print("無効な送料の形式です。")
                                                                found_postage = True
                                                                break

                                                #---------------------------------------
                                                # ポイント利用を抽出
                                                #---------------------------------------

                                                # 'spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk' クラスを持つすべてのdivタグを取得
                                                spacer_divs = soup.find_all('div', class_='spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk')
                                                found_point = False

                                                # 各divをチェックして、'ポイント利用'が含まれているかを確認
                                                for spacer_div in spacer_divs:
                                                    if spacer_div.find(text='ポイント利用'):
                                                        # 'text-display--1Iony type-body--1W5uC size-large--3esfg align-right--2ACTn color-gray-darker--1SJFG layout-inline--1ajCj' クラスを持つdivを探す
                                                        point_div = spacer_div.find('div', class_='text-display--1Iony type-body--1W5uC size-large--3esfg align-right--2ACTn color-gray-darker--1SJFG layout-inline--1ajCj')
                                                        if point_div:
                                                            # 金額のテキストを取得し、コンマと円記号を取り除く
                                                            point_amount = point_div.text.strip().replace(',', '').replace('円', '').replace('-', '')
                                                            try:
                                                                point_amount = int(point_amount)
                                                                print("【割引ポイント】", point_amount)
                                                                found_point = True
                                                                break
                                                            except ValueError:
                                                                print("無効なポイント利用の形式です。")
                                                                found_point = True
                                                                break

                                                # 割引金額を抽出
                                                discount_amount = soup.find('td', class_='couponUse')
                                                if discount_amount:
                                                    discount_amount = discount_amount.text.strip()
                                                    # コンマと円記号を取り除き、数値に変換
                                                    try:
                                                        discount_amount = int(discount_amount.replace(',', '').replace('円', '').replace('-', ''))
                                                        print("【割引】", discount_amount)
                                                    except ValueError:
                                                        print("無効な割引金額です。")

                                                # 支払い金額を抽出
                                                # 'spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk' クラスを持つ全てのdivを探す
                                                spacer_divs = soup.find_all('div', class_='spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk')
                                                found = False

                                                # 各divの中をチェックして、'支払い金額'が含まれているかを確認
                                                for spacer_div in spacer_divs:
                                                    if spacer_div.find(text='支払い金額'):
                                                        # 'value--3Z7Nj layout-inline--TxdJ_ size-custom-24--1fKI- color-gray-darker--3TKgt align-right--1LuZY' クラスを持つdivを探す
                                                        value_div = spacer_div.find('div', class_='value--3Z7Nj layout-inline--TxdJ_ size-custom-24--1fKI- color-gray-darker--3TKgt align-right--1LuZY')
                                                        if value_div:
                                                            payment_amount = value_div.text.strip()
                                                            # コンマと円記号を取り除き、数値に変換
                                                            try:
                                                                payment_amount = int(payment_amount.replace(',', '').replace('円', ''))
                                                                print("【支払金額2】", payment_amount)
                                                                found = True
                                                                break
                                                            except ValueError:
                                                                print("無効な金額形式です。")
                                                                found = True
                                                                break

                                                # 割引やポイントを確認
                                                print()
                                                if discount_amount or point_amount:
                                                    # None チェックを簡略化し、割引金額とポイントを合算
                                                    discount_amount = discount_amount or 0
                                                    point_amount = point_amount or 0
                                                    all_discount = discount_amount + point_amount
                                                    print("全体の割引金額：", all_discount, "円")
                                                    print("全体の注文数:", total_td_number, "件")

                                                    # 1商品の割引額を計算
                                                    if total_td_number > 0:
                                                        if all_discount > 0:
                                                            discount_price = all_discount // total_td_number
                                                            print("1商品の割引額：", discount_price, "円")
                                                        else:
                                                            print("※※※ 割引額がありません")
                                                    else:
                                                        print("※※※ 合計数が 0 または無効です")
                                                else:
                                                    print("※※※ 割引やポイントがありません")

                                                # total_td_number と送料の確認
                                                if total_td_number != 0:
                                                    if postage_amount:  # None チェックは不要、ゼロ値も除外される
                                                        each_shipping = postage_amount // total_td_number
                                                        print("1商品の送料：", each_shipping, "円")
                                                    else:
                                                        print("1※※※ 送料はかかっていません")
                                                else:
                                                    print("※※※ 合計数が 0 または無効です")

                                    #------------------------------------------------------------------------

                                    else:
                                        # total_td_numberを整数型に変換してから割り算を行う
                                        total_td_number = int(total_td_number)  # total_td_numberも整数型に変換

                                        # 合計金額を取得
                                        html_content = browser.page_source
                                        soup = BeautifulSoup(html_content, 'html.parser')

                                        # 'spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk' クラスを持つ全てのdivを探す
                                        spacer_divs = soup.find_all('div', class_='spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk')

                                        # 各divの中をチェックして、'小計'が含まれているかを確認
                                        for spacer_div in spacer_divs:
                                            if spacer_div.find(text='小計'):
                                                # 'number-display--3L2fG layout-inline--TxdJ_' クラスを持つdivを探す
                                                value_div = spacer_div.find('div', class_='number-display--3L2fG layout-inline--TxdJ_')
                                                if value_div:
                                                    # 内部の金額を取得
                                                    amount_div = value_div.find('div', class_='text-display--1Iony type-body--1W5uC size-large--3esfg align-right--2ACTn color-gray-darker--1SJFG layout-inline--1ajCj')
                                                    if amount_div:
                                                        # 金額のテキストを取得し、コンマと円記号を取り除く
                                                        total_amount = amount_div.text.strip().replace(',', '').replace('円', '')
                                                        try:
                                                            total_amount = int(total_amount)
                                                            print("【小計】 ", total_amount)
                                                            break
                                                        except ValueError:
                                                            print(f"無効な金額形式です: {total_amount}")
                                                            break

                                        # 送料を抽出　ここ
                                        # 'spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk' クラスを持つ全てのdivを探す
                                        spacer_divs = soup.find_all('div', class_='spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk')
                                        found_postage = False

                                        # 各divの中をチェックして、'送料'が含まれているかを確認
                                        for spacer_div in spacer_divs:
                                            if spacer_div.find(text='送料'):
                                                # 'text-display--1Iony type-body--1W5uC size-large--3esfg align-right--2ACTn color-gray-darker--1SJFG layout-inline--1ajCj' クラスを持つdivを探す
                                                postage_div = spacer_div.find('div', class_='text-display--1Iony type-body--1W5uC size-large--3esfg align-right--2ACTn color-gray-darker--1SJFG layout-inline--1ajCj')
                                                if postage_div:
                                                    # 金額のテキストを取得し、コンマと円記号を取り除く
                                                    postage_amount = postage_div.text.strip().replace(',', '').replace('円', '')
                                                    try:
                                                        postage_amount = int(postage_amount)
                                                        print("【送料】 ", postage_amount)
                                                        found_postage = True
                                                        break
                                                    except ValueError:
                                                        print("無効な送料の形式です。")
                                                        found_postage = True
                                                        break

                                        # ポイント利用を抽出
                                        # 'spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk' クラスを持つ全てのdivを探す
                                        spacer_divs = soup.find_all('div', class_='spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk')
                                        found_point = False

                                        # 各divの中をチェックして、'ポイント利用'が含まれているかを確認
                                        for spacer_div in spacer_divs:
                                            if spacer_div.find(text='ポイント利用'):
                                                # 'text-display--1Iony type-body--1W5uC size-large--3esfg align-right--2ACTn color-gray-darker--1SJFG layout-inline--1ajCj' クラスを持つdivを探す
                                                point_div = spacer_div.find('div', class_='text-display--1Iony type-body--1W5uC size-large--3esfg align-right--2ACTn color-gray-darker--1SJFG layout-inline--1ajCj')
                                                if point_div:
                                                    # 金額のテキストを取得し、コンマと円記号を取り除く
                                                    point_amount = point_div.text.strip().replace(',', '').replace('円', '').replace('-', '')
                                                    try:
                                                        point_amount = int(point_amount)
                                                        print("【割引ポイント】 ", point_amount)
                                                        found_point = True
                                                        break
                                                    except ValueError:
                                                        print("無効なポイント利用の形式です。")
                                                        found_point = True
                                                        break

                                        # 支払い金額
                                        # 'spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk' クラスを持つ全てのdivを探す
                                        spacer_divs = soup.find_all('div', class_='spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk')
                                        found = False

                                        # 各divの中をチェックして、'支払い金額'が含まれているかを確認
                                        for spacer_div in spacer_divs:
                                            if spacer_div.find(text='支払い金額'):
                                                # 'value--3Z7Nj layout-inline--TxdJ_ size-custom-24--1fKI- color-gray-darker--3TKgt align-right--1LuZY' クラスを持つdivを探す
                                                value_div = spacer_div.find('div', class_='value--3Z7Nj layout-inline--TxdJ_ size-custom-24--1fKI- color-gray-darker--3TKgt align-right--1LuZY')
                                                if value_div:
                                                    # 金額のテキストを取得し、コンマと円記号を取り除く
                                                    payment_amount = value_div.text.strip().replace(',', '').replace('円', '')
                                                    try:
                                                        payment_amount = int(payment_amount)
                                                        print("【支払金額3】 ", payment_amount)
                                                        found = True
                                                        break
                                                    except ValueError:
                                                        print("無効な金額形式です。")
                                                        found = True
                                                        break


                                        print("確認：",discount_amount)

                                        print()
                                        if discount_amount or point_amount:
                                            discount_amount = discount_amount if discount_amount is not None else 0
                                            point_amount = point_amount if point_amount is not None else 0
                                            all_discount = discount_amount + point_amount
                                            print("全体の割引金額：", all_discount, "円")
                                            print("全体の注文数:", total_td_number, "件")



                                        if total_td_number is not None and total_td_number != 0:
                                            if all_discount > 0:
                                                discount_price = all_discount // total_td_number
                                                print("1商品の割引額：", discount_price, "円")

                                                print()
                                            else:
                                                print("※※※ 割引額がありません")
                                        else:
                                            print("※※※ 合計数が 0 または無効です")

                                #--------------------------------------------------    

                                else:
                                    print("※※※ クーポン割引がありません")
                                    print()

                                    html_content = browser.page_source
                                    soup = BeautifulSoup(html_content, 'html.parser')

                                    # 変更前のコード
                                    # 合計金額を抽出
                                    #total_amount = soup.find('div', class_='value--3Z7Nj layout-inline--TxdJ_ size-custom-20--10d5j  color-gray-darker--3TKgt align-right--1LuZY')
                                    #if total_amount:
                                        #total_amount = total_amount.text                   
                                        # コンマと円記号を取り除く
                                        #total_amount = total_amount.replace(',', '').replace('円', '')
                                        #total = int(total_amount)
                                        #print("【合計】 　", total_amount)


                                    # number-display--3L2fG クラスを持つ全ての div を取得
                                    total_amount_divs = soup.find_all('div', class_='number-display--3L2fG layout-inline--TxdJ_')

                                    # 取得した数値のリスト
                                    amounts = []

                                    # 合計金額を取得
                                    html_content = browser.page_source
                                    soup = BeautifulSoup(html_content, 'html.parser')

                                    # 'spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk' クラスを持つ全てのdivを探す
                                    spacer_divs = soup.find_all('div', class_='spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk')
                                    found = False

                                    # 各divの中をチェックして、'小計'が含まれているかを確認
                                    for spacer_div in spacer_divs:
                                        if spacer_div.find(text='小計'):
                                            # 'number-display--3L2fG layout-inline--TxdJ_' クラスを持つdivを探す
                                            value_div = spacer_div.find('div', class_='number-display--3L2fG layout-inline--TxdJ_')
                                            if value_div:
                                                # 内部の金額を取得
                                                amount_div = value_div.find('div', class_='text-display--1Iony type-body--1W5uC size-large--3esfg align-right--2ACTn color-gray-darker--1SJFG layout-inline--1ajCj')
                                                if amount_div:
                                                    # 金額のテキストを取得し、コンマと円記号を取り除く
                                                    total_amount = amount_div.text.strip().replace(',', '').replace('円', '')
                                                    try:
                                                        total_amount = int(total_amount)
                                                        print("【小計】 ", total_amount)
                                                        found = True
                                                        break
                                                    except ValueError:
                                                        print("無効な金額形式です。")
                                                        found = True
                                                        break

                                    # 'spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk' クラスを持つ全てのdivを探す
                                    spacer_divs = soup.find_all('div', class_='spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk')
                                    found_postage = False

                                    # 各divの中をチェックして、'送料'が含まれているかを確認
                                    for spacer_div in spacer_divs:
                                        if spacer_div.find(text='送料'):
                                            # 'text-display--1Iony type-body--1W5uC size-large--3esfg align-right--2ACTn color-gray-darker--1SJFG layout-inline--1ajCj' クラスを持つdivを探す
                                            postage_div = spacer_div.find('div', class_='text-display--1Iony type-body--1W5uC size-large--3esfg align-right--2ACTn color-gray-darker--1SJFG layout-inline--1ajCj')
                                            if postage_div:
                                                # 金額のテキストを取得し、コンマと円記号を取り除く
                                                postage_amount = postage_div.text.strip().replace(',', '').replace('円', '')
                                                try:
                                                    postage_amount = int(postage_amount)
                                                    print("【送料】 ", postage_amount)
                                                    found_postage = True
                                                    break
                                                except ValueError:
                                                    print("無効な送料の形式です。")
                                                    found_postage = True
                                                    break

                                    # ポイント利用を抽出
                                    # 'spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk' クラスを持つ全てのdivを探す
                                    spacer_divs = soup.find_all('div', class_='spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk')
                                    found_point = False

                                    # 各divの中をチェックして、'ポイント利用'が含まれているかを確認
                                    for spacer_div in spacer_divs:
                                        if spacer_div.find(text='ポイント利用'):
                                            point_div = spacer_div.find('div', class_='text-display--1Iony type-body--1W5uC size-large--3esfg align-right--2ACTn color-gray-darker--1SJFG layout-inline--1ajCj')
                                            if point_div:
                                                point_amount = point_div.text.strip().replace(',', '').replace('円', '').replace('-', '')
                                                try:
                                                    point_amount = int(point_amount)
                                                    print("【割引ポイント】 ", point_amount)
                                                    found_point = True
                                                    break
                                                except ValueError:
                                                    print("無効なポイント利用の形式です。")
                                                    found_point = True
                                                    break

                                    # クーポン利用を抽出
                                    spacer_divs = soup.find_all('div', class_='spacer--xFAdr flex-row-space-between--2x2Xr padding-bottom-xxsmall--14_zk')
                                    found_coupon = False

                                    for spacer_div in spacer_divs:
                                        if spacer_div.find(text='クーポン利用'):
                                            discount_div = spacer_div.find('div', class_='text-display--1Iony type-body--1W5uC size-large--3esfg align-right--2ACTn color-gray-darker--1SJFG layout-inline--1ajCj')
                                            if discount_div:
                                                discount_amount_str = discount_div.text.strip().replace(',', '').replace('円', '').replace('-', '')
                                                try:
                                                    discount_amount = int(discount_amount_str)
                                                    print("【クーポン現金割引】", discount_amount)
                                                    found_coupon = True
                                                    break
                                                except ValueError:
                                                    print("無効なクーポン割引の形式です。")
                                                    found_coupon = True
                                                    break
                                    else:
                                        print("クーポン利用なし")

                                    # 支払い金額を抽出
                                    spacer_divs = soup.find_all('div', class_='spacer--xFAdr flex-row-space-between-end--1qEGg padding-bottom-xxsmall--14_zk')
                                    found = False

                                    for spacer_div in spacer_divs:
                                        if spacer_div.find(text='支払い金額'):
                                            value_div = spacer_div.find('div', class_='value--3Z7Nj layout-inline--TxdJ_ size-custom-24--1fKI- color-gray-darker--3TKgt align-right--1LuZY')
                                            if value_div:
                                                payment_amount = value_div.text.strip().replace(',', '').replace('円', '')
                                                try:
                                                    payment_amount = int(payment_amount)
                                                    print("【支払金額】 ", payment_amount)
                                                    found = True
                                                    break
                                                except ValueError:
                                                    print("無効な金額形式です。")
                                                    found = True
                                                    break

                                    # 割引金額とポイントの合算処理
                                    if discount_amount or point_amount:
                                        discount_amount = discount_amount if discount_amount is not None else 0
                                        point_amount = point_amount if point_amount is not None else 0
                                        all_discount = discount_amount + point_amount

                                        print("全体の割引金額：", all_discount, "円")
                                        print("全体の注文数:", total_td_number, "件")

                                        # 1商品の割引額を計算
                                        if all_discount > 0:
                                            if total_td_number > 0:
                                                discount_price = all_discount // total_td_number
                                                print("1商品の割引額：", discount_price, "円")
                                            else:
                                                print("※※※ 合計数が0または無効です")
                                        else:
                                            print("※※※ 割引額がありません")
                                    else:
                                        print("※※※ 割引やポイントがありません")

                            #--------------------------------------------------

                            each_shipping = None

                            if total_td_number != 0:
                                if postage_amount is not None and postage_amount != 0:  # None チェックを追加
                                    each_shipping = postage_amount // total_td_number
                                    print("1商品の送料：", each_shipping, "円")
                                    print()
                                else:
                                    print("2※※※ 送料はかかっていません")
                                    print()
                            else:
                                print()

                            print("-" * 8)

                            #--------------------------------------------------
                            # ここから個別処理
                            #--------------------------------------------------

                            total_td_number = 0  # 合計数を保持する変数を初期化

                            td_prices = []

                            # 各カラー・サイズ情報を取得
                            html_content = browser.page_source
                            soup = BeautifulSoup(html_content, 'html.parser')

                            # 'spacer--xFAdr block--2PK_L padding-all-none--3xhH7 border-bottom-gray-1px--2y2-c' を持つ div タグを探す
                            div_tag = soup.find('div', class_='spacer--xFAdr block--2PK_L padding-all-none--3xhH7 border-bottom-gray-1px--2y2-c')

                            # a タグを格納するリストを初期化
                            a_tags_list = []

                            if div_tag:
                                # 'spacer--xFAdr flex-row-start--2xPqj padding-left-xlarge--2d9GV' を持つ div タグを全て取得する
                                inner_div_tags = div_tag.find_all('div', class_='spacer--xFAdr flex-row-start--2xPqj padding-left-xlarge--2d9GV')

                                # 各内側の div タグ内の a タグを探し、リストに格納する
                                for inner_div_tag in inner_div_tags:
                                    # そのdivの中でさらに 'spacer--xFAdr padding-bottom-xsmall--38EdM' の div を探して、その中のaタグを取得
                                    target_div = inner_div_tag.find('div', class_='spacer--xFAdr padding-bottom-xsmall--38EdM')
                                    if target_div:
                                        a_tags = target_div.find_all('a')

                                        # 取得した a タグをリストに追加
                                        if a_tags:
                                            a_tags_list.extend(a_tags)

                            # 商品ごとのカラー・サイズを抽出して格納するリスト
                            c_s_texts = []

                            # 'spacer--xFAdr block--2PK_L padding-all-none--3xhH7 border-bottom-gray-1px--2y2-c' を持つ div タグを探す
                            div_tag = soup.find('div', class_='spacer--xFAdr block--2PK_L padding-all-none--3xhH7 border-bottom-gray-1px--2y2-c')

                            # 商品情報リストを初期化
                            product_info_list = []

                            if div_tag:
                                column_divs = div_tag.find_all('div', class_='spacer--xFAdr flex-column--zlXTp padding-all-none--3xhH7')

                                print(f"{len(column_divs)} 件の商品情報が見つかりました。")
                                print()

                                for index, column_div in enumerate(column_divs):
                                    # 商品名を含む a タグを取得
                                    a_tag = column_div.find('a', class_='button--3SNaj')
                                    item_text = a_tag.get_text(strip=True) if a_tag else "商品名がありません"
                                    href = a_tag.get('href') if a_tag else "URLがありません"

                                    # カラー・サイズ情報を初期化
                                    color_size_texts = []

                                    # "spacer--xFAdr padding-bottom-xsmall--38EdM" が振られた div の中にある情報を取得
                                    content_wrappers = column_div.find_all('div', class_='spacer--xFAdr padding-bottom-xsmall--38EdM')
                                    for content_wrapper in content_wrappers:
                                        # すべての子要素のdivからテキストを取得
                                        text_divs = content_wrapper.find_all(
                                            'div',
                                            class_='text-display--1Iony type-body--1W5uC size-custom-12--18yBN align-left--1hi1x color-gray-darker--1SJFG line-height-x-medium--11iQZ layout-block--3v24U word-break-break-all--2ytck'
                                        )
                                        for text_div in text_divs:
                                            text = text_div.get_text(strip=True)
                                            if text:  # テキストがあればリストに追加
                                                color_size_texts.append(text)

                                    # 取得したテキストを連結して1つの文字列にする
                                    color_size_text = ' '.join(color_size_texts) if color_size_texts else ""

                                    # カラー・サイズ情報をリストに追加
                                    c_s_texts.append(color_size_text)

                                    # 商品名とカラー・サイズ情報をリストに格納
                                    product_info_list.append({
                                        '商品名': item_text,
                                        '商品URL': href,
                                        'カラー・サイズ情報': color_size_text
                                    })

                            # 商品情報の出力
                            for product in product_info_list:
                                print(f"商品名: {product['商品名']}")
                                print(f"商品URL: {product['商品URL']}")
                                print(f"カラー・サイズ情報: {product['カラー・サイズ情報']}")
                                print("-" * 50)

                            print()
                            print()
                            print()

                            #---------------------------------------------- 

                            # 商品番号をURLから抽出する関数
                            def extract_part_from_url(url):
                                pattern = r"https://item\.rakuten\.co\.jp/[^/]+/([^/]+)/"
                                match = re.search(pattern, url)
                                if match:
                                    return match.group(1)
                                else:
                                    return None

                            #---------------------------------------------- 

                            # すべての商品の金額を格納するリスト
                            td_prices = []

                            # 商品名リストに対して対応する金額を適用
                            if a_tags_list:
                                # a_tags_listとquantitiesの両方を同時に取り出す
                                for idx, (a_tag, td_number) in enumerate(zip(a_tags_list, quantities)):
                                    # 商品名を取得
                                    span_tag = a_tag.find('span')
                                    if span_tag:
                                        item_text = span_tag.get_text()
                                        href = a_tag.get('href')

                                        # カラー・サイズのテキストを取得
                                        c_s_text = c_s_texts[idx] if idx < len(c_s_texts) else ""

                                        # 変数を使用する前に初期化
                                        extracted_part = None  # または空文字列''で初期化

                                        # 商品情報を生成
                                        not_span_data = f"{item_text}\n{c_s_text}"
                                        item_data = f"{item_text}\n{extracted_part}\n{c_s_text}" if extracted_part else not_span_data

                                        # 商品名とURLを出力
                                        print(f"商品名: {item_text}")
                                        if href:
                                            print(f"商品URL: {href}")

                                            # カラー・サイズのテキストを出力
                                            print(f"カラー・サイズ: {c_s_text}")

                                            #---------------------------------------------- 

                                            # 商品情報を生成する際にカラー・サイズ情報を追加
                                            if c_s_text:
                                                not_span_data = f"{item_text}\n{c_s_text}"
                                                item_data = f"{item_text}\n{extracted_part}\n{c_s_text}" if extracted_part else not_span_data
                                            else:
                                                not_span_data = item_text
                                                item_data = f"{item_text}\n{extracted_part}" if extracted_part else item_text

                                            # 金額のテキストを出力
                                            if idx < len(td_prices):
                                                td_price = td_prices[idx]  # td_pricesリストから順番に金額を取得
                                                print(f"単価: {td_price}")

                                            # td_numberを使った処理
                                            #print(f"【個数】 商品 {idx + 1}: {td_number}")

                                            # カラー・サイズ情報がある場合のみ、not_span_data にカラー・サイズ情報を含める
                                            if c_s_text:
                                                not_span_data = item_text + '\n' + c_s_text
                                            else:
                                                not_span_data = item_text

                                            # 商品番号を使った情報の生成
                                            extracted_part = None
                                            if href:
                                                # 商品番号をURLから取得
                                                extracted_part = extract_part_from_url(href)
                                                if extracted_part:
                                                    dictionary_data = extracted_part + c_s_text
                                                    item_data = item_text + '\n' + extracted_part + c_s_text
                                                else:
                                                    not_span_data = item_text + '\n' + c_s_text

                                            # 金額を取得する処理
                                            html_content = browser.page_source
                                            soup = BeautifulSoup(html_content, 'html.parser')

                                            # 正常に金額を取得するために、先ほどのロジックを応用
                                            # number-display--3L2fG クラスを持つすべての div を取得
                                            total_amount_divs = soup.find_all('div', class_='number-display--3L2fG layout-inline--TxdJ_')

                                            # 商品ごとの金額をリストに格納
                                            td_prices = []  # 初期化

                                            for total_amount_div in total_amount_divs:
                                                # 内部の value--3Z7Nj クラスを持つ div を探す
                                                value_div = total_amount_div.find('div', class_='value--3Z7Nj layout-inline--TxdJ_ size-custom-20--10d5j color-gray-darker--3TKgt align-right--1LuZY')

                                                if value_div:
                                                    price_text = value_div.get_text(strip=True).replace('円', '').replace(',', '')
                                                    try:
                                                        # 金額を整数に変換してリストに追加
                                                        price_value = int(price_text)
                                                        td_prices.append(price_value)
                                                        #print(f"取得した金額: {price_value}")
                                                    except ValueError:
                                                        print(f"無効な金額: {price_text}")

                                            # 最終的に取得した金額リストを出力
                                            print(f"取得した金額リスト: {td_prices}")

                                            # 価格リストに存在するか確認し、該当商品に紐づける
                                            if idx < len(td_prices):
                                                td_price = td_prices[idx]  # インデックスで取得
                                                print(f"単価: {td_price}")

                                            # 合計数をリセット
                                            total_td_number = 0

                                            # 商品ごとの数量を処理
                                            for idx, quantity in enumerate(quantities):
                                                # 各商品の数量を出力
                                                #print(f"【個数】 商品 {idx + 1}: {quantity}")

                                                # 合計数に追加
                                                total_td_number += quantity

                                            # 正確な合計数を出力
                                            #print("合計数: ", total_td_number)

                                            #----------------------------------------------

                                            # 商品の個別ページで商品番号がない時のシートに書き込む内容の変数
                                            not_span_data = item_text + '\n' + c_s_text
                                            url_href = None

                                            # 個別の商品URLを取得
                                            print("【商品ページ / 商品番号】 ")
                                            print(href)

                                            # 関数でURLから商品番号を取得するために代入し直す
                                            current_url = href

                                            #----------------------------------------------   

                                            # 上部で関数を定義
                                            def extract_part_from_url(url):
                                                pattern = r"https://item\.rakuten\.co\.jp/[^/]+/([^/]+)/"
                                                match = re.search(pattern, url)
                                                if match:
                                                    return match.group(1)
                                                else:
                                                    return None

                                            # メインのコード
                                            extracted_part = None

                                            if href:
                                                print()
                                                print('※ 商品番号をURLから取得します')

                                                # 関数を使って抽出
                                                extracted_part = extract_part_from_url(href)
                                                print('商品番号:', extracted_part)

                                                #----------------------------------------------

                                                if extracted_part:
                                                    print()
                                                    print("-" * 8)
                                                    print("↓↓↓↓↓↓↓↓")
                                                    print()
                                                    dictionary_data = extracted_part + c_s_text
                                                    print()

                                                    item_data = item_text + '\n' + extracted_part + c_s_text
                                                    print()

                                                    # 商品の個別ページで商品番号がない時のシートに書き込む内容の変数
                                                    not_span_data = item_text + '\n' + c_s_text

                                                else:
                                                    print("ーーーーーーーーーーーーー ※※※ URLから商品番号を取得できませんでした")

                                                    # 商品の個別ページで商品番号がない時のシートに書き込む内容の変数
                                                    not_span_data = item_text + '\n' + c_s_text
                                                    print()
                                                    print("-" * 8)
                                                    print("↓↓↓↓↓↓↓↓")
                                                    print()

                                            #----------------------------------------------

                                            else:
                                                print('ーーーーーーーーーーーーー ※※※ 商品URLを取得できませんでした')

                                                not_span_data = item_text + '\n' + c_s_text
                                                print()
                                                print("-" * 8)
                                                print("↓↓↓↓↓↓↓↓")
                                                print()

                                        #----------------------------------------------  

                                        else:
                                            print()
                                            print('ーーーーーーーーーーーーー ※※※ 商品情報がありません_1')

                                            # 商品の個別ページで商品番号がない時のシートに書き込む内容の変数
                                            not_span_data = item_text + '\n' + c_s_text
                                            print(not_span_data)
                                            print()
                                            print("-" * 8)
                                            print("↓↓↓↓↓↓↓↓")
                                            print()

                                    #----------------------------------------------  

                                    else:
                                        print()
                                        print('ーーーーーーーーーーーーー ※※※ 商品情報がありません_2')

                                        # 商品の個別ページで商品番号がない時のシートに書き込む内容の変数
                                        not_span_data = item_text + '\n' + c_s_text
                                        print(not_span_data)
                                        print()
                                        print("-" * 8)
                                        print("↓↓↓↓↓↓↓↓")
                                        print()

                                    #----------------------------------------------                                        
                                    # ここからスプレッドシートに書き込み
                                    #---------------------------------------------- 

                                    print('接続2')
                                    print()

                                    # 関数を使って取得
                                    spreadsheet, worksheet_rakuten, worksheet_all, worksheet_dic = open_spreadsheet()

                                    # 辞書に登録されているか確認してSKU管理番号を取得
                                    if extracted_part:
                                        # 商品番号がある場合注文の個数分繰り返す
                                        for _ in range(td_number):
                                            # 全セルを検索
                                            cell_list = worksheet_dic.findall(dictionary_data)

                                            worksheet = worksheet_dic

                                            # 値を保存するリスト
                                            values_list = []

                                            # 検索結果が存在する場合
                                            if cell_list:

                                                # cell_list 内のセルごとに処理
                                                for cell in cell_list:
                                                    # 現在のセルの row 情報を取得
                                                    row = cell.row

                                                    # 列を "4" に変更して新たにスプレッドシートの値を取得
                                                    new_cell = worksheet_dic.cell(row, 4)
                                                    # 取得した値をリストに保存（Noneの場合は空文字に変換）
                                                    values_list.append(new_cell.value if new_cell.value is not None else "")
                                                    cell_sku = values_list[-1]
                                                    print('SKU管理番号: ', cell_sku)
                                                    print()

                                                    # 列を "5" に変更して新たにスプレッドシートの値を取得
                                                    new_cell = worksheet.cell(row, 5)
                                                    # 取得した値をリストに保存（Noneの場合は空文字に変換）
                                                    values_list.append(new_cell.value if new_cell.value is not None else "")
                                                    print(f"セル {row}, 5: {values_list[-1]}")

                                                    # 列を "6" に変更して新たにスプレッドシートの値を取得
                                                    new_cell = worksheet.cell(row, 6)
                                                    # 取得した値をリストに保存（Noneの場合は空文字に変換）
                                                    values_list.append(new_cell.value if new_cell.value is not None else "")
                                                    print(f"セル {row}, 6: {values_list[-1]}")


                                                    # 列を "2" に変更して新たにスプレッドシートの値を取得
                                                    new_cell = worksheet.cell(row, 2)
                                                    # 取得した値をリストに保存（Noneの場合は空文字に変換）
                                                    values_list.append(new_cell.value if new_cell.value is not None else "")
                                                    print(f"セル {row}, 2: {values_list[-1]}")
                                                    print()

                                                #--------------------------------------------------

                                                print()
                                                print('接続3')
                                                print()

                                                # 関数を使って取得
                                                spreadsheet, worksheet_rakuten, worksheet_all, worksheet_dic = open_spreadsheet()

                                                # C7以降で空いている場所を探す
                                                cell_list = worksheet_rakuten.range('C7:C')

                                                worksheet = worksheet_rakuten

                                                # 最初に空いているセルを見つける
                                                empty_cell = None
                                                for cell in cell_list:
                                                    if not cell.value:
                                                        empty_cell = cell
                                                        break

                                                # 空いているセルが見つかった場合、同じ行のG列に値を入力する
                                                if empty_cell:
                                                    row = empty_cell.row

                                                    # 日付を入力
                                                    worksheet.update_acell(f'A{row}', orderdate)
                                                    print('購入日: ', orderdate)

                                                    # ショップ名を入力
                                                    worksheet.update_acell(f'B{row}', shop_name)
                                                    print('ショップ名: ', shop_name)

                                                    # 注文番号を入力
                                                    worksheet.update_acell(f'C{row}', order_id)
                                                    print('注文番号: ', order_id)

                                                    # SKU管理番号を入力
                                                    worksheet.update_acell(f'G{row}', cell_sku)
                                                    print('SKU管理番号: ', cell_sku)

                                                    # 円と,を削除して文字列に変更
                                                    cleaned_price = str(td_price).replace("円", "").replace(",", "")

                                                    # 必要に応じて整数型に変換
                                                    try:
                                                        cleaned_price = int(cleaned_price)
                                                    except ValueError:
                                                        print(f"無効な金額: {cleaned_price}")

                                                    if discount_price:
                                                        # cleaned_priceとdiscount_priceを整数に変換
                                                        try:
                                                            discount_price = int(discount_price)
                                                            new_price = cleaned_price - discount_price
                                                            print('割引後の単価: ', new_price)
                                                            worksheet.update_acell(f'M{row}', new_price)
                                                        except ValueError:
                                                            print(f"無効な割引金額: {discount_price}")
                                                    else:
                                                        print('1 仕入れ値: ', cleaned_price)
                                                        worksheet.update_acell(f'M{row}', cleaned_price)

                                                    # 対円通貨レート
                                                    worksheet.update_acell(f'O{row}', '1')

                                                    # 送料があれば記入
                                                    if each_shipping:
                                                        worksheet.update_acell(f'P{row}', each_shipping)
                                                        print('送料: ', each_shipping)

                                                    # 割引の%があれば記入
                                                    if percent:
                                                        worksheet.update_acell(f'Q{row}', percent)
                                                        print('割引％: ', percent)

                                                    print()
                                                    print("-" * 8)
                                                    print()
                                                    print()

                                                #--------------------------------------------------

                                            else:
                                                print("※※※ 辞書に登録がないので、SKU管理番号が取得できませんでした_1")
                                                print()

                                                print('接続4')
                                                print()

                                                # 関数を使って取得
                                                spreadsheet, worksheet_rakuten, worksheet_all, worksheet_dic = open_spreadsheet()

                                                # C7以降で空いている場所を探す
                                                cell_list = worksheet_rakuten.range('C7:C')

                                                worksheet = worksheet_rakuten

                                                # 最初に空いているセルを見つける
                                                empty_cell = None
                                                for cell in cell_list:
                                                    if not cell.value:
                                                        empty_cell = cell
                                                        break

                                                # 空いているセルが見つかった場合、同じ行のG列に値を入力する
                                                if empty_cell:
                                                    row = empty_cell.row

                                                    # 日付を入力
                                                    worksheet.update_acell(f'A{row}', orderdate)
                                                    print('購入日: ', orderdate)

                                                    # ショップ名を入力
                                                    worksheet.update_acell(f'B{row}', shop_name)
                                                    print('ショップ名: ', shop_name)

                                                    # 注文番号を入力
                                                    worksheet.update_acell(f'C{row}', order_id)
                                                    print('注文番号: ', order_id)
                                                    print()

                                                    # 割引の%があれば記入
                                                    if item_data:
                                                        worksheet.update_acell(f'E{row}', item_data)
                                                        print('【商品情報】')
                                                        print(item_data)
                                                        print()
                                                    else:
                                                        print('商品情報がありません_1')
                                                        print()

                                                    # 円と,を削除して文字列に変更
                                                    cleaned_price = str(td_price).replace("円", "").replace(",", "")

                                                    # 必要に応じて整数型に変換
                                                    try:
                                                        cleaned_price = int(cleaned_price)
                                                    except ValueError:
                                                        print(f"無効な金額: {cleaned_price}")

                                                    # 支払い金額を使って割引後の金額を入力する処理
                                                    if discount_price:
                                                        # cleaned_priceとdiscount_priceを整数に変換
                                                        try:
                                                            discount_price = int(discount_price)
                                                            new_price = cleaned_price - discount_price
                                                            print('割引後の単価: ', new_price)
                                                            worksheet.update_acell(f'M{row}', new_price)
                                                        except ValueError:
                                                            print(f"無効な割引金額: {discount_price}")
                                                    else:
                                                        print('仕入れ値: ', cleaned_price)
                                                        worksheet.update_acell(f'M{row}', cleaned_price)

                                                    # 対円通貨レート
                                                    worksheet.update_acell(f'O{row}', '1')

                                                    # 送料があれば記入
                                                    if each_shipping:
                                                        worksheet.update_acell(f'P{row}', each_shipping)
                                                        print('送料: ', each_shipping)

                                                    # 割引の%があれば記入
                                                    if percent is not None:
                                                        worksheet.update_acell(f'Q{row}', percent)
                                                        print('割引％: ', percent)
                                                    else:
                                                        print("1 割引％が設定されていません")

                                                print()
                                                print("-" * 8)
                                                print()

                                                # 個別ページにアクセス
                                                browser.get(detail_url)
                                                print()

                                    #-----------------------------------------------------            

                                    else:
                                        # 商品番号がないので、商品番号なしの変数not_span_dataを入力
                                        print('※※※ 商品番号がないので、商品名とカラー・サイズだけ入力します')
                                        print()

                                        print()
                                        print('接続5')
                                        print()

                                        # 関数を使って取得
                                        spreadsheet, worksheet_rakuten, worksheet_all, worksheet_dic = open_spreadsheet()

                                        # 商品番号がある場合注文の個数分繰り返す
                                        for _ in range(td_number):

                                            cell_list = None

                                            # 全セルを検索
                                            cell_list = worksheet_dic.findall(not_span_data)

                                            worksheet = worksheet_dic

                                            # 値を保存するリスト
                                            values_list = []

                                            # 検索結果が存在する場合
                                            if cell_list:

                                                # cell_list 内のセルごとに処理
                                                for cell in cell_list:
                                                    # 現在のセルの row 情報を取得
                                                    row = cell.row

                                                    # 列を "4" に変更して新たにスプレッドシートの値を取得
                                                    new_cell = worksheet.cell(row, 4)
                                                    # 取得した値をリストに保存（Noneの場合は空文字に変換）
                                                    values_list.append(new_cell.value if new_cell.value is not None else "")
                                                    cell_sku = values_list[-1]
                                                    print('SKU管理番号: ', cell_sku)
                                                    print()

                                                    # 列を "5" に変更して新たにスプレッドシートの値を取得
                                                    new_cell = worksheet.cell(row, 5)
                                                    # 取得した値をリストに保存（Noneの場合は空文字に変換）
                                                    values_list.append(new_cell.value if new_cell.value is not None else "")
                                                    print(f"セル {row}, 5: {values_list[-1]}")

                                                    # 列を "6" に変更して新たにスプレッドシートの値を取得
                                                    new_cell = worksheet.cell(row, 6)
                                                    # 取得した値をリストに保存（Noneの場合は空文字に変換）
                                                    values_list.append(new_cell.value if new_cell.value is not None else "")
                                                    print(f"セル {row}, 6: {values_list[-1]}")


                                                    # 列を "2" に変更して新たにスプレッドシートの値を取得
                                                    new_cell = worksheet.cell(row, 2)
                                                    # 取得した値をリストに保存（Noneの場合は空文字に変換）
                                                    values_list.append(new_cell.value if new_cell.value is not None else "")
                                                    print(f"セル {row}, 2: {values_list[-1]}")
                                                    print()

                                                #--------------------------------------------------

                                                print()
                                                print('接続6')
                                                print()

                                                # 関数を使って取得
                                                spreadsheet, worksheet_rakuten, worksheet_all, worksheet_dic = open_spreadsheet()

                                                # C7以降で空いている場所を探す
                                                cell_list = worksheet_rakuten.range('C7:C')

                                                worksheet = worksheet_rakuten

                                                # 最初に空いているセルを見つける
                                                empty_cell = None
                                                for cell in cell_list:
                                                    if not cell.value:
                                                        empty_cell = cell
                                                        break

                                                # 空いているセルが見つかった場合、同じ行のG列に値を入力する
                                                if empty_cell:
                                                    row = empty_cell.row

                                                    # 日付を入力
                                                    worksheet.update_acell(f'A{row}', orderdate)
                                                    print('購入日: ', orderdate)

                                                    # ショップ名を入力
                                                    worksheet.update_acell(f'B{row}', shop_name)
                                                    print('ショップ名: ', shop_name)

                                                    # 注文番号を入力
                                                    worksheet.update_acell(f'C{row}', order_id)
                                                    print('注文番号: ', order_id)

                                                    # SKU管理番号を入力
                                                    worksheet.update_acell(f'G{row}', cell_sku)
                                                    print('SKU管理番号: ', cell_sku)

                                                    # 円と,を削除して文字列に変更
                                                    cleaned_price = td_price.replace("円", "").replace(",", "")

                                                    if discount_price:
                                                        # cleaned_priceとdiscount_priceを整数に変換
                                                        cleaned_price = int(cleaned_price)
                                                        discount_price = int(discount_price)

                                                        new_price = cleaned_price - discount_price
                                                        print('割引後の仕入れ値: ', new_price)
                                                        worksheet.update_acell(f'M{row}', new_price)

                                                    else:
                                                        print('仕入れ値: ', cleaned_price)
                                                        worksheet.update_acell(f'M{row}', cleaned_price)

                                                    # 対円通貨レート
                                                    worksheet.update_acell(f'O{row}', '1')

                                                    # 送料があれば記入
                                                    if each_shipping:
                                                        worksheet.update_acell(f'P{row}', each_shipping)
                                                        print('送料: ', each_shipping)

                                                    # 割引の%があれば記入
                                                    if percent is not None:
                                                        worksheet.update_acell(f'Q{row}', percent)
                                                        print('割引％: ', percent)
                                                    else:
                                                        print("2 割引％が設定されていません")

                                                    print()
                                                    print("-" * 8)
                                                    print()
                                                    print()

                                                #--------------------------------------------------

                                            else:
                                                print("※※※ 辞書に登録がないので、SKU管理番号が取得できませんでした_2")
                                                print()

                                                print()
                                                print('接続7')
                                                print()

                                                # 関数を使って取得
                                                spreadsheet, worksheet_rakuten, worksheet_all, worksheet_dic = open_spreadsheet()


                                                # C7以降で空いている場所を探す
                                                cell_list = worksheet_rakuten.range('C7:C')

                                                worksheet = worksheet_rakuten

                                                # 最初に空いているセルを見つける
                                                empty_cell = None
                                                for cell in cell_list:
                                                    if not cell.value:
                                                        empty_cell = cell
                                                        break

                                                # 空いているセルが見つかった場合、同じ行のG列に値を入力する
                                                if empty_cell:
                                                    row = empty_cell.row

                                                    # 日付を入力
                                                    worksheet.update_acell(f'A{row}', orderdate)
                                                    print('購入日: ', orderdate)

                                                    # ショップ名を入力
                                                    worksheet.update_acell(f'B{row}', shop_name)
                                                    print('ショップ名: ', shop_name)

                                                    # 注文番号を入力
                                                    worksheet.update_acell(f'C{row}', order_id)
                                                    print('注文番号: ', order_id)
                                                    print()

                                                    # 割引の%があれば記入
                                                    if not_span_data:
                                                        worksheet.update_acell(f'E{row}', not_span_data)
                                                        print('【商品情報】')
                                                        print(not_span_data)
                                                        print()
                                                    else:
                                                        print('商品情報がありません_2')
                                                        print()


                                                    # 円と,を削除して文字列に変更
                                                    cleaned_price = str(td_price).replace("円", "").replace(",", "")

                                                    # 必要に応じて整数型に変換
                                                    try:
                                                        cleaned_price = int(cleaned_price)
                                                    except ValueError:
                                                        print(f"無効な金額: {cleaned_price}")

                                                    # 割引後の価格計算                        
                                                    if discount_price:
                                                        # cleaned_priceとdiscount_priceを整数に変換
                                                        try:
                                                            discount_price = int(discount_price)
                                                            new_price = cleaned_price - discount_price
                                                            print('割引後の単価: ', new_price)
                                                            worksheet.update_acell(f'M{row}', new_price)
                                                        except ValueError:
                                                            print(f"無効な割引金額: {discount_price}")
                                                    else:
                                                        print('仕入れ値: ', cleaned_price)
                                                        worksheet.update_acell(f'M{row}', cleaned_price)

                                                    # 対円通貨レート
                                                    worksheet.update_acell(f'O{row}', '1')

                                                    # 送料があれば記入
                                                    if each_shipping:
                                                        worksheet.update_acell(f'P{row}', each_shipping)
                                                        print('送料: ', each_shipping)

                                                    # 割引の%があれば記入
                                                    if percent is not None:
                                                        worksheet.update_acell(f'Q{row}', percent)
                                                        print('割引％: ', percent)
                                                    else:
                                                        print("3 割引％が設定されていません")

                                                # 個別ページにアクセス
                                                browser.get(detail_url)
                                                print()
                                                print()

                                    #----------------------------------------------

                                    # 個別ページにアクセス
                                    browser.get(detail_url)
                                    print()


                                else:
                                    print("※※※ 該当の項目がありません")

                                #---------------------------------------

                            else:
                                print("※※※ URLを取得できませんでした")
                                print()
      
                #---------------------------------------

            # 一致する項目がなかった場合のメッセージ
            if not found:
                print("※※※ 一致するorder_idがありません")
                print()
                continue

            # 合計数を出力
            print("合計数:", total_td_number)
            print()

            #--------------------------------------------------

            print()
            print("-" * 80)
            print()
            print()
            print()
            print()

            url_login = "https://order.my.rakuten.co.jp/?l-id=pc_header_func_ph"
            browser.get(url_login)
            time.sleep(1)

    except Exception as e:
        print(f"An error occurred: {e}")


# 現在の日付と時間を取得
now = datetime.now()
print()
formatted_date = now.strftime("%m/%d")
formatted_time = now.strftime("%H:%M")
print("処理完了:", formatted_date, formatted_time)
print("-" * 80)
print("\n\n\n")

browser.quit()
