import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional

# 公式サンプル(ver9)のキー前提。欠損や別名フォールバックはしない。
STRICT_VALIDATE = True

def _utcnow_iso() -> str:
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

def _ts(val: Optional[str]) -> Optional[pd.Timestamp]:
    if not val:
        return None
    return pd.to_datetime(val, utc=True, errors="coerce")

def _date(val: Optional[str]):
    ts = _ts(val)
    return ts.date() if ts is not None else None

def _f(x) -> Optional[float]:
    if x is None or x == "":
        return None
    return float(x)

def _i(x) -> Optional[int]:
    if x is None or x == "":
        return None
    return int(x)

def _req(d: Dict[str, Any], key: str):
    if key not in d or d[key] is None:
        raise ValueError(f"Required key missing: {key}")
    return d[key]

# ------------------------------------------------------------
# orders
# ------------------------------------------------------------
def normalize_orders(getorder_json: Dict[str, Any], inserted_at: Optional[str] = None) -> pd.DataFrame:
    inserted_at = inserted_at or _utcnow_iso()
    orders_src: List[Dict[str, Any]] = getorder_json.get("OrderModelList", [])
    if STRICT_VALIDATE and not isinstance(orders_src, list):
        raise ValueError("OrderModelList must be a list")

    rows = []
    for o in orders_src:
        # 必須チェック（最低限）
        order_number = _req(o, "orderNumber")

        settlement = o.get("SettlementModel", {})  # 以下は存在しなくてもNoneでよい
        delivery   = o.get("DeliveryModel", {})
        point      = o.get("PointModel", {})
        orderer    = o.get("OrdererModel", {})

        row = {
            "order_number": order_number,
            "order_datetime": _ts(o.get("orderDatetime")),
            # ver9で一般的なのは orderProgress（int）。スキーマはSTRINGなのでstr化。
            "order_status": str(o.get("orderProgress")) if o.get("orderProgress") is not None else None,
            "cancel_due_date": _date(o.get("cancelDueDate")),
            "total_price": _f(o.get("totalPrice")),
            "goods_price": _f(o.get("goodsPrice")),
            "postage_price": _f(o.get("postagePrice")),
            "payment_fee": _f(o.get("paymentFee")),
            "used_point": _f(point.get("usedPoint")),
            "payment_method": settlement.get("settlementMethod"),
            "card_name": settlement.get("cardName"),
            "delivery_name": delivery.get("deliveryName"),
            "delivery_date": _date(o.get("deliveryDate")),
            "rakuten_member_flag": bool(o.get("rakutenMemberFlag")) if o.get("rakutenMemberFlag") is not None else None,
            "user_email": orderer.get("emailAddress"),
            "prefecture": orderer.get("prefecture"),
            "city": orderer.get("city"),
            "zip_code": orderer.get("zipCode"),
            "order_update_datetime": _ts(o.get("orderUpdateDatetime")),
            "inserted_at": pd.to_datetime(inserted_at, utc=True),
        }

        if STRICT_VALIDATE:
            # 最低限：注文番号＋日時は必須に近い扱い
            if row["order_datetime"] is None:
                raise ValueError(f"orderDatetime is missing/invalid in order {order_number}")

        rows.append(row)

    return pd.DataFrame(
        rows,
        columns=[
            "order_number","order_datetime","order_status","cancel_due_date",
            "total_price","goods_price","postage_price","payment_fee","used_point",
            "payment_method","card_name","delivery_name","delivery_date",
            "rakuten_member_flag","user_email","prefecture","city","zip_code",
            "order_update_datetime","inserted_at",
        ],
    )

# ------------------------------------------------------------
# order_items
# ------------------------------------------------------------
def normalize_order_items(getorder_json: Dict[str, Any], inserted_at: Optional[str] = None) -> pd.DataFrame:
    inserted_at = inserted_at or _utcnow_iso()
    orders_src: List[Dict[str, Any]] = getorder_json.get("OrderModelList", [])
    if STRICT_VALIDATE and not isinstance(orders_src, list):
        raise ValueError("OrderModelList must be a list")

    rows = []
    for o in orders_src:
        order_number = _req(o, "orderNumber")
        packages: List[Dict[str, Any]] = o.get("PackageModelList", []) or []

        for pkg in packages:
            basket_id = pkg.get("basketId")
            delivery_company = pkg.get("defaultDeliveryCompanyCode")
            delivery_status = pkg.get("deliveryStatus")

            items: List[Dict[str, Any]] = pkg.get("ItemModelList", []) or []
            for it in items:
                # 必須に近いキー
                item_id = it.get("itemId")
                if STRICT_VALIDATE and item_id is None:
                    raise ValueError(f"itemId missing in order {order_number}")

                units = _i(it.get("units"))
                price_tax_incl = _f(it.get("priceTaxIncl"))

                # subtotal は「税込単価×数量」で素直に算出（フィールドがあるならそれを使ってもOK）
                subtotal = _f(it.get("subtotal"))
                if subtotal is None and price_tax_incl is not None and units is not None:
                    subtotal = round(price_tax_incl * units, 2)

                rows.append({
                    "order_number": order_number,
                    "basket_id": basket_id,
                    "item_id": item_id,
                    "item_name": it.get("itemName"),
                    "manage_number": it.get("manageNumber"),
                    "genre": it.get("genre"),
                    "price": _f(it.get("price")),                 # 税抜
                    "price_tax_incl": price_tax_incl,             # 税込
                    "quantity": units,
                    "subtotal": subtotal,
                    "tax_rate": _f(it.get("taxRate")),
                    "discount_price": _f(it.get("discountPrice")),
                    "point_given": _f(it.get("pointGiven")),
                    "delivery_company": delivery_company,
                    "delivery_status": delivery_status,
                    "inserted_at": pd.to_datetime(inserted_at, utc=True),
                })

    return pd.DataFrame(
        rows,
        columns=[
            "order_number","basket_id","item_id","item_name","manage_number","genre",
            "price","price_tax_incl","quantity","subtotal","tax_rate",
            "discount_price","point_given","delivery_company","delivery_status","inserted_at",
        ],
    )

# ------------------------------------------------------------
# まとめて作るユーティリティ
# ------------------------------------------------------------
def normalize_all(getorder_json: Dict[str, Any], inserted_at: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    return (
        normalize_orders(getorder_json, inserted_at),
        normalize_order_items(getorder_json, inserted_at),
    )
