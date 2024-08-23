from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import concurrent.futures
from tqdm import tqdm

# WebDriverの設定
chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument('--headless')
# chrome_options.add_argument('--no-sandbox')
# chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

# スクレイピング画面
url = "https://www.amazon.co.jp/s?k=%E6%99%82%E8%A8%88&__mk_ja_JP=%E3%82%AB%E3%82%BF%E3%82%AB%E3%83%8A&crid=2GA5Q5PCRJLLG&sprefix=%E6%99%82%E8%A8%88%2Caps%2C259&ref=nb_sb_noss_1"

# 並列処理数
window = 5

# スプレッドシート設定
spread_url = "https://docs.google.com/spreadsheets/d/1Ge-6EEo571WzaQ-RcAgbW4n0ZcDgIf-f-27T8IcvDE8/edit#gid=0"
header = ["商品名", "価格", "ポイント", "ASIN", "梱包サイズ", "商品画像URL", "product_link"]
key_json = "gasKey.json"

def extract_amazon_data():
    driver = create_webdriver()
    # 商品検索結果ページにアクセス
    driver.get(url)

    # 商品リストをすべて取得
    product_list = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.s-main-slot div[data-component-type='s-search-result']"))
    )

    # 商品名と価格を保存するリスト
    products = []

    product_list = product_list[0:10]
    # 並行処理
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=window)
    futures = [executor.submit(extract_amazon_detail_data, product) for product in product_list]

    # 処理件数
    progress = tqdm(total = len(product_list))
    for future in concurrent.futures.as_completed(futures):
        progress.update(1)
        products.append(future.result())

    # 終了
    executor.shutdown()
    driver.quit()
         
    return products

def extract_amazon_detail_data(product):
    driver = create_webdriver()

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

    # 詳細ページで梱包サイズを取得
    try:
        # 各商品の詳細ページにアクセスして梱包サイズを取得
        driver.get(product_link)
        package_size = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "梱包サイズ")]/following-sibling::span'))
        ).text
    except Exception:
        package_size = "梱包サイズが見つかりませんでした"

    # 終了
    driver.quit()

    return [
        product_name,
        product_price,
        product_point,
        asin,
        package_size,
        product_image_url,
        product_link
    ]

def create_webdriver():
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    return driver

def save_to_google_sheet(data):
    # Googleスプレッドシートに接続
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(key_json, scope)
    client = gspread.authorize(creds)
    
    # スプレッドシートを開く
    sheet = client.open_by_url(spread_url)
    worksheet = sheet.get_worksheet(0)
    
    # 既存のデータをクリア（オプション）
    worksheet.clear()
    
    # ヘッダーを書き込む
    worksheet.append_row(header)
    
    # データを書き込む
    for product in data:
        worksheet.append_row(product)

    print("Data saved to Google Spreadsheet")

if __name__ == '__main__':
    try:
        # メイン処理
        product_data = extract_amazon_data()
        save_to_google_sheet(product_data)

    except Exception as e:
        print(f"エラーが発生しました: {e}")