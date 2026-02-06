# 商品マスタ（Googleスプレッドシート）連携

このパイプラインでは、受注データ側の `item_name` が揺れる場合でも表示名を安定させるために、Googleスプレッドシートで管理している商品マスタをBigQueryに同期し、ビューで参照できるようにしています。

## 仕組み

- Cloud Function 実行時（`dry_run` 以外）に商品マスタを取得し、BigQueryのマスタテーブルを **全件入れ替え（TRUNCATE + LOAD）** します。
- `deploy_views.py` のビューは、マスタテーブルをJOINして商品名/バリエーションを表示します。

## 必要なスプレッドシートの列

ヘッダ行（1行目）に以下の列名がある想定です。

- `商品管理番号`（= `manage_number`） - B列
- `商品名`（= `product_name`） - C列
- `カテゴリ名`（= `category_name`） - D列
- `ブランド名`（= `brand_name`） - E列

## セットアップ手順（推奨: Sheets APIで非公開のまま参照）

1) Cloud Function のサービスアカウントにスプレッドシートの閲覧権限を付与  
2) GCP側で Google Sheets API を有効化  
3) Cloud Function の環境変数を設定（下記）

## 環境変数

- `PRODUCT_MASTER_SHEET_ID`（推奨）: スプレッドシートID（`/d/{THIS}/` の部分）
- `PRODUCT_MASTER_SHEET_RANGE`（任意）: A1レンジ。未指定時は `B:E` を使用（シート名は自動で先頭シートを使用）
- `BQ_TABLE_PRODUCT_MASTER_RAW`（任意）: 同期先テーブル名（デフォルト `product_master_raw`）
- `PRODUCT_MASTER_SYNC_REQUIRED`（任意）: `true` の場合、商品マスタが取得できないとETLを失敗にします（デフォルト `false`）

## ビュー側の変更点

- `view_manageNumber_sales`: `item_name` はマスタの `product_name` を優先して使用
- 新しく追加された `category_name` と `brand_name` は商品マスタテーブルに保存され、必要に応じてビューやクエリで参照可能

