#!/usr/bin/env python3
"""13F TSV -> GraphRAG 정규화 가공물 생성.

산출 4종 (poc/data/sec-edgar/ 루트):
  managers.csv     기관(filer) 노드: accession/cik/기관명/주소 (SUBMISSION+COVERPAGE)
  holdings.csv     (기관)-[OWNS]->(종목) 엣지: accession/cusip/발행사/가치/주식수 (INFOTABLE)
  co_managers.csv  (기관)-[CO_MANAGES]-(기관) 엣지 (OTHERMANAGER)
  top_issuers.csv  CUSIP별 보유 기관 수 내림차순 (10-K 수집 대상 선정용)

INFOTABLE 3.27M 행 -> holdings.csv 전체 보존 (그래프 엣지 원천).
top_issuers 는 CUSIP+발행사명 기준 distinct accession(기관) 수 집계.
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
T = HERE / "13f"
csv.field_size_limit(sys.maxsize)


def read_tsv(name):
    f = open(T / name, encoding="utf-8", newline="")
    r = csv.reader(f, delimiter="\t")
    header = next(r)
    idx = {c: i for i, c in enumerate(header)}
    return r, idx, f


def build_managers():
    # SUBMISSION: ACCESSION_NUMBER, FILING_DATE, SUBMISSIONTYPE, CIK, PERIODOFREPORT
    sub = {}
    r, idx, f = read_tsv("SUBMISSION.tsv")
    for row in r:
        if not row:
            continue
        sub[row[idx["ACCESSION_NUMBER"]]] = (
            row[idx["CIK"]],
            row[idx["FILING_DATE"]],
            row[idx["SUBMISSIONTYPE"]],
            row[idx["PERIODOFREPORT"]],
        )
    f.close()

    out = HERE / "managers.csv"
    n = 0
    r, idx, f = read_tsv("COVERPAGE.tsv")
    with open(out, "w", encoding="utf-8", newline="") as o:
        w = csv.writer(o)
        w.writerow([
            "accession_number", "cik", "manager_name", "city",
            "state_or_country", "zipcode", "filing_date",
            "submission_type", "period_of_report",
        ])
        for row in r:
            if not row:
                continue
            acc = row[idx["ACCESSION_NUMBER"]]
            cik, fdate, stype, period = sub.get(acc, ("", "", "", ""))
            w.writerow([
                acc, cik,
                row[idx["FILINGMANAGER_NAME"]],
                row[idx["FILINGMANAGER_CITY"]],
                row[idx["FILINGMANAGER_STATEORCOUNTRY"]],
                row[idx["FILINGMANAGER_ZIPCODE"]],
                fdate, stype, period,
            ])
            n += 1
    f.close()
    print(f"[ok] managers.csv  rows={n}")
    return n


def build_holdings():
    """INFOTABLE -> OWNS 엣지. CUSIP별 (accession set) 동시 집계."""
    out = HERE / "holdings.csv"
    issuer_filers = defaultdict(set)   # cusip -> set(accession)
    issuer_name = {}                   # cusip -> 대표 발행사명
    issuer_value = defaultdict(int)    # cusip -> 총 보유가치 합
    n = 0
    r, idx, f = read_tsv("INFOTABLE.tsv")
    iA = idx["ACCESSION_NUMBER"]
    iN = idx["NAMEOFISSUER"]
    iC = idx["CUSIP"]
    iV = idx["VALUE"]
    iS = idx["SSHPRNAMT"]
    iT = idx["SSHPRNAMTTYPE"]
    iP = idx["PUTCALL"]
    with open(out, "w", encoding="utf-8", newline="") as o:
        w = csv.writer(o)
        w.writerow([
            "accession_number", "cusip", "name_of_issuer",
            "value_usd_thousands", "shares", "shares_type", "put_call",
        ])
        for row in r:
            if not row:
                continue
            acc = row[iA]
            cusip = row[iC].strip()
            name = row[iN].strip()
            try:
                val = int(float(row[iV])) if row[iV] else 0
            except ValueError:
                val = 0
            w.writerow([acc, cusip, name, row[iV], row[iS], row[iT], row[iP]])
            n += 1
            if cusip:
                issuer_filers[cusip].add(acc)
                issuer_value[cusip] += val
                if cusip not in issuer_name and name:
                    issuer_name[cusip] = name
    f.close()
    print(f"[ok] holdings.csv  rows={n}")
    return n, issuer_filers, issuer_name, issuer_value


def build_co_managers():
    """OTHERMANAGER: 한 filing(accession)에 보고된 other manager 들 ->
    같은 accession 의 filing manager 와 CO_MANAGES 엣지.
    accession -> filing manager name 은 COVERPAGE 에서 가져온다.
    """
    fm = {}
    r, idx, f = read_tsv("COVERPAGE.tsv")
    for row in r:
        if not row:
            continue
        fm[row[idx["ACCESSION_NUMBER"]]] = row[idx["FILINGMANAGER_NAME"]]
    f.close()

    out = HERE / "co_managers.csv"
    n = 0
    r, idx, f = read_tsv("OTHERMANAGER.tsv")
    with open(out, "w", encoding="utf-8", newline="") as o:
        w = csv.writer(o)
        w.writerow([
            "accession_number", "filing_manager", "other_manager_cik",
            "other_manager_name", "other_form13f_filenumber",
        ])
        for row in r:
            if not row:
                continue
            acc = row[idx["ACCESSION_NUMBER"]]
            w.writerow([
                acc, fm.get(acc, ""),
                row[idx["CIK"]], row[idx["NAME"]],
                row[idx["FORM13FFILENUMBER"]],
            ])
            n += 1
    f.close()
    print(f"[ok] co_managers.csv  rows={n}")
    return n


def build_top_issuers(issuer_filers, issuer_name, issuer_value):
    rows = []
    for cusip, accs in issuer_filers.items():
        rows.append((
            cusip,
            issuer_name.get(cusip, ""),
            len(accs),
            issuer_value.get(cusip, 0),
        ))
    rows.sort(key=lambda x: (-x[2], -x[3]))
    out = HERE / "top_issuers.csv"
    with open(out, "w", encoding="utf-8", newline="") as o:
        w = csv.writer(o)
        w.writerow(["cusip", "name_of_issuer", "n_filer_managers", "total_value_usd_thousands"])
        for row in rows:
            w.writerow(row)
    print(f"[ok] top_issuers.csv  rows={len(rows)} (distinct CUSIP)")
    return len(rows)


if __name__ == "__main__":
    nm = build_managers()
    nh, ifilers, iname, ival = build_holdings()
    nc = build_co_managers()
    nt = build_top_issuers(ifilers, iname, ival)
    print(f"\nSUMMARY managers={nm} holdings={nh} co_managers={nc} top_issuers={nt}")
