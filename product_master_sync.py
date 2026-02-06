from __future__ import annotations

import argparse
import io
import os
import logging
from typing import Any, Dict, Optional, Tuple
from urllib.parse import quote

import pandas as pd
import requests
import google.auth
from google.auth.transport.requests import AuthorizedSession

from bigquery_client import insert_dataframe

# ============================================================
# Product master (Google Sheets -> BigQuery)
# ============================================================
#
# Goal:
# - Keep product naming stable by referencing a master maintained in Google Sheets.
# - Sync master into BigQuery on each ETL run (same timing as order ingestion).
#
# Environment variables:
# - PRODUCT_MASTER_SHEET_ID: Google Spreadsheet ID (recommended, private sheet OK)
# - PRODUCT_MASTER_SHEET_RANGE: A1 range (optional, default "A:D"; sheet title auto-resolved)
# - PRODUCT_MASTER_CSV_URL: Published CSV URL (optional alternative)
# - PRODUCT_MASTER_CSV_PATH: Local CSV path (optional, mainly for local dev)
# - BQ_TABLE_PRODUCT_MASTER_RAW: BigQuery table name (default "product_master_raw")
# - PRODUCT_MASTER_SYNC_REQUIRED: if true, fail when sync cannot run (default false)
#
# Output BigQuery columns:
# - manage_number, product_name, category_name, brand_name


_REQUIRED_BOOL = ("true", "1", "t", "yes", "y")


def _is_truthy(v: Optional[str]) -> bool:
    return (v or "").strip().lower() in _REQUIRED_BOOL


def _normalize_master_df(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "商品管理番号": "manage_number",
        "商品名": "product_name",
        "カテゴリ名": "category_name",
        "ブランド名": "brand_name",
    }
    df = df.rename(columns=rename_map)

    cols = ["manage_number", "product_name", "category_name", "brand_name"]
    for c in cols:
        if c not in df.columns:
            df[c] = pd.NA

    df = df[cols].copy()
    for c in cols:
        df[c] = df[c].astype("string").str.strip()

    # Treat empty strings as missing.
    df = df.replace({"": pd.NA})

    # Drop rows missing manage_number.
    df = df[df["manage_number"].notna()].copy()

    # Remove exact duplicates to reduce BigQuery load size.
    df = df.drop_duplicates()
    return df


def _fetch_master_from_csv_path(path: str) -> Tuple[pd.DataFrame, str]:
    df = pd.read_csv(path, dtype="string", encoding="utf-8")
    return df, f"csv_path:{path}"


def _fetch_master_from_csv_url(url: str) -> Tuple[pd.DataFrame, str]:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    df = pd.read_csv(io.BytesIO(resp.content), dtype="string")
    return df, f"csv_url:{url}"


def _authed_session() -> AuthorizedSession:
    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    return AuthorizedSession(creds)


def _get_first_sheet_title(sheet_id: str, session: AuthorizedSession) -> str:
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}"
    resp = session.get(url, params={"fields": "sheets.properties.title"}, timeout=30)
    resp.raise_for_status()
    data = resp.json() or {}
    sheets = data.get("sheets") or []
    if not sheets:
        raise ValueError("No sheets found in the spreadsheet")
    title = ((sheets[0] or {}).get("properties") or {}).get("title")
    if not title:
        raise ValueError("Failed to resolve the first sheet title")
    return title


def _fetch_master_from_sheets(sheet_id: str, sheet_range: str) -> Tuple[pd.DataFrame, str]:
    session = _authed_session()

    a1 = sheet_range or "A:D"
    if "!" not in a1:
        title = _get_first_sheet_title(sheet_id, session)
        a1 = f"{title}!{a1}"

    url = (
        "https://sheets.googleapis.com/v4/spreadsheets/"
        f"{sheet_id}/values/{quote(a1, safe='')}"
    )
    resp = session.get(
        url,
        params={"valueRenderOption": "UNFORMATTED_VALUE"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json() or {}
    values = data.get("values") or []
    if not values:
        return pd.DataFrame(), f"sheets:{sheet_id}:{a1}"

    header = values[0] or []
    rows = values[1:] or []
    if not header:
        return pd.DataFrame(), f"sheets:{sheet_id}:{a1}"

    width = len(header)
    padded = [r + [None] * (width - len(r)) if len(r) < width else r[:width] for r in rows]
    df = pd.DataFrame(padded, columns=header)
    return df, f"sheets:{sheet_id}:{a1}"


def sync_product_master(
    *,
    dataset: Optional[str] = None,
    table: Optional[str] = None,
    required: Optional[bool] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Fetch product master and replace BigQuery table unless dry_run is true.

    Returns a small dict for logging/response JSON.
    """
    dataset = dataset or os.getenv("BQ_DATASET", "rakuten_orders")
    table = table or os.getenv("BQ_TABLE_PRODUCT_MASTER_RAW", "product_master_raw")
    required = required if required is not None else _is_truthy(
        os.getenv("PRODUCT_MASTER_SYNC_REQUIRED", "false")
    )

    sheet_id = os.getenv("PRODUCT_MASTER_SHEET_ID")
    sheet_range = os.getenv("PRODUCT_MASTER_SHEET_RANGE", "B:E")
    csv_url = os.getenv("PRODUCT_MASTER_CSV_URL")
    csv_path = os.getenv("PRODUCT_MASTER_CSV_PATH")

    if not sheet_id and not csv_url and not csv_path:
        msg = "Product master sync skipped (no source configured)"
        logging.info(f"[MASTER] {msg}")
        if required:
            raise ValueError("PRODUCT_MASTER_SYNC_REQUIRED is true but no source configured")
        return {"status": "skipped", "reason": "no_source"}

    try:
        if sheet_id:
            src_df, source = _fetch_master_from_sheets(sheet_id, sheet_range)
        elif csv_url:
            src_df, source = _fetch_master_from_csv_url(csv_url)
        else:
            src_df, source = _fetch_master_from_csv_path(csv_path)

        df = _normalize_master_df(src_df)
        if df.empty:
            logging.warning("[MASTER] Source is empty after normalization; skip overwrite")
            if required:
                raise ValueError("Product master is empty")
            return {"status": "skipped", "reason": "empty_master", "source": source}

        table_id = f"{dataset}.{table}"
        if dry_run:
            logging.info(f"[MASTER] Dry run: {len(df)} rows from {source}")
            return {"status": "dry_run", "rows": len(df), "table": table_id, "source": source}

        insert_dataframe(df, table_id, write_disposition="WRITE_TRUNCATE")
        logging.info(f"[MASTER] Synced {len(df)} rows into {table_id} ({source})")
        return {
            "status": "success",
            "rows": len(df),
            "table": table_id,
            "source": source,
        }
    except Exception as e:
        logging.exception("[MASTER] Sync failed")
        if required:
            raise
        return {"status": "error", "error": str(e)}


def _cli() -> None:
    parser = argparse.ArgumentParser(description="Sync product master into BigQuery.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and normalize only; do not write to BigQuery.",
    )
    parser.add_argument(
        "--required",
        action="store_true",
        default=None,
        help="Fail if master cannot be loaded or is empty.",
    )
    parser.add_argument("--dataset", help="Override BQ_DATASET")
    parser.add_argument("--table", help="Override BQ_TABLE_PRODUCT_MASTER_RAW")
    parser.add_argument("--sheet-id", help="Override PRODUCT_MASTER_SHEET_ID")
    parser.add_argument("--sheet-range", help="Override PRODUCT_MASTER_SHEET_RANGE")
    parser.add_argument("--csv-url", help="Override PRODUCT_MASTER_CSV_URL")
    parser.add_argument("--csv-path", help="Override PRODUCT_MASTER_CSV_PATH")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.sheet_id:
        os.environ["PRODUCT_MASTER_SHEET_ID"] = args.sheet_id
    if args.sheet_range:
        os.environ["PRODUCT_MASTER_SHEET_RANGE"] = args.sheet_range
    if args.csv_url:
        os.environ["PRODUCT_MASTER_CSV_URL"] = args.csv_url
    if args.csv_path:
        os.environ["PRODUCT_MASTER_CSV_PATH"] = args.csv_path

    result = sync_product_master(
        dataset=args.dataset,
        table=args.table,
        required=args.required,
        dry_run=args.dry_run,
    )
    print(result)


if __name__ == "__main__":
    _cli()
