#!/usr/bin/env python3
"""정책뉴스 소상공인 서브셋 - 병렬 수집기 (이어받기).
policyNewsView.do 경로만 사용. pressReleaseView 절대 금지.
글자수 >= 800 필터. 기존 policy_news.jsonl 의 doc_id 이어받기.
"""
import re, html as ihtml, json, subprocess, sys, os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
OUT = "policy_news.jsonl"
MIN_CHARS = 800
TARGET = 300
HARD_MIN = 80
WORKERS = 16

KEYWORDS = [
    "소상공인", "자영업", "전통시장", "상권", "창업", "소상공", "골목상권",
    "소공인", "노란우산", "상생", "지역상권", "온누리상품권", "벤처", "중소기업",
    "스타트업", "기업가", "재기", "폐업", "점포", "상가", "백년가게", "프랜차이즈",
    "소상공인시장진흥공단", "중기부", "중소벤처기업부", "혁신창업", "소상공인진흥",
    "소상공인·전통시장", "소상공인 정책자금", "지역화폐",
]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def fetch(news_id):
    url = f"https://www.korea.kr/news/policyNewsView.do?newsId={news_id}"
    try:
        p = subprocess.run(
            ["curl", "-s", "-L", "-A", UA, url, "--max-time", "25"],
            capture_output=True, timeout=35,
        )
        return news_id, url, p.stdout.decode("utf-8", "ignore")
    except Exception:
        return news_id, url, ""


def parse(raw):
    mt = re.search(r'<meta property="og:title" content="([^"]*)"', raw)
    if not mt:
        mt = re.search(r"<title>(.*?)</title>", raw, re.S)
    title = ihtml.unescape(mt.group(1)).strip() if mt else ""
    title = re.sub(r"\s*\|\s*대한민국 정책브리핑\s*$", "", title)
    m = re.search(r'<div[^>]*class="[^"]*article_body[^"]*"[^>]*>', raw)
    if not m:
        return title, ""
    start = m.end()
    depth = 1
    i = start
    while i < len(raw) and depth > 0:
        no = raw.find("<div", i)
        nc = raw.find("</div>", i)
        if nc == -1:
            break
        if no != -1 and no < nc:
            depth += 1
            i = no + 4
        else:
            depth -= 1
            i = nc + 6
    inner = raw[start : i - 6]
    inner = re.sub(r"<script[\s\S]*?</script>", "", inner)
    inner = re.sub(r"<style[\s\S]*?</style>", "", inner)
    inner = re.sub(r"<[^>]+>", " ", inner)
    inner = ihtml.unescape(inner)
    inner = re.sub(r"\([^)]*ⓒ[^)]*\)", "", inner)
    inner = re.sub(r"대한민국 정책주간지 <K-공감> 바로가기", "", inner)
    inner = re.sub(r"\s+", " ", inner).strip()
    return title, inner


def is_relevant(title, body):
    text = title + " " + body[:1500]
    return any(k in text for k in KEYWORDS)


def main():
    # 기존 수집분 로드 (이어받기)
    existing = {}
    seen_titles = set()
    seen_nid = set()
    if os.path.exists(OUT):
        for line in open(OUT, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            existing[d["doc_id"]] = d
            seen_titles.add(d["title"])
            seen_nid.add(int(d["doc_id"].split("_")[1]))

    # seed 범위 (policy RSS)
    seeds = [int(x.strip()) for x in open("policy_newsids.txt") if x.strip()]
    base = max(seeds)
    lo = min(seeds)
    # part1 마지막 스캔이 ~148963920 → 더 아래까지 넓게 스캔
    scan_lo = lo - 6000
    candidates = [n for n in range(base, scan_lo, -1) if n not in seen_nid]

    collected = list(existing.values())
    char_counts = [d["char_count"] for d in collected]
    attempts = 0

    out_f = open(OUT, "a", encoding="utf-8")
    BATCH = 240
    idx = 0
    while idx < len(candidates) and len(collected) < TARGET:
        batch = candidates[idx : idx + BATCH]
        idx += BATCH
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futs = [ex.submit(fetch, n) for n in batch]
            for fu in as_completed(futs):
                attempts += 1
                nid, url, raw = fu.result()
                if not raw or "article_body" not in raw:
                    continue
                title, body = parse(raw)
                if not body or len(body) < MIN_CHARS:
                    continue
                if not is_relevant(title, body):
                    continue
                if title in seen_titles:
                    continue
                seen_titles.add(title)
                doc = {
                    "doc_id": f"policy_{nid}",
                    "title": title,
                    "body": body,
                    "url": url,
                    "collected_at": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S %Z%z"),
                    "char_count": len(body),
                }
                out_f.write(json.dumps(doc, ensure_ascii=False) + "\n")
                out_f.flush()
                collected.append(doc)
                char_counts.append(len(body))
                if len(collected) >= TARGET:
                    break
        print(f"[progress] collected={len(collected)} attempts={attempts} scanned_to={batch[-1]}", flush=True)
    out_f.close()

    n = len(collected)
    print(f"DONE collected={n} attempts={attempts}")
    if n:
        cs = sorted(char_counts)
        print(f"char_count min={cs[0]} median={cs[n//2]} max={cs[-1]} avg={sum(cs)//n}")
    print("HARD_MIN_MET:", n >= HARD_MIN)


if __name__ == "__main__":
    main()
