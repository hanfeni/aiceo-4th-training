#!/usr/bin/env python3
"""정책뉴스 소상공인 서브셋 수집기.
반드시 policyNewsView.do 경로만 사용. pressReleaseView 절대 금지.
글자수 >= 800 필터. 소상공인/창업/상권/전통시장/자영업 주제 위주.
"""
import re, html as ihtml, json, subprocess, sys, time
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
OUT = "policy_news.jsonl"
MIN_CHARS = 800
TARGET = 300
HARD_MIN = 80

# 소상공인 도메인 키워드 (제목/본문 매칭)
KEYWORDS = [
    "소상공인", "자영업", "전통시장", "상권", "창업", "소상공", "골목상권",
    "소공인", "노란우산", "상생", "지역상권", "온누리상품권", "벤처", "중소기업",
    "스타트업", "기업가", "재기", "폐업", "점포", "상가", "백년가게", "프랜차이즈",
    "소상공인시장진흥공단", "중기부", "중소벤처기업부", "혁신창업", "소상공인진흥",
]

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def fetch(news_id):
    url = f"https://www.korea.kr/news/policyNewsView.do?newsId={news_id}"
    try:
        p = subprocess.run(
            ["curl", "-s", "-L", "-A", UA, url, "--max-time", "30"],
            capture_output=True, timeout=40,
        )
        return url, p.stdout.decode("utf-8", "ignore")
    except Exception as e:
        return url, ""


def parse(raw):
    """returns (title, body) or (None, None)"""
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
    # 사진캡션 (ⓒ뉴스1...) 제거
    inner = re.sub(r"\([^)]*ⓒ[^)]*\)", "", inner)
    inner = re.sub(r"대한민국 정책주간지 <K-공감> 바로가기", "", inner)
    inner = re.sub(r"\s+", " ", inner).strip()
    return title, inner


def is_relevant(title, body):
    text = title + " " + body[:1500]
    return any(k in text for k in KEYWORDS)


def load_seed_ids():
    ids = []
    seen = set()
    # 1) policy RSS newsIds (정책뉴스 대역)
    for fn in ("policy_newsids.txt",):
        try:
            for line in open(fn):
                v = line.strip()
                if v and v not in seen:
                    seen.add(v)
                    ids.append(int(v))
        except FileNotFoundError:
            pass
    return ids


def main():
    seeds = load_seed_ids()
    if not seeds:
        print("no seed ids", file=sys.stderr)
        sys.exit(1)
    base = max(seeds)  # 최신 정책뉴스 ID 근처에서 역순 스캔
    lo = min(seeds)

    collected = []
    seen_doc = set()
    attempts = 0
    max_attempts = 2600

    # 후보 ID: seed 전체 + base 근처에서 아래로 순차 스캔 (정책뉴스 대역 유지)
    candidates = list(dict.fromkeys(seeds))
    cur = base
    while len(candidates) < max_attempts:
        cur -= 1
        if cur < lo - 4000:
            break
        candidates.append(cur)

    out_f = open(OUT, "w", encoding="utf-8")
    for nid in candidates:
        if len(collected) >= TARGET:
            break
        attempts += 1
        url, raw = fetch(nid)
        if not raw or "article_body" not in raw:
            continue
        title, body = parse(raw)
        if not body or len(body) < MIN_CHARS:
            continue
        if not is_relevant(title, body):
            continue
        if title in seen_doc:
            continue
        seen_doc.add(title)
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
        collected.append(len(body))
        if len(collected) % 20 == 0:
            print(f"[progress] collected={len(collected)} attempts={attempts} last_nid={nid}", flush=True)
    out_f.close()

    n = len(collected)
    print(f"DONE collected={n} attempts={attempts}")
    if n:
        cs = sorted(collected)
        print(f"char_count min={cs[0]} median={cs[n//2]} max={cs[-1]} avg={sum(cs)//n}")
    print("HARD_MIN_MET:", n >= HARD_MIN)


if __name__ == "__main__":
    main()
