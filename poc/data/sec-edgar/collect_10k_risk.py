#!/usr/bin/env python3
"""top_issuers.csv 상위 N개 발행사 -> 최신 10-K Risk Factors(Item 1A) 추출.

매핑 경로 (CUSIP↔CIK 직접 매핑은 SEC 무료 제공 없음):
  top_issuers 발행사명 (13F NAMEOFISSUER, 예 'MICROSOFT CORP COM')
    -> 정규화(접미사 COM/CL A/INC 등 제거)
    -> company_tickers.json title 정규화 매칭 -> CIK
  -> data.sec.gov/submissions/CIK{10}.json 최신 10-K accession
  -> Archives 인덱스 -> 1차 문서(.htm) -> Item 1A(Risk Factors) 텍스트 추출

출력: tenk_risk.jsonl  {cik, ticker, company, cusip, issuer_13f,
                        accession, form, fiscal_year, filed, risk_text, char_count}

SEC.gov rate limit 준수: 요청 간 sleep, User-Agent 필수.
재현: python3 collect_10k_risk.py [TOP_N]
"""
import csv
import html
import json
import os
import re
import sys
import time
import urllib.request

csv.field_size_limit(1 << 24)

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "aiceo-4th-training-lecture dhkim@medicnc.co.kr"
TOP_N = int(sys.argv[1]) if len(sys.argv) > 1 else 30

# 13F 발행사명 접미사 — 정규화 시 제거
SUFFIX = re.compile(
    r"\b("
    r"COM|COMMON|CL\s*[A-Z]|CLASS\s*[A-Z]|INC|CORP|CORPORATION|CO|LTD|"
    r"PLC|LP|HLDG|HLDGS|HOLDING|HOLDINGS|GROUP|GRP|NEW|DEL|CAP\s*STK|"
    r"STK|SHS|ADR|ADS|SPONSORED|THE|TR|TRUST|ETF|FD|FUND|NV|SA|AG"
    r")\b",
    re.I,
)
NONALNUM = re.compile(r"[^a-z0-9]+")


def norm(name):
    s = name.upper()
    s = re.sub(r"&", " AND ", s)
    s = SUFFIX.sub(" ", s)
    s = NONALNUM.sub(" ", s.lower()).strip()
    return re.sub(r"\s+", " ", s)


def http(url, timeout=30, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", UA)
            req.add_header("Accept-Encoding", "gzip, deflate")
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                enc = r.headers.get("Content-Encoding", "")
                if enc == "gzip":
                    import gzip
                    raw = gzip.decompress(raw)
                elif enc == "deflate":
                    import zlib
                    raw = zlib.decompress(raw)
                return r.status, raw
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return 404, b""
            time.sleep(1.5 * (i + 1))
        except Exception:
            time.sleep(1.5 * (i + 1))
    return 0, b""


def build_ticker_index():
    """company_tickers.json -> {normalized_title: (cik, ticker, title)}.
    중복 정규화 키는 첫 항목 유지(파일 순서 = SEC 내부 순)."""
    d = json.load(open(os.path.join(HERE, "company_tickers.json")))
    idx = {}
    for v in d.values():
        cik = str(v["cik_str"]).zfill(10)
        t = v["title"]
        k = norm(t)
        if k and k not in idx:
            idx[k] = (cik, v["ticker"], t)
    return idx


TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"[ \t ]+")
NL = re.compile(r"\n{3,}")


def strip_html(raw):
    txt = raw
    txt = re.sub(r"(?is)<(script|style|head)[^>]*>.*?</\1>", " ", txt)
    txt = re.sub(r"(?i)<br\s*/?>", "\n", txt)
    txt = re.sub(r"(?i)</(p|div|tr|li|h[1-6]|table)>", "\n", txt)
    txt = TAG.sub(" ", txt)
    txt = html.unescape(txt)
    txt = WS.sub(" ", txt)
    txt = NL.sub("\n\n", txt)
    return txt.strip()


# Item 1A. Risk Factors -> Item 1B/Item 2 사이 텍스트
ITEM1A = re.compile(
    r"item[\s ]*1a[\s\.\:—\-]*risk\s+factors", re.I
)
ITEM_NEXT = re.compile(
    r"item[\s ]*1b[\s\.\:—\-]|"
    r"item[\s ]*2[\s\.\:—\-]*propert", re.I
)


def extract_risk(text):
    """본문 텍스트에서 Item 1A 섹션 추출. 목차의 첫 매치는 건너뛰기 위해
    가장 긴 (1A start -> next item) 구간을 채택."""
    starts = [m.start() for m in ITEM1A.finditer(text)]
    if not starts:
        return ""
    best = ""
    for st in starts:
        tail = text[st:]
        nm = ITEM_NEXT.search(tail, 200)  # 200자 이후부터 종료 탐색
        seg = tail[: nm.start()] if nm else tail[:200000]
        if len(seg) > len(best):
            best = seg
    return best.strip()


def latest_10k(cik):
    """submissions JSON -> 가장 최근 10-K accession/primaryDoc/filed."""
    st, raw = http(f"https://data.sec.gov/submissions/CIK{cik}.json")
    if st != 200:
        return None
    try:
        j = json.loads(raw)
    except Exception:
        return None
    rec = j.get("filings", {}).get("recent", {})
    forms = rec.get("form", [])
    accs = rec.get("accessionNumber", [])
    docs = rec.get("primaryDocument", [])
    dates = rec.get("filingDate", [])
    for i, fm in enumerate(forms):
        if fm == "10-K":
            return {
                "accession": accs[i],
                "primary_doc": docs[i],
                "filed": dates[i],
            }
    return None


def main():
    idx = build_ticker_index()
    rows = list(csv.DictReader(open(os.path.join(HERE, "top_issuers.csv"))))

    out = os.path.join(HERE, "tenk_risk.jsonl")
    stats = {
        "attempted": 0, "name_mapped": 0, "name_unmapped": 0,
        "no_10k": 0, "fetch_fail": 0, "no_risk_section": 0, "saved": 0,
        "char_counts": [],
    }
    unmapped = []
    seen_cik = set()

    with open(out, "w", encoding="utf-8") as fo:
        for r in rows:
            if stats["saved"] >= TOP_N:
                break
            stats["attempted"] += 1
            issuer = r["name_of_issuer"]
            cusip = r["cusip"]
            k = norm(issuer)
            hit = idx.get(k)
            if not hit:
                # 부분 매칭 폴백: 정규화 토큰 첫 2어절 일치
                toks = k.split()
                if toks:
                    pref = " ".join(toks[:2])
                    cand = [v for kk, v in idx.items()
                            if kk == pref or kk.startswith(pref + " ")]
                    if len(cand) == 1:
                        hit = cand[0]
            if not hit:
                stats["name_unmapped"] += 1
                unmapped.append(issuer)
                continue
            cik, ticker, title = hit
            if cik in seen_cik:
                continue  # 같은 기업 중복(클래스주 GOOGL/GOOG 등) 스킵
            stats["name_mapped"] += 1

            f10 = latest_10k(cik)
            time.sleep(0.4)
            if not f10:
                stats["no_10k"] += 1
                seen_cik.add(cik)
                continue

            acc_nodash = f10["accession"].replace("-", "")
            doc_url = (
                f"https://www.sec.gov/Archives/edgar/data/"
                f"{int(cik)}/{acc_nodash}/{f10['primary_doc']}"
            )
            st, raw = http(doc_url)
            time.sleep(0.4)
            if st != 200 or not raw:
                stats["fetch_fail"] += 1
                seen_cik.add(cik)
                continue
            text = strip_html(raw.decode("utf-8", errors="replace"))
            risk = extract_risk(text)
            if len(risk) < 500:
                stats["no_risk_section"] += 1
                seen_cik.add(cik)
                continue

            fy = ""
            m = re.search(r"(20\d{2})", f10["filed"])
            if m:
                fy = m.group(1)
            rec = {
                "cik": cik,
                "ticker": ticker,
                "company": title,
                "cusip": cusip,
                "issuer_13f": issuer,
                "accession": f10["accession"],
                "form": "10-K",
                "fiscal_year": fy,
                "filed": f10["filed"],
                "risk_text": risk[:120000],
                "char_count": len(risk[:120000]),
            }
            fo.write(json.dumps(rec, ensure_ascii=False) + "\n")
            stats["saved"] += 1
            stats["char_counts"].append(rec["char_count"])
            seen_cik.add(cik)
            print(f"[{stats['saved']:>3}/{TOP_N}] {ticker:<6} "
                  f"{title[:38]:<38} risk={rec['char_count']:>7}c")

    cc = stats.pop("char_counts")
    stats["risk_char_min"] = min(cc) if cc else 0
    stats["risk_char_max"] = max(cc) if cc else 0
    stats["risk_char_avg"] = round(sum(cc) / len(cc)) if cc else 0
    stats["unmapped_sample"] = unmapped[:15]
    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
