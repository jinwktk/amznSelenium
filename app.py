from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import concurrent.futures
from tqdm import tqdm
from tempfile import mkdtemp

# WebDriverの設定
options = webdriver.ChromeOptions()
service = webdriver.ChromeService("/opt/chromedriver")

options.binary_location = '/opt/chrome/chrome'
options.add_argument("--headless=new")
options.add_argument('--no-sandbox')
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1280x1696")
options.add_argument("--single-process")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-dev-tools")
options.add_argument("--no-zygote")
options.add_argument(f"--user-data-dir={mkdtemp()}")
options.add_argument(f"--data-path={mkdtemp()}")
options.add_argument(f"--disk-cache-dir={mkdtemp()}")
options.add_argument("--remote-debugging-port=9222")

# スクレイピング画面
url = "https://www.amazon.co.jp/s?k=%E6%99%82%E8%A8%88&__mk_ja_JP=%E3%82%AB%E3%82%BF%E3%82%AB%E3%83%8A&crid=2GA5Q5PCRJLLG&sprefix=%E6%99%82%E8%A8%88%2Caps%2C259&ref=nb_sb_noss_1"

# 並列処理数
window = 10

# スプレッドシート設定
spread_url = "https://docs.google.com/spreadsheets/d/1Ge-6EEo571WzaQ-RcAgbW4n0ZcDgIf-f-27T8IcvDE8/edit#gid=0"
header = ["商品名", "金額", "ポイント", "ASIN", "商品URL", "商品画像（複数）", "梱包サイズ", "Category_AMAZON", "Description", "Features", "Amazon_Brand", "梱包サイズ（Length）","梱包サイズ（Width）","梱包サイズ（Height）","梱包サイズ（Weight）","在庫有無", "在庫数"]
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

    # DEBUG  ###########
    product_list = product_list[0:30]
    # /DEBUG ###########

    # 並行処理
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=window)
    futures = [executor.submit(extract_amazon_detail_data, product) for product in product_list]

    # 処理件数
    print("商品情報取得中...")
    progress = tqdm(total = len(product_list))
    for future in concurrent.futures.as_completed(futures):
        progress.update(1)
        products.append(future.result())

    # 終了
    executor.shutdown()
    driver.quit()
         
    return products

def extract_amazon_detail_data(product):
    product_dict = {}
    try:
        # 商品名を取得
        product_dict["product_name"] = product.find_element(By.CSS_SELECTOR, "h2 a span").text
    except Exception:
        product_dict["product_name"] = "商品名が見つかりませんでした"

    try:
        # 価格の取得
        product_dict["product_price"] = product.find_element(By.CSS_SELECTOR, "span.a-price-whole").text
    except:
        try:
            # セール価格またはその他の形式の価格を探す
            product_dict["product_price"] = product.find_element(By.CSS_SELECTOR, "span.a-color-price span.a-offscreen").text
        except Exception:
            product_dict["product_price"] = "価格が見つかりませんでした"

    try:
        # ポイントの取得
        product_dict["product_point"] = product.find_element(By.CSS_SELECTOR, "span.a-size-base.a-color-price").text
    except Exception:
        product_dict["product_point"] = "ポイントが見つかりませんでした"

    try:
        # ASINの取得
        product_dict["asin"] = product.get_attribute("data-asin")
        # 商品URLの作成
        product_dict["product_url"] = "https://www.amazon.co.jp/dp/" + product_dict["asin"]
    except Exception:
        product_dict["asin"] = "ASINが見つかりませんでした"
        product_dict["product_url"] = "商品URLが見つかりませんでした"

    return list(product_dict.values())
    # DockerでSeleniumを2個WebDriverを作成できない

    if product_dict["product_url"] != "商品URLが見つかりませんでした":
        # 各商品の詳細ページにアクセスして梱包サイズを取得
        detail = create_webdriver()
        detail.get(product_dict["product_url"])
        WebDriverWait(detail, 10).until(EC.presence_of_all_elements_located)

        try:
            image_urls = []
            # 商品画像の取得
            for img in detail.find_elements(By.CSS_SELECTOR, "#altImages li.imageThumbnail img"):
                image_urls.append(img.get_attribute("src"))
            product_dict["product_image_url"] = "\n".join(image_urls)
        except Exception:
            product_dict["product_image_url"] = "商品画像が見つかりませんでした"

        # 詳細ページで梱包サイズを取得
        try:
            product_dict["package_size"] = detail.find_element(By.XPATH, "//*[contains(text(), \"梱包サイズ\")]/following-sibling::span").text
        except Exception:
            product_dict["package_size"] = "梱包サイズが見つかりませんでした"

        # 終了
        detail.quit()

    return list(product_dict.values())

def create_webdriver():
    driver = webdriver.Chrome(options=options, service=service)
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
    print("スプレッドシート書き込み中取得中...")
    progress = tqdm(total = len(data))
    for product in data:
        progress.update(1)
        worksheet.append_row(product)

def handler(event, context):
    try:
        # メイン処理
        product_data = extract_amazon_data()
        save_to_google_sheet(product_data)

    except Exception as e:
        print(f"エラーが発生しました: {e}")

handler(False,False)