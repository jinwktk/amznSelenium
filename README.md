# amznSelenium

## 導入
```sh
# パッケージインストール（初回のみ）
pip install -r requirements.txt

py app.py
```

## 出力先スプシ
https://docs.google.com/spreadsheets/d/1Ge-6EEo571WzaQ-RcAgbW4n0ZcDgIf-f-27T8IcvDE8/edit?gid=0#gid=0


## ECR

```sh
docker build -t 533267382959.dkr.ecr.ap-northeast-1.amazonaws.com/amazon_tracking_selenium:latest .

aws ecr get-login-password | docker login --username AWS --password-stdin 533267382959.dkr.ecr.ap-northeast-1.amazonaws.com/amazon_tracking_selenium

docker push 533267382959.dkr.ecr.ap-northeast-1.amazonaws.com/amazon_tracking_selenium
```