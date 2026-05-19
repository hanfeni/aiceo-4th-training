#!/usr/bin/env python3
"""
build_subset.py — SEC EDGAR 13F 그래프를 강의용 서브셋으로 압축.

배경: 전체 holdings.csv(327만 엣지·221MB)는 GitHub 100MB 하드리밋
초과 → 기존 5도메인처럼 PUBLIC 공개·search-lab raw fetch 불가.
유명 자산운용사만 골라 수십 MB 로 줄여 강의 배포(자기완결) 가능케 함.

핵심 필터:
  1. FAMOUS_MANAGERS 의 기관명을 manager_name 에 부분포함
  2. submission_type 이 13F-HR* (HR = holdings report, 실제 보유내역 보유.
     13F-NT = notice 라 보유 0 → 그래프 엣지 없음, 반드시 제외)
  3. 그 기관들이 보유한 종목(holdings) + 종목 간 공통보유로 자연 연결

산출(서브셋, GitHub 공개 가능 크기):
  managers_subset.csv / holdings_subset.csv /
  co_managers_subset.csv / top_issuers_subset.csv

재현: cd poc/data/sec-edgar && python3 build_subset.py
입력: 같은 폴더의 managers.csv / holdings.csv / co_managers.csv
"""

import csv
import sys
from pathlib import Path

HERE = Path(__file__).parent

# 청중(금융/투자 최다)이 즉시 아는 유명 기관. 대문자 부분일치(대소문자
# 무시). 13F-HR 제출 = 실제 보유내역 있는 것만 결과에 남음.
FAMOUS_MANAGERS = [
    "VANGUARD GROUP",
    "BLACKROCK",
    "STATE STREET",
    "BERKSHIRE HATHAWAY",
    "FMR LLC",  # Fidelity
    "FIDELITY",
    "GOLDMAN SACHS",
    "MORGAN STANLEY",
    "JPMORGAN",
    "JP MORGAN",
    "BANK OF AMERICA",
    "WELLS FARGO",
    "GEODE CAPITAL",
    "RENAISSANCE TECHNOLOGIES",
    "CITADEL ADVISORS",
    "BRIDGEWATER ASSOCIATES",
    "TWO SIGMA",
    "MILLENNIUM MANAGEMENT",
    "POINT72",
    "TIGER GLOBAL",
    "COATUE",
    "BAILLIE GIFFORD",
    "T. ROWE PRICE",
    "T ROWE PRICE",
    "CAPITAL RESEARCH",
    "WELLINGTON MANAGEMENT",
    "INVESCO",
    "CHARLES SCHWAB",
    "NORTHERN TRUST",
    "BNY MELLON",
    "UBS",
    "DEUTSCHE BANK",
    "BARCLAYS",
    "DIMENSIONAL FUND",
    "AQR CAPITAL",
    "DODGE & COX",
    "SOROS FUND",
    "PERSHING SQUARE",
    "THIRD POINT",
    "ELLIOTT",
    "ICAHN",
]


def is_famous(name: str) -> bool:
    up = name.upper()
    return any(fm in up for fm in FAMOUS_MANAGERS)


def main() -> int:
    managers_p = HERE / "managers.csv"
    holdings_p = HERE / "holdings.csv"
    comgr_p = HERE / "co_managers.csv"
    for p in (managers_p, holdings_p):
        if not p.exists():
            print(f"[ERROR] 입력 없음: {p} — collect_13f.py 먼저 실행", file=sys.stderr)
            return 1

    # 1) 유명 + 13F-HR 매니저 선별 (accession_number 가 holdings 조인 키)
    famous_acc: set[str] = set()
    kept_mgr_rows: list[dict] = []
    with managers_p.open(newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        mgr_fields = rd.fieldnames or []
        for row in rd:
            st = (row.get("submission_type") or "").upper()
            if not st.startswith("13F-HR"):
                continue  # NT = 보유 0, 그래프 엣지 없음 → 제외
            if is_famous(row.get("manager_name", "")):
                famous_acc.add(row["accession_number"])
                kept_mgr_rows.append(row)

    if not kept_mgr_rows:
        print("[ERROR] 매칭된 유명 13F-HR 기관 0 — FAMOUS_MANAGERS 확인", file=sys.stderr)
        return 1

    # 2) 그 기관들의 holdings 만 (엣지). 동시에 종목 보유빈도 집계.
    issuer_holders: dict[str, set[str]] = {}
    issuer_name: dict[str, str] = {}
    issuer_value: dict[str, int] = {}
    kept_hold = 0
    with holdings_p.open(newline="", encoding="utf-8") as f, (
        HERE / "holdings_subset.csv"
    ).open("w", newline="", encoding="utf-8") as out:
        rd = csv.DictReader(f)
        wr = csv.DictWriter(out, fieldnames=rd.fieldnames or [])
        wr.writeheader()
        for row in rd:
            if row["accession_number"] not in famous_acc:
                continue
            wr.writerow(row)
            kept_hold += 1
            cusip = row.get("cusip", "")
            if cusip:
                issuer_holders.setdefault(cusip, set()).add(
                    row["accession_number"]
                )
                issuer_name.setdefault(cusip, row.get("name_of_issuer", ""))
                try:
                    issuer_value[cusip] = issuer_value.get(cusip, 0) + int(
                        row.get("value_usd_thousands") or 0
                    )
                except ValueError:
                    pass

    # 3) managers_subset.csv
    with (HERE / "managers_subset.csv").open(
        "w", newline="", encoding="utf-8"
    ) as out:
        wr = csv.DictWriter(out, fieldnames=mgr_fields)
        wr.writeheader()
        wr.writerows(kept_mgr_rows)

    # 4) co_managers_subset.csv (서브셋 매니저 관련 엣지만)
    co_kept = 0
    if comgr_p.exists():
        with comgr_p.open(newline="", encoding="utf-8") as f, (
            HERE / "co_managers_subset.csv"
        ).open("w", newline="", encoding="utf-8") as out:
            rd = csv.DictReader(f)
            wr = csv.DictWriter(out, fieldnames=rd.fieldnames or [])
            wr.writeheader()
            for row in rd:
                if row.get("accession_number") in famous_acc:
                    wr.writerow(row)
                    co_kept += 1

    # 5) top_issuers_subset.csv (서브셋 내 보유빈도 내림차순)
    rows = sorted(
        issuer_holders.items(), key=lambda kv: len(kv[1]), reverse=True
    )
    with (HERE / "top_issuers_subset.csv").open(
        "w", newline="", encoding="utf-8"
    ) as out:
        wr = csv.writer(out)
        wr.writerow(
            ["cusip", "name_of_issuer", "n_filer_managers", "total_value_usd_thousands"]
        )
        for cusip, holders in rows:
            wr.writerow(
                [cusip, issuer_name.get(cusip, ""), len(holders), issuer_value.get(cusip, 0)]
            )

    print("=== SEC EDGAR 강의 서브셋 생성 완료 ===")
    print(f"  유명 13F-HR 기관(노드) : {len(kept_mgr_rows):,}")
    print(f"  보유 엣지(OWNS)        : {kept_hold:,}")
    print(f"  공동운용 엣지          : {co_kept:,}")
    print(f"  종목(issuer) 노드      : {len(issuer_holders):,}")
    if rows:
        print("  상위 보유 종목 Top5:")
        for cusip, holders in rows[:5]:
            print(f"    {issuer_name.get(cusip,''):<28} {len(holders)} 기관")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
