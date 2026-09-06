# -*- coding: utf-8 -*-
"""
MARKET COLLECTOR V14

FIX FOCUS:
- Company/brand is explicitly extracted and saved.
- For black sheet, brand is read from the actual "برند" <td>, not from
  product name/chart metadata.
- Existing rows are repaired by site_product_id/site_product_code when possible.
- Only:
    * Rebar A3 (آجدار)
    * Black sheet / فولاد مبارکه / برش خورده / بنگاه تهران
"""

import re
import os
import sys
import builtins
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

ROOT = Path(__file__).resolve().parent
DB = Path(os.environ.get("PRICE_MONITOR_DB", str(ROOT / "prices.db"))).resolve()
DIAG = Path(os.environ.get("PRICE_MONITOR_DIAG", str(ROOT / "diagnostics_market_v14"))).resolve()
DIAG.mkdir(parents=True, exist_ok=True)

REBAR_URL = "https://ahanonline.com/product-category/میلگرد/قیمت-میلگرد/میلگرد-آجدار/"
BEAM_URL = "https://ahanonline.com/product-category/%D8%AA%DB%8C%D8%B1%D8%A2%D9%87%D9%86-%D9%88-%D9%87%D8%A7%D8%B4/%D8%AA%DB%8C%D8%B1%D8%A2%D9%87%D9%86/"

PROFILE_URL = "https://ahanonline.com/product-category/%D8%A7%D9%86%D9%88%D8%A7%D8%B9-%D9%BE%D8%B1%D9%88%D9%81%DB%8C%D9%84/%D9%BE%D8%B1%D9%88%D9%81%DB%8C%D9%84/"

CHANNEL_URL = "https://ahanonline.com/product-category/%D9%86%D8%A8%D8%B4%DB%8C-%D9%88-%D9%86%D8%A7%D9%88%D8%AF%D8%A7%D9%86%DB%8C/%D9%86%D8%A7%D9%88%D8%AF%D8%A7%D9%86%DB%8C/"

ANGLE_URL = "https://ahanonline.com/product-category/%D9%86%D8%A8%D8%B4%DB%8C-%D9%88-%D9%86%D8%A7%D9%88%D8%AF%D8%A7%D9%86%DB%8C/%D9%86%D8%A8%D8%B4%DB%8C/"

SHEET_URL = "https://ahanonline.com/product-category/انواع-ورق/ورق-سیاه/?brand=فولاد+مبارکه"

CHROME_PATHS = [
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]

TRANS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")



def configure_utf8_console():
    """
    Windows consoles may use cp1252/cp1256 and crash when Persian text is printed.
    Force UTF-8 when possible and fall back to backslash replacement instead of crashing.
    """
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:
            pass

configure_utf8_console()

def safe_print(*args, **kwargs):
    """Safe Windows console output without recursion."""
    try:
        builtins.print(*args, **kwargs)
        return
    except UnicodeEncodeError:
        pass
    except Exception:
        pass

    text = " ".join(str(x) for x in args)
    try:
        data = (text + "\n").encode("utf-8", errors="backslashreplace")
        stream = getattr(sys, "stdout", None)
        if stream is not None and hasattr(stream, "buffer"):
            stream.buffer.write(data)
            stream.buffer.flush()
        elif stream is not None:
            stream.write(text.encode("ascii", errors="backslashreplace").decode("ascii") + "\n")
            stream.flush()
    except Exception:
        pass


def norm(v):
    return re.sub(r"\s+", " ", str(v or "").translate(TRANS)).strip()


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def price_value(v):
    s = norm(v).replace(",", "").replace("٬", "")
    m = re.search(r"\d{4,12}", s)
    if not m:
        return None
    n = int(m.group())
    return n if n >= 1000 else None


def table_columns(conn, table):
    return {r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')}


def ensure_column(conn, table, col, typ="TEXT"):
    if col not in table_columns(conn, table):
        conn.execute(f'ALTER TABLE "{table}" ADD COLUMN "{col}" {typ}')


def migrate_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_key TEXT UNIQUE,
            name TEXT,
            size TEXT,
            grade TEXT,
            rebar_type TEXT,
            brand TEXT,
            factory TEXT,
            location TEXT,
            state TEXT,
            length TEXT,
            unit TEXT,
            site_product_id TEXT,
            site_product_code TEXT,
            source_url TEXT,
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS price_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            price INTEGER,
            price_text TEXT,
            site_update_date TEXT,
            collected_at TEXT,
            source_url TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS collection_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT,
            finished_at TEXT,
            rebar_found INTEGER,
            rebar_valid INTEGER,
            sheet_found INTEGER,
            sheet_valid INTEGER,
            angle_found INTEGER,
            angle_valid INTEGER,
            channel_found INTEGER,
            channel_valid INTEGER,
            profile_found INTEGER,
            profile_valid INTEGER,
            beam_found INTEGER,
            beam_valid INTEGER,
            incomplete_pages INTEGER,
            duplicates INTEGER,
            snapshots_saved INTEGER,
            status TEXT
        )
    """)

    for c, t in [
        ("product_key","TEXT"), ("name","TEXT"), ("size","TEXT"),
        ("grade","TEXT"), ("rebar_type","TEXT"), ("brand","TEXT"),
        ("factory","TEXT"), ("location","TEXT"), ("state","TEXT"),
        ("length","TEXT"), ("unit","TEXT"), ("site_product_id","TEXT"),
        ("site_product_code","TEXT"), ("source_url","TEXT"),
        ("created_at","TEXT")
    ]:
        ensure_column(conn, "products", c, t)

    for c, t in [
        ("product_id","INTEGER"), ("price","INTEGER"), ("price_text","TEXT"),
        ("site_update_date","TEXT"), ("collected_at","TEXT"),
        ("source_url","TEXT")
    ]:
        ensure_column(conn, "price_snapshots", c, t)

    for c, t in [
        ("started_at","TEXT"), ("finished_at","TEXT"),
        ("rebar_found","INTEGER"), ("rebar_valid","INTEGER"),
        ("sheet_found","INTEGER"), ("sheet_valid","INTEGER"),
        ("angle_found","INTEGER"), ("angle_valid","INTEGER"),
        ("channel_found","INTEGER"), ("channel_valid","INTEGER"),
        ("profile_found","INTEGER"), ("profile_valid","INTEGER"),
        ("beam_found","INTEGER"), ("beam_valid","INTEGER"),
        ("incomplete_pages","INTEGER"), ("duplicates","INTEGER"),
        ("snapshots_saved","INTEGER"), ("status","TEXT")
    ]:
        ensure_column(conn, "collection_runs", c, t)

    conn.commit()


def headers(table):
    ths = table.locator("thead th")
    return [norm(ths.nth(i).inner_text()) for i in range(ths.count())]


def header_map(table):
    hs = headers(table)
    mapping = {}
    for i, h in enumerate(hs):
        if h:
            mapping[h] = i
    return hs, mapping


def get_cell_texts(tr):
    cells = tr.locator(":scope > td")
    return [norm(cells.nth(i).inner_text()) for i in range(cells.count())]


def by_header(values, hs, names):
    for name in names:
        for i, h in enumerate(hs):
            if name in h:
                return values[i] if i < len(values) else ""
    return ""


def chart_attrs(tr):
    chart = tr.locator(".table-chart")
    if not chart.count():
        return "", "", ""
    el = chart.first
    return (
        norm(el.get_attribute("data-id")),
        norm(el.get_attribute("data-code")),
        norm(el.get_attribute("data-name")),
    )



def clean_angle_brand(value, chart_name=""):
    """
    Extract a clean company/brand for angle products.
    Examples:
      "آونگان 80*80*8" -> "آونگان"
      "نبشی آونگان 80*80*8" -> "آونگان"
      "نبشی 80*80*8 آونگان" -> "آونگان"  (fallback token scan)
    """
    def tidy(s):
        s = norm(s or "")
        s = re.sub(r"^\s*نبشی\s+", "", s).strip()
        # Remove dimension/thickness expressions wherever they appear.
        s = re.sub(r"\b\d+(?:[.,]\d+)?\s*[*×xX]\s*\d+(?:[.,]\d+)?(?:\s*[*×xX]\s*\d+(?:[.,]\d+)?)?\b", " ", s)
        s = re.sub(r"\b\d+(?:[.,]\d+)?\s*(?:میلی\s*متر|میلیمتر|mm|متری|متر)\b", " ", s, flags=re.I)
        # Remove known non-brand product words.
        s = re.sub(r"\b(?:سبک|سنگین|بال\s*مساوی|بال\s*نامساوی|کارخانه|بنگاه|انبار|شاخه|نبشی)\b", " ", s)
        s = re.sub(r"[\-_/|]+", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    # Best source: actual brand cell.
    candidate = tidy(value)
    if candidate:
        return candidate

    # Fallback: chart/product name.
    s = norm(chart_name or "")
    if not s:
        return ""

    # Common case: text after "نبشی" until first dimension.
    m = re.search(
        r"نبشی\s+(?P<brand>[^\d*×xX]+?)\s+(?=\d+(?:[.,]\d+)?\s*[*×xX])",
        s,
        flags=re.I
    )
    if m:
        candidate = tidy(m.group("brand"))
        if candidate:
            return candidate

    # Another common ordering: dimensions first, company later.
    # Remove dimensions/specs and then keep remaining textual token(s).
    stripped = tidy(s)
    if stripped:
        return stripped

    return ""
def fallback_brand_from_name(name):
    """
    Only a fallback. The primary source is the real 'برند' cell.
    """
    s = norm(name)
    known = [
        "فولاد مبارکه", "ذوب آهن اصفهان", "ذوب‌آهن اصفهان",
        "اکسین اهواز", "فولاد گیلان", "فولاد کاویان",
        "قطعات", "متفرقه", "نورد لوله اهواز"
    ]
    for b in known:
        if b in s:
            return b
    return ""


def extract_table(table, kind, source_url):
    hs, _ = header_map(table)

    thickness = ""
    if kind == "sheet":
        thickness = norm(table.get_attribute("data-value"))
        if not thickness:
            return []

    rows = table.locator("tbody tr")
    result = []

    for ri in range(rows.count()):
        tr = rows.nth(ri)
        values = get_cell_texts(tr)
        if not values:
            continue

        # PRIMARY extraction follows the actual table structure.
        size = by_header(values, hs, ["سایز"])
        row_thickness = by_header(values, hs, ["ضخامت"])
        brand = by_header(values, hs, ["برند", "شرکت", "کارخانه", "تولیدکننده"])
        state = by_header(values, hs, ["حالت"])
        unit = by_header(values, hs, ["واحد"])
        weight = by_header(values, hs, ["وزن"])
        location = by_header(values, hs, ["محل تحویل"])
        update_date = by_header(values, hs, ["تاریخ بروزرسانی", "آخرین بروزرسانی"])
        price_text = by_header(values, hs, ["قیمت"])

        # Rebar pages do NOT have a "برند" column.
        # Their real company/factory is embedded in .table-chart data-name,
        # e.g. "میلگرد 14 ابهر آجدار A3 کارخانه".
        # Do not change the working row/price extraction; only derive brand
        # from the existing chart name for rebar.
        price_el = tr.locator(".product-price[data-price]")
        raw_price = (
            price_el.first.get_attribute("data-price")
            if price_el.count() else ""
        )
        price = price_value(raw_price) or price_value(price_text)
        if price is None:
            continue

        site_id, site_code, chart_name = chart_attrs(tr)

        if kind == "rebar":
            # Actual AhanOnline rebar HTML has no brand <td>.
            # Example from the supplied HTML:
            # "میلگرد 14 ابهر آجدار A3 کارخانه"
            # The company is the token(s) between size and "آجدار".
            m = re.search(
                r"^میلگرد\s+(?P<size>.+?)\s+(?P<brand>.+?)\s+آجدار(?:\s+A[0-9]+)?(?:\s+.*)?$",
                chart_name,
                re.IGNORECASE,
            )
            if m:
                parsed_size = norm(m.group("size"))
                parsed_brand = norm(m.group("brand"))

                # Remove accidental trailing grade/factory words if the site
                # changes the chart-name suffix slightly.
                parsed_brand = re.sub(
                    r"\s+(?:A[0-9]+|کارخانه|بنگاه|انبار)\s*$",
                    "",
                    parsed_brand,
                    flags=re.IGNORECASE,
                ).strip()

                # Use the site's size cell as the authority when available.
                if not size:
                    size = parsed_size
                brand = parsed_brand

            if not brand:
                brand = fallback_brand_from_name(chart_name)

        # For sheet, brand comes from the actual "برند" cell.
        elif not brand:
            brand = fallback_brand_from_name(chart_name)

        if kind == "sheet":
            # Exact requested filters, based on actual cells.
            if brand != "فولاد مبارکه":
                continue
            if state != "برش خورده":
                continue
            if location != "بنگاه تهران":
                continue

            product_type = "ورق سیاه"
            grade = thickness

        elif kind == "angle":
            # Angle page columns are: size / thickness / state / unit / delivery / price.
            # Keep thickness and state as separate DB fields:
            # grade = thickness, state = state.
            if not size or not row_thickness or not state:
                continue
            product_type = "نبشی"
            grade = row_thickness

            # Keep company/brand clean. The site chart name may contain dimensions
            # such as "آونگان 80*80*8"; only "آونگان" belongs in company.
            brand = clean_angle_brand(brand, chart_name)

            # Last fallback: use existing known-brand matcher, but only if it finds something.
            if not brand:
                fallback = fallback_brand_from_name(chart_name)
                if fallback:
                    brand = clean_angle_brand(fallback, chart_name)

        elif kind == "channel":
            if not size or not state or not location:
                continue
            product_type = "ناودانی"
            grade = ""
            table_brand = norm(table.get_attribute("data-value"))
            brand = table_brand or brand or fallback_brand_from_name(chart_name)
            brand = norm(brand)

        elif kind == "profile":
            # Building profile tables are split by brand:
            # table[data-split="brand"][data-value="<brand>"]
            if not size or not row_thickness or not state or not location:
                continue
            product_type = "پروفیل ساختمانی"
            grade = row_thickness

            table_brand = norm(table.get_attribute("data-value"))
            brand = table_brand or brand or fallback_brand_from_name(chart_name)
            brand = norm(brand)

        elif kind == "beam":
            # Beam page HTML:
            # table[data-split="brand"][data-value="<brand>"]
            # columns: size / delivery / unit / weight / price
            if not size or not location or not unit:
                continue
            product_type = "تیرآهن"

            table_brand = norm(table.get_attribute("data-value"))
            brand = table_brand or brand or fallback_brand_from_name(chart_name)
            brand = norm(brand)

            # Standard/length are not dedicated table columns on this page;
            # when present they are embedded in chart data-name, e.g. "12 متری IPE".
            standard = ""
            m_std = re.search(r"(?<![A-Z])(IPE|INP|IPB|HEA|HEB)(?![A-Z])", chart_name or "", re.I)
            if m_std:
                standard = m_std.group(1).upper()

            length_text = ""
            m_len = re.search(r"(\d+(?:[.,]\d+)?)\s*متری", chart_name or "")
            if m_len:
                length_text = norm(m_len.group(1)) + " متری"

            specs = []
            if standard:
                specs.append(f"استاندارد {standard}")
            if length_text:
                specs.append(f"طول {length_text}")
            grade = " | ".join(specs)

        else:
            full = norm(" ".join(values) + " " + chart_name)
            if not re.search(r"(?<![A-Z0-9])A3(?![A-Z0-9])", full, re.I):
                continue

            product_type = "آجدار"
            grade = "A3"

        if not size:
            # Do not guess a size from the product name.
            # If the site row has no size cell, skip it.
            continue

        identity = site_id or site_code
        if identity:
            key_source = f"{kind}|site_id|{identity}"
        else:
            key_source = (
                f"{kind}|{size}|{grade}|{product_type}|"
                f"{brand}|{state}|{location}"
            )

        product_key = hashlib.sha256(
            key_source.encode("utf-8")
        ).hexdigest()

        result.append({
            "product_key": product_key,
            "name": chart_name or f"{product_type} {brand} {size}",
            "size": size,
            "grade": grade,
            "rebar_type": product_type,
            "brand": brand,
            "factory": brand,
            "location": location,
            "state": state,
            "length": "",
            "unit": unit,
            "site_product_id": site_id,
            "site_product_code": site_code,
            "source_url": source_url,
            "price": price,
            "price_text": price_text or norm(price_el.first.inner_text()) if price_el.count() else price_text,
            "site_update_date": update_date,
        })

    return result


def collect_rebar(page):
    page.goto(REBAR_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2500)

    # Keep compatibility with the site's current HTML.
    tables = page.locator("table[data-split='brand']")
    rows = []

    for i in range(tables.count()):
        rows.extend(extract_table(tables.nth(i), "rebar", REBAR_URL))

    return list({r["product_key"]: r for r in rows}.values())


def collect_sheet(page):
    page.goto(SHEET_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3000)

    tables = page.locator("table[data-split='thickness']")
    rows = []

    for i in range(tables.count()):
        rows.extend(extract_table(tables.nth(i), "sheet", SHEET_URL))

    return list({r["product_key"]: r for r in rows}.values())


def collect_beam(page):
    page.goto(BEAM_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3000)

    tables = page.locator('table[data-split="brand"]')
    rows = []

    for i in range(tables.count()):
        table = tables.nth(i)
        try:
            hs = headers(table)
        except Exception:
            continue

        header_text = " | ".join(hs)
        required = ["سایز", "محل تحویل", "واحد", "وزن", "قیمت"]
        if not all(x in header_text for x in required):
            continue

        rows.extend(extract_table(table, "beam", BEAM_URL))

    return list({r["product_key"]: r for r in rows}.values())


def collect_profile(page):
    page.goto(PROFILE_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3000)

    tables = page.locator('table[data-split="brand"]')
    rows = []

    for i in range(tables.count()):
        table = tables.nth(i)
        try:
            hs = headers(table)
        except Exception:
            continue

        header_text = " | ".join(hs)
        required = ["سایز", "ضخامت", "حالت", "محل تحویل", "واحد", "قیمت"]
        if not all(x in header_text for x in required):
            continue

        rows.extend(extract_table(table, "profile", PROFILE_URL))

    return list({r["product_key"]: r for r in rows}.values())


def collect_channel(page):
    page.goto(CHANNEL_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3000)

    tables = page.locator('table[data-split="brand"]')
    rows = []

    for i in range(tables.count()):
        table = tables.nth(i)
        try:
            hs = headers(table)
        except Exception:
            continue

        header_text = " | ".join(hs)
        required = ["سایز", "حالت", "واحد", "محل تحویل", "قیمت"]
        if not all(x in header_text for x in required):
            continue

        rows.extend(extract_table(table, "channel", CHANNEL_URL))

    return list({r["product_key"]: r for r in rows}.values())


def collect_angle(page):
    page.goto(ANGLE_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3000)

    # Do not rely on one data-split value. Select tables by their real headers.
    tables = page.locator("table")
    rows = []
    for i in range(tables.count()):
        table = tables.nth(i)
        try:
            hs = headers(table)
        except Exception:
            continue
        header_text = " | ".join(hs)
        if "سایز" not in header_text or "ضخامت" not in header_text or "حالت" not in header_text or "قیمت" not in header_text:
            continue
        rows.extend(extract_table(table, "angle", ANGLE_URL))

    return list({r["product_key"]: r for r in rows}.values())


def find_existing_product(conn, row):
    # 1) Strongest: actual site product ID.
    if row["site_product_id"]:
        q = conn.execute(
            "SELECT id FROM products WHERE site_product_id=? LIMIT 1",
            (row["site_product_id"],)
        ).fetchone()
        if q:
            return q[0]

    # 2) Site code fallback.
    if row["site_product_code"]:
        q = conn.execute(
            "SELECT id FROM products WHERE site_product_code=? LIMIT 1",
            (row["site_product_code"],)
        ).fetchone()
        if q:
            return q[0]

    # 3) Current product key.
    q = conn.execute(
        "SELECT id FROM products WHERE product_key=? LIMIT 1",
        (row["product_key"],)
    ).fetchone()
    return q[0] if q else None


def save_rows(conn, rows, collected_at):
    cols = table_columns(conn, "products")
    saved = 0
    repaired_brand = 0

    for row in rows:
        if row.get("rebar_type") == "نبشی":
            cleaned = clean_angle_brand(row.get("brand",""), row.get("name",""))
            row["brand"] = cleaned
            row["factory"] = cleaned
        pid = find_existing_product(conn, row)

        if pid is None:
            fields = [
                "product_key","name","size","grade","rebar_type",
                "brand","factory","location","state","length","unit",
                "site_product_id","site_product_code","source_url"
            ]
            fields = [f for f in fields if f in cols]
            if "created_at" in cols:
                fields.append("created_at")

            vals = [row[f] for f in fields if f != "created_at"]
            if "created_at" in fields:
                vals.append(collected_at)

            sql_fields = ", ".join(f'"{f}"' for f in fields)
            marks = ", ".join("?" for _ in fields)

            pid = conn.execute(
                f"INSERT INTO products ({sql_fields}) VALUES ({marks})",
                vals
            ).lastrowid

        else:
            # IMPORTANT: repair brand/company on already existing records.
            old = conn.execute(
                "SELECT brand, factory FROM products WHERE id=?",
                (pid,)
            ).fetchone()

            fields = [
                "product_key","name","size","grade","rebar_type",
                "brand","factory","location","state","length","unit",
                "site_product_id","site_product_code","source_url"
            ]
            fields = [f for f in fields if f in cols]

            assignments = ", ".join(f'"{f}"=?' for f in fields)
            vals = [row[f] for f in fields]
            vals.append(pid)

            conn.execute(
                f"UPDATE products SET {assignments} WHERE id=?",
                vals
            )

            if row["brand"] and (not old or not old[0]):
                repaired_brand += 1

        conn.execute(
            """
            INSERT INTO price_snapshots(
                product_id, price, price_text,
                site_update_date, collected_at, source_url
            )
            VALUES(?,?,?,?,?,?)
            """,
            (
                pid,
                row["price"],
                row["price_text"],
                row["site_update_date"],
                collected_at,
                row["source_url"],
            )
        )
        saved += 1

    conn.commit()
    return saved, repaired_brand


def save_run(conn, started, finished, rebar, sheet, angle, channel, profile, beam, snapshots, status):
    try:
        migrate_db(conn)
        conn.execute(
            """
            INSERT INTO collection_runs(
                started_at, finished_at,
                rebar_found, rebar_valid,
                sheet_found, sheet_valid,
                angle_found, angle_valid,
                channel_found, channel_valid,
                profile_found, profile_valid,
                beam_found, beam_valid,
                incomplete_pages, duplicates,
                snapshots_saved, status
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                started, finished,
                len(rebar), len(rebar),
                len(sheet), len(sheet),
                len(angle), len(angle),
                len(channel), len(channel),
                len(profile), len(profile),
                len(beam), len(beam),
                0, 0,
                snapshots, status
            )
        )
        conn.commit()
        return True
    except Exception as exc:
        try:
            (DIAG / "run_logging_error.txt").write_text(
                repr(exc), encoding="utf-8"
            )
        except Exception:
            pass
        return False



def write_beam_diagnostic(rows):
    lines = []
    for r in rows:
        if r.get("rebar_type") != "تیرآهن":
            continue
        lines.append(" | ".join([
            f"name={r.get('name','')}",
            f"size={r.get('size','')}",
            f"spec={r.get('grade','')}",
            f"brand={r.get('brand','')}",
            f"unit={r.get('unit','')}",
            f"location={r.get('location','')}",
            f"price={r.get('price','')}",
        ]))
    try:
        (DIAG / "beam_products.txt").write_text("\n".join(lines), encoding="utf-8")
    except Exception:
        pass


def write_profile_diagnostic(rows):
    lines = []
    for r in rows:
        if r.get("rebar_type") != "پروفیل ساختمانی":
            continue
        lines.append(" | ".join([
            f"name={r.get('name','')}",
            f"size={r.get('size','')}",
            f"thickness={r.get('grade','')}",
            f"state={r.get('state','')}",
            f"brand={r.get('brand','')}",
            f"unit={r.get('unit','')}",
            f"location={r.get('location','')}",
            f"price={r.get('price','')}",
            f"update={r.get('site_update_date','')}",
        ]))
    try:
        (DIAG / "profile_products.txt").write_text("\n".join(lines), encoding="utf-8")
    except Exception:
        pass


def write_channel_diagnostic(rows):
    lines = []
    for r in rows:
        if r.get("rebar_type") != "ناودانی":
            continue
        lines.append(" | ".join([
            f"name={r.get('name','')}",
            f"size={r.get('size','')}",
            f"state={r.get('state','')}",
            f"brand={r.get('brand','')}",
            f"unit={r.get('unit','')}",
            f"location={r.get('location','')}",
            f"price={r.get('price','')}",
            f"update={r.get('site_update_date','')}",
        ]))
    try:
        (DIAG / "channel_products.txt").write_text("\n".join(lines), encoding="utf-8")
    except Exception:
        pass


def write_angle_diagnostic(rows):
    lines = []
    for r in rows:
        if r.get("rebar_type") != "نبشی":
            continue
        lines.append(
            " | ".join([
                f"name={r.get('name','')}",
                f"size={r.get('size','')}",
                f"thickness={r.get('grade','')}",
                f"state={r.get('state','')}",
                f"brand={r.get('brand','')}",
                f"location={r.get('location','')}",
                f"price={r.get('price','')}",
            ])
        )
    try:
        (DIAG / "angle_products.txt").write_text("\n".join(lines), encoding="utf-8")
    except Exception:
        pass


def write_brand_diagnostic(rows):
    """
    Makes it easy to verify what was actually extracted without opening DB.
    """
    lines = []
    for r in rows:
        lines.append(
            " | ".join([
                r["rebar_type"],
                f"size={r['size']}",
                f"grade={r['grade']}",
                f"brand={r['brand']}",
                f"state={r['state']}",
                f"location={r['location']}",
                f"site_id={r['site_product_id']}",
                f"price={r['price']}",
            ])
        )
    (DIAG / "extracted_products.txt").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def report_error(code, reason, details=""):
    msg = f"ERROR_CODE: {code}\nERROR_REASON: {reason}"
    if details:
        msg += f"\nERROR_DETAILS: {details}"
    try:
        (DIAG / "last_error.txt").write_text(msg, encoding="utf-8")
    except Exception:
        pass
    safe_print(msg)


def main():
    chrome = next(
        (p for p in CHROME_PATHS if Path(p).exists()),
        None
    )
    if not chrome:
        report_error("CHROME_NOT_FOUND", "Google Chrome روی سیستم پیدا نشد.", "Chrome را نصب کنید یا مسیر آن را در Collector تنظیم کنید.")
        return 2

    conn = sqlite3.connect(DB)
    migrate_db(conn)
    started = now()

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                executable_path=chrome,
                headless=False
            )
            context = browser.new_context(
                locale="fa-IR",
                viewport={"width": 1440, "height": 950}
            )
            page = context.new_page()

            try:
                safe_print("Collecting rebar A3 with company/brand...")
                rebar = collect_rebar(page)

                safe_print(
                    "Collecting black sheet with company/brand: "
                    "Mobarakeh / cut / Tehran..."
                )
                sheet = collect_sheet(page)

                safe_print("Collecting angle (نبشی)...")
                angle = collect_angle(page)

                safe_print("Collecting channel (ناودانی)...")
                channel = collect_channel(page)

                safe_print("Collecting building profile (پروفیل ساختمانی)...")
                profile = collect_profile(page)

                safe_print("Collecting beam (تیرآهن)...")
                beam = collect_beam(page)

                missing = []
                if not rebar: missing.append("میلگرد A3")
                if not sheet: missing.append("ورق سیاه")
                if not angle: missing.append("نبشی")
                if not channel: missing.append("ناودانی")
                if not profile: missing.append("پروفیل ساختمانی")
                if not beam: missing.append("تیرآهن")
                if missing:
                    reason = "داده معتبر برای این بخش‌ها پیدا نشد: " + "، ".join(missing)
                    report_error("EMPTY_DATA", reason, "هیچ داده‌ای در دیتابیس ذخیره نشد.")
                    return 1

            except PlaywrightTimeoutError as exc:
                try:
                    page.screenshot(
                        path=str(DIAG / "timeout.png"),
                        full_page=True
                    )
                    (DIAG / "timeout.html").write_text(
                        page.content(), encoding="utf-8"
                    )
                except Exception:
                    pass
                report_error("TIMEOUT", "مهلت بارگذاری صفحه یا جدول سایت تمام شد.", repr(exc))
                return 1

            except Exception as exc:
                try:
                    page.screenshot(
                        path=str(DIAG / "fatal.png"),
                        full_page=True
                    )
                    (DIAG / "fatal.html").write_text(
                        page.content(), encoding="utf-8"
                    )
                except Exception:
                    pass
                report_error("COLLECTOR_EXCEPTION", "خطای غیرمنتظره هنگام خواندن سایت رخ داد.", repr(exc))
                return 1

            finally:
                try:
                    browser.close()
                except Exception:
                    pass

        all_rows = rebar + sheet + angle + channel + profile + beam
        write_brand_diagnostic(all_rows)
        write_angle_diagnostic(all_rows)
        write_channel_diagnostic(all_rows)
        write_profile_diagnostic(all_rows)
        write_beam_diagnostic(all_rows)

        collected_at = now()
        snapshots, repaired_brand = save_rows(
            conn, all_rows, collected_at
        )

        status = "OK" if rebar and sheet and angle and channel and profile and beam else "ERROR"
        run_logged = save_run(
            conn, started, now(),
            rebar, sheet, angle, channel, profile, beam, snapshots, status
        )

        safe_print()
        safe_print("========== MARKET V14 RESULT ==========")
        safe_print(f"Rebar A3 products:                  {len(rebar)}")
        safe_print(
            "Black sheet cut Mobarakeh Tehran: "
            f"{len(sheet)}"
        )
        safe_print(f"Angle products (نبشی):               {len(angle)}")
        safe_print(f"Channel products (ناودانی):          {len(channel)}")
        safe_print(f"Profile products (پروفیل ساختمانی): {len(profile)}")
        safe_print(f"Beam products (تیرآهن):              {len(beam)}")
        rebar_with_brand = sum(1 for r in rebar if r["brand"])
        sheet_with_brand = sum(1 for r in sheet if r["brand"])
        safe_print(f"Rebar with company/brand:            {rebar_with_brand}/{len(rebar)}")
        safe_print(f"Sheet with company/brand:            {sheet_with_brand}/{len(sheet)}")
        safe_print(f"Products with company/brand:         {sum(1 for r in all_rows if r['brand'])}/{len(all_rows)}")
        safe_print(f"Existing rows repaired with brand:  {repaired_brand}")
        safe_print(f"Total products saved:                {len(all_rows)}")
        safe_print(f"Snapshots saved:                     {snapshots}")
        safe_print(f"Run log saved:                       {'YES' if run_logged else 'NO'}")
        safe_print(f"Brand diagnostic:                    {DIAG / 'extracted_products.txt'}")
        safe_print(f"Database:                            {DB}")
        safe_print(f"Diagnostics:                         {DIAG}")
        safe_print(f"Status:                              {status}")
        safe_print("=======================================")

        return 0 if status == "OK" else 1

    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
