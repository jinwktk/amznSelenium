# amznSelenium

## 導入
```sh
docker-compose up

# 別窓で実行
docker-compose exec selenium python app.py
```

## 出力先スプシ
https://docs.google.com/spreadsheets/d/1Ge-6EEo571WzaQ-RcAgbW4n0ZcDgIf-f-27T8IcvDE8/edit?gid=0#gid=0


## ECR

```sh
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin 533267382959.dkr.ecr.ap-northeast-1.amazonaws.com

docker build -t amazon_tracking_selenium .

docker tag amazon_tracking_selenium:latest 533267382959.dkr.ecr.ap-northeast-1.amazonaws.com/amazon_tracking_selenium:latest

docker push 533267382959.dkr.ecr.ap-northeast-1.amazonaws.com/amazon_tracking_selenium:latest
```

## S3

https://amazon-tracking-selenium.s3.ap-northeast-1.amazonaws.com/${asin}/{画像名}

## TODO

毎回書き出し先のスプシを変える  
2ページ目まで取る  
ユーザーエージェントのカスタマイズ
```
options = webdriver.ChromeOptions()
proxy = "http://your_proxy_here:port"
options.add_argument(f'--proxy-server={proxy}')
driver = webdriver.Chrome(options=options)
```

IPアドレスのローテーション
```
from selenium import webdriver

options = webdriver.ChromeOptions()
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36")
driver = webdriver.Chrome(options=options)
```