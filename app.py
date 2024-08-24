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
header = ["商品名", "金額", "ポイント", "ASIN", "商品URL", "商品画像（複数）", "Category_AMAZON", "Description", "Features", "Amazon_Brand", "製品サイズ（Length）","製品サイズ（Width）","製品サイズ（Height）","製品サイズ（Weight）","在庫状況"]
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
    # product_list = product_list[0:30]
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
        product_dict["product_name"] = "取得不可"

    try:
        # 価格の取得
        product_dict["product_price"] = product.find_element(By.CSS_SELECTOR, "span.a-price-whole").text
    except:
        try:
            # セール価格またはその他の形式の価格を探す
            product_dict["product_price"] = product.find_element(By.CSS_SELECTOR, "span.a-color-price span.a-offscreen").text
        except Exception:
            product_dict["product_price"] = "取得不可"

    try:
        # ポイントの取得
        product_dict["product_point"] = product.find_element(By.CSS_SELECTOR, "span.a-size-base.a-color-price").text
    except Exception:
        product_dict["product_point"] = "取得不可"

    try:
        # ASINの取得
        product_dict["asin"] = product.get_attribute("data-asin")
        # 商品URLの作成
        product_dict["product_url"] = "https://www.amazon.co.jp/dp/" + product_dict["asin"]
    except Exception:
        product_dict["asin"] = "取得不可"
        product_dict["product_url"] = "取得不可"

    if product_dict["product_url"] != "取得不可":
        detail = create_webdriver()
        detail.get(product_dict["product_url"])
        WebDriverWait(detail, 10).until(EC.presence_of_all_elements_located)

        try:
            image_urls = []
            # 商品画像の取得
            for i in range(0, 7):
                product_dict["product_image_url" + i] = detail.find_elements(By.CSS_SELECTOR, "#altImages li.imageThumbnail img")[i].get_attribute("src")
        except Exception:
            product_dict["product_image_url"] = "取得不可"
        
        try:
            # Category_AMAZONの取得
            product_dict["category"] = detail.find_element(By.CSS_SELECTOR, ".cat-link").text.replace("- カテゴリ ", "")
        except Exception:
            product_dict["category"] = "取得不可"

        try:
            # Descriptionの取得
            product_dict["description"] = detail.find_element(By.CSS_SELECTOR, "#productDescription span").text
        except Exception:
            product_dict["description"] = "取得不可"
        
        try:
            # Featuresの取得
            product_dict["features"] = detail.find_element(By.CSS_SELECTOR, "#feature-bullets .a-unordered-list").text
        except Exception:
            try:
                # その他の形式のFeaturesを探す
                features = []
                for feature in detail.find_elements(By.CSS_SELECTOR, "#productFactsDesktop_feature_div ul"):
                    features.append(feature.text)
                product_dict["features"] = "\n".join(features)
            except Exception:
                product_dict["features"] = "取得不可"

        try:
            # Amazon_Brandの取得
            product_dict["brand"] = detail.find_element(By.CSS_SELECTOR, ".po-brand .po-break-word").text
        except Exception:
            product_dict["brand"] = "取得不可"
        
        try:
            # 梱包サイズの取得
            package_size = detail.find_element(By.XPATH, "//*[contains(text(), \"製品サイズ\")]/following-sibling::td").text
            product_dict["package_size_length"] = package_size.split()[0]
            product_dict["package_size_width"] = package_size.split()[2]
            product_dict["package_size_height"] = package_size.split()[4]
            product_dict["package_size_weight"] = package_size.split()[6]
        except Exception:
            product_dict["package_size_length"] = "取得不可"
            product_dict["package_size_width"] = "取得不可"
            product_dict["package_size_height"] = "取得不可"
            product_dict["package_size_weight"] = "取得不可"

        try:
            # 在庫状況の取得
            product_dict["stock"] = detail.find_element(By.CSS_SELECTOR, "#availability span").text.replace("。", "").replace("ご注文はお早めに", "").replace(" ", "")
        except Exception:
            product_dict["stock"] = "取得不可"
            
        # 終了
        detail.quit()

    return list(product_dict.values())

def create_webdriver():
    driver = webdriver.Remote(
        command_executor='http://selenium-hub:4444/wd/hub',
        options=options
    )
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

def handler(event=None, context=None):
    try:
        # メイン処理
        product_data = extract_amazon_data()
        save_to_google_sheet(product_data)

    except Exception as e:
        print(f"エラーが発生しました: {e}")

handler()