#!/usr/bin/env python3
"""nedrug 의약품안전나라 허가상세 본문 수집 (전문약 위주, 본문 >=2000자 필터)."""
import json, re, time, sys, html as ihtml, urllib.request, urllib.parse, datetime, random

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
BASE = "https://nedrug.mfds.go.kr"
SEARCH = BASE + "/searchDrug"
SEC_URL = BASE + "/pbp/cmn/html/drb/{seq}/{sec}"
DETAIL = BASE + "/pbp/CCBBB01/getItemDetail?itemSeq={seq}"

TARGET = 300
MIN_DOC = 80
MIN_CHARS = 2000

stats = {"pages_fetched": 0, "itemseq_collected": 0, "detail_attempts": 0,
         "blocked_responses": 0, "too_short": 0, "saved": 0, "errors": 0}


def http_get(url, data=None, timeout=30, retries=2):
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, data=data, method="POST" if data else "GET")
            req.add_header("User-Agent", UA)
            req.add_header("Accept", "text/html,application/xhtml+xml,*/*")
            req.add_header("Accept-Language", "ko-KR,ko;q=0.9")
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code in (403, 429, 503):
                stats["blocked_responses"] += 1
                return e.code, ""
            if attempt == retries:
                stats["errors"] += 1
                return e.code, ""
            time.sleep(1.5 * (attempt + 1))
        except Exception:
            if attempt == retries:
                stats["errors"] += 1
                return 0, ""
            time.sleep(1.5 * (attempt + 1))
    return 0, ""


def strip_html(s):
    s = re.sub(r"<script[\s\S]*?</script>", " ", s)
    s = re.sub(r"<style[\s\S]*?</style>", " ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = ihtml.unescape(s)
    s = re.sub(r"[ \t ]+", " ", s)
    s = re.sub(r"\s*\n\s*", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def collect_itemseqs(max_pages):
    seqs = []
    seen = set()
    for page in range(1, max_pages + 1):
        body = urllib.parse.urlencode({
            "page": page, "searchYn": "true",
            "etcOtcCode": "02", "sortOrder": "false"}).encode()
        st, htmlt = http_get(SEARCH, data=body, timeout=40)
        stats["pages_fetched"] += 1
        if st != 200 or not htmlt:
            print(f"  [page {page}] HTTP {st} -> stop", file=sys.stderr)
            break
        found = re.findall(r"itemSeq=(\d+)", htmlt)
        new = [s for s in dict.fromkeys(found) if s not in seen]
        for s in new:
            seen.add(s); seqs.append(s)
        print(f"  [page {page}] +{len(new)} (total {len(seqs)})", file=sys.stderr)
        time.sleep(random.uniform(0.6, 1.2))
    stats["itemseq_collected"] = len(seqs)
    return seqs


def fetch_meta(seq):
    """상세 페이지에서 제품명/품목기준코드/표준코드/성분명/전문일반 추출."""
    st, htmlt = http_get(DETAIL.format(seq=seq), timeout=30)
    if st != 200 or not htmlt:
        if st in (403, 429, 503):
            return None, "blocked"
        return None, "err"
    meta = {"item_name": "", "item_base_code": "", "std_code": "",
            "ingredient": "", "etc_otc": "", "entp_name": ""}
    def cell(label):
        m = re.search(r'<th[^>]*>\s*' + re.escape(label) +
                      r'\s*</th>\s*<td[^>]*>([\s\S]*?)</td>', htmlt)
        return strip_html(m.group(1))[:300] if m else ""
    meta["item_name"] = cell("제품명")
    meta["item_base_code"] = cell("품목기준코드")
    meta["std_code"] = cell("표준코드")
    meta["entp_name"] = cell("업체명")
    meta["etc_otc"] = cell("전문/일반")
    mi = re.search(r"성분명[\s\S]{0,40}?</caption>([\s\S]*?)</table>", htmlt)
    if mi:
        names = re.findall(r"<td[^>]*>([^<]{2,60})</td>", mi.group(1))
        meta["ingredient"] = "; ".join(dict.fromkeys(
            n.strip() for n in names if re.search(r"[A-Za-z가-힣]", n)))[:300]
    return meta, "ok"


def fetch_body(seq):
    parts = []
    for sec, label in (("EE", "효능효과"), ("UD", "용법용량"), ("NB", "사용상의 주의사항")):
        st, h = http_get(SEC_URL.format(seq=seq, sec=sec), timeout=25)
        if st == 200 and h:
            txt = strip_html(h)
            if txt:
                parts.append(txt)
        elif st in (403, 429, 503):
            return None
        time.sleep(random.uniform(0.25, 0.5))
    return "\n\n".join(parts)


def main():
    max_pages = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    out_path = "drug_detail.jsonl"
    print(f"[1] collecting itemSeq from up to {max_pages} pages...", file=sys.stderr)
    seqs = collect_itemseqs(max_pages)
    print(f"[1] {len(seqs)} unique itemSeq collected", file=sys.stderr)

    print("[2] fetching detail bodies...", file=sys.stderr)
    fout = open(out_path, "w", encoding="utf-8")
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    ts = now.isoformat()
    for i, seq in enumerate(seqs):
        if stats["saved"] >= TARGET:
            break
        stats["detail_attempts"] += 1
        meta, mstatus = fetch_meta(seq)
        if mstatus == "blocked":
            print(f"  [{i}] {seq} META BLOCKED", file=sys.stderr)
            time.sleep(2.0)
            continue
        if meta is None:
            continue
        body = fetch_body(seq)
        if body is None:
            print(f"  [{i}] {seq} BODY BLOCKED", file=sys.stderr)
            time.sleep(2.0)
            continue
        full = ((meta.get("item_name") or "") + "\n\n" + body).strip()
        cc = len(full)
        if cc < MIN_CHARS:
            stats["too_short"] += 1
        else:
            rec = {
                "doc_id": f"nedrug-{seq}",
                "item_seq": seq,
                "title": meta.get("item_name", "") or f"itemSeq {seq}",
                "body": full,
                "url": DETAIL.format(seq=seq),
                "collected_at": ts,
                "char_count": cc,
                "item_base_code": meta.get("item_base_code", ""),
                "std_code": meta.get("std_code", ""),
                "ingredient": meta.get("ingredient", ""),
                "entp_name": meta.get("entp_name", ""),
                "etc_otc": meta.get("etc_otc", ""),
            }
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fout.flush()
            stats["saved"] += 1
            if stats["saved"] % 10 == 0:
                print(f"  saved={stats['saved']} (last {seq} {cc}c)", file=sys.stderr)
        time.sleep(random.uniform(0.5, 1.0))
    fout.close()
    print("STATS=" + json.dumps(stats, ensure_ascii=False))


if __name__ == "__main__":
    main()
