import base64
import csv
import os
import time
from pathlib import Path
from urllib.parse import quote

import requests

# 認証情報は環境変数に退避することを推奨
SERVICE_SECRET = "SP427270_VjEHnN7xj5JALZ92"
LICENSE_KEY = "SL427270_7I6UtBfmDz33MCcs"


def resolve_manage_number_file() -> Path:
    """manage_numbers.csv の配置場所を探索して返す。"""
    candidates = [
        Path("_reference/manage_numbers.csv"),
        Path("manage_numbers.csv"),
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        f"manage_numbers.csv not found. Tried: {', '.join(str(p) for p in candidates)}"
    )


MANAGE_NUMBER_FILE = resolve_manage_number_file()


def auth_header():
    token = base64.b64encode(f"{SERVICE_SECRET}:{LICENSE_KEY}".encode()).decode()
    return {"Authorization": f"ESA {token}"}


def load_manage_numbers(path: Path):
    """
    1列目ヘッダが「商品管理番号（商品URL）」のCSVを読み込み、重複を除去して返す。
    エンコーディングは Shift_JIS(cp932) 優先、だめなら UTF-8(BOM)。
    """
    expected_header = "商品管理番号（商品URL）"
    encodings = ["cp932", "utf-8-sig"]
    for enc in encodings:
        try:
            with path.open(newline="", encoding=enc) as f:
                rows = list(csv.reader(f))
        except UnicodeDecodeError:
            continue
        if not rows:
            return []
        header = [c.strip() for c in rows[0]]
        if not header or header[0] != expected_header:
            raise RuntimeError(
                f"Unexpected header in {path}: {header[0] if header else ''} (expected {expected_header})"
            )
        nums = []
        for r in rows[1:]:
            if not r:
                continue
            n = r[0].strip()
            if n:
                nums.append(n)
        return list(dict.fromkeys(nums))  # 重複排除し順序維持
    raise RuntimeError(f"Failed to decode {path}")


def build_rows(item_json):
    selectors = {s["key"]: s["displayName"] for s in item_json.get("variantSelectors", [])}
    order = [s["key"] for s in item_json.get("variantSelectors", [])]
    rows = []
    for vid, v in item_json.get("variants", {}).items():
        sel_vals = v.get("selectorValues", {}) or {}
        parts = [f"{selectors.get(k, k)}:{sel_vals[k]}" for k in order if k in sel_vals]
        rows.append((item_json["manageNumber"], vid, " ".join(parts)))
    return rows


def fetch_with_retry(session: requests.Session, m: str, max_retry: int = 5):
    url = f"https://api.rms.rakuten.co.jp/es/2.0/items/manage-numbers/{quote(m)}"
    backoff = 2
    for attempt in range(1, max_retry + 1):
        res = session.get(url, timeout=15)
        if res.status_code == 404:
            print(f"Not found: {m}")
            return None
        if res.status_code in (429,) or res.status_code >= 500:
            retry_after = res.headers.get("Retry-After")
            sleep_sec = int(retry_after) if retry_after and retry_after.isdigit() else backoff
            print(f"{res.status_code} for {m}, retry in {sleep_sec}s (attempt {attempt}/{max_retry})")
            time.sleep(sleep_sec)
            backoff = min(backoff * 2, 60)
            continue
        res.raise_for_status()
        return res
    res.raise_for_status()  # give up


manage_numbers = load_manage_numbers(MANAGE_NUMBER_FILE)

with requests.Session() as s, open("manage_variant_skuinfo.csv", "w", newline="", encoding="utf-8") as f:
    s.headers.update(auth_header())
    w = csv.writer(f)
    w.writerow(["manageNumber", "variantId", "skuInfo"])
    total = len(manage_numbers)
    for i, m in enumerate(manage_numbers, 1):
        print(f"{i}/{total} {m}")
        time.sleep(1)  # throttle between calls
        res = fetch_with_retry(s, m)
        if not res:
            continue
        for row in build_rows(res.json()):
            w.writerow(row)
            f.flush()
