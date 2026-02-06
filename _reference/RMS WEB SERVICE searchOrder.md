# RMS WEB SERVICE : searchOrder

1. **Overview**
    
    この機能を利用すると、楽天ペイ注文の「注文検索」を行うことができます。こちらは同期処理となります。
    
    検索結果が 15000 件以上の場合、15001 件目以降の受注番号は取得できません。
    
    SKUプロジェクトにて追加・修正となる項目は背景色を緑に変更しています。
    
2. **Endpoint**
    
    https://api.rms.rakuten.co.jp/es/2.0/order/searchOrder/
    
3. **Request**
    1. **Request Method**
        
        
        | Method |
        | --- |
        | POST |
    2. **Request Header**
        
        
        | **Key** | **Value** |
        | --- | --- |
        | Authorization | ESA Base64(serviceSecret:licenseKey) |
        | Content-Type | application/json; charset=utf-8 |
    3. **Request Parameter**
        1. **Level 1: base**
            
            
            | **No** | **Logical Name** | **Parameter Name** | **Required** | **Type** | **Max Byte** | **Default** | **Description** | **Sample** |
            | --- | --- | --- | --- | --- | --- | --- | --- | --- |
            | 1 | ステータスリスト | orderProgressList | no | List <Number> | 128 | - | 以下のいずれか
            
            100: 注文確認待ち
            200: 楽天処理中
            300: 発送待ち
            400: 変更確定待ち
            500: 発送済
            600: 支払手続き中
            700: 支払手続き済
            800: キャンセル確定待ち
            900: キャンセル確定 | [100,300] |
            | 2 | サブステータスIDリスト | subStatusIdList | no | List <Number> | 512 | - | ・作成されたサブステータスを指定する場合は複数のIDを同時に指定することが可能です。
            ・[-1]を指定した場合、サブステータスが設定されていない注文を取得することが可能です。[-1]を指定する場合、ステータスリスト（orderProgressList）の指定が必須となります。 | [100,300] |
            | 3 | 期間検索種別 | dateType | yes | Number | 2 | - | 以下のいずれか
            
            1: 注文日
            2: 注文確認日
            3: 注文確定日
            4: 発送日
            5: 発送完了報告日
            6: 決済確定日 | 3 |
            | 4 | 期間検索開始日時 | startDatetime | yes | Datetime | 25 | - | 過去 730 日(2年)以内の注文を指定可能 | 2017-10-14T00:00:00+0900 |
            | 5 | 期間検索終了日時 | endDatetime | yes | Datetime | 25 | - | 開始日から 63 日以内 | 2017-10-15T23:59:59+0900 |
            | 6 | 販売種別リスト | orderTypeList | no | List <Number> | 32 | - | 以下のいずれか
            
            1: 通常購入
            4: 定期購入
            5: 頒布会
            6: 予約商品 | 4,6 |
            | 7 | 支払方法名 | settlementMethod | no | Number | 2 | - | 以下のいずれか
            
            1: クレジットカード
            2: 代金引換
            3: 後払い
            4: ショッピングクレジット／ローン
            5: オートローン
            6: リース
            7: 請求書払い
            9: 銀行振込
            12: Apple Pay
            13: セブンイレブン（前払）
            14: ローソン、郵便局ATM等（前払）
            16: Alipay
            17: PayPal
            21: 後払い決済（楽天市場の共通決済）
            27: Alipay（支付宝） | 2 |
            | 8 | 配送方法 | deliveryName | no | String | 192 | - |  | 宅配便 |
            | 9 | 発送日未指定有無フラグ | shippingDateBlankFlag | no | Number | 1 | 0 | 以下のいずれか
            
            0: 発送日の指定の有無によらず取得
            1: 発送日が未指定のものだけを取得 | 1 |
            | 10 | お荷物伝票番号未指定有無フラグ | shippingNumberBlankFlag | no | Number | 1 | 0 | 以下のいずれか
            
            0: お荷物伝票番号の指定の有無によらず取得
            1: お荷物伝票番号が未指定のものだけを取得 | 1 |
            | 11 | 検索キーワード種別 | searchKeywordType | no | Number | 2 | 0 | 以下のいずれか
            
            0: なし
            1: 商品名
            2: 商品番号
            3: ひとことメモ
            4: 注文者氏名
            5: 注文者氏名フリガナ
            6: 送付先氏名
            7: SKU管理番号
            8: システム連携用SKU番号
            9: SKU情報 | 2 |
            | 12 | 検索キーワード | searchKeyword | no | String | 4000 | - | 以下の入力チェックが適用されます
            
            ・機種依存文字などの不正文字以外
            ・キーワード前後の空白は削除
            ・全角、半角にかかわらず、それぞれのキーワードの文字数は下記のとおり
            
            1: 商品名：1024 文字以下
            2: 商品番号：127文字以下
            3: ひとことメモ：1000文字以下
            4: 注文者氏名：254文字以下
            5: 注文者氏名フリガナ：254文字以下
            6: 送付先氏名：254文字以下
            7: SKU管理番号：40文字以下
            8: システム連携用SKU番号：96文字以下
            9: SKU情報：400文字以下 | keyword |
            | 13 | 注文メールアドレス種別 | mailSendType | no | Number | 2 | 0 | 以下のいずれか
            
            0: PC/モバイル
            1: PC
            2: モバイル | 1 |
            | 14 | 注文者メールアドレス | ordererMailAddress | no | String | 256 | - | 完全一致 |  |
            | 15 | 電話番号種別 | phoneNumberType | no | Number | 2 | - | 以下のいずれか
            
            1: 注文者
            2: 送付先 | 1 |
            | 16 | 電話番号 | phoneNumber | no | String | 36 | - | 完全一致 | 0344445555 |
            | 17 | 申込番号 | reserveNumber | no | String | 382 | - | 完全一致 | 290333-20170915-215337-r |
            | 18 | 購入サイトリスト | purchaseSiteType | no | Number | 3 | 0 | 以下のいずれか
            
            0: すべて
            1: PCで注文
            2: モバイルで注文
            3: スマートフォンで注文
            4: タブレットで注文 | 2 |
            | 19 | あす楽希望フラグ | asurakuFlag | no | Number | 1 | - | 以下のいずれか
            
            0: あす楽希望の有無によらず取得
            1: あす楽希望のものだけを取得 | 1 |
            | 20 | クーポン利用有無フラグ | couponUseFlag | no | Number | 1 | - | 以下のいずれか
            
            0: クーポン利用の有無によらず取得
            1: クーポン利用のものだけを取得 | 1 |
            | 21 | 医薬品受注フラグ | drugFlag | no | Number | 1 | - | 以下のいずれか
            
            0: 医薬品の有無によらず取得
            1: 医薬品を含む注文だけを取得 | 1 |
            | 22 | 海外カゴ注文フラグ | overseasFlag | no | Number | 1 | - | 以下のいずれか
            
            0: 海外カゴ注文の有無によらず取得
            1: 海外カゴ注文のものだけを取得
            ※2020/06/30以降の注文の場合、1は取得できません。
            ※version8以降は取得できない項目です。 | 1 |
            | 23 | ページングリクエストモデル | PaginationRequestModel | no | PaginationRequestModel | - | - |  |  |
            | 24 | 注文当日出荷フラグ | oneDayOperationFlag | no | Number | 1 | - | 以下のいずれか
            0: 注文当日出荷によらず取得
            1: 注文当日出荷のものだけを取得
            ※購入時に最短お届け可能日が指定された注文です。 | 1 |
        2. **Level 2: PaginationRequestModel**
            
            
            | **No** | **Logical Name** | **Parameter Name** | **Required** | **Type** | **Max Byte** | **Default** | **Description** | **Sample** |
            | --- | --- | --- | --- | --- | --- | --- | --- | --- |
            | 1 | 1ページあたりの取得結果数 | requestRecordsAmount | yes | Number | 10 | 30 | 最大 1000 件まで指定可能 | 30 |
            | 2 | リクエストページ番号 | requestPage | yes | Number | 10 | 1 |  | 5 |
            | 3 | 並び替えモデルリスト | SortModelList | no | List <SortModel> | - | - | 現在は「注文日時」のみ指定可能 |  |
        3. **Level 3: SortModel**
            
            
            | **No** | **Logical Name** | **Parameter Name** | **Required** | **Type** | **Max Byte** | **Default** | **Description** | **Sample** |
            | --- | --- | --- | --- | --- | --- | --- | --- | --- |
            | 1 | 並び替え項目 | sortColumn | yes | Number | 5 | 1 | 以下のいずれか
            
            1: 注文日時 | 1 |
            | 2 | 並び替え方法 | sortDirection | yes | Number | 5 | 2 | 以下のいずれか
            
            1: 昇順（小さい順、古い順）
            2: 降順（大きい順、新しい順） | 2 |
4. **Response**
    1. **HTTP Status**
        
        
        | **Code** | **Status** | **Description** |
        | --- | --- | --- |
        | 200 | OK | リクエストが成功した。 |
        | 400 | Bad Request | リクエストが不正である。 |
        | 404 | Not Found | Request-URI に一致するものを見つけられなかった。 |
        | 405 | Method Not Allowed | 許可されていないメソッドを使用しようとした。 |
        | 500 | Internal Server Error | サーバ内部にエラーが発生した。 |
        | 503 | Service Unavailable | サービスが一時的に過負荷やメンテナンスで使用不可能である。 |
    2. **Response Header**
        
        
        | **Key** | **Value** |
        | --- | --- |
        | Content-Type | application/json;charset=utf-8 |
    3. **Response Parameter**
        1. **Level 1: base**
            
            
            | **No** | **Logical Name** | **Parameter Name** | **Not Null** | **Type** | **Max Byte** | **Default** | **Description** | **Sample** |
            | --- | --- | --- | --- | --- | --- | --- | --- | --- |
            | 1 | メッセージモデルリスト | MessageModelList | yes | List <MessageModel> | - | - |  |  |
            | 2 | 注文番号リスト | orderNumberList | no | List <String> | 40960 | - |  | ["290333-20171006-10640141","290333-20170929-10635460"] |
            | 3 | ページングレスポンスモデル | PaginationResponseModel | no | PaginationResponseModel | - | - |  |  |
        2. **Level 2: MessageModel**
            
            
            | **No** | **Logical Name** | **Parameter Name** | **Not Null** | **Type** | **Max Byte** | **Default** | **Description** | **Sample** |
            | --- | --- | --- | --- | --- | --- | --- | --- | --- |
            | 1 | メッセージ種別 | messageType | yes | String | 16 | - | 以下のいずれか
            
            ・INFO
            ・ERROR
            ・WARNING | INFO |
            | 2 | メッセージコード | messageCode | yes | String | 128 | - | メッセージコードの一覧は[こちら](https://webservice.rms.rakuten.co.jp/merchant-portal/view/ja/common/1-1_service_index/rakutenpayorderapi/rakutenpaymsgcodereference) | MESSAGE_CODE_SAMPLE |
            | 3 | メッセージ | message | yes | String | 1024 | - |  | メッセージサンプル |
        3. **Level 2: PaginationResponseModel**
            
            
            | **No** | **Logical Name** | **Parameter Name** | **Not Null** | **Type** | **Max Byte** | **Default** | **Description** | **Sample** |
            | --- | --- | --- | --- | --- | --- | --- | --- | --- |
            | 1 | 総結果数 | totalRecordsAmount | no | Number | 10 | - |  | 997 |
            | 2 | 総ページ数 | totalPages | no | Number | 10 | - |  | 34 |
            | 3 | リクエストページ番号 | requestPage | no | Number | 10 | - | リクエストされたページ数 | 2 |
5. **Sample**
    1. **検索結果が取得できた場合**
        - Request (curl コマンドを使った例)
            
            `curl -X POST \
              https://api.rms.rakuten.co.jp/es/2.0/order/searchOrder/ \
              -H 'Authorization: ESA xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' \
              -H 'Content-Type: application/json; charset=utf-8' \
              -d '{
                "dateType" : 1,
                "startDatetime" : "2017-12-14T00:00:00+0900",
                "endDatetime" : "2018-01-14T00:00:00+0900",
                "PaginationRequestModel" :
                {
                    "requestRecordsAmount" : 30,
                    "requestPage" : 1,
                    "SortModelList" : [
                        {
                            "sortColumn" : 1,
                            "sortDirection" : 1
                        }
                    ]
                }
            }'`
            
        - Response in JSON format (Status: 200 OK)
            
            `{
                "orderNumberList": [
                    "123456-20180101-00068801",
                    "123456-20180101-00067801",
                    "123456-20180101-00062801",
                    "123456-20180101-00059801",
                    "123456-20180101-00058801",
                    "123456-20180101-00057801",
                    "123456-20180101-00048801",
                    "123456-20180101-00046801",
                    "123456-20180101-00043801",
                    "123456-20180101-00039801",
                    "123456-20180101-00038801",
                    "123456-20180101-00037801",
                    "123456-20180101-00030801",
                    "123456-20180101-00028801",
                    "123456-20180101-00023801",
                    "123456-20180101-00022801",
                    "123456-20180101-00019801",
                    "123456-20180101-00017801",
                    "123456-20180101-00016801",
                    "123456-20180101-00076901",
                    "123456-20180101-00074901",
                    "123456-20180101-00073901",
                    "123456-20180101-00072901",
                    "123456-20180101-00071901",
                    "123456-20180101-00070901",
                    "123456-20180101-00068901",
                    "123456-20180101-00067901",
                    "123456-20180101-00066901",
                    "123456-20180101-00065901",
                    "123456-20180101-00064901"
                ],
                "MessageModelList": [
                    {
                        "messageType": "INFO",
                        "messageCode": "ORDER_EXT_API_SEARCH_ORDER_INFO_101",
                        "message": "注文検索に成功しました。"
                    }
                ],
                "PaginationResponseModel": {
                    "totalRecordsAmount": 79,
                    "totalPages": 3,
                    "requestPage": 1
                }
            }`
            
    2. **検索結果がなかった場合**
        - Request (curl コマンドを使った例)
            
            `curl -X POST \
              https://api.rms.rakuten.co.jp/es/2.0/order/searchOrder/ \
              -H 'Authorization: ESA xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' \
              -H 'Content-Type: application/json; charset=utf-8' \
              -d '{
                "dateType" : 1,
                "startDatetime" : "2017-10-14T00:00:00+0900",
                "endDatetime" : "2017-12-14T00:00:00+0900",
                "PaginationRequestModel" :
                {
                    "requestRecordsAmount" : 30,
                    "requestPage" : 1,
                    "SortModelList" : [
                        {
                            "sortColumn" : 1,
                            "sortDirection" : 1
                        }
                    ]
                }
            }'`
            
        - Response in JSON format (Status: 200 OK)
            
            `{
                "orderNumberList": [],
                "MessageModelList": [
                    {
                        "messageType": "INFO",
                        "messageCode": "ORDER_EXT_API_SEARCH_ORDER_INFO_102",
                        "message": "注文検索に成功しました。(検索結果０件)"
                    }
                ],
                "PaginationResponseModel": {
                    "totalRecordsAmount": null,
                    "totalPages": null,
                    "requestPage": null
                }
            }`
            
    3. **パラメータ指定に誤りがあった場合**
        - Request (curl コマンドを使った例)
            
            `curl -X POST \
              https://api.rms.rakuten.co.jp/es/2.0/order/searchOrder/ \
              -H 'Authorization: ESA xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' \
              -H 'Content-Type: application/json; charset=utf-8' \
              -d '{
                "startDatetime" : "10-14T00:00:00+0900",
                "endDatetime" : "2017-12-14T00:00:00+0900",
                "PaginationRequestModel" :
                {
                    "requestRecordsAmount" : 30,
                    "requestPage" : 1,
                    "SortModelList" : [
                        {
                            "sortColumn" : 1,
                            "sortDirection" : 1
                        }
                    ]
                }
            }'`
            
        - Response in JSON format (Status: 400 Bad Request)
            
            `{
                "orderNumberList": null,
                "MessageModelList": [
                    {
                        "messageType": "ERROR",
                        "messageCode": "ORDER_EXT_API_SEARCH_ORDER_ERROR_009",
                        "message": "dateTypeの項目を指定して下さい。"
                    },
                    {
                        "messageType": "ERROR",
                        "messageCode": "ORDER_EXT_API_SEARCH_ORDER_ERROR_011",
                        "message": "startDatetimeの書式が不正です。"
                    }
                ],
                "PaginationResponseModel": null
            }`