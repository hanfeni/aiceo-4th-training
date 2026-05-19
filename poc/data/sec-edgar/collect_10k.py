#!/usr/bin/env python3
"""top_issuers.csv 상위 N개 발행사 -> 최신 10-K Risk Factors(Item 1A) 추출.

CUSIP -> CIK 직접 매핑은 SEC 공개 무인증 소스에 없음(상용 DB 필요).
대안: 13F name_of_issuer 를 정규화해 company_tickers.json title 과
이름 매칭 -> CIK 확보 -> data.sec.gov/submissions/CIK{10}.json 에서
최신 10-K accession -> 1차 문서 HTML -> Item 1A(Risk Factors) 본문 추출.

SEC.gov 는 User-Agent 필수. rate limit -> 요청 간 sleep 0.3s.
산출: tenk_risk.jsonl {cik,ticker,company,cusip,fiscal_year,risk_text,...}
"""
import csv
import json
import re
import subprocess
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

KST = timezone(timedelta(hours=9))
UA = "aiceo-4th-training-lecture dhkim@medicnc.co.kr"
HERE = Path(__file__).parent
TOP_N = 55                       # 상위 55개 시도 (ETF 4~6개는 10-K 없음)
OUT = HERE / "tenk_risk.jsonl"
SLEEP = 0.34                     # SEC 초당 ~3건 (10건 한도 내 안전)


def curl(url, max_time=40):
    p = subprocess.run(
        ["curl", "-sS", "-L", "-A", UA, url, "--max-time", str(max_time)],
        capture_output=True, timeout=max_time + 10,
    )
    return p.stdout.decode("utf-8", "ignore")


# 13F 발행사명 접미어 노이즈 (COM / CL A / CORP DEL NEW ...) 제거용
SUFFIX = re.compile(
    r"\b(COM|COMMON|STK|CAP|CL\s*[A-Z]|CLASS\s*[A-Z]|SHS|NEW|DEL|"
    r"INC|CORP|CORPORATION|CO|LTD|PLC|HLDGS?|HOLDINGS?|GROUP|"
    r"THE|& ?CO|AND ?CO|SER(IES)?\s*[A-Z0-9]*|TR(UST)?|ETF|FD)\b",
    re.I,
)


def norm(name):
    s = name.upper()
    s = re.sub(r"[.,/&'’\-()]", " ", s)
    s = SUFFIX.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def load_tickers():
    d = json.load(open(HERE / "company_tickers.json"))
    by_norm = {}
    for v in d.values():
        n = norm(v["title"])
        by_norm.setdefault(n, v)            # 첫 매칭 우선
        first = n.split(" ")[0]
        if first and len(first) >= 4:
            by_norm.setdefault("__pfx__" + first, v)
        by_norm["__ticker__" + v["ticker"]] = v
    return by_norm


# 정규화로도 안 잡히는 알려진 발행사 -> ticker 별칭 (수동, 검증된 것만)
ALIAS = {
    "ELI LILLY": "LLY",
    "DISNEY WALT": "DIS",
    "BERKSHIRE HATHAWAY": "BRK-B",
    "EXXON MOBIL": "XOM",
    "COSTCO WHSL": "COST",
    "MCDONALDS": "MCD",
    "MICROSOFT": "MSFT",
}


def match_cik(issuer_name, table):
    key = norm(issuer_name)
    if key in table:
        return table[key]
    # 첫 토큰 prefix 매칭 (MICROSOFT, NVIDIA 등 단일 토큰 브랜드)
    first = key.split(" ")[0] if key else ""
    if first and "__pfx__" + first in table:
        return table["__pfx__" + first]
    # 수동 별칭 (정규화 한계 보정)
    for alias_prefix, tk in ALIAS.items():
        if key.startswith(alias_prefix):
            t = table.get("__ticker__" + tk)
            if t:
                return t
    return None


def latest_10k(cik):
    cik10 = str(int(cik)).zfill(10)
    j = curl(f"https://data.sec.gov/submissions/CIK{cik10}.json")
    try:
        d = json.loads(j)
    except json.JSONDecodeError:
        return None
    recent = d.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    accs = recent.get("accessionNumber", [])
    docs = recent.get("primaryDocument", [])
    dates = recent.get("reportDate", [])
    for i, f in enumerate(forms):
        if f == "10-K":
            acc = accs[i].replace("-", "")
            return {
                "accession": accs[i],
                "doc": docs[i],
                "report_date": dates[i] if i < len(dates) else "",
                "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{docs[i]}",
            }
    return None


# iXBRL 인라인 파일은 단어 중간에 태그가 끼어 평문화 시 'RIS K FACTORS'
# 처럼 글자 사이 공백이 생긴다. 헤딩 토큰을 글자-사이-공백 허용 패턴으로.
def _loose(word):
    return r"\s*".join(re.escape(c) for c in word)


HDR_1A = re.compile(
    r"Item\s*1A\s*[.\-:]?\s*" + _loose("RISK") + r"\s*" + _loose("FACTORS"),
    re.I,
)
HDR_END = re.compile(
    r"Item\s*1B\s*[.\-:]?\s*" + _loose("UNRESOLVED")
    + r"|Item\s*2\s*[.\-:]?\s*" + _loose("PROPERTIES")
    + r"|Item\s*1C\s*[.\-:]?\s*" + _loose("CYBERSECURITY"),
    re.I,
)


def extract_risk(html):
    """Item 1A Risk Factors ~ Item 1B/1C/2 사이 평문 (iXBRL 인라인 대응)."""
    import html as ihtml

    txt = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    txt = re.sub(r"<style[\s\S]*?</style>", " ", txt, flags=re.I)
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = ihtml.unescape(txt)
    txt = re.sub(r"\s+", " ", txt)

    starts = list(HDR_1A.finditer(txt))
    if not starts or all(
        re.match(r"^[\d,\.\s\-–KAB]{0,12}(Item\s*1[BC]|Page\s*\d)", txt[m.end(): m.end() + 60].lstrip(" ."), re.I)
        for m in starts
    ):
        # Fallback: 'Item 1A' 라벨 없이 'RISK FACTORS' 본문 헤딩만 쓰는 파일
        # (예: McDonald's). 대문자 헤딩 + 직후 'Cautionary'/문장 시작.
        alt = list(re.finditer(
            r"\bRISK FACTORS\b\s+(Cautionary|Our business|The following|"
            r"You should|We are subject|Investing|Set forth below)",
            txt,
        ))
        if alt:
            b = alt[0].start()
            em = HDR_END.search(txt[b:])
            if not em:
                em = re.search(
                    r"\b(Cybersecurity|Legal Proceedings|Properties)\b",
                    txt[b + 2000:],
                )
                e = (b + 2000 + em.start()) if em else min(len(txt), b + 120000)
            else:
                e = b + em.start()
            return txt[b:e].strip()
    if not starts:
        return ""

    # 각 헤딩 후보를 점수화해 '본문 시작'을 고른다.
    #  - TOC/목차: 헤딩 직후 페이지번호·점선리더(. . 9), 또는 곧장 Item 1B 가 옴
    #  - 교차참조 문장: "...refer to Item 1A. Risk Factors in this Form 10-K..." (앞에 소문자)
    #  - 본문: 헤딩 후 다음 종료헤딩(1B/1C/2)까지 거리가 가장 길다
    best = None
    best_len = -1
    for m in starts:
        s = m.end()
        after = txt[s: s + 60].lstrip(" .")
        # TOC: 숫자/점선리더로 시작하거나 바로 Item 1B 로 이어짐
        if re.match(r"^[\d,\.\s\-–KAB]{0,12}Item\s*1[BC]", after, re.I):
            continue
        if re.match(r"^[\dKAB\-–]{1,8}\s", after):
            continue
        em = HDR_END.search(txt[s:])
        seg = em.start() if em else (len(txt) - s)
        # 교차참조(앞 60자에 소문자 문장 + 'refer'/'see'/'in this Form') 감점
        before = txt[max(0, m.start() - 80): m.start()].lower()
        xref = bool(re.search(r"(refer to|see|described in|set forth in|pages?)\s*$", before))
        score = seg - (10_000 if xref else 0)
        if score > best_len:
            best_len = score
            best = s
    if best is None:
        best = starts[-1].end()

    em = HDR_END.search(txt[best:])
    e = best + em.start() if em else min(len(txt), best + 120000)
    out = txt[best:e].strip()
    # 'RIS K' 류 단어내 공백은 검색 토큰화에 영향 적어 원문 유지
    return out


def main():
    table = load_tickers()
    rows = []
    with open(HERE / "top_issuers.csv", encoding="utf-8", newline="") as f:
        rdr = csv.reader(f)
        next(rdr)                       # header
        for rec in rdr:                 # cusip,name_of_issuer,n_filer_managers,total_value
            if len(rec) < 4:
                continue
            rows.append((rec[0], rec[1]))
            if len(rows) >= TOP_N:
                break

    out_f = open(OUT, "w", encoding="utf-8")
    ok = 0
    miss = []
    seen_cik = set()                 # CIK 중복 제거 (Alphabet A/C 등)
    for cusip, issuer in rows:
        m = match_cik(issuer, table)
        if not m:
            miss.append((cusip, issuer, "no-name-match"))
            continue
        if m["cik_str"] in seen_cik:
            miss.append((cusip, issuer, f"dup-cik({m['ticker']})"))
            continue
        seen_cik.add(m["cik_str"])
        time.sleep(SLEEP)
        fil = latest_10k(m["cik_str"])
        if not fil:
            miss.append((cusip, issuer, "no-10K"))
            continue
        time.sleep(SLEEP)
        html = curl(fil["url"], max_time=60)
        risk = extract_risk(html)
        if len(risk) < 500:
            miss.append((cusip, issuer, f"risk-too-short({len(risk)})"))
            continue
        fy = fil["report_date"][:4] if fil["report_date"] else ""
        doc = {
            "doc_id": f"tenk_{m['ticker']}",
            "cik": int(m["cik_str"]),
            "ticker": m["ticker"],
            "company": m["title"],
            "cusip": cusip,
            "issuer_13f_name": issuer,
            "fiscal_year": fy,
            "accession": fil["accession"],
            "source_url": fil["url"],
            "risk_text": risk[:120000],
            "char_count": len(risk),
            "collected_at": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S %Z%z"),
        }
        out_f.write(json.dumps(doc, ensure_ascii=False) + "\n")
        out_f.flush()
        ok += 1
        print(f"[ok {ok}] {m['ticker']:6s} {m['title'][:40]:40s} risk={len(risk):>7d} chars")
    out_f.close()

    print(f"\nDONE mapped/collected={ok}/{TOP_N}  missed={len(miss)}")
    for c, n, why in miss:
        print(f"  MISS {c} {n[:40]:40s} -> {why}")


if __name__ == "__main__":
    main()
