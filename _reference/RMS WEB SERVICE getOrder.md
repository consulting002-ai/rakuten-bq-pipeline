# RMS WEB SERVICE : getOrder

1. **Overview**
    
    この機能を利用すると、楽天ペイ注文の「注文情報の取得」を行うことができます。こちらは同期処理となります。
    
2. **Endpoint**
    
    https://api.rms.rakuten.co.jp/es/2.0/order/getOrder/
    
3. **Request**
    1. **Request Method**
        
        Method：POST
        
    2. **Request Header**
        
        
        | **Key** | **Value** |
        | --- | --- |
        | Authorization | ESA Base64(serviceSecret:licenseKey) |
        | Content-Type | application/json; charset=utf-8 |
    3. **Request Parameter**
        1. **Level 1: base**
            
            
            | **No** | **Logical Name** | **Parameter Name** | **Required** | **Type** | **Max Byte** | **Default** | **Descripiton** | **Sample** |
            | --- | --- | --- | --- | --- | --- | --- | --- | --- |
            | 1 | 注文番号リスト | orderNumberList | yes | List <String> | 4096 | - | 最大 100 件まで指定可能
            
            過去 730 日(2年)以内の注文を取得可能 | ["502763-20171027-00006701","502763-20171027-00006702"] |
            | 2 | バージョン番号 | version | yes | Number | 5 | - | 以下のいずれか
            
            3: 消費税増税対応
            4: 共通の送料込みライン対応
            5: 領収書、前払い期限版
            6: 顧客・配送対応注意表示詳細対応
            7: SKU対応
            8: 配送品質向上制度対応
            9: 置き配対応
            10: ソーシャルギフト対応
            
            ※versionは今後も追加されます。
            最新version(数字の大きい方)をご利用ください。
            ※古いversionは順次廃止予定となります。時期は決まり次第ご連絡いたします。 | 10 |
4. **Response**
    1. Tips：RMSの受注管理画面で表示されている「総合計（税込）」および「商品小計（税込）」の項目について
        - 「総合計（税込）」および「商品小計（税込）」の項目については、以下の通り算出することが可能です。
            - 総合計（税込）
                
                Level 2: OrderModel(totalPrice - couponAllTotalPrice + deliveryPrice + paymentCharge + additionalFeeOccurAmountToUser)
                
            - 商品小計（税込）
                
                注文ごとの商品小計（税込）：Level 2: OrderModel(goodsPrice) の税込価格
                
                Level 4: ItemModel(priceTaxIncl × units) + Level 3: WrappingModel(price)
                
                ※送付先ごとの総和
                
            - 送付先ごとの商品小計（税込）：Level 3: Package Model(goodsPrice) の税込価格
                
                Level 4: ItemModel(priceTaxIncl × units) + Level 3: WrappingModel(price)
                
                ※Level 4: ItemModel(priceTaxIncl × units)は商品ごとの総和
                
    2. **HTTP Status**
        
        
        | **Code** | **Status** | **Description** |
        | --- | --- | --- |
        | 200 | OK | リクエストが成功した。 |
        | 400 | Bad Request | リクエストが不正である。 |
        | 404 | Not Found | Request-URI に一致するものを見つけられなかった。 |
        | 405 | Method Not Allowed | 許可されていないメソッドを使用しようとした。 |
        | 500 | Internal Server Error | サーバ内部にエラーが発生した。 |
        | 503 | Service Unavailable | サービスが一時的に過負荷やメンテナンスで使用不可能である。 |
    3. **Response Header**
        
        
        | **Key** | **Value** |
        | --- | --- |
        | Content-Type | application/json;charset=utf-8 |
    4. **Response Parameter**
        1. **Level 1: base**
            
            
            | **No** | **Logical Name** | **Parameter Name** | **Not Null** | **Type** | **Max Byte** | **Default** | **Description** | **Sample** |
            | --- | --- | --- | --- | --- | --- | --- | --- | --- |
            | 1 | メッセージモデルリスト | MessageModelList | yes | List <MessageModel> | - | - |  |  |
            | 2 | 受注情報モデルリスト | OrderModelList | no | List <OrderModel> | - | - |  |  |
            | 3 | バージョン番号 | version | yes | Number | 5 | - | Request Parameterの「version」に「6」以降の値を指定すると取得可能 |  |
        2. **Level 2: MessageModel**
            
            
            | **No** | **Logical Name** | **Parameter Name** | **Not Null** | **Type** | **Max Byte** | **Default** | **Description** | **Sample** |
            | --- | --- | --- | --- | --- | --- | --- | --- | --- |
            | 1 | メッセージ種別 | messageType | yes | String | 16 | - | 以下のいずれか
            
            ・INFO
            ・ERROR
            ・WARNING | INFO |
            | 2 | メッセージコード | messageCode | yes | String | 128 | - | メッセージコードの一覧は[こちら](https://webservice.rms.rakuten.co.jp/merchant-portal/view/ja/common/1-1_service_index/rakutenpayorderapi/rakutenpaymsgcodereference/) | MESSAGE_CODE_SAMPLE |
            | 3 | メッセージ | message | yes | String | 1024 | - |  | メッセージサンプル |
            | 4 | 注文番号 | orderNumber | no | String | 382 | - |  | 502763-20171027-00006701 |
        3. **Level 2: OrderModel**
            
            
            | **No** | **Logical Name** | **Parameter Name** | **Not Null** | **Type** | **Max Byte** | **Default** | **Description** | **Sample** |
            | --- | --- | --- | --- | --- | --- | --- | --- | --- |
            | 1 | 注文番号 | orderNumber | yes | String | 382 | - |  | 502763-20171027-00006701 |
            | 2 | ステータス | orderProgress | yes | Number | 10 | - | 以下のいずれか
            
            100: 注文確認待ち
            200: 楽天処理中
            300: 発送待ち
            400: 変更確定待ち
            500: 発送済
            600: 支払手続き中
            700: 支払手続き済
            800: キャンセル確定待ち
            900: キャンセル確定 | 200 |
            | 3 | サブステータスID | subStatusId | no | Number | 10 | - |  | 1101 |
            | 4 | サブステータス | subStatusName | no | String | 255 | - |  | 03.サブステータスC |
            | 5 | 注文日時 | orderDatetime | yes | Datetime | 32 | - |  | 2017-09-25T20:03:43+0900 |
            | 6 | 注文確認日時 | shopOrderCfmDatetime | no | Datetime | 32 | - |  | 2017-09-25T20:03:43+0900 |
            | 7 | 注文確定日時 | orderFixDatetime | no | Datetime | 32 | - |  | 2017-09-25T20:36:07+0900 |
            | 8 | 発送指示日時 | shippingInstDatetime | no | Datetime | 32 | - |  | 2017-09-25T20:36:07+0900 |
            | 9 | 発送完了報告日時 | shippingCmplRptDatetime | no | Datetime | 32 | - |  | 2017-09-26T00:05:06+0900 |
            | 10 | キャンセル期限日 | cancelDueDate | no | Date | 16 | - |  | 2017-09-25 |
            | 11 | お届け日指定 | deliveryDate | no | Date | 10 | - |  | 2017-10-29 |
            | 12 | お届け時間帯 | shippingTerm | no | Number | 10 | - | 以下のいずれか
            
            0: なし
            1: 午前
            2: 午後
            9: その他
            
            h1h2: h1時-h2時 (h1は7～24まで任意で数値指定可能。h2は07～24まで任意で数値指定可能) | 708
            2324 |
            | 13 | コメント | remarks | no | String | 32767 | - | 備考欄のこと | [配送日時指定:]
            2017-11-01(水)
            14:00
            自由記入欄の入力 |
            | 14 | ギフト配送希望フラグ | giftCheckFlag | yes | Number | 1 | - | 以下のいずれか
            
            0: ギフト注文ではない
            1: ギフト注文である | 1 |
            | 15 | ソーシャルギフト注文フラグ | socialGiftFlag | yes | Number | 1 | - | 以下のいずれか
            
            0: ソーシャルギフト注文ではない
            1: ソーシャルギフト注文である | 1 |
            | 16 | 複数送付先フラグ | severalSenderFlag | yes | Number | 1 | - | 以下のいずれか
            
            0: 複数配送先無し
            1: 複数配送先有り | 0 |
            | 17 | 送付先一致フラグ | equalSenderFlag | yes | Number | 1 | - | 以下のいずれか
            
            0: 注文者と送付者の住所が同じではない
            1: 注文が単数で注文者と送付者の住所が同じ | 1 |
            | 18 | 離島フラグ | isolatedIslandFlag | yes | Number | 1 | - | 以下のいずれか
            
            0: 送付先に離島が含まれていない
            1: 送付先に離島が含まれている | 1 |
            | 19 | 楽天会員フラグ | rakutenMemberFlag | yes | Number | 1 | - | 以下のいずれか
            
            0: 楽天会員ではない
            1: 楽天会員である | 1 |
            | 20 | 利用端末 | carrierCode | yes | Number | 10 | - | 以下のいずれか
            
            0: PC (Windows系のスマートフォン、タブレットを含む)
            1: モバイル(docomo) フィーチャーフォン
            2: モバイル(KDDI) フィーチャーフォン
            3: モバイル(Softbank) フィーチャーフォン
            5: モバイル(WILLCOM) フィーチャーフォン
            11: スマートフォン（iPhone系）
            12: スマートフォン（Android系）
            19: スマートフォン（その他）
            21: タブレット（iPad系）
            22: タブレット（Android系）
            29: タブレット（その他）
            99: その他　不明な場合も含む | 11 |
            | 21 | メールキャリアコード | emailCarrierCode | yes | Number | 10 | - | 以下のいずれか
            
            0: PC ("@i.softbank.jp"を含む)
            1: DoCoMo
            2: au
            3: SoftBank
            5: WILLCOM
            99: その他 | 2 |
            | 22 | 注文種別 | orderType | yes | Number | 10 | - | 以下のいずれか
            
            1: 通常購入
            4: 定期購入
            5: 頒布会
            6: 予約商品 | 1 |
            | 23 | 申込番号 | reserveNumber | no | String | 382 | - | 定期購入、予約、頒布会の申込番号 | 502763-20171027-00003701-r |
            | 24 | 申込お届け回数 | reserveDeliveryCount | no | Number | 5 | - | 予約は常に１、定期購入、頒布会は確定した回数 | 6 |
            | 25 | 警告表示タイプ | cautionDisplayType | yes | Number | 5 | - | 以下のいずれか
            
            0: 表示なし
            1: 表示あり 注意喚起
            2: 表示あり キャンセル確定
            ※「顧客・配送対応注意表示」のこと | 0 |
            | 26 | 警告表示タイプ詳細 | cautionDisplayDetailType | no | Number | 10 | - | 以下のいずれか
            
            101: 前払い未払いに注意
            102: 受取拒否に注意
            103: 長期不在による受取拒否に注意
            104: 開梱後の返品に注意
            105: 高いサービスレベルの要望に注意
            
            ※2021年10月13日（水）以降に、警告表示タイプ（cautionDisplayType）が「1: 表示あり 注意喚起」と判断された注文にのみ、本項目内に値が設定されます。
            2021年10月13日（水）以前に、警告表示タイプ（cautionDisplayType）が「1: 表示あり 注意喚起」と判断された注文、または「1: 表示あり 注意喚起」以外と判断された注文には、本項目内に値は設定されません。
             
            ※Request Parameterの「version」に「6」以降の値を指定すると取得可能 | 101 |
            | 27 | 楽天確認中フラグ | rakutenConfirmFlag | yes | Number | 1 | - | 以下のいずれか
            
            0: 楽天確認中ではない
            1: 楽天確認中 | 0 |
            | 28 | 商品合計金額 | goodsPrice | yes | Number | 10 | -9999 | 商品金額 + ラッピング料 | 1000 |
            | 29 | 外税合計 | goodsTax | yes | Number | 10 | -9999 | 税込み商品の場合は0が取得される
            
            ※未確定の場合、-9999になります。
            ※廃止予定項目のため、version8以降は取得できません。"請求額に対する税額(reqPriceTax)"をご使用ください。 | 80 |
            | 30 | 送料合計 | postagePrice | yes | Number | 10 | -9999 | 対象受注に紐付く送料（送付先毎の送料の合計）
            
            ※未確定の場合、-9999になります。 | 100 |
            | 31 | 代引料合計 | deliveryPrice | yes | Number | 10 | -9999 | 代引手数料が掛からない決済手段の場合は、0になります。
            
            ※未確定の場合、-9999になります。 | 50 |
            | 32 | 決済手数料合計 | paymentCharge | yes | Number | 10 | -9999 | 決済手数料が掛からない決済手段の場合は、0になります。
            
            ※未確定の場合、-9999になります。
            ※決済手数料については、[こちら](https://navi-manual.faq.rakuten.net/service/000008025)をご確認ください。 | 250 |
            | 33 | 決済手続税率 | paymentChargeTaxRate | yes | Number | - | - |  | 0.1 |
            | 34 | 合計金額 | totalPrice | yes | Number | 10 | -9999 | 商品金額 + 送料 + ラッピング料
            ※未確定の場合、-9999になります。 | 1230 |
            | 35 | 請求金額 | requestPrice | yes | Number | 10 | -9999 | 商品金額 + 送料 + ラッピング料 + 決済手数料 + 注文者負担金 - クーポン利用総額 - ポイント利用額
            ※未確定の場合、-9999になります。 | 1000 |
            | 36 | クーポン利用総額 | couponAllTotalPrice | yes | Number | 10 | - | クーポンの総額 | 100 |
            | 37 | 店舗発行クーポン利用額 | couponShopPrice | yes | Number | 10 | - | クーポン原資コードが「1」のクーポンの総額
            
            ※未確定の場合、-9999になります。 | 70 |
            | 38 | 楽天発行クーポン利用額 | couponOtherPrice | yes | Number | 10 | - | クーポン原資コードが「1」以外のクーポンの総額
            
            ※未確定の場合、-9999になります。 | 30 |
            | 39 | 注文者負担金合計 | additionalFeeOccurAmountToUser | yes | Number | 10 | -9999 | 注文者が支払う負担金の合計
            負担金がない場合は、0になります。
            
            ※負担金はRMS画面や[マニュアル](https://navi-manual.faq.rakuten.net/shop-setting/000010508)上では、後払い利用手数料と表記されています。
            ※未確定の場合、-9999になります。 | 250 |
            | 40 | 店舗負担金合計 | additionalFeeOccurAmountToShop | yes | Number | 10 | -9999 | 店舗様が支払う負担金の合計
            負担金がない場合は、0になります。
            
            ※負担金はRMS画面や[マニュアル](https://navi-manual.faq.rakuten.net/shop-setting/000010508)上では、後払い利用手数料と表記されています。
            ※未確定の場合、-9999になります。 | 250 |
            | 41 | あす楽希望フラグ | asurakuFlag | yes | Number | 1 | - | 以下のいずれか
            
            0: あす楽希望無し注文
            1: あす楽希望有り注文 | 0 |
            | 42 | 医薬品受注フラグ | drugFlag | yes | Number | 1 | - | 以下のいずれか
            
            0: 医薬品を含む注文ではない
            1: 医薬品を含む注文である | 0 |
            | 43 | 楽天スーパーDEAL商品受注フラグ | dealFlag | yes | Number | 1 | - | 以下のいずれか
            
            0: 楽天スーパーディール商品を含む受注ではない
            1: 楽天スーパーディール商品を含む受注である | 1 |
            | 44 | メンバーシッププログラム受注タイプ | membershipType | yes | Number | 5 | - | 以下のいずれか
            
            0: 楽天プレミアムでも楽天学割対象受注でもない
            1: 楽天プレミアム対象受注である
            2: 楽天学割対象受注である
            
            ※2020/10/27以降の注文の場合、2は取得できません。
            　2021/12/1以降の注文の場合、1は取得できません。 | 2 |
            | 45 | ひとことメモ | memo | no | String | 4000 | - | 全角、半角にかかわらず1000文字以下 | ひとことメモ |
            | 46 | 担当者 | operator | no | String | 382 | - |  | 担当者 |
            | 47 | メール差込文
            (お客様へのメッセージ) | mailPlugSentence | no | String | 3072 | - |  | メール差込文 |
            | 48 | 購入履歴修正有無フラグ | modifyFlag | yes | Number | 1 | - | 以下のいずれか
            
            0: 購入履歴画面からの修正無し
            1: 購入履歴画面からの修正有り | 0 |
            | 49 | 領収書発行回数 | receiptIssueCount | yes | Number | Long型の最大値に準ずる | - | ※Request Parameterの「version」に「5」以降の値を指定すると取得可能 | 2 |
            | 50 | 領収書発行履歴リスト | receiptIssueHistoryList | no | List <Datetime> | - | - | 発行回数に準ずる(32byte × 発行回数)
            ※Request Parameterの「version」に「5」以降の値を指定すると取得可能 | ["2019-09-26T00:05:06+0900", "2020-09-26T00:05:06+0900"] |
            | 51 | 注文者モデル | OrdererModel | yes | OrdererModel | - | - |  |  |
            | 52 | 支払方法モデル | SettlementModel | no | SettlementModel | - | - |  |  |
            | 53 | 配送方法モデル | DeliveryModel | yes | DeliveryModel | - | - |  |  |
            | 54 | ポイントモデル | PointModel | no | PointModel | - | - |  |  |
            | 55 | ラッピングモデル1 | WrappingModel1 | no | WrappingModel | - | - |  |  |
            | 56 | ラッピングモデル2 | WrappingModel2 | no | WrappingModel | - | - |  |  |
            | 57 | 送付先モデルリスト | PackageModelList | yes | List <PackageModel> | - | - |  |  |
            | 58 | クーポンモデルリスト | CouponModelList | no | List <CouponModel> | - | - |  |  |
            | 59 | 変更・キャンセルモデルリスト | ChangeReasonModelList | no | List <ChangeReasonModel> | - | - |  |  |
            | 60 | 税情報モデルリスト | TaxSummaryModelList | no | List <TaxSummaryModel> | - | - | ※2019/7/30の増税対応リリース前の注文の場合、初期値は[]（空のモデル）となります。
            店舗様にて税率等の項目を更新した後は値が設定されます。
            なお、リリース後の注文には最初から値が設定されています。 |  |
            | 61 | 期限日モデルリスト | DueDateModelList | no | List<DueDateModel> | - | - | ※Request Parameterの「version」に「5」以降の値を指定すると取得可能 |  |
            | 62 | 最強翌日配送フラグ | deliveryCertPrgFlag | yes | Number | 1 | - | 以下のいずれか
            0: 最強翌日配送対象外注文
            1: 最強翌日配送対象注文
            ※購入時に遅延補償対象となった注文です。補償対象外となった場合でもフラグは変更されません。
            ※2024年11月20日（水）のサービス名称変更（「最強配送」から「最強翌日配送」に変更）に伴いLogical Nameのみ変更。 | 1 |
            | 63 | 当日出荷フラグ | oneDayOperationFlag | yes | Number | 1 | - | 以下のいずれか
            0: 1営業日以内出荷ではない注文
            1: 1営業日以内出荷の注文
            ※購入時に最短お届け可能日が指定された注文、またはソーシャルギフト注文において受取情報入力時に最短お届け可能日が指定された注文です。 | 1 |
        4. **Level 3: OrdererModel**
            
            
            | **No** | **Logical Name** | **Parameter Name** | **Not Null** | **Type** | **Max Byte** | **Default** | **Description** | **Sample** |
            | --- | --- | --- | --- | --- | --- | --- | --- | --- |
            | 1 | 郵便番号1 | zipCode1 | yes | String | 382 | - |  | 158 |
            | 2 | 郵便番号2 | zipCode2 | yes | String | 382 | - |  | 0094 |
            | 3 | 都道府県 | prefecture | yes | String | 382 | - |  | 東京都 |
            | 4 | 郡市区 | city | yes | String | 382 | - |  | 世田谷区 |
            | 5 | それ以降の住所 | subAddress | yes | String | 382 | - |  | 玉川 |
            | 6 | 姓 | familyName | yes | String | 382 | - |  | 楽天 |
            | 7 | 名 | firstName | yes | String | 382 | - |  | 太郎 |
            | 8 | 姓カナ | familyNameKana | no | String | 382 | - |  | ラクテン |
            | 9 | 名カナ | firstNameKana | no | String | 382 | - |  | タロウ |
            | 10 | 電話番号1 | phoneNumber1 | no
            
            電話番号の1,2,3の内、nullは１つまで許可 | String | 382 | - |  | 090 |
            | 11 | 電話番号2 | phoneNumber2 |  | String | 382 | - |  | 1111 |
            | 12 | 電話番号3 | phoneNumber3 |  | String | 382 | - |  | 2222 |
            | 13 | メールアドレス | emailAddress | yes | String | 382 | - | メールアドレスはマスキングされています | 815db15ff6ee7c0285bf7f5ce8485450s1@pc.fw.rakuten.ne.jp |
            | 14 | 性別 | sex | no | String | 382 | - |  | 男 |
            | 15 | 誕生日(年) | birthYear | no | Number | 4 | - |  | 1984 |
            | 16 | 誕生日(月) | birthMonth | no | Number | 2 | - |  | 1 |
            | 17 | 誕生日(日) | birthDay | no | Number | 2 | - |  | 2 |
    5. **Level 3: SettlementModel**
        
        
        | **No** | **Logical Name** | **Parameter Name** | **Not Null** | **Type** | **Max Byte** | **Default** | **Description** | **Sample** |
        | --- | --- | --- | --- | --- | --- | --- | --- | --- |
        | 1 | 支払方法コード | settlementMethodCode | yes | Number | 6 | - | 以下のいずれか
        
        1: クレジットカード
        2: 代金引換
        4: ショッピングクレジット／ローン
        5: オートローン
        6: リース
        7: 請求書払い
        8: ポイント
        9: 銀行振込
        12: Apple Pay
        13: セブンイレブン（前払）
        14: ローソン、郵便局ATM等（前払）、または、ファミリーマート、ローソン等（前払）※
        16: Alipay
        17: PayPal
        21: 後払い決済
        27: Alipay（支付宝）
        
        ※2026年1月22日（木）の支払方法名変更に伴い、新旧名称どちらの注文もコードは14となります。 | 1 |
        | 2 | 支払方法名 | settlementMethod | yes | String | 382 | - |  | クレジットカード |
        | 3 | 楽天市場の共通決済手段フラグ | rpaySettlementFlag | yes | Number | 1 | - | 支払方法の種別が以下のいずれか
        
        0: 選択制決済
        1: 楽天市場の共通決済手段 | 1 |
        | 4 | クレジットカード種類 | cardName | no | String | 382 | - | 支払方法名が「クレジットカード」の場合のみ値があります | VISA |
        | 5 | クレジットカード番号 | cardNumber | no | String | 382 | - | 支払方法名が「クレジットカード」の場合のみ値があります | XXXX-XXXX-XXXX-0015 |
        | 6 | クレジットカード名義人 | cardOwner | no | String | 382 | - | 支払方法名が「クレジットカード」の場合のみ値があります | TARO RAKUTEN |
        | 7 | クレジットカード有効期限 | cardYm | no | String | 382 | - | 支払方法名が「クレジットカード」の場合のみ値があります | 2017-11 |
        | 8 | クレジットカード支払い方法 | cardPayType | no | Number | 5 | - | 以下のいずれか
        
        0: 一括払い
        1: リボ払い
        2: 分割払い
        3: その他払い
        4: ボーナス一括払い
        
        支払方法名が「クレジットカード」の場合のみ値があります | 0 |
        | 9 | クレジットカード支払い回数 | cardInstallmentDesc | no | String | 382 | - | 以下のいずれか
        
        103: 3回払い
        105: 5回払い
        106: 6回払い
        110: 10回払い
        112: 12回払い
        115: 15回払い
        118: 18回払い
        120: 20回払い
        124: 24回払い
        
        支払方法名が「クレジットカード」、かつ、「クレジットカード支払い方法」が「2: 分割払い」の場合のみ値があります |  |
    6. **Level 3: DeliveryModel**
        
        
        | **No** | **Logical Name** | **Parameter Name** | **Not Null** | **Type** | **Max Byte** | **Default** | **Description** | **Sample** |
        | --- | --- | --- | --- | --- | --- | --- | --- | --- |
        | 1 | 配送方法 | deliveryName | yes | String | 382 | - | 店舗設定で設定した配送方法。 | 宅配便 |
        | 2 | 配送区分 | deliveryClass | no | Number | 10 | - | 0: 選択なし
        1: 普通
        2: 冷蔵
        3: 冷凍
        4: その他１
        5: その他２
        6: その他３
        7: その他４
        8: その他５ |  |
    7. **Level 3: PointModel**
        
        
        | **No** | **Logical Name** | **Parameter Name** | **Not Null** | **Type** | **Max Byte** | **Default** | **Description** | **Sample** |
        | --- | --- | --- | --- | --- | --- | --- | --- | --- |
        | 1 | ポイント利用額 | usedPoint | yes | Number | 10 | - |  | 100 |
    8. **Level 3: WrappingModel**
        
        
        | **No** | **Logical Name** | **Parameter Name** | **Not Null** | **Type** | **Max Byte** | **Default** | **Description** | **Sample** |
        | --- | --- | --- | --- | --- | --- | --- | --- | --- |
        | 1 | ラッピングタイトル | title | yes | Number | 5 | - | 以下のいずれか
        
        1: 包装紙
        2: リボン | 1 |
        | 2 | ラッピング名 | name | yes | String | 396 | - |  | ラッピング名 |
        | 3 | 料金 | price | no | Number | 10 | - |  | 100 |
        | 4 | 税込別 | includeTaxFlag | yes | Number | 1 | 0 | 以下のいずれか
        
        0: 税別
        1: 税込 | 1 |
        | 5 | ラッピング削除フラグ | deleteWrappingFlag | yes | Number | 1 | 0 |  | 0 |
        | 6 | ラッピング税率 | taxRate | yes | Number | - | - |  | 0.1 |
        | 7 | ラッピング税額 | taxPrice | yes | Number | 10 | - | ※税込/税抜に関わらず、値が設定されます。 | 10 |
    9. **Level 3: PackageModel**
        
        
        | **No** | **Logical Name** | **Parameter Name** | **Not Null** | **Type** | **Max Byte** | **Default** | **Description** | **Sample** |
        | --- | --- | --- | --- | --- | --- | --- | --- | --- |
        | 1 | 送付先ID | basketId | yes | Number | 10 | - |  | 10631675 |
        | 2 | 送料 | postagePrice | yes | Number | 10 | -9999 | 送付先に紐付く送料 （R-StoreFrontで指定した送料設定に準拠）
        
        ※未設定の場合、-9999になります。 | 100 |
        | 3 | 送料税率 | postageTaxRate | yes | Number | - | - |  | 0.1 |
        | 4 | 代引料 | deliveryPrice | yes | Number | 10 | -9999 | ※未設定の場合、-9999になります | 0 |
        | 5 | 代引料税率 | deliveryTaxRate | yes | Number | - | - |  | 0.1 |
        | 6 | 送付先外税合計 | goodsTax | yes | Number | 10 | -9999 | 税込み商品の場合は0が取得される
        
        ※未設定の場合、-9999になります。
        ※廃止予定項目のため、version8以降は取得できません。"請求額に対する税額(reqPriceTax)"をご使用ください。 | 0 |
        | 7 | 商品合計金額 | goodsPrice | yes | Number | 10 | -9999 | 送付先に紐付く
        商品金額 + ラッピング料 | 10000 |
        | 8 | 合計金額 | totalPrice | yes | Number | 10 | -9999 | 送付先に紐付く
        商品金額 + 送料 + ラッピング料
        
        ※代引手数料は含まれません。
        ※未確定の場合、-9999になります。 | 10100 |
        | 9 | のし | noshi | no | String | 382 | - |  | のし |
        | 10 | 送付先モデル削除フラグ | packageDeleteFlag | yes | Number | 1 | 0 | 以下のいずれか
        
        0: 送付先モデルを削除しない
        1: 送付先モデルを削除する | 0 |
        | 11 | 送付者モデル | SenderModel | yes | SenderModel | - | - |  |  |
        | 12 | 商品モデルリスト | ItemModelList | yes | List <ItemModel> | - | - |  |  |
        | 13 | 発送モデルリスト | ShippingModelList | no | List <ShippingModel> | - | - |  |  |
        | 14 | コンビニ配送モデル | DeliveryCvsModel | no | DeliveryCvsModel | - | - | 配送方法がコンビニ、郵便局受取の場合、参照可能。 |  |
        | 15 | 購入時配送会社 | defaultDeliveryCompanyCode | yes | String | 382 | - | 以下のいずれか
        
        1000: その他
        1001: ヤマト運輸
        1002: 佐川急便
        1003: 日本郵便
        1004: 西濃運輸
        1005: セイノースーパーエクスプレス
        1006: 福山通運
        1007: 名鉄運輸
        1008: トナミ運輸
        1009: 第一貨物
        1010: 新潟運輸
        1011: 中越運送
        1012: 岡山県貨物運送
        1013: 久留米運送
        1014: 山陽自動車運送
        1015: NXトランスポート
        1016: エコ配
        1017: EMS
        1018: DHL
        1019: FedEx
        1020: UPS
        1021: 日本通運
        1022: TNT
        1023: OCS
        1024: USPS
        1025: SFエクスプレス
        1026: Aramex
        1027: SGHグローバル・ジャパン
        1028: Rakuten EXPRESS
        1029: 日本郵便 楽天倉庫出荷
        1030: ヤマト運輸 クロネコゆうパケット
        1031: 名鉄NX運輸
        
        ※Request Parameterの「version」に「4」以降の値を指定すると取得可能。 | 1001 |
        | 16 | 置き配フラグ | dropOffFlag | yes | Number | 1 | - | 以下のいずれか
        
        0: 置き配対象外注文
        1: 置き配注文
        
        ※対面受取り (置き配を利用しない）を選ばれた時、0となります。 | 1 |
        | 17 | 置き配場所 | dropOffLocation | no | String | 382 | - | 宅配ボックス
        玄関前
        玄関前鍵付容器
        ポスト（郵便受箱）
        メーターボックス
        物置
        車庫
        
        ※置き配対象外注文の場合、Nullとなります。 | 宅配ボックス |
        | 18 | ソーシャルギフト情報モデル | SocialGiftModel | no | SocialGiftModel | - | - | ソーシャルギフト注文の場合、参照可能 |  |
    10. **Level 4: SenderModel**
        
        
        | **No** | **Logical Name** | **Parameter Name** | **Not Null** | **Type** | **Max Byte** | **Default** | **Description** | **Sample** |
        | --- | --- | --- | --- | --- | --- | --- | --- | --- |
        | 1 | 郵便番号1 | zipCode1 | yes | String | 382 | - | ※ソーシャルギフト注文において受取情報が未入力の場合、ダミーデータ"999"になります。 | 158 |
        | 2 | 郵便番号2 | zipCode2 | yes | String | 382 | - | ※ソーシャルギフト注文において受取情報が未入力の場合、ダミーデータ"9999"になります。 | 0094 |
        | 3 | 都道府県 | prefecture | yes | String | 382 | - | ※ソーシャルギフト注文において受取情報が未入力の場合、ダミーデータ"入力待ち"になります。 | 東京都 |
        | 4 | 郡市区 | city | yes | String | 382 | - | ※ソーシャルギフト注文において受取情報が未入力の場合、ダミーデータ"入力待ち"になります。 | 世田谷区 |
        | 5 | それ以降の住所 | subAddress | yes | String | 382 | - | ※ソーシャルギフト注文において受取情報が未入力の場合、ダミーデータ"入力待ち"になります。 | 玉川 |
        | 6 | 姓 | familyName | yes | String | 382 | - | ※ソーシャルギフト注文において受取情報が未入力の場合、ダミーデータ"入力待ち"になります。 | 楽天 |
        | 7 | 名 | firstName | no | String | 382 | - | ※ソーシャルギフト注文において受取情報が未入力の場合、ダミーデータ"入力待ち"になります。 | 太郎 |
        | 8 | 姓カナ | familyNameKana | no | String | 382 | - | ※ソーシャルギフト注文において受取情報が未入力の場合、ダミーデータ"ニュウリョクマチ"になります。 | ラクテン |
        | 9 | 名カナ | firstNameKana | no | String | 382 | - | ※ソーシャルギフト注文において受取情報が未入力の場合、ダミーデータ"ニュウリョクマチ"になります。 | タロウ |
        | 10 | 電話番号1 | phoneNumber1 | no
        
        電話番号の1,2,3の内、nullは１つまで許可 | String | 382 | - | ※ソーシャルギフト注文において受取情報が未入力の場合、ダミーデータ"999"になります。 | 090 |
        | 11 | 電話番号2 | phoneNumber2 |  | String | 382 | - | ※ソーシャルギフト注文において受取情報が未入力の場合、ダミーデータ"9999"になります。 | 0000 |
        | 12 | 電話番号3 | phoneNumber3 |  | String | 382 | - | ※ソーシャルギフト注文において受取情報が未入力の場合、ダミーデータ"9999"になります。 | 0000 |
        | 13 | 離島フラグ | isolatedIslandFlag | yes | Number | 1 | - | 以下のいずれか
        
        0: 離島ではない
        1: 離島である | 0 |
    11. **Level 4: ItemModel**
        
        
        | **No** | **Logical Name** | **Parameter Name** | **Not Null** | **Type** | **Max Byte** | **Default** | **Description** | **Sample** |
        | --- | --- | --- | --- | --- | --- | --- | --- | --- |
        | 1 | 商品明細ID | itemDetailId | yes | Number | 10 | - |  | 10631675 |
        | 2 | 商品名 | itemName | yes | String | 3072 | - |  | 商品名 |
        | 3 | 商品ID | itemId | yes | Number | 10 | - |  | 10000119 |
        | 4 | 商品番号 | itemNumber | no | String | 382 | - | 項目選択肢別在庫が指定された商品の場合、以下のルールで値が表示されます
        
        SKU移行前注文：商品番号（店舗様が登録した番号）＋項目選択肢ID（横軸）＋項目選択肢ID（縦軸）
        
        SKU移行後注文：商品番号（店舗様が登録した番号） | 商品番号mgreen |
        | 5 | 商品管理番号 | manageNumber | yes | String | 382 | - |  | mikan |
        | 6 | 単価 | price | yes | Number | 10 | - |  | 100 |
        | 7 | 個数 | units | yes | Number | 10 | - |  | 2 |
        | 8 | 送料込別 | includePostageFlag | yes | Number | 1 | - | 以下のいずれか
        
        0: 送料別
        1: 送料込みもしくは送料無料 | 1 |
        | 9 | 税込別 | includeTaxFlag | yes | Number | 1 | - | 以下のいずれか
        
        0: 税別
        1: 税込み | 0 |
        | 10 | 代引手数料込別 | includeCashOnDeliveryPostageFlag | yes | Number | 1 | - | 以下のいずれか
        
        0: 代引手数料別
        1: 代引手数料込み | 1 |
        | 11 | 項目・選択肢 | selectedChoice | no | String | 12000 | - | HTMLタグ除去済み。
        項目選択肢、項目選択肢別在庫が指定された商品が購入された注文の場合、以下のルールで値が入ります。
        
        SKU移行前注文：項目選択肢情報、項目選択肢別在庫情報が入ります。
        
        SKU移行後注文：項目選択肢情報は引き続き入ります。
        バリエーション項目名・バリエーション選択肢（旧・項目選択肢別在庫情報）は入りません。Level 5: skuModel > skuInfo にて取得可能です。 | 項目選択肢A:A選択肢１
        項目選択肢B:B選択肢２ |
        | 12 | ポイント倍率 | pointRate | yes | Number | 5 | 0 | ポイントレート | 1 |
        | 13 | ポイントタイプ | pointType | yes | Number | 5 | 0 | 以下のいずれか
        
        0: 変倍なし
        1: 店舗別変倍
        2: 商品別変倍
        -99: エラー時無効値 | 0 |
        | 14 | 在庫タイプ | inventoryType | yes | Number | 5 | - | 以下のいずれか
        
        0: 在庫設定なし
        1: 通常在庫設定
        2: 項目選択肢在庫設定 | 2 |
        | 15 | 納期情報 | delvdateInfo | no | String | 96 | - |  | 2～5日以内に発送 |
        | 16 | 在庫連動オプション | restoreInventoryFlag | yes | Number | 1 | 0 | 以下のいずれか
        
        0: 商品の設定に従う
        1: 在庫連動する
        2: 在庫連動しない | 0 |
        | 17 | 楽天スーパーDEAL商品フラグ | dealFlag | yes | Number | 1 | - | 以下のいずれか
        
        0: 楽天スーパーディール商品ではない
        1: 楽天スーパーディール商品である | 0 |
        | 18 | 医薬品フラグ | drugFlag | yes | Number | 1 | - | 以下のいずれか
        
        0: 医薬品ではない
        1: 医薬品である | 1 |
        | 19 | 商品削除フラグ | deleteItemFlag | yes | Number | 1 | 0 | 以下のいずれか
        
        0: 商品を削除しない
        1: 商品を削除する | 0 |
        | 20 | 商品税率 | taxRate | yes | Number | - | - |  | 0.1 |
        | 21 | 商品毎税込価格 | priceTaxIncl | yes | Number | 10 | - | ・税込商品の場合：
            商品単価＝商品毎税込価格
        ・税別商品の場合：
            商品単価＝税別価格
            商品毎税込単価＝税込価格（商品単価 * (1+税率））
            端数処理は、店舗設定に準ずる | 1100 |
        | 22 | 単品配送フラグ | isSingleItemShipping | yes | Number | 1 | - | 以下のいずれか
        
        0: 単品配送ではない
        1: 単品配送である
        
        ※Request Parameterの「version」に「4」以降の値を指定すると取得可能 | 1 |
        | 23 | SKUモデルリスト | SkuModelList | yes | List<skuModel> | - | - |  |  |
    12. **Level 4: ShippingModel**
        
        
        | **No** | **Logical Name** | **Parameter Name** | **Not Null** | **Type** | **Max Byte** | **Default** | **Description** | **Sample** |
        | --- | --- | --- | --- | --- | --- | --- | --- | --- |
        | 1 | 発送明細ID | shippingDetailId | yes | Number | 12 | - | 楽天が発行するIDで更新・削除の場合に利用します | 56486 |
        | 2 | お荷物伝票番号 | shippingNumber | no | String | 382 | - |  | 111-22-334 |
        | 3 | 配送会社 | deliveryCompany | no | String | 382 | - | 以下のいずれか
        
        1000: その他
        1001: ヤマト運輸
        1002: 佐川急便
        1003: 日本郵便
        1004: 西濃運輸
        1005: セイノースーパーエクスプレス
        1006: 福山通運
        1007: 名鉄運輸
        1008: トナミ運輸
        1009: 第一貨物
        1010: 新潟運輸
        1011: 中越運送
        1012: 岡山県貨物運送
        1013: 久留米運送
        1014: 山陽自動車運送
        1015: NXトランスポート
        1016: エコ配
        1017: EMS
        1018: DHL
        1019: FedEx
        1020: UPS
        1021: 日本通運
        1022: TNT
        1023: OCS
        1024: USPS
        1025: SFエクスプレス
        1026: Aramex
        1027: SGHグローバル・ジャパン
        1028: Rakuten EXPRESS
        1029: 日本郵便 楽天倉庫出荷
        1030: ヤマト運輸 クロネコゆうパケット
        1031: 名鉄NX運輸 | 1001 |
        | 4 | 配送会社名 | deliveryCompanyName | no | String | 64 | - |  | ヤマト運輸 |
        | 5 | 発送日 | shippingDate | no | Date | 10 | YYYY-MM-DD |  |  |
    13. **Level 4: DeliveryCVSModel**
        
        
        | **No** | **Logical Name** | **Parameter Name** | **Not Null** | **Type** | **Max Byte** | **Default** | **Description** | **Sample** |
        | --- | --- | --- | --- | --- | --- | --- | --- | --- |
        | 1 | コンビニコード | cvsCode | no | Number | 5 | - | 以下のいずれか
        
        1: ファミリーマート
        20: ミニストップ
        40: サークルK
        41: サンクス
        50: ローソン
        60: 郵便局
        70: スリーエフ
        71: エブリワン
        72: ココストア
        74: セーブオン
        80: デイリーヤマザキ
        81: ヤマザキデイリーストア
        82: ニューヤマザキデイリーストア
        85: ニューデイズ
        90: ポプラ
        91: くらしハウス
        92: スリーエイト
        93: 生活彩家 | 41 |
        | 2 | ストア分類コード | storeGenreCode | no | String | 96 | - |  | 8895 |
        | 3 | ストアコード | storeCode | no | String | 96 | - |  | 15358 |
        | 4 | ストア名称 | storeName | no | String | 382 | - |  | 楽天クリムゾンハウス |
        | 5 | 郵便番号 | storeZip | no | String | 18 | - |  | 158-0094 |
        | 6 | 都道府県 | storePrefecture | no | String | 24 | - |  | 東京都 |
        | 7 | その他住所 | storeAddress | no | String | 382 | - |  | 世田谷区玉川一丁目14番1号 楽天クリムゾンハウス |
        | 8 | 発注エリアコード | areaCode | no | String | 96 | - |  | 01 |
        | 9 | センターデポコード | depo | no | String | 96 | - |  | 07 |
        | 10 | 開店時間 | openTime | no | String | 7 | - |  | 06:00 |
        | 11 | 閉店時間 | closeTime | no | String | 7 | - |  | 24:00 |
        | 12 | 特記事項 | cvsRemarks | no | String | 382 | - |  | 備考 |
    14. **Level 4: SocialGiftModel**
        
        
        | **No** | **Logical Name** | **Parameter Name** | **Not Null** | **Type** | **Max Byte** | **Default** | **Description** | **Sample** |
        | --- | --- | --- | --- | --- | --- | --- | --- | --- |
        | 1 | ソーシャルギフト管理番号 | sgMngNumber | yes | String | 382 | - | 受取人からの問合せ用に発行される管理番号。 | 502763-20171027-000155555-sg |
        | 2 | 受取情報入力期限日 | inputDueDate | yes | Date | 10 | - | YYYY-MM-DD | 2026-06-15 |
        | 3 | 受取情報入力済フラグ | inputFlag | yes | Number | 1 | 0 | 以下のいずれか
        
        0: 受取情報未入力
        1: 受取情報入力済み | 0 |
        | 4 | 受取情報入力日時 | inputCompDatetime | no | Datetime | 32 | - | YYYY-MM-DDThh:mm:ss+09:00 | 2026-06-10T09:59:47+0900 |
        | 5 | 受取人メールアドレス | receiverEmailAddress | no | String | 382 | - | メールアドレスはマスキングされています。 | 815db15ff6ee7c0285bf7f5ce8485450s1@pc.fw.rakuten.ne.jp |
    15. **Level 3: CouponModel**
        
        
        | **No** | **Logical Name** | **Parameter Name** | **Not Null** | **Type** | **Max Byte** | **Default** | **Description** | **Sample** |
        | --- | --- | --- | --- | --- | --- | --- | --- | --- |
        | 1 | クーポンコード | couponCode | yes | String | 28 | - |  | UCSK-XEPV-LEGJ-H0SW |
        | 2 | クーポン対象の商品ID | itemId | yes | Number | 10 | - | 該当する商品がない場合は 0 が指定されます。 | 10631675 |
        | 3 | クーポン名 | couponName | yes | String | 382 | - |  | テストクーポンです |
        | 4 | クーポン効果(サマリー) | couponSummary | yes | String | 382 | - |  | 定額割引 100円 |
        | 5 | クーポン原資 | couponCapital | yes | String | 64 | - | 以下のいずれか
        
        ・ショップ
        ・メーカー
        ・サービス
        
        ※RMS画面ではショップは店舗原資、メーカーは楽天原資、サービスは楽天原資と表記されています。 | ショップ |
        | 6 | クーポン原資コード | couponCapitalCode | yes | Number | 5 | - | 以下のいずれか
        
        1：ショップ
        2：メーカー
        3：サービス
        
        ※RMS画面ではショップは店舗原資、メーカーは楽天原資、サービスは楽天原資と表記されています。 | 1 |
        | 7 | 有効期限 | expiryDate | yes | Date | 10 | - | 日付のみ取得可能です。時分秒は無効な値です。 | 2017-01-29 |
        | 8 | クーポン割引単価 | couponPrice | yes | Number | 10 | - |  | 100 |
        | 9 | クーポン利用数 | couponUnit | yes | Number | 10 | - |  | 1 |
        | 10 | クーポン利用金額 | couponTotalPrice | yes | Number | 10 | - | クーポン割引単価
        ×
        クーポン利用数
        
        ※クーポン割引単価もしくはクーポン利用数がnullの場合、-9999になります。 | 100 |
        | 11 | 商品明細ID | itemDetailId | yes | Number | 10 | - | 商品指定クーポンの場合：対象商品のitemDetailId
        商品指定クーポン以外の場合：0 | 10631675 |
    16. **Level 3: ChangeReasonModel**
        
        
        | **No** | **Logical Name** | **Parameter Name** | **Not Null** | **Type** | **Max Byte** | **Default** | **Description** | **Sample** |
        | --- | --- | --- | --- | --- | --- | --- | --- | --- |
        | 1 | 変更ID | changeId | yes | Number | 12 | - |  | 12345 |
        | 2 | 変更種別 | changeType | no | Number | 10 | - | 以下のいずれか
        
        0: キャンセル申請
        1: キャンセル確定
        2: キャンセル完了
        3: キャンセル取消
        4: 変更申請
        5: 変更確定
        6: 変更完了
        7: 変更取消
        8: 注文確認
        9: 再決済手続き | 1 |
        | 3 | 変更種別(詳細) | changeTypeDetail | no | Number | 10 | - | 以下のいずれか
        
        0: 減額
        1: 増額
        2: その他
        10: 支払方法変更
        11: 支払方法変更・減額
        12: 支払方法変更・増額
        
        ※「2: その他」は後払い決済選択注文で金額以外の変更が行われた場合のみ | 1 |
        | 4 | 変更理由 | changeReason | no | Number | 10 | - | 以下のいずれか
        
        0: 店舗様都合
        1: お客様都合 | 1 |
        | 5 | 変更理由(小分類) | changeReasonDetail | no | Number | 10 | - | 以下のいずれか
        
        1: キャンセル
        2: 受取後の返品
        3: 長期不在による受取拒否
        4: 未入金
        5: 代引決済の受取拒否
        6: お客様都合 - その他
        8: 欠品
        10: 店舗様都合 - その他
        13: 発送遅延
        14: 顧客・配送対応注意表示
        15: 返品(破損・品間違い)
        16: 受取情報入力期限切れ | 1 |
        | 6 | 変更申請日 | changeApplyDatetime | no | Datetime | 32 | - |  | 2017-09-25T20:03:43+0900 |
        | 7 | 変更確定日 | changeFixDatetime | no | Datetime | 32 | - |  | 2017-09-25T20:03:43+0900 |
        | 8 | 変更完了日 | changeCmplDatetime | no | Datetime | 32 | - |  | 2017-09-25T20:03:43+0900 |
    17. **Level 3: TaxSummaryModel**
        
        
        | **No** | **Logical Name** | **Parameter Name** | **Not Null** | **Type** | **Max Byte** | **Default** | **Description** | **Sample** |
        | --- | --- | --- | --- | --- | --- | --- | --- | --- |
        | 1 | 税率 | taxRate | yes | Number | - | - |  | 0.1 |
        | 2 | 請求金額 | reqPrice | yes | Number | 10 | -9999 | 税率ごとの請求金額（税込）
        以下の場合、-9999になります。
        ・送料未確定
        ・代引手数料未確定
         
        <楽天ポイントに係る消費税の課税処理および税込金額表示対応>に伴い、注文日が2022年4月1日（金）以降のデータから計算方法が変更されます。
         
        注文日が2022年3月31日（木）以前のデータ：商品金額 + 送料 + ラッピング料 + 決済手数料 + 注文者負担金 - クーポン割引額 - 利用ポイント数
        注文日が2022年4月1日（金）以降のデータ：商品金額 + 送料 + ラッピング料 + 決済手数料 + 注文者負担金 - クーポン割引額
        ※利用ポイント数を減算する前に計算
        <適格請求書等保存方式（インボイス制度）対応>に伴い、2023年9 月14日（木）以降に初回決済確定・発送完了となった注文より、後払い手数料（追加）分が含まれなくなります。 | 1000 |
        | 3 | 請求額に対する税額 | reqPriceTax | yes | Number | 10 | -9999 | 請求額に対する税額
        以下の場合、-9999になります。
        ・送料未確定
        ・代引手数料未確定
        
        <楽天ポイントに係る消費税の課税処理および税込金額表示対応>に伴い、注文日が2022年4月1日（金）以降のデータから計算方法が変更されます。
         
        注文日が2022年3月31日（木）以前のデータ：（商品金額 + 送料 + ラッピング料 + 決済手数料 + 注文者負担金 - クーポン割引額 - 利用ポイント数）に対する税額
        注文日が2022年4月1日（金）以降のデータ：（商品金額 + 送料 + ラッピング料 + 決済手数料 + 注文者負担金 - クーポン割引額）に対する税額
        ※利用ポイント数を減算する前の各税額
        <適格請求書等保存方式（インボイス制度）対応>に伴い、2023年9 月14日（木）以降に初回決済確定・発送完了となった注文より、後払い手数料（追加）分が含まれなくなります。 | 100 |
        | 4 | 合計金額 | totalPrice | yes | Number | 10 | -9999 | 商品金額 + 送料 + ラッピング料
        
        送料未確定の場合、-9999になります。
        
        ※クーポン値引額、利用ポイント数、決済手数料、注文者負担金を含みません。 | 1250 |
        | 5 | 決済手数料 | paymentCharge | yes | Number | 10 | -9999 | 代引手数料未確定の場合、-9999になります。 | 50 |
        | 6 | クーポン割引額 | couponPrice | yes | Number | 10 | -9999 |  | 100 |
        | 7 | 利用ポイント数 | point | yes | Number | 10 | -9999 | <楽天ポイントに係る消費税の課税処理および税込金額表示対応>に伴い、注文日が2022年4月1日（金）以降のデータから計算方法が変更されます。
         
        注文日が2022年3月31日（木）以前のデータは対象税率ごとの利用ポイント数
        注文日が2022年4月1日（金）以降のデータは常に0 | 150 |
    18. **Level 3: DueDateModel**
        
        
        | **No** | **Logical Name** | **Parameter Name** | **Not Null** | **Type** | **Max Byte** | **Default** | **Description** | **Sample** |
        | --- | --- | --- | --- | --- | --- | --- | --- | --- |
        | 1 | 期限日タイプ | dueDateType | yes | Number | 10 | - | 以下のいずれか
        
        0: 支払い期限日
        1: 支払い方法変更期限日
        2: 返金手続き期限日
        
        ※複数の期限日が発生する場合は上書きではなく、追記となります。 | 0 |
        | 2 | 期限日 | dueDate | yes | Date | 10 | - |  | 2020-08-01 |
    19. **Level 5: skuModel**
        
        
        | **No** | **Logical Name** | **Parameter Name** | **Not Null** | **Type** | **Max Byte** | **Default** | **Description** | **Sample** |
        | --- | --- | --- | --- | --- | --- | --- | --- | --- |
        | 1 | SKU管理番号 | variantId | yes | String | 40 | - | SKU移行前の注文の場合、値は空になります。
        
        ※Request Parameterの「version」に「7」以降の値を指定すると取得可能 | 17095519 |
        | 2 | システム連携用SKU番号 | merchantDefinedSkuId | no | String | 386 | - | SKU移行前の注文の場合、値は空になります。
        
        ※Request Parameterの「version」に「7」以降の値を指定すると取得可能 | itemNumber-m-white |
        | 3 | SKU情報 | skuInfo | no | String | 1600 | - | 以下のルールで値が入ります。
        SKU移行前注文：値は空になります。
        SKU移行後注文：バリエーション項目名・バリエーション選択肢（旧・項目選択肢別在庫情報）が入ります。
        項目選択肢情報は入りません。Level 4: ItemModel > selectedChoiceにて取得可能です。
        **商品種別内容**シングルSKU該当項目は無い為、データ無しマルチSKUバリエーション項目名とバリエーション選択肢。 下記のフォーマットで返却されます。バリエーション項目名:バリエーション選択肢
        ※Request Parameterの「version」に「7」以降の値を指定すると取得可能 | 容量:560ml
        本数:24本（1ケース）
        ラベル:あり |
5. **Sample**
    
    getOrder バージョン 7 Samples
    
    getOrder バージョン 8 Samples
    
    getOrder バージョン 9 Samples
    
    getOrder バージョン 10 Samples