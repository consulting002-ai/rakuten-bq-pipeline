# RMS WEB SERVICE : items.get

1. **Overview**
    
    この機能を利用すると、商品管理番号を指定し、商品情報を取得することができます。
    
2. **Endpoint / HTTP Method**
    
    
    | **Endpoint** | **HTTP Method** |
    | --- | --- |
    | https://api.rms.rakuten.co.jp/es/2.0/items/manage-numbers/{manageNumber} | GET |
3. **Request**
    1. **HTTP Header**
        
        
        | **No** | **Key** | **Value** |
        | --- | --- | --- |
        | 1 | Authorization | ESA Base64(serviceSecret:licenseKey) |
    2. **Path Parameter**
        
        
        | **No** | **Parameter Name** | **Logical Name** | **Required** | **Type** | **Multiplicity** | **Description** |
        | --- | --- | --- | --- | --- | --- | --- |
        | 1 | manageNumber | 商品管理番号 | yes | string | 1 | 1件のみ指定可能以下の英数字、記号が使用可能。・"a~z"・"A~Z"・"0~9"・"-", "_"大文字は小文字に自動変換。 |
    3. **HTTP Body**
        
        None
        
4. **Response**
    1. **HTTP Header**
        
        
        | **No** | **Key** | **Value** |
        | --- | --- | --- |
        | 1 | Content-Type | application/json |
    2. **HTTP Body**
        1. **成功した場合**
            
            
            | **No** | **Parameter Name** |  |  |  |  | **Logical Name** | **Not Null** | **Type** | **Max Byte** | **Multiplicity** | **Description** |
            | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
            |  | L1 | L2 | L3 | L4 | L5 |  |  |  |  |  |  |
            | 1 | manageNumber |  |  |  |  | 商品管理番号 | yes | string | 32 | 1 | 以下の英数字、記号。・"a~z"・"0~9"・"-", "_" |
            | 2 | itemNumber |  |  |  |  | 商品番号 | no | string | 32 | 0,1 |  |
            | 3 | title |  |  |  |  | 商品名 | yes | string | 255 | 1 |  |
            | 4 | tagline |  |  |  |  | キャッチコピー | no | string | 174 | 0,1 |  |
            | 5 | productDescription |  |  |  |  | 商品説明文 | no | object | - | 0,1 |  |
            | 6 |  | pc |  |  |  | PC用商品説明文 | no | string | 10240 | 0,1 |  |
            | 7 |  | sp |  |  |  | スマートフォン用商品説明文 | no | string | 10240 | 0,1 |  |
            | 8 | salesDescription |  |  |  |  | PC用販売説明文 | no | string | 10240 | 0,1 |  |
            | 9 | precautions |  |  |  |  | 医薬品説明文・注意事項 | no | object | - | 0,1 |  |
            | 10 |  | description |  |  |  | 医薬品説明文 | no | string | 20480 | 0,1 |  |
            | 11 |  | agreement |  |  |  | 医薬品注意事項 | no | string | 20480 | 0,1 |  |
            | 12 | itemType |  |  |  |  | 商品種別 | yes | enum | - | 1 | ・NORMAL：通常商品・PRE_ORDER：予約商品・BUYING_CLUB：頒布会商品 |
            | 13 | images |  |  |  |  | 商品画像 | no | List<images> | - | 0..20 | 商品画像のリスト |
            | 14 |  | type |  |  |  | 商品画像種別 | no | enum | 255 | 1 | ・CABINET：R-Cabinetの画像・GOLD：GOLDの画像 |
            | 15 |  | location |  |  |  | 商品画像URL | no | string | 255 | 1 | 画像URLの"/画像パス”部分。CABINET：https://image.rakuten.co.jp/[SHOP_URL]/cabinet/画像パスGOLD：https://www.rakuten.ne.jp/gold/[SHOP_URL]/画像パス |
            | 16 |  | alt |  |  |  | 商品画像名（ALT） | no | string | 255 | 0,1 | 商品レベルでの画像の代替テキスト。 |
            | 17 | whiteBgImage |  |  |  |  | 白背景画像 | no | object | - | 0,1 |  |
            | 18 |  | type |  |  |  | 白背景画像種別 | no | enum | - | 1 | ・CABINET：R-Cabinetの画像・GOLD：GOLDの画像 |
            | 19 |  | location |  |  |  | 白背景画像URL | no | string | - | 1 | 画像URLの"/画像パス”部分。CABINET：https://image.rakuten.co.jp/[SHOP_URL]/cabinet/画像パスGOLD：https://www.rakuten.ne.jp/gold/[SHOP_URL]/画像パス |
            | 20 | video |  |  |  |  | 動画 | no | object | - | 0,1 |  |
            | 21 |  | type |  |  |  | 動画種別 | no | enum | - | 1 | ・HTML：HTML形式 |
            | 22 |  | parameters |  |  |  | 動画パラメータ | no | object | - | 1 |  |
            | 23 |  |  | value |  |  | 動画のURL | no | string | 2048 | 1 | フォーマット：<script src="(https:)?//stream.cms.rakuten.co.jp/gate/play/[^\"]*" type="text/javascript"></script> |
            | 24 | genreId |  |  |  |  | ジャンルID | yes | string | 6 | 1 | 6桁の数字：100000 ～ 999999 |
            | 25 | tags |  |  |  |  | 非製品属性タグID | no | List<int> | - | 0..32 | 商品の詳細属性情報。7桁の数字：5000000～9999999 |
            | 26 | hideItem |  |  |  |  | 倉庫指定 | yes | boolean | - | 1 | ・true：倉庫に入れる・false：販売中 |
            | 27 | unlimitedInventoryFlag |  |  |  |  | 在庫設定なし | yes | boolean | - | 1 | ・true：在庫設定なし※・false：在庫設定あり※2016年9月20日以前に登録かつ、その後更新されていない商品のみ。 |
            | 28 | customizationOptions |  |  |  |  | 商品オプション（項目選択肢） | no | List <customizationOptions> | - | 0..20 |  |
            | 29 |  | displayName |  |  |  | 商品オプション（項目選択肢）項目名 | no | string | 255 | 1 |  |
            | 30 |  | inputType |  |  |  | 商品オプション選択肢タイプ | no | enum | - | 1 | ・SINGLE_SELECTION：セレクトボックス・MULTIPLE_SELECTION：チェックボックス・FREE_TEXT：フリーテキスト |
            | 31 |  | required |  |  |  | 商品オプション必須フラグ | no | boolean | - | 1 | ・true：必須・false：任意 |
            | 32 |  | selections |  |  |  | Select/Checkbox用選択肢リスト | no | List<selections> | - | 0..n | 範囲・inputType=SINGLE_SELECTION：1～100・inputType=MULTIPLE_SELECTION：1～40 |
            | 33 |  |  | displayValue |  |  | 商品オプション選択肢名 | no | string | 32 | 1 |  |
            | 34 | releaseDate |  |  |  |  | 予約商品発売日 | no | string | - | 0,1 | フォーマットはISO 8601、タイムゾーンは日本標準時（JST）、日まで。 |
            | 35 | purchasablePeriod |  |  |  |  | 販売期間指定 | no | object | - | 0,1 |  |
            | 36 |  | start |  |  |  | 販売開始日時 | no | string | - | 1 | フォーマットはISO 8601、タイムゾーンは日本標準時（JST）。 |
            | 37 |  | end |  |  |  | 販売終了日時 | no | string | - | 1 | フォーマットはISO 8601、タイムゾーンは日本標準時（JST）。 |
            | 38 | subscription |  |  |  |  | 定期購入商品設定 | no | object | - | 0,1 |  |
            | 39 |  | shippingDateFlag |  |  |  | お届け日付指定フラグ | no | boolean | - | 1 | ・true：指定可能・false：指定不可 |
            | 40 |  | shippingIntervalFlag |  |  |  | お届け間隔（曜日）指定フラグ | no | boolean | - | 1 | ・true：指定可能・false：指定不可 |
            | 41 | buyingClub |  |  |  |  | 頒布会商品設定 | no | object | - | 0,1 |  |
            | 42 |  | numberOfDeliveries |  |  |  | お届け回数 | no | number | - | 1 | 許容値：2～12 |
            | 43 |  | displayItems |  |  |  | 商品内訳情報の表示 | no | boolean | - | 1 | ・true：表示・false：非表示 |
            | 44 |  | items |  |  |  | 商品内訳情報 | no | List<string> | 127 | 0..12 |  |
            | 45 |  | shippingDateFlag |  |  |  | お届け日付指定フラグ | no | boolean | - | 1 | ・true：指定可能・false：指定不可 |
            | 46 |  | shippingIntervalFlag |  |  |  | お届け間隔（曜日）指定フラグ | no | boolean | - | 1 | ・true：指定可能・false：指定不可 |
            | 47 | features |  |  |  |  | その他設定 | yes | object | - | 1 |  |
            | 48 |  | searchVisibility |  |  |  | サーチ表示 | yes | enum | - | 1 | ・ALWAYS_VISIBLE：表示・ALWAYS_HIDDEN：非表示 |
            | 49 |  | displayNormalCartButton |  |  |  | 注文ボタン | yes | boolean | - | 1 | ・true：表示・false：非表示 |
            | 50 |  | displaySubscriptionCartButton |  |  |  | 定期購入・頒布会ボタン | yes | boolean | - | 1 | ・true：表示・false：非表示 |
            | 51 |  | inventoryDisplay |  |  |  | 在庫数表示 | yes | enum | - | 1 | ・DISPLAY_ABSOLUTE_STOCK_COUNT：表示・HIDDEN_STOCK：非表示・DISPLAY_LOW_STOCK：残り在庫数表示閾値より小さい場合、△を表示する |
            | 52 |  | lowStockThreshold |  |  |  | 残り在庫数表示閾値 | no | number | - | 0,1 | 許容値：1～20 |
            | 53 |  | shopContact |  |  |  | 商品問い合わせボタン | yes | boolean | - | 1 | ・true：表示・false：非表示 |
            | 54 |  | review |  |  |  | レビュー本文表示 | yes | enum | - | 1 | ・SHOP_SETTING：店舗設定に従う・VISIBLE：表示・HIDDEN：非表示 |
            | 55 |  | displayManufacturerContents |  |  |  | メーカー提供情報表示 | yes | boolean | - | 1 | ・true：表示・false：非表示 |
            | 56 |  | socialGiftFlag |  |  |  | ソーシャルギフトフラグ | yes | boolean | - | 1 | ・true：対応する・false：対応しない |
            | 57 | accessControl |  |  |  |  | アクセスコントロール | no | object | - | 1 |  |
            | 58 |  | accessPassword |  |  |  | 闇市パスワード | no | string | 32 | 1 | 小文字で以下の英数字、記号。・"a~z"・"0-9"・"-", "_" |
            | 59 | payment |  |  |  |  | 決済情報 | yes | object | - | 1 |  |
            | 60 |  | taxIncluded |  |  |  | 消費税込み | yes | boolean | - | 1 | ・true：税込・false：税別 |
            | 61 |  | taxRate |  |  |  | 消費税税率 | no | string | - | 0,1 | 以下のいずれか・0：非課税・0.08：8%・0.1：10%・null：店舗設定に従う |
            | 62 |  | cashOnDeliveryFeeIncluded |  |  |  | 代引料 | yes | boolean | - | 1 | ・true：代引料込・false：代引料別 |
            | 63 | pointCampaign |  |  |  |  | ポイント変倍情報 | no | object | - | 0,1 |  |
            | 64 |  | applicablePeriod |  |  |  | ポイント変倍適用期間 | no | object | - | 1 |  |
            | 65 |  |  | start |  |  | 開始日時 | no | string | - | 1 | フォーマットはISO 8601、タイムゾーンは日本標準時（JST）。 |
            | 66 |  |  | end |  |  | 終了日時 | no | string | - | 1 | フォーマットはISO 8601、タイムゾーンは日本標準時（JST）。"9999-12-31T23:59:59+09:00"が設定されている場合は終了日時が設定されていないポイント変倍情報であることを示す。 |
            | 67 |  | benefits |  |  |  | ポイント情報 | no | object | - | 1 |  |
            | 68 |  |  | pointRate |  |  | ポイント変倍率 | no | number | - | 1 | 許容値：1～20 |
            | 69 |  | optimization |  |  |  | 運用型ポイント情報 | no | object | - | 0,1 | 運用型ポイント変倍サービスを申し込んだ店舗のみ返される。 |
            | 70 |  |  | maxPointRate |  |  | ポイント上限倍率 | no | number | - | 1 | 許容値：5～20 |
            | 71 | itemDisplaySequence |  |  |  |  | 店舗内カテゴリでの表示順位 | yes | number | - | 1 | 許容値：1～999999999 |
            | 72 | layout |  |  |  |  | レイアウト設定 | yes | object | - | 1 |  |
            | 73 |  | itemLayoutId |  |  |  | 商品ページレイアウト | yes | number | - | 1 | ・1：テンプレートA・2：テンプレートB・3：テンプレートC・4：テンプレートD・5：テンプレートE・6：テンプレートF・8：テンプレートG |
            | 74 |  | navigationId |  |  |  | ヘッダー・フッター・レフトナビのテンプレートID | yes | number | - | 1 |  |
            | 75 |  | layoutSequenceId |  |  |  | 表示項目の並び順テンプレートID | yes | number | - | 1 |  |
            | 76 |  | smallDescriptionId |  |  |  | 共通説明文(小)テンプレートID | yes | number | - | 1 |  |
            | 77 |  | largeDescriptionId |  |  |  | 共通説明文(大)テンプレートID | yes | number | - | 1 |  |
            | 78 |  | showcaseId |  |  |  | 目玉商品テンプレートID | yes | number | - | 1 |  |
            | 79 | variantSelectors |  |  |  |  | バリエーション項目 | no | List<variantSelectors> | - | 0..6 | 商品ページ上の表示はリクエストの順番と同一。 |
            | 80 |  | key |  |  |  | バリエーション項目キー | no | string | - | 1 | バリエーション項目名の識別子。 |
            | 81 |  | displayName |  |  |  | バリエーション項目名 | no | string | 32 | 1 |  |
            | 82 |  | values |  |  |  | バリエーション選択肢リスト | no | List<selectorValues> | - | 1..40 |  |
            | 83 |  |  | displayValue |  |  | バリエーション選択肢 | no | string | 32 | 1 | 商品ページ上の表示はリクエストの順番と同一。 |
            | 84 | variants |  |  |  |  | SKU | yes | object | - | 1..400 |  |
            | 85 |  | {variantId} |  |  |  | SKU管理番号 | no | string | 32 | 1 | 以下の英数字、記号。・"a~z"・"A~Z"・"0~9"・"-", "_" |
            | 86 |  |  | merchantDefinedSkuId |  |  | システム連携用SKU番号 | no | string | 96 | 0,1 | 英数字または日本語の文字列。 |
            | 87 |  |  | selectorValues |  |  | SKU情報 | no | object | - | 0..6 |  |
            | 88 |  |  |  | {key} |  | バリエーション項目キー・選択肢 | no | string | - | 1 | variantSelectors.key:variantSelectors.values.displayValue の形式。 |
            | 89 |  |  | images |  |  | SKU画像 | no | List<images> | - | 0..1 |  |
            | 90 |  |  |  | type |  | SKU画像タイプ | no | enum | - | 1 | ・CABINET：R-Cabinetの画像・GOLD：GOLDの画像 |
            | 91 |  |  |  | location |  | SKU画像パス | no | string | 255 | 1 | 画像URLの"/画像パス”部分。CABINET：https://image.rakuten.co.jp/[SHOP_URL]/cabinet/画像パスGOLD：https://www.rakuten.ne.jp/gold/[SHOP_URL]/画像パス |
            | 92 |  |  |  | alt |  | SKU画像名（ALT） | no | string | 255 | 0,1 |  |
            | 93 |  |  | restockOnCancel |  |  | 在庫戻しフラグ | no | boolean | - | 1 | ・true：在庫戻しする・false：在庫戻ししない |
            | 94 |  |  | backOrderFlag |  |  | 在庫切れ時の注文受付 | no | boolean | - | 1 | ・true：注文を受け付ける・false：注文を受け付けない |
            | 95 |  |  | normalDeliveryDateId |  |  | 在庫あり時納期管理番号 | no | number | - | 0,1 |  |
            | 96 |  |  | backOrderDeliveryDateId |  |  | 在庫切れ時納期管理番号 | no | number | - | 0,1 |  |
            | 97 |  |  | orderQuantityLimit |  |  | 注文受付数 | no | number | - | 0,1 | 許容値：0～400・0：非表示（最大個数1個）・n （1～400）：最大購入数を設定・null： 自由入力 |
            | 98 |  |  | referencePrice |  |  | 表示価格情報 | no | object | - | 0,1 |  |
            | 99 |  |  |  | displayType |  | 表示価格種別 | no | enum | - | 1 | ・REFERENCE_PRICE：選択した表示価格文言・SHOP_SETTING：店舗設定に従う・OPEN_PRICE：メーカー希望小売価格 オープン価格 |
            | 100 |  |  |  | type |  | 表示価格文言 | no | number | - | 0,1 | ・1：当店通常価格・2：メーカー希望小売価格・4：商品価格ナビのデータ参照 |
            | 101 |  |  |  | value |  | 表示価格 | no | string | - | 0,1 | 許容値：1～999999999 |
            | 102 |  |  | features |  |  | その他設定 | no | object | - | 0,1 |  |
            | 103 |  |  |  | restockNotification |  | 再入荷お知らせボタン | no | boolean | - | 1 | ・true：表示・false：非表示 |
            | 104 |  |  |  | noshi |  | のし対応 | no | boolean | - | 1 | ・true：対応する・false：対応しない |
            | 105 |  |  | hidden |  |  | SKU倉庫設定 | no | boolean | - | 1 | ・true：倉庫・false：販売中 |
            | 106 |  |  | standardPrice |  |  | 販売価格 | no | string | - | 0,1 | 許容値：0～999999999 |
            | 107 |  |  | subscriptionPrice |  |  | 定期購入販売価格設定・頒布会販売価格設定 | no | object | - | 0,1 |  |
            | 108 |  |  |  | basePrice |  | 定期購入販売価格・頒布会販売価格 | no | string | - | 0,1 | 許容値：1～999999999 |
            | 109 |  |  |  | individualPrices |  | 個別価格 | no | object | - | 0,1 |  |
            | 110 |  |  |  |  | firstPrice | 初回価格 | no | string | - | 0,1 | 許容値：1～999999999 |
            | 111 |  |  | articleNumberForSet |  |  | セット商品用カタログID | no | List<string> | 30 | 0..20 | 通常商品かつカタログIDなしの理由に「セット商品」を指定した商品のみが対象。セットの構成であるSKUのカタログID。 |
            | 112 |  |  | articleNumber |  |  | カタログID情報 | no | object | - | 0,1 |  |
            | 113 |  |  |  | value |  | カタログID | no | string | 30 | 0,1 | 商品の標準製品コード。 |
            | 114 |  |  |  | exemptionReason |  | カタログIDなしの理由 | no | number | - | 0,1 | ・1：セット商品・2：サービス商品・3：店舗オリジナル商品・4：項目選択肢在庫商品・5：該当製品コードなし・6：頒布会商品 |
            | 115 |  |  | shipping |  |  | 送料情報 | yes | object | - | 0,1 |  |
            | 116 |  |  |  | fee |  | 個別送料 | no | string | - | 0,1 | 許容値：0～999999999 |
            | 117 |  |  |  | postageIncluded |  | 送料無料フラグ | no | boolean | - | 1 | ・true：送料無料・false：送料別 |
            | 118 |  |  |  | shopAreaSoryoPatternId |  | 地域別個別送料管理番号 | no | number | - | 0,1 | 許容値：1～20 |
            | 119 |  |  |  | shippingMethodGroup |  | 配送方法セット管理番号 | no | string | 40 | 0,1 | 配送方法セット管理番号に自動選択対象以外の設定がある場合のみ、この項目を返却します。※配送方法セット管理番号は、以下より確認してください。ShopAPI の [shop.deliverySetInfo.get](https://webservice.rms.rakuten.co.jp/merchant-portal/view/ja/common/1-1_service_index/shopapi/deliverysetinfo/) の下記項目から取得可能。　4.2.6. Level 4: deliverySetInfo - deliverySetId |
            | 120 |  |  |  | postageSegment |  | 送料区分情報 | no | object | - | 0,1 |  |
            | 121 |  |  |  |  | local | 送料区分1（ローカル） | no | number | - | 0,1 | ローカルの送料区分番号。 |
            | 122 |  |  |  |  | overseas | 送料区分2（海外） | no | number | - | 0,1 | 海外の送料区分番号。 |
            | 123 |  |  |  | overseasDeliveryId |  | 海外配送管理番号 | no | number | - | 0,1 | 許容値：1～5 |
            | 124 |  |  |  | singleItemShipping |  | 単品配送設定 | no | number | - | 1 | ・0：設定なし・1：産地直送の商品・2：メーカー直送の商品・3： ケース売りの商品・4：長尺・異形の商品・5：出荷地が異なる商品・6：温度帯が異なる商品 |
            | 125 |  |  |  | okihaiSetting |  | 置き配設定 | yes | boolean | - | 1 | ・true : 受け付ける・false : 受け付けない |
            | 126 |  |  | specs |  |  | 属性情報自由入力行 | no | List<object> | - | 0..5 | 商品ページ上の「商品仕様」に追記できる任意項目。 |
            | 127 |  |  |  | label |  | 属性情報自由入力行（項目） | no | string | 40 | 1 |  |
            | 128 |  |  |  | value |  | 属性情報自由入力行（値） | no | string | 140 | 1 |  |
            | 129 |  |  | attributes |  |  | 属性情報 | no | List<object> | - | 0..n | 商品ページ上に「商品仕様」として表示される項目。 |
            | 130 |  |  |  | name |  | 属性情報名 | no | string | - | 1 |  |
            | 131 |  |  |  | values |  | 属性情報（実値） | no | List<string> | - | 1..n | フォーマットはNavigationAPI 2.0 の [genres.attributes.get](https://webservice.rms.rakuten.co.jp/merchant-portal/view/ja/common/1-1_service_index/navigationapi2/genresattributesget/) あるいは [genres.attributes.dictionaryValues.get](https://webservice.rms.rakuten.co.jp/merchant-portal/view/ja/common/1-1_service_index/navigationapi2/genresattributesdictionaryvaluesget/) の下記項目の値に準ずる。　4.2.6. Level 3: attributes - dataType |
            | 132 |  |  |  | unit |  | 単位 | no | string | - | 0,1 | 属性情報の単位。 |
            | 133 | created |  |  |  |  | 登録日時 | yes | string | - | 1 | 商品の登録日時。フォーマットはISO 8601、タイムゾーンは日本標準時（JST）、秒まで。 |
            | 134 | updated |  |  |  |  | 更新日時 | yes | string | - | 1 | 商品の更新日時。フォーマットはISO 8601、タイムゾーンは日本標準時（JST）、秒まで。 |
        2. **失敗した場合**
            
            
            | **No** | **Parameter Name** |  | **Logical Name** | **Not Null** | **Type** | **Max Byte** | **Multiplicity** | **Description** |
            | --- | --- | --- | --- | --- | --- | --- | --- | --- |
            |  | **L1** | **L2** |  |  |  |  |  |  |
            | 1 | errors |  | エラー | yes | List<error> | - | 1..n | エラーのリスト |
            | 2 |  | code | コード | yes | string | - | 1 | メッセージコードの一覧は[こちら](https://webservice.rms.rakuten.co.jp/merchant-portal/view/ja/common/1-1_service_index/itemapi2_0/responsecodesreference/) |
            | 3 |  | message | メッセージ | yes | string | - | 1 |  |
5. **Sample**
    1. **成功した場合**
        1. **全フィールドの例**
            - Request (curl コマンドを使った例)
                
                ```bash
                curl --location --request GET 'https://api.rms.rakuten.co.jp/es/2.0/items/manage-numbers/6650' \
                --header 'Authorization: ESA xxx'
                ```
                
            - Response in JSON format (Status: 200 OK)
                
                ```bash
                {
                    "manageNumber": "6650",
                    "itemNumber": "2100011223431",
                    "title": "日本語",
                    "tagline": "キャッチコピー",
                    "productDescription": {
                        "pc": "PC用商品説明文",
                        "sp": "スマートフォン用商品説明文"
                    },
                    "salesDescription": "PC販売説明文",
                    "precautions": {
                        "description": "医薬品説明文",
                        "agreement": "医薬品注意事項"
                    },
                    "itemType": "NORMAL",
                    "images": [
                        {
                            "type": "CABINET",
                            "location": "/myfolder-1/tv01.jpg",
                            "alt": "l2_17-Inventory-Test"
                        }
                    ],
                    "whiteBgImage": {
                        "type": "CABINET",
                        "location": "/harryporter.jpg"
                    },
                    "video": {
                            "type": "HTML",
                            "parameters": {
                                "value": "<script src=\"//stream.cms.rakuten.co.jp/gate/play/?w=320&h=286&mid=1101692986&vid=5792214557001\" type=\"text/javascript\"></script>"
                            }
                     },
                    "tags": [
                        5000001,
                        5000002
                    ],
                    "hideItem": false,
                    "unlimitedInventoryFlag": false,
                    "customizationOptions": [
                        {
                            "displayName": "ギフト目的",
                            "inputType": "SINGLE_SELECTION",
                            "required": false,
                            "selections": {
                                "displayValue": "のし必要の方は必ずお選び下さい。"
                            }
                        }
                    ],
                    "releaseDate": "2021-07-14",
                    "purchasablePeriod": {
                        "start": "2021-07-11T15:00:00+09:00",
                        "end": "2021-07-31T14:59:59+09:00"
                    },
                    "subscription": {
                        "shippingDateFlag": true,
                        "shippingIntervalFlag": false
                    },
                    "buyingClub": {
                        "numberOfDeliveries": 2,
                        "displayItems": true,
                        "items": ["1回目 商品", "2回目 商品"],
                        "shippingDateFlag": true,
                        "shippingIntervalFlag": false
                    },
                    "features": {
                        "searchVisibility": "ALWAYS_VISIBLE",
                        "displayNormalCartButton": false,
                        "displaySubscriptionCartButton": false,
                        "inventoryDisplay": "DISPLAY_ABSOLUTE_STOCK_COUNT",
                        "lowStockThreshold": 5,
                        "shopContact": false,
                        "review": "SHOP_SETTING",
                        "displayManufacturerContents": false,
                        "socialGiftFlag": false
                    },
                    "payment": {
                        "taxIncluded": false,
                        "taxRate": 0.08,
                        "cashOnDeliveryFeeIncluded": false
                    },
                    "pointCampaign": {
                        "applicablePeriod": {
                            "start": "2021-10-13T04:07:08+09:00",
                            "end": "2021-11-13T04:07:08+09:00"
                        },
                        "benefits": {
                            "pointRate": 6
                        },
                        "optimization": {
                            "maxPointRate": 6
                        }
                    },
                    "itemDisplaySequence": 999999999,
                    "layout": {
                        "itemLayoutId": 1,
                        "navigationId": 0,
                        "layoutSequenceId": 0,
                        "smallDescriptionId": 0,
                        "largeDescriptionId": 0,
                        "showcaseId": 0
                    },
                    "variantSelectors": [
                        {
                            "key": "size-key",
                            "displayName": "サイズ",
                            "values": [
                                {
                                    "displayValue": "L サイズ"
                                }
                            ]
                        }
                    ],
                    "variants": {
                        "pinot-noir": {
                            "merchantDefinedSkuId": "112233",
                            "selectorValues": {
                                "size-key": "L サイズ"
                            },
                            "images": [
                                {
                                    "type": "CABINET",
                                    "location": "/myfolder-1/tv01.jpg",
                                    "alt": "l2_17-Inventory-Test"
                                }
                            ],
                            "restockOnCancel": false,
                            "backOrderFlag": false,
                            "normalDeliveryDateId": 1,
                            "backOrderDeliveryDateId": 2,
                            "orderQuantityLimit": 100,
                            "referencePrice": {
                                "displayType": "REFERENCE_PRICE ",
                                "type": 1,
                                "value": 1000
                            },
                            "features": {
                                "restockNotification": true,
                                "noshi": true
                            },
                            "hidden": false,
                            "standardPrice": 1000,
                            "articleNumberForSet": [
                                "45000000000",
                                "45000000001"
                            ],
                            "articleNumber": {
                                "value": "0689640032932",
                                "exemptionReason": "1"
                            }
                        "shipping": {
                                "fee": 1000,
                                "postageIncluded": false,
                                "shopAreaSoryoPatternId": 1,
                                "shippingMethodGroup": 2,
                                "postageSegment": {
                                    "local": 1,
                                    "overseas": 1
                                },
                                "overseasDeliveryId": 1,
                                "singleItemShipping": 1,
                                 "okihaiSetting": true
                            },
                            "specs": {
                                "label": "スペック情報ラベル",
                                "value": "スペック情報内容"
                            },
                            "attributes": {
                                "name": "attributeName1",
                                "values": [
                                    "赤色",
                                    "100"
                                ]
                            }
                        }
                    },
                    "created": "2021-10-07T05:05:35+09:00",
                    "updated": "2021-10-07T05:05:35+09:00",
                    "genreId": "555555"
                }
                ```
                
        2. **SKU在庫商品の場合**
            - Request (curl コマンドを使った例)
                
                ```bash
                curl --location --request GET 'https://api.rms.rakuten.co.jp/es/2.0/items/manage-numbers/6650' \
                --header 'Authorization: ESA xxx'
                ```
                
            - Response in JSON format (Status: 200 OK)
                
                ```bash
                {
                    "itemType": "NORMAL",
                    "itemNumber": "11829",
                    "title": "い・ろ・は・す ラベルレス(560ml*24本/48本入)【いろはす(I LOHAS)】",
                    "tagline": "いろはす(I LOHAS) / い・ろ・は・す PET",
                    "productDescription": {
                        "pc": "explanation for PC",
                        "sp": "explanation for SP"
                    },
                    "salesDescription": "salesexplanation for PC",
                    "images": [
                        {
                            "type": "CABINET",
                            "location": "/01003752/ilohas.jpg",
                            "alt": "ilohas"
                        }
                    ],
                    "whiteBgImage": {
                        "type": "GOLD",
                        "location": "/ilohas-white-bg.jpg"
                    },
                    "video": {
                        "type": "HTML",
                        "parameters": {
                            "value": "<script src=\"//stream.cms.rakuten.co.jp/gate/play/?w=320&h=286&mid=1101692986&vid=5792214557001\" type=\"text/javascript\"></script>"
                        }
                    },
                    "genreId": "206878",
                    "tags": [
                        7654321,
                        9000000
                    ],
                    "hideItem": false,
                    "unlimitedInventoryFlag": false,
                    "customizationOptions": [
                        {
                            "displayName": "ギフト包装",
                            "inputType": "SINGLE_SELECTION",
                            "required": true,
                            "selections": [
                                {
                                    "displayValue": "はい"
                                }
                            ]
                        }
                    ],
                    "purchasablePeriod": {
                        "start": "2021-07-11T15:00:00+09:00",
                        "end": "2021-07-31T14:59:59+09:00"
                    },
                    "features": {
                        "searchVisibility": "ALWAYS_VISIBLE",
                        "shopContact": true,
                        "review": "SHOP_SETTING",
                        "displayManufacturerContents": false,
                        "displayNormalCartButton": true,
                        "displaySubscriptionCartButton": false,
                        "inventoryDisplay": "DISPLAY_LOW_STOCK",
                        "lowStockThreshold": 1,
                        "socialGiftFlag": false
                    },
                    "payment": {
                        "taxIncluded": false,
                        "taxRate": "0.1",
                        "cashOnDeliveryFeeIncluded": true
                    },
                    "pointCampaign": {
                        "applicablePeriod": {
                            "start": "2018-04-28T07:59:49+09:00",
                            "end": "2018-05-28T07:59:49+09:00"
                        },
                        "benefits": {
                            "pointRate": 15
                        },
                        "optimization": {
                            "maxPointRate": 15
                        }
                    },
                    "itemDisplaySequence": 999999999,
                    "layout": {
                        "itemLayoutId": 1,
                        "navigationId": 10,
                        "layoutSequenceId": 20,
                        "smallDescriptionId": 30,
                        "largeDescriptionId": 40,
                        "showcaseId": 50
                    },
                    "variantSelectors": [
                        {
                            "key": "num-key",
                            "displayName": "本数",
                            "values": [
                                {
                                    "displayValue": "24本"
                                },
                                {
                                    "displayValue": "48本"
                                }
                            ]
                        }
                    ],
                    "variants": {
                        "sku-1": {
                            "merchantDefinedSkuId": "システム連携SKU商品番号",
                            "selectorValues": {
                                "num-key": "24本"
                            },
                            "images": [
                                {
                                    "type": "CABINET",
                                    "location": "/01003752/ilohas_1.jpg",
                                    "alt": "sku-image"
                                }
                            ],
                            "restockOnCancel": true,
                            "backOrderFlag": false,
                            "normalDeliveryDateId": 1,
                            "backOrderDeliveryDateId": 2,
                            "articleNumber": {
                                "value": "4902102091862"
                            },
                            "hidden": true,
                            "orderQuantityLimit": 3,
                            "features": {
                                "restockNotification": true,
                                "noshi": true
                            },
                            "standardPrice": "2894",
                            "referencePrice": {
                                "displayType": "REFERENCE_PRICE",
                                "type": 1,
                                "value": "2894"
                            },
                            "shipping": {
                                "postageIncluded": true,
                                "shippingMethodGroup": "10",
                                "singleItemShipping": 5,
                                 "okihaiSetting": true
                            },
                            "specs": [
                                {
                                    "label": "Country of origin",
                                    "value": "Japan"
                                }
                            ],
                            "attributes": [
                                {
                                    "name": "単位内容量",
                                    "values": [
                                        "560"
                                    ],
                                    "unit": "ml"
                                }
                            ]
                        },
                        "sku-2": {
                            "selectorValues": {
                                "num-key": "48本"
                            },
                           "articleNumber": {
                                "value": "4902780029294"
                           },
                           "standardPrice": "6,220",
                            "restockOnCancel": false,
                            "backOrderFlag": false,
                             "shipping": {
                                 "okihaiSetting": true
                             },
                            "attributes": [
                                {
                                    "name": "単位内容量",
                                    "values": [
                                        "560"
                                    ],
                                    "unit": "ml"
                                }
                            ]
                        }
                    },
                    "created": "2021-07-08T01:05:31+09:00",
                    "updated": "2021-07-29T00:24:22+09:00"
                }
                ```
                
        3. **通常在庫商品の場合**
            - Request (curl コマンドを使った例)
                
                ```bash
                curl --location --request GET 'https://api.rms.rakuten.co.jp/es/2.0/items/manage-numbers/torimesi' \
                --header 'Authorization: ESA xxx'
                ```
                
            - Response in JSON format (Status: 200 OK)
                
                ```bash
                {
                    "manageNumber": "torimesi",
                    "itemType": "NORMAL",
                    "itemNumber": "torimesi",
                    "title": "水郷どり炊き込みご飯 2合用 鶏めし 鶏飯 お取り寄せグルメ テレビ とりめし 炊き込みご飯の素 釜めし 釜飯 釜飯の素 鶏肉",
                    "tagline": "料亭の味をご家庭で・・・上品で繊細、それでいて鶏肉の旨みが凝縮されている逸品です。［鶏肉 炊き込みご飯の素 お取り寄せグルメ テレビ ］",
                    "productDescription": {
                        "pc": "explanation for PC",
                        "sp": "explanation for SP"
                    },
                    "salesDescription": "salesexplanation for PC",
                    "images": [
                        {
                            "type": "CABINET",
                            "location": "/01003752/torimesi.jpg",
                            "alt": "itemname"
                        }
                    ],
                    "whiteBgImage": {
                        "type": "GOLD",
                        "location": "/torimesi.jpg"
                    },
                    "video": {
                        "type": "HTML",
                        "parameters": {
                            "value": "<script src=\"//stream.cms.rakuten.co.jp/gate/play/?w=320&h=286&mid=1101692986&vid=5792214557001\" type=\"text/javascript\"></script>"
                        }
                    },
                    "genreId": "201198",
                    "tags": [
                        7654321,
                        9000000
                    ],
                    "hideItem": false,
                    "unlimitedInventoryFlag": false,
                    "customizationOptions": [
                        {
                            "displayName": "ギフト包装",
                            "inputType": "SINGLE_SELECTION",
                            "required": true,
                            "selections": [
                                {
                                    "displayValue": "はい"
                                }
                            ]
                        }
                    ],
                    "features": {
                        "searchVisibility": "ALWAYS_VISIBLE",
                        "shopContact": true,
                        "review": "SHOP_SETTING",
                        "displayManufacturerContents": false,
                        "displayNormalCartButton": true,
                        "displaySubscriptionCartButton": false,
                        "inventoryDisplay": "DISPLAY_LOW_STOCK",
                        "lowStockThreshold": 1,
                        "socialGiftFlag": false
                    },
                    "payment": {
                        "taxIncluded": false,
                        "taxRate": "0.1",
                        "cashOnDeliveryFeeIncluded": true
                    },
                    "pointCampaign": {
                        "applicablePeriod": {
                            "start": "2018-04-28T07:59:49+09:00",
                            "end": "2018-05-28T07:59:49+09:00"
                        },
                        "benefits": {
                            "pointRate": 15
                        },
                        "optimization": {
                            "maxPointRate": 20
                        }
                    },
                    "itemDisplaySequence": 999999999,
                    "layout": {
                        "itemLayoutId": 1,
                        "navigationId": 10,
                        "layoutSequenceId": 20,
                        "smallDescriptionId": 30,
                        "largeDescriptionId": 40,
                        "showcaseId": 50
                    },
                    "variants": {
                        "normal-inventory": {
                            "restockOnCancel": false,
                            "normalDeliveryDateId": 1,
                            "backOrderFlag": false,
                            "standardPrice": 1000,
                            "articleNumber": {
                              "value": "0689640032932",
                            },
                            "shipping": {
                                "okihaiSetting": true
                             },
                            "attributes": [
                              {
                                "name": "ブランド名",
                                "values": [
                                  "お米"
                                ]
                              },
                              {
                                "name": "シリーズ名",
                                "values": [
                                  "鶏めし"
                                ]
                              },
                              {
                                "name": "原産国／製造国",
                                "values": [
                                  "日本"
                                ]
                              },
                              {
                                "name": "総個数",
                                "values": [
                                  "1"
                                ]
                              },
                              {
                                "name": "総重量",
                                "values": [
                                   "10"
                                 ],
                                 "unit": "kg"
                              }
                           ]
                        }
                    },
                    "created": "2021-07-08T01:05:31+09:00",
                    "updated": "2021-07-29T00:24:22+09:00"
                }
                ```
                
        4. **通常商品（定期購入設定なし）の場合**
            - Request (curl コマンドを使った例)
                
                ```bash
                curl --location --request GET 'https://api.rms.rakuten.co.jp/es/2.0/items/manage-numbers/torimesi' \
                --header 'Authorization: ESA xxx'
                ```
                
            - Response in JSON format (Status: 200 OK)
                
                ```bash
                {
                    "manageNumber": "normal-item",
                    "itemType": "NORMAL",
                    "itemNumber": "torimesi",
                    "title": "水郷どり炊き込みご飯 2合用 鶏めし 鶏飯 お取り寄せグルメ テレビ とりめし 炊き込みご飯の素 釜めし 釜飯 釜飯の素 鶏肉",
                    "tagline": "料亭の味をご家庭で・・・上品で繊細、それでいて鶏肉の旨みが凝縮されている逸品です。［鶏肉 炊き込みご飯の素 お取り寄せグルメ テレビ ］",
                    "productDescription": {
                        "pc": "explanation for PC",
                        "sp": "explanation for SP"
                    },
                    "salesDescription": "salesexplanation for PC",
                    "images": [
                        {
                            "type": "CABINET",
                            "location": "/01003752/torimesi.jpg",
                            "alt": "itemname"
                        }
                    ],
                    "whiteBgImage": {
                        "type": "GOLD",
                        "location": "/torimesi.jpg"
                    },
                    "video": {
                        "type": "HTML",
                        "parameters": {
                            "value": "<script src=\"//stream.cms.rakuten.co.jp/gate/play/?w=320&h=286&mid=1101692986&vid=5792214557001\" type=\"text/javascript\"></script>"
                        }
                    },
                    "genreId": "201198",
                    "tags": [
                        7654321,
                        9000000
                    ],
                    "hideItem": false,
                    "unlimitedInventoryFlag": false,
                    "customizationOptions": [
                        {
                            "displayName": "ギフト包装",
                            "inputType": "SINGLE_SELECTION",
                            "required": true,
                            "selections": [
                                {
                                    "displayValue": "はい"
                                }
                            ]
                        }
                    ],
                    "purchasablePeriod": {
                        "start": "2021-07-11T15:00:00+09:00",
                        "end": "2021-07-31T14:59:59+09:00"
                    },
                    "features": {
                        "searchVisibility": "ALWAYS_VISIBLE",
                        "shopContact": true,
                        "review": "SHOP_SETTING",
                        "displayManufacturerContents": false,
                        "displayNormalCartButton": true,
                        "displaySubscriptionCartButton": false,
                        "inventoryDisplay": "HIDDEN_STOCK",
                        "socialGiftFlag": false
                    },
                    "payment": {
                        "taxIncluded": false,
                        "taxRate": "0.1",
                        "cashOnDeliveryFeeIncluded": true
                    },
                    "pointCampaign": {
                        "applicablePeriod": {
                            "start": "2018-04-28T07:59:49+09:00",
                            "end": "2018-05-28T07:59:49+09:00"
                        },
                        "benefits": {
                            "pointRate": 15
                        },
                        "optimization": {
                            "maxPointRate": 15
                        }
                    },
                    "itemDisplaySequence": 999999999,
                    "layout": {
                        "itemLayoutId": 1,
                        "navigationId": 10,
                        "layoutSequenceId": 20,
                        "smallDescriptionId": 30,
                        "largeDescriptionId": 40,
                        "showcaseId": 50
                    },
                    "variantSelectors": [
                        {
                           "key":"size-key",
                            "displayName": "サイズ",
                            "values": [
                                {
                                    "displayValue": "Sサイズ"
                                },
                                {
                                    "displayValue": "Mサイズ"
                                }
                            ]
                        },
                        {
                           "key":"color-key",
                            "displayName": "カラー",
                            "values": [
                                {
                                    "displayValue": "青色"
                                }
                            ]
                        }
                    ],
                    "variants": {
                        "sku-1": {
                            "merchantDefinedSkuId": "システム連携SKU商品番号",
                            "selectorValues": {
                                "color-key": "青色",
                                "size-key": "Sサイズ"
                            },
                            "images": [
                                {
                                    "type": "CABINET",
                                    "location": "/01003752/dog_15.jpg",
                                    "alt": "sku-image"
                                }
                            ],
                            "restockOnCancel": true,
                            "backOrderFlag": false,
                            "normalDeliveryDateId": 1,
                            "backOrderDeliveryDateId": 2,
                            "articleNumber": {
                                "value": "4902780029294"
                            },
                            "hidden": true,
                            "orderQuantityLimit": 3,
                            "features": {
                                "restockNotification": true,
                                "noshi": true
                            },
                            "standardPrice": "810",
                            "referencePrice": {
                                "displayType": "REFERENCE_PRICE",
                                "type": 1,
                                "value": "15000"
                            },
                            "shipping": {
                                "fee": "1000",
                                "postageIncluded": false,
                                "shopAreaSoryoPatternId": 2,
                                "shippingMethodGroup": "10",
                                "postageSegment": {
                                    "local": 1,
                                    "overseas": 2
                                },
                                "overseasDeliveryId": 3,
                                "singleItemShipping": 5,
                                "okihaiSetting": true
                            },
                            "specs": [
                                {
                                    "label": "Country of origin",
                                    "value": "Japan"
                                }
                            ],
                            "attributes": [
                              {
                                "name": "ブランド名",
                                "values": [
                                  "お米"
                                ]
                                },
                                {
                                  "name": "シリーズ名",
                                  "values": [
                                    "鶏めし"
                                  ]
                                },
                               {
                                  "name": "原産国／製造国",
                                  "values": [
                                    "日本"
                                  ]
                               },
                               {
                                 "name": "総個数",
                                 "values": [
                                   "1"
                                 ]
                               },
                               {
                                 "name": "総重量",
                                 "values": [
                                   "10"
                                  ],
                                 "unit": "kg"
                                }
                             ]
                        },
                        "sku-2": {
                            "selectorValues": {
                                "color-key": "青色",
                                "size-key": "Mサイズ"
                            },
                            "restockOnCancel": false,
                            "backOrderFlag": false,
                            "standardPrice": "810",
                            "articleNumber":{
                              "value":"0689640032932",
                            },
                            "shipping": {
                                 "okihaiSetting": true
                             },
                            "attributes": [
                              {
                                "name": "ブランド名",
                                "values": [
                                  "お米"
                                ]
                                },
                                {
                                  "name": "シリーズ名",
                                  "values": [
                                    "鶏めし"
                                  ]
                                },
                               {
                                  "name": "原産国／製造国",
                                  "values": [
                                    "日本"
                                  ]
                               },
                               {
                                 "name": "総個数",
                                 "values": [
                                   "1"
                                 ]
                               },
                               {
                                 "name": "総重量",
                                 "values": [
                                   "10"
                                  ],
                                 "unit": "kg"
                                }
                             ]
                        }
                    },
                    "created": "2021-07-08T01:05:31+09:00",
                    "updated": "2021-07-29T00:24:22+09:00"
                }
                ```
                
        5. **通常商品（定期購入設定あり）の場合**
            - Request (curl コマンドを使った例)
                
                ```bash
                curl --location --request GET 'https://api.rms.rakuten.co.jp/es/2.0/items/manage-numbers/6650' \
                --header 'Authorization: ESA xxx'
                ```
                
            - Response in JSON format (Status: 200 OK)
                
                ```bash
                {
                    "manageNumber": "subscription-item",
                    "itemType": "NORMAL",
                    "itemNumber": "VEGE-001-234",
                    "title": "通常商品（定期購入設定あり）の商品名",
                    "tagline": "PCブラウザ向けに最適化されたキャッチコピー的なフィールド",
                    "productDescription": {
                        "pc": "<div>PCブラウザ向けに最適化された商品説明分(HTML)</div>",
                        "sp": "<div>携帯端末ブラウザ向けに最適化された商品説明分(HTML)</div>"
                    },
                    "salesDescription": "販売説明分人間用の新野菜",
                    "images": [
                        {
                            "type": "CABINET",
                            "location": "/myfolder-1/myfolder-2/vegetable-red.jpg",
                            "alt": "vegetable-red"
                        },
                        {
                            "type": "GOLD",
                            "location": "/folder-1/folder-2/vegetable-blue.jpg",
                            "alt": "vegetable-blue"
                        },
                        {
                            "type": "ABSOLUTE",
                            "location": "https://image.books.rakuten.co.jp/vegetable-green.jpg",
                            "alt": "vegetable-green"
                        }
                    ],
                    "whiteBgImage": {
                        "type": "GOLD",
                        "location": "/vegetable-blue-jp.jpg"
                    },
                    "video": {
                        "type": "HTML",
                        "parameters": {
                            "value": "<scriptsrc=\"//stream.cms.rakuten.co.jp/gate/play/?w=320&h=286&mid=1101692986&vid=5792214557001\"type=\"text/javascript\"></script>"
                        }
                    },
                    "genreId": "558863",
                    "tags": [
                        7654321,
                        9000000
                    ],
                    "hideItem": false,
                    "customizationOptions": [
                        {
                            "displayName": "野菜にアレルギーの経験はありますか",
                            "inputType": "SINGLE_SELECTION",
                            "required": true,
                            "selections": [
                                {
                                    "displayValue": "はい"
                                },
                                {
                                    "displayValue": "いいえ"
                                }
                            ]
                        }
                    ],
                    "purchasablePeriod": {
                        "start": "2021-07-11T15:00:00+09:00",
                        "end": "2021-07-31T14:59:59+09:00"
                    },
                    "subscription": {
                        "shippingDateFlag": true,
                        "shippingIntervalFlag": true
                    },
                    "features": {
                        "searchVisibility": "ALWAYS_VISIBLE",
                        "displayNormalCartButton": true,
                        "displaySubscriptionCartButton": true,
                        "inventoryDisplay": "DISPLAY_LOW_STOCK",
                        "lowStockThreshold": 10,
                        "shopContact": true,
                        "review": "HIDDEN",
                        "displayManufacturerContents": true,
                        "socialGiftFlag": false
                    },
                    "payment": {
                        "taxIncluded": false,
                        "taxRate": "0.1",
                        "cashOnDeliveryFeeIncluded": true
                    },
                    "pointCampaign": {
                        "applicablePeriod": {
                            "start": "2018-04-28T07:59:49+09:00",
                            "end": "2018-05-28T07:59:49+09:00"
                        },
                        "benefits": {
                            "pointRate": 15
                        },
                        "optimization": {
                            "maxPointRate": 15
                        }
                    },
                    "itemDisplaySequence": 9999,
                    "layout": {
                        "itemLayoutId": 1,
                        "navigationId": 2933,
                        "layoutSequenceId": 46272,
                        "smallDescriptionId": 2,
                        "largeDescriptionId": 566,
                        "showcaseId": 199
                    },
                    "variantSelectors": [
                        {
                           "key":"color-key",
                            "displayName": "カラー",
                            "values": [
                                {
                                    "displayValue": "赤",
                                },
                                {
                                    "displayValue": "青",
                                }
                            ]
                        },
                        {
                           "key":"size-key",
                            "displayName": "サイズ",
                            "values": [
                                {
                                    "displayValue": "S",
                                },
                                {
                                    "displayValue": "M",
                                }
                            ]
                        }
                    ],
                    "variants": {
                        "sku-001": {
                            "merchantDefinedSkuId": "システム連携SKU商品番号",
                            "selectorValues": {
                                "color-key": "赤",
                                "size-key": "S"
                            },
                            "images": [
                                {
                                    "type": "CABINET",
                                    "location": "/01003752/dog_15.jpg",
                                    "alt": "sku-image"
                                }
                            ],
                            "restockOnCancel": true,
                            "backOrderFlag": false,
                            "normalDeliveryDateId": 1,
                            "backOrderDeliveryDateId": 2,
                            "hidden": false,
                            "orderQuantityLimit": 3,
                            "features": {
                                "restockNotification": false,
                                "noshi": true
                            },
                            "standardPrice": "2000",
                            "subscriptionPrice": {
                                "basePrice": "1500",
                                "individualPrices": {
                                    "firstPrice": "1000"
                                }
                            },
                            "articleNumber": {
                                "value": "4902780029294"
                            },
                            "referencePrice": {
                                "displayType": "REFERENCE_PRICE",
                                "type": 1,
                                "value": "2000"
                            },
                            "shipping": {
                                "fee": "1000",
                                "postageIncluded": true,
                                "shopAreaSoryoPatternId": 2,
                                "shippingMethodGroup": "10",
                                "postageSegment": {
                                    "local": 1,
                                    "overseas": 2
                                },
                                "overseasDeliveryId": 3,
                                "singleItemShipping": 5,
                                 "okihaiSetting": true
                            },
                            "specs": [
                                {
                                    "label": "Country of origin",
                                    "value": "Japan"
                                }
                            ],
                            "attributes": [
                                {
                                    "name": "attributeName1",
                                    "values": [
                                        "赤色",
                                        "100",
                                        "2021-10-15"
                                    ]
                                },
                                {
                                    "name": "attributeName20",
                                    "values": [
                                        "10"
                                    ],
                                    "unit": "kg"
                                }
                            ]
                        },
                        "sku-002": {
                            "selectorValues": {
                                "color-key": "赤",
                                "size-key": "M"
                            },
                            "standardPrice": "10000",
                            "articleNumber": {
                                "value": "4902780029294"
                            },
                            "restockOnCancel": false,
                            "backOrderFlag": false,
                             "shipping": {
                                "okihaiSetting": true
                             }
                        }
                    },
                    "created": "2018-04-28T07:59:49+09:00",
                    "updated": "2021-08-31T07:59:49+09:00"
                }
                ```
                
        6. **予約商品の場合**
            - Request (curl コマンドを使った例)
                
                ```bash
                curl --location --request GET 'https://api.rms.rakuten.co.jp/es/2.0/items/manage-numbers/6650' \
                --header 'Authorization: ESA xxx'
                ```
                
            - Response in JSON format (Status: 200 OK)
                
                ```bash
                {
                    "manageNumber": "pre-order-item",
                    "itemType": "PRE_ORDER",
                    "itemNumber": "itemnumber",
                    "title": "予約商品の商品名",
                    "tagline": "pc and sp catchcopy",
                    "productDescription": {
                        "pc": "explanation for PC",
                        "sp": "explanation for SP"
                    },
                    "salesDescription": "salesexplanation for PC",
                    "images": [
                        {
                            "type": "CABINET",
                            "location": "/01003752/dog_07.jpg",
                            "alt": "itemname"
                        }
                    ],
                    "whiteBgImage": {
                        "type": "GOLD",
                        "location": "/vegetable-blue-jp.jpg"
                    },
                    "video": {
                        "type": "HTML",
                        "parameters": {
                            "value": "<scriptsrc=\"//stream.cms.rakuten.co.jp/gate/play/?w=320&h=286&mid=1101692986&vid=5792214557001\"type=\"text/javascript\"></script>"
                        }
                    },
                    "genreId": "206878",
                    "tags": [
                        7654321,
                        9000000
                    ],
                    "hideItem": false,
                    "unlimitedInventoryFlag": false,
                    "releaseDate": "2018-04-28",
                    "customizationOptions": [
                        {
                            "displayName": "ギフト包装",
                            "inputType": "SINGLE_SELECTION",
                            "required": true,
                            "selections": [
                                {
                                    "displayValue": "はい"
                                }
                            ]
                        }
                    ],
                    "purchasablePeriod": {
                        "start": "2021-07-11T15:00:00+09:00",
                        "end": "2021-07-31T14:59:59+09:00"
                    },
                    "features": {
                        "searchVisibility": "ALWAYS_VISIBLE",
                        "shopContact": true,
                        "review": "SHOP_SETTING",
                        "displayManufacturerContents": false,
                        "displayNormalCartButton": true,
                        "displaySubscriptionCartButton": false,
                        "inventoryDisplay": "HIDDEN_STOCK",
                        "lowStockThreshold": 1,
                        "socialGiftFlag": false
                    },
                    "payment": {
                        "taxIncluded": false,
                        "taxRate": "0.1",
                        "cashOnDeliveryFeeIncluded": true
                    },
                    "pointCampaign": {
                        "applicablePeriod": {
                            "start": "2018-04-28T07:59:49+09:00",
                            "end": "2018-05-28T07:59:49+09:00"
                        },
                        "benefits": {
                            "pointRate": 15
                        },
                        "optimization": {
                            "maxPointRate": 15
                        }
                    },
                    "itemDisplaySequence": 999999999,
                    "layout": {
                        "itemLayoutId": 1,
                        "navigationId": 10,
                        "layoutSequenceId": 20,
                        "smallDescriptionId": 30,
                        "largeDescriptionId": 40,
                        "showcaseId": 50
                    },
                    "variantSelectors": [
                        {
                           "key":"size-key",
                            "displayName": "サイズ",
                            "values": [
                                {
                                    "displayValue": "Sサイズ"
                                },
                                {
                                    "displayValue": "Mサイズ"
                                }
                            ]
                        },
                        {
                           "key":"color-key",
                            "displayName": "カラー",
                            "values": [
                                {
                                    "displayValue": "青色"
                                }
                            ]
                        }
                    ],
                    "variants": {
                        "sku-1": {
                            "merchantDefinedSkuId": "システム連携SKU商品番号",
                            "selectorValues": {
                                "color-key": "青色",
                                "size-key": "Sサイズ"
                            },
                            "images": [
                                {
                                    "type": "CABINET",
                                    "location": "/01003752/dog_15.jpg",
                                    "alt": "sku-image"
                                }
                            ],
                            "restockOnCancel": true,
                            "backOrderFlag": false,
                            "normalDeliveryDateId": 1,
                            "backOrderDeliveryDateId": 2,
                            "articleNumber": {
                                "value": "4902780029294"
                            },
                            "articleNumberForSet": [
                                "4901777312067",
                                "w301628",
                                "JR-VT-CTAK-S20I-JPGY4A",
                                "pc-desk-hp-800g1-sf-02"
                            ],
                            "hidden": true,
                            "orderQuantityLimit": 3,
                            "features": {
                                "restockNotification": true,
                                "noshi": true
                            },
                            "standardPrice": "10000",
                            "referencePrice": {
                                "displayType": "REFERENCE_PRICE",
                                "type": 1,
                                "value": "15000"
                            },
                            "shipping": {
                                "fee": "1000",
                                "postageIncluded": true,
                                "shopAreaSoryoPatternId": 2,
                                "shippingMethodGroup": "10",
                                "postageSegment": {
                                    "local": 1,
                                    "overseas": 2
                                },
                                "overseasDeliveryId": 3,
                                "singleItemShipping": 5,
                                 "okihaiSetting": true
                            },
                            "specs": [
                                {
                                    "label": "Country of origin",
                                    "value": "Japan"
                                }
                            ],
                            "attributes": [
                                {
                                    "name": "attributeName1",
                                    "values": [
                                        "赤色",
                                        "100",
                                        "2021-10-15"
                                    ]
                                },
                                {
                                    "name": "attributeName20",
                                    "values": [
                                        "10"
                                    ],
                                    "unit": "kg"
                                }
                            ]
                        },
                        "sku-2": {
                            "selectorValues": {
                                "color-key": "青色",
                                "size-key": "Mサイズ"
                            },
                            "standardPrice": "10000",
                            "articleNumber": {
                                "value": "4902780029294"
                            },
                            "restockOnCancel": false,
                            "backOrderFlag": false,
                             "shipping": {
                                "okihaiSetting": true
                            },
                            "attributes": [
                                {
                                    "name": "attributeName1",
                                    "values": [
                                        "赤色",
                                        "100",
                                        "2021-10-15"
                                    ]
                                },
                                {
                                    "name": "attributeName20",
                                    "values": [
                                        "10"
                                    ],
                                    "unit": "kg"
                                }
                            ]
                        }
                    },
                    "created": "2021-07-08T01:05:31+09:00",
                    "updated": "2021-07-29T00:24:22+09:00"
                }
                ```
                
        7. **頒布会商品の場合**
            - Request (curl コマンドを使った例)
                
                ```bash
                curl --location --request GET 'https://api.rms.rakuten.co.jp/es/2.0/items/manage-numbers/6650' \
                --header 'Authorization: ESA xxx'
                ```
                
            - Response in JSON format (Status: 200 OK)
                
                ```bash
                {
                    "manageNumber": "buyingclub-item",
                    "itemType": "BUYING_CLUB",
                    "itemNumber": "VEGE-001-234",
                    "title": "頒布会商品の商品名",
                    "tagline": "PCブラウザ向けに最適化されたキャッチコピー的なフィールド",
                    "productDescription": {
                        "pc": "<div>PCブラウザ向けに最適化された商品説明分(HTML)</div>",
                        "sp": "<div>携帯端末ブラウザ向けに最適化された商品説明分(HTML)</div>"
                    },
                    "salesDescription": "販売説明分人間用の新野菜",
                    "images": [
                        {
                            "type": "CABINET",
                            "location": "/myfolder-1/myfolder-2/vegetable-red.jpg",
                            "alt": "vegetable-red"
                        },
                        {
                            "type": "GOLD",
                            "location": "/folder-1/folder-2/vegetable-blue.jpg",
                            "alt": "vegetable-blue"
                        },
                        {
                            "type": "ABSOLUTE",
                            "location": "https://image.books.rakuten.co.jp/vegetable-green.jpg",
                            "alt": "vegetable-green"
                        }
                    ],
                    "whiteBgImage": {
                        "type": "GOLD",
                        "location": "/vegetable-blue-jp.jpg"
                    },
                    "video": {
                        "type": "HTML",
                        "parameters": {
                            "value": "<scriptsrc=\"//stream.cms.rakuten.co.jp/gate/play/?w=320&h=286&mid=1101692986&vid=5792214557001\"type=\"text/javascript\"></script>"
                        }
                    },
                    "genreId": "558863",
                    "tags": [
                        7654321,
                        9000000
                    ],
                    "hideItem": false,
                    "customizationOptions": [
                        {
                            "displayName": "野菜にアレルギーの経験はありますか",
                            "inputType": "SINGLE_SELECTION",
                            "required": true,
                            "selections": [
                                {
                                    "displayValue": "はい"
                                },
                                {
                                    "displayValue": "いいえ"
                                }
                            ]
                        }
                    ],
                    "purchasablePeriod": {
                        "start": "2021-07-11T15:00:00+09:00",
                        "end": "2021-07-31T14:59:59+09:00"
                    },
                    "buyingClub": {
                        "numberOfDeliveries": 2,
                        "displayItems": true,
                        "items": ["1回目 商品", "2回目 商品"],
                        "shippingDateFlag": true,
                        "shippingIntervalFlag": false
                    },
                    "features": {
                        "searchVisibility": "ALWAYS_VISIBLE",
                        "displayNormalCartButton": false,
                        "displaySubscriptionCartButton": true,
                        "inventoryDisplay": "DISPLAY_LOW_STOCK",
                        "lowStockThreshold": 10,
                        "shopContact": true,
                        "review": "HIDDEN",
                        "displayManufacturerContents": true,
                        "socialGiftFlag": false
                    },
                    "payment": {
                        "taxIncluded": false,
                        "taxRate": "0.1",
                        "cashOnDeliveryFeeIncluded": true
                    },
                    "pointCampaign": {
                        "applicablePeriod": {
                            "start": "2018-04-28T07:59:49+09:00",
                            "end": "2018-05-28T07:59:49+09:00"
                        },
                        "benefits": {
                            "pointRate": 15
                        }
                    },
                    "itemDisplaySequence": 9999,
                    "layout": {
                        "itemLayoutId": 1,
                        "navigationId": 2933,
                        "layoutSequenceId": 46272,
                        "smallDescriptionId": 2,
                        "largeDescriptionId": 566,
                        "showcaseId": 199
                    },
                    "variantSelectors": [
                        {
                           "key":"color-key",
                            "displayName": "カラー",
                            "values": [
                                {
                                    "displayValue": "赤"
                                },
                                {
                                    "displayValue": "青"
                                }
                            ]
                        },
                        {
                           "key":"size-key",
                            "displayName": "サイズ",
                            "values": [
                                {
                                    "displayValue": "S"
                                },
                                {
                                    "displayValue": "M"
                                }
                            ]
                        }
                    ],
                    "variants": {
                        "sku-001": {
                            "merchantDefinedSkuId": "システム連携SKU商品番号",
                            "selectorValues": {
                                "color-key": "赤",
                                "size-key": "S"
                            },
                            "images": [
                                {
                                    "type": "CABINET",
                                    "location": "/01003752/dog_15.jpg",
                                    "alt": "sku-image"
                                }
                            ],
                            "restockOnCancel": false,
                            "backOrderFlag": false,
                            "hidden": false,
                            "orderQuantityLimit": 3,
                            "features": {
                                "restockNotification": false
                            },
                            "subscriptionPrice": {
                                "basePrice": "2000",
                                "individualPrices": {
                                    "firstPrice": "1000"
                                }
                            },
                            "articleNumber": {
                                "value": "4902780029294"
                            },
                            "referencePrice": {
                                "displayType": "REFERENCE_PRICE",
                                "type": 1,
                                "value": "2000"
                            },
                            "shipping": {
                                "fee": "1000",
                                "postageIncluded": true,
                                "shippingMethodGroup": "10",
                                "singleItemShipping": 5,
                                 "okihaiSetting": true
                            },
                            "specs": [
                                {
                                    "label": "Country of origin",
                                    "value": "Japan"
                                }
                            ],
                            "attributes": [
                                {
                                    "name": "attributeName1",
                                    "values": [
                                        "赤色",
                                        "100",
                                        "2021-10-15"
                                    ]
                                },
                                {
                                    "name": "attributeName20",
                                    "values": [
                                        "10"
                                    ],
                                    "unit": "kg"
                                }
                            ]
                        },
                        "sku-002": {
                            "selectorValues": {
                                "color-key": "赤",
                                "size-key": "M"
                            },
                            "subscriptionPrice": {
                                "basePrice": "2000",
                                "individualPrices": {
                                    "firstPrice": "1000"
                                }
                            },
                            "articleNumber": {
                                "value": "4902780029294"
                            },
                            "restockOnCancel": false,
                            "backOrderFlag": false,
                             "shipping": {
                                 "okihaiSetting": true
                             }
                        }
                    },
                    "created": "2018-04-28T07:59:49+09:00",
                    "updated": "2021-08-31T07:59:49+09:00"
                }
                ```
                
        8. **SKU移行前の商品を取得した場合**
            - Request (curl コマンドを使った例)
                
                ```bash
                curl --location --request GET 'https://api.rms.rakuten.co.jp/es/2.0/items/manage-numbers/20220426_sato_check_mngnumber' \
                --header 'Authorization: ESA xxx'
                ```
                
            - Response in JSON format (Status: 200 OK)
                
                ```bash
                {
                    "manageNumber": "20220426_sato_check_mngnumber",
                    "itemNumber": "20220426_sato_check_itemid",
                    "itemType": "NORMAL",
                    "title": "20220426_sato_check_title",
                    "tagline": "20220426_sato_check_pc_catchcopy",
                    "genreId": "555555",
                    "hideItem": false,
                    "unlimitedInventoryFlag": false,
                    "customizationOptions": [
                        {
                            "displayName": "customizationOptions1",
                            "inputType": "SINGLE_SELECTION",
                            "required": false,
                            "selections": [
                                {
                                    "displayValue": "opt_answer1"
                                },
                                {
                                    "displayValue": "opt_answer2"
                                },
                                {
                                    "displayValue": "opt_answer3"
                                }
                            ]
                        },
                        {
                            "displayName": "customizationOptions2",
                            "inputType": "SINGLE_SELECTION",
                            "required": true,
                            "selections": [
                                {
                                    "displayValue": "must_answer1"
                                },
                                {
                                    "displayValue": "must_answer2"
                                },
                                {
                                    "displayValue": "must_answer3"
                                }
                            ]
                        }
                    ],
                    "features": {
                        "searchVisibility": "ALWAYS_VISIBLE",
                        "shopContact": false,
                        "review": "SHOP_SETTING",
                        "displayManufacturerContents": true,
                        "displayNormalCartButton": true,
                        "displaySubscriptionCartButton": false,
                        "inventoryDisplay": "HIDDEN_STOCK",
                        "socialGiftFlag": false
                    },
                    "payment": {
                        "taxIncluded": true,
                        "cashOnDeliveryFeeIncluded": false
                    },
                    "itemDisplaySequence": 999999999,
                    "layout": {
                        "itemLayoutId": 1,
                        "navigationId": 0,
                        "layoutSequenceId": 0,
                        "smallDescriptionId": 0,
                        "largeDescriptionId": 0,
                        "showcaseId": 0
                    },
                    "variants": {
                        "normal-inventory": {
                            "restockOnCancel": false,
                            "backOrderFlag": false,
                            "normalDeliveryDateId": 1000,
                            "backOrderDeliveryDateId": 1,
                            "articleNumber": {
                                "exemptionReason": 5
                            },
                            "standardPrice": "5000",
                            "shipping": {
                                "postageIncluded": true,
                                "singleItemShipping": 0,
                                "okihaiSetting": true
                            },
                            "hidden": false,
                            "features": {
                                "restockNotification": false,
                                "noshi": false
                            }
                        }
                    },
                    "created": "2022-04-26T09:01:26+09:00",
                    "updated": "2022-04-26T09:01:26+09:00"
                }
                ```
                
    2. **失敗した場合**
        - Request (curl コマンドを使った例)
            
            ```bash
            curl --location --request GET 'https://api.rms.rakuten.co.jp/es/2.0/items/manage-numbers/6651' \
            --header 'Authorization: ESA xxx'
            ```
            
        - Response in JSON format (Status: 404 Not Found)
            
            ```bash
            {
                "errors": [
                    {
                        "code": "GE0014",
                        "message": "No item found for inputs; manageNumber=6651"
                    }
                ]
            }
            ```