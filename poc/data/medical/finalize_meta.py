#!/usr/bin/env python3
"""수집 완료 후 _collect_meta.json 생성 + 최종 검증 리포트 출력."""
import json, csv, statistics, datetime, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
JL = os.path.join(BASE, "drug_detail.jsonl")
CSVP = os.path.join(BASE, "drug_master_sample.csv")
RUNLOG = os.path.join(BASE, "collect_run.log")

# --- drug_detail.jsonl 통계 ---
docs = []
with open(JL, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            docs.append(json.loads(line))

ccs = [d["char_count"] for d in docs]
etc = {}
for d in docs:
    k = (d.get("etc_otc") or "").strip() or "(미상)"
    etc[k] = etc.get(k, 0) + 1
pro = sum(v for k, v in etc.items() if "전문" in k)
with_base = sum(1 for d in docs if (d.get("item_base_code") or "").strip())

def pct(p):
    s = sorted(ccs)
    if not s:
        return 0
    i = min(len(s) - 1, int(len(s) * p))
    return s[i]

# --- run log 통계 ---
stats_line = ""
blocked = too_short = 0
if os.path.exists(RUNLOG):
    txt = open(RUNLOG, encoding="utf-8", errors="replace").read()
    m = re.search(r"STATS=(\{.*\})", txt)
    if m:
        stats_line = m.group(1)
    blocked = len(re.findall(r"BLOCKED", txt))

run_stats = json.loads(stats_line) if stats_line else {}

# --- drug_master_sample.csv 통계 ---
with open(CSVP, encoding="utf-8") as f:
    r = csv.reader(f)
    hdr = next(r)
    mrows = list(r)
mcols = len(hdr)
base_idx = hdr.index("품목기준코드")
csv_base = set(x[base_idx].strip() for x in mrows if x[base_idx].strip())

# JOIN 가능 검증
join_hits = [d for d in docs
             if (d.get("item_base_code") or "").strip() in csv_base]

now = datetime.datetime.now(
    datetime.timezone(datetime.timedelta(hours=9))).isoformat()

meta = {
    "generated_at": now,
    "purpose": "서울대 AI CEO 4기 강의(2026-05-22) RAG/임베딩 실습용 "
               "의료/제약 도메인 샘플 데이터 (전부 실제 수집, 시뮬레이션 없음)",
    "structured_dataset": {
        "file": "drug_master_sample.csv",
        "source_name": "건강보험심사평가원_약가마스터_의약품표준코드_20251031",
        "source_page": "https://www.data.go.kr/data/15067462/fileData.do",
        "direct_link": "https://www.data.go.kr/cmm/cmm/fileDownload.do"
                       "?atchFileId=FILE_000000003550228"
                       "&fileDetailSn=1&insertDataPrcus=N",
        "atch_file_id": "FILE_000000003550228",
        "atch_file_id_still_valid": True,
        "fallback_if_expired": "data.go.kr/data/15067462/fileData.do HTML의 "
                               "schema.org contentUrl에서 최신 FILE_xxx 재추출",
        "original_encoding": "EUC-KR",
        "converted_encoding": "UTF-8 (iconv -f EUC-KR -t UTF-8)",
        "original_rows": 305522,
        "original_size_bytes": 54880067,
        "sample_rows": len(mrows),
        "sample_columns": mcols,
        "sampling_method": "1/15 systematic sampling (tail -n+2 | awk NR%15==1)",
        "columns": hdr,
        "dataset_reference_date": "2025-10-31",
        "dataset_registered": "2025-11-04",
        "dataset_modified": "2025-12-01",
        "license": "공공누리 제1유형 (출처표시) — 출처: 건강보험심사평가원",
    },
    "search_documents": {
        "file": "drug_detail.jsonl",
        "source": "식약처 의약품안전나라 nedrug.mfds.go.kr (무인증)",
        "search_endpoint": "POST https://nedrug.mfds.go.kr/searchDrug "
                           "(etcOtcCode=02 = 전문의약품 필터)",
        "body_endpoint": "GET /pbp/cmn/html/drb/<itemSeq>/{EE,UD,NB} "
                         "(EE=효능효과, UD=용법용량, NB=사용상의주의사항)",
        "detail_url_template":
            "https://nedrug.mfds.go.kr/pbp/CCBBB01/getItemDetail"
            "?itemSeq=<itemSeq>",
        "filter": "전문의약품 위주 + 본문 char_count >= 2000",
        "itemseq_pool": run_stats.get("itemseq_collected"),
        "detail_attempts": run_stats.get("detail_attempts"),
        "doc_count": len(docs),
        "min_target": 80,
        "goal_target": 300,
        "min_target_met": len(docs) >= 80,
        "char_count_min": min(ccs) if ccs else 0,
        "char_count_avg": round(statistics.mean(ccs), 1) if ccs else 0,
        "char_count_median": int(statistics.median(ccs)) if ccs else 0,
        "char_count_max": max(ccs) if ccs else 0,
        "char_count_p25_p50_p75_p90": [pct(.25), pct(.5),
                                       pct(.75), pct(.9)] if ccs else [],
        "etc_otc_distribution": etc,
        "prescription_count": pro,
        "prescription_ratio": round(pro / len(docs), 3) if docs else 0,
        "docs_with_item_base_code": with_base,
        "too_short_filtered": run_stats.get("too_short"),
        "blocked_responses": run_stats.get("blocked_responses", blocked),
        "bot_block_detected": (run_stats.get("blocked_responses", 0) or 0) > 0,
        "license": "식약처 공공저작물 (저작권법 §24의2, "
                   "출처표시 — 식품의약품안전처)",
    },
    "join": {
        "key": "drug_detail.jsonl.item_base_code "
               "<-> drug_master_sample.csv.품목기준코드",
        "docs_joinable_with_sample_csv": len(join_hits),
        "note": "샘플 CSV는 원본의 1/15라 전체 매칭률은 낮으나, "
                "원본 305,522행 전체와는 품목기준코드로 1:1 조인 가능",
    },
    "run_stats": run_stats,
}

with open(os.path.join(BASE, "_collect_meta.json"), "w",
          encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

# --- 리포트 ---
print("=" * 60)
print("drug_master_sample.csv")
print(f"  rows(data)={len(mrows)} cols={mcols} enc=UTF-8(from EUC-KR)")
print(f"  size={os.path.getsize(CSVP)} bytes")
print("drug_detail.jsonl")
print(f"  docs={len(docs)} (min80={'OK' if len(docs)>=80 else 'FAIL'} "
      f"goal300={'OK' if len(docs)>=300 else 'partial'})")
if ccs:
    print(f"  char_count min/avg/med/max="
          f"{min(ccs)}/{round(statistics.mean(ccs),1)}/"
          f"{int(statistics.median(ccs))}/{max(ccs)}")
    print(f"  p25/50/75/90={pct(.25)}/{pct(.5)}/{pct(.75)}/{pct(.9)}")
print(f"  etc_otc={etc}")
print(f"  prescription_ratio={round(pro/len(docs),3) if docs else 0}")
print(f"  with_item_base_code={with_base}/{len(docs)}")
print(f"  blocked={run_stats.get('blocked_responses', blocked)} "
      f"too_short={run_stats.get('too_short')}")
print(f"  joinable_with_sample_csv={len(join_hits)}")
if join_hits:
    j = join_hits[0]
    print(f"  JOIN sample: doc_id={j['doc_id']} "
          f"item_base_code={j['item_base_code']} title={j['title'][:30]}")
print("_collect_meta.json written.")
