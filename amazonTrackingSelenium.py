from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# WebDriverの設定とブラウザの起動
driver = webdriver.Chrome()
driver.implicitly_wait(10)

# 商品検索結果ページにアクセス
driver.get("https://www.amazon.co.jp/s?k=%E6%99%82%E8%A8%88&__mk_ja_JP=%E3%82%AB%E3%82%BF%E3%82%AB%E3%83%8A&crid=2GA5Q5PCRJLLG&sprefix=%E6%99%82%E8%A8%88%2Caps%2C259&ref=nb_sb_noss_1")

def extract_amazon_data():
    # 商品リストをすべて取得
    product_list = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.s-main-slot div[data-component-type='s-search-result']"))
    )

    # 商品名と価格を保存するリスト
    products = []

    # 各商品の名前、価格、ポイント、ASIN、商品画像URLを取得し、梱包サイズのみ詳細ページで取得
    product_links = []

    for product in product_list:
        try:
            # 商品名を取得
            product_name = product.find_element(By.CSS_SELECTOR, "h2 a span").text
        except Exception:
            product_name = "商品名が見つかりませんでした"

        try:
            # 価格の取得
            product_price = product.find_element(By.CSS_SELECTOR, "span.a-price-whole").text
        except:
            try:
                # セール価格またはその他の形式の価格を探す
                product_price = product.find_element(By.CSS_SELECTOR, "span.a-color-price span.a-offscreen").text
            except Exception:
                product_price = "価格が見つかりませんでした"

        try:
            # ポイントの取得
            product_point = product.find_element(By.CSS_SELECTOR, "span.a-size-base.a-color-price").text
        except Exception:
            product_point = "ポイントが見つかりませんでした"

        try:
            # ASINの取得 (商品ページのリンクから抽出)
            product_link = product.find_element(By.CSS_SELECTOR, "h2 a").get_attribute("href")
            asin = product_link.split("/dp/")[1][:10] if "/dp/" in product_link else "ASINが見つかりませんでした"
        except Exception:
            asin = "ASINが見つかりませんでした"

        try:
            # 商品画像の取得
            product_image_url = product.find_element(By.CSS_SELECTOR, "img.s-image").get_attribute("src")
        except Exception:
            product_image_url = "商品画像が見つかりませんでした"

        # 詳細ページで梱包サイズを取得するためにリンクを保存
        product_links.append({
            "name": product_name,
            "price": product_price,
            "point": product_point,
            "asin": asin,
            "image": product_image_url,
            "link": product_link
        })

    # 詳細ページで梱包サイズを取得
    for product in product_links:
        try:
            # 各商品の詳細ページにアクセスして梱包サイズを取得
            driver.get(product['link'])
            package_size = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//th[text()='梱包サイズ']/following-sibling::td"))
            ).text
        except Exception:
            package_size = "梱包サイズが見つかりませんでした"
        
        # 商品情報に梱包サイズを追加
        products.append([product['name'], product['price'], product['point'], product['asin'], package_size, product['image']])

    return products

def save_to_google_sheet(data):
    # Googleスプレッドシートに接続
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('model-axle-432403-i3-18213d0830c3.json', scope)
    client = gspread.authorize(creds)
    
    # スプレッドシートを開く
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ge-6EEo571WzaQ-RcAgbW4n0ZcDgIf-f-27T8IcvDE8/edit#gid=0")
    worksheet = sheet.get_worksheet(0)
    
    # 既存のデータをクリア（オプション）
    worksheet.clear()
    
    # ヘッダーを書き込む
    worksheet.append_row(["商品名", "価格", "ポイント", "ASIN", "梱包サイズ", "商品画像URL"])
    
    # データを書き込む
    for product in data:
        worksheet.append_row(product)

    print("Data saved to Google Spreadsheet")

try:
    # メイン処理
    product_data = extract_amazon_data()
    save_to_google_sheet(product_data)

except Exception as e:
    print(f"エラーが発生しました: {e}")

finally:
    # ブラウザを閉じる
    driver.quit()
