#!/usr/bin/env python3
"""SEC 13F TSV -> GraphRAG 정규화 가공물 생성.

입력: 13f/ 폴더의 SEC Form 13F Q3-2025 데이터셋 TSV
  - SUBMISSION.tsv   (ACCESSION_NUMBER, FILING_DATE, SUBMISSIONTYPE, CIK, PERIODOFREPORT)
  - COVERPAGE.tsv    (filer 이름·주소 등)
  - INFOTABLE.tsv    (보유종목 명세 — OWNS 엣지 원천, 327만 행)
  - OTHERMANAGER.tsv (공동운용 — CO_MANAGES 엣지 원천)

출력 (poc/data/sec-edgar/):
  - managers.csv     기관(filer) 노드
  - holdings.csv     (기관)-[OWNS]->(종목) 엣지
  - co_managers.csv  (기관)-[CO_MANAGES]-(기관) 엣지
  - top_issuers.csv  CUSIP별 보유 기관 수 내림차순 (10-K 대상 결정)

데이터 본체는 퍼블릭 도메인(SEC.gov)이지만 대용량이라 git 미추적.
재현: python3 collect_13f_graph.py
"""
import csv
import json
import os
import sys
from collections import defaultdict

csv.field_size_limit(1 << 24)

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "13f")
OUT = HERE


def read_tsv(name):
    path = os.path.join(SRC, name)
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            yield row


def main():
    stats = {}

    # ── 1. SUBMISSION: accession -> (cik, filing_date, period, type) ──
    sub = {}
    for row in read_tsv("SUBMISSION.tsv"):
        acc = row["ACCESSION_NUMBER"]
        sub[acc] = {
            "cik": row["CIK"],
            "filing_date": row["FILING_DATE"],
            "period": row["PERIODOFREPORT"],
            "submission_type": row["SUBMISSIONTYPE"],
        }
    stats["submission_rows"] = len(sub)

    # ── 2. COVERPAGE: accession -> filer 이름/주소 ──
    cover = {}
    for row in read_tsv("COVERPAGE.tsv"):
        acc = row["ACCESSION_NUMBER"]
        cover[acc] = {
            "manager_name": (row.get("FILINGMANAGER_NAME") or "").strip(),
            "street1": (row.get("FILINGMANAGER_STREET1") or "").strip(),
            "city": (row.get("FILINGMANAGER_CITY") or "").strip(),
            "state_or_country": (row.get("FILINGMANAGER_STATEORCOUNTRY") or "").strip(),
            "zipcode": (row.get("FILINGMANAGER_ZIPCODE") or "").strip(),
            "report_type": (row.get("REPORTTYPE") or "").strip(),
            "is_amendment": (row.get("ISAMENDMENT") or "").strip(),
        }
    stats["coverpage_rows"] = len(cover)

    # ── 3. managers.csv : 기관 노드 (SUBMISSION + COVERPAGE 조인) ──
    # 노드 키는 ACCESSION_NUMBER (한 분기 한 filer 한 제출 = 한 그래프 노드).
    # CIK는 기관 식별자지만 amendment/notice로 한 CIK가 여러 accession 가질 수 있어
    # accession을 노드 PK로, CIK는 속성으로 둔다.
    mpath = os.path.join(OUT, "managers.csv")
    n_mgr = 0
    with open(mpath, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "accession_number", "cik", "manager_name", "city",
            "state_or_country", "zipcode", "filing_date", "period",
            "submission_type", "report_type", "is_amendment",
        ])
        for acc, s in sub.items():
            c = cover.get(acc, {})
            w.writerow([
                acc, s["cik"], c.get("manager_name", ""),
                c.get("city", ""), c.get("state_or_country", ""),
                c.get("zipcode", ""), s["filing_date"], s["period"],
                s["submission_type"], c.get("report_type", ""),
                c.get("is_amendment", ""),
            ])
            n_mgr += 1
    stats["managers_csv_rows"] = n_mgr

    # ── 4. holdings.csv : (기관)-[OWNS]->(종목) 엣지 (INFOTABLE) ──
    #   + top_issuers 집계 동시 수행 (327만 행 1-pass).
    hpath = os.path.join(OUT, "holdings.csv")
    n_hold = 0
    # CUSIP -> {issuer_name, holder_accessions(set), total_value, total_shares}
    iss = defaultdict(lambda: {
        "name": "", "holders": set(), "value": 0, "shares": 0, "rows": 0,
    })
    with open(hpath, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "accession_number", "cik", "manager_name", "cusip",
            "name_of_issuer", "title_of_class", "value_usd",
            "shares_or_principal", "shares_type", "put_call",
            "investment_discretion",
        ])
        for row in read_tsv("INFOTABLE.tsv"):
            acc = row["ACCESSION_NUMBER"]
            s = sub.get(acc)
            c = cover.get(acc, {})
            cik = s["cik"] if s else ""
            mname = c.get("manager_name", "")
            cusip = (row.get("CUSIP") or "").strip()
            issuer = (row.get("NAMEOFISSUER") or "").strip()
            try:
                val = int(float(row.get("VALUE") or 0))
            except ValueError:
                val = 0
            try:
                sh = int(float(row.get("SSHPRNAMT") or 0))
            except ValueError:
                sh = 0
            w.writerow([
                acc, cik, mname, cusip, issuer,
                (row.get("TITLEOFCLASS") or "").strip(), val, sh,
                (row.get("SSHPRNAMTTYPE") or "").strip(),
                (row.get("PUTCALL") or "").strip(),
                (row.get("INVESTMENTDISCRETION") or "").strip(),
            ])
            n_hold += 1
            if cusip:
                e = iss[cusip]
                if not e["name"] and issuer:
                    e["name"] = issuer
                e["holders"].add(acc)
                e["value"] += val
                e["shares"] += sh
                e["rows"] += 1
    stats["holdings_csv_rows"] = n_hold
    stats["distinct_cusip"] = len(iss)

    # ── 5. co_managers.csv : (기관)-[CO_MANAGES]-(기관) 엣지 (OTHERMANAGER) ──
    cpath = os.path.join(OUT, "co_managers.csv")
    n_co = 0
    with open(cpath, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "accession_number", "filer_cik", "filer_manager_name",
            "other_manager_cik", "other_manager_name",
            "other_manager_sk", "form13f_filenumber",
        ])
        for row in read_tsv("OTHERMANAGER.tsv"):
            acc = row["ACCESSION_NUMBER"]
            s = sub.get(acc)
            c = cover.get(acc, {})
            w.writerow([
                acc,
                s["cik"] if s else "",
                c.get("manager_name", ""),
                (row.get("CIK") or "").strip(),
                (row.get("NAME") or "").strip(),
                (row.get("OTHERMANAGER_SK") or "").strip(),
                (row.get("FORM13FFILENUMBER") or "").strip(),
            ])
            n_co += 1
    stats["co_managers_csv_rows"] = n_co

    # ── 6. top_issuers.csv : CUSIP별 보유 기관 수 내림차순 ──
    tpath = os.path.join(OUT, "top_issuers.csv")
    rows = []
    for cusip, e in iss.items():
        rows.append((
            cusip, e["name"], len(e["holders"]), e["rows"],
            e["value"], e["shares"],
        ))
    rows.sort(key=lambda x: (-x[2], -x[4]))
    with open(tpath, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "cusip", "name_of_issuer", "n_holder_filings",
            "n_holding_rows", "total_value_usd", "total_shares",
        ])
        for r in rows:
            w.writerow(r)
    stats["top_issuers_csv_rows"] = len(rows)

    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
