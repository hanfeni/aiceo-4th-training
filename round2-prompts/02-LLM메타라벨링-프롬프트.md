# 작업 지시: 검색 문서에 LLM 메타 정보 라벨링 (사내 커뮤니티 AI검색 1단계 분류 이식)

> 서울대 빅데이터 AI CEO 4기 2회차 강의(2026-05-22) 복붙용 프롬프트.
> 이 블록 전체를 코딩에이전트(Claude Code / Cursor / Codex 등)에 그대로 붙여넣으면,
> 에이전트가 **이미 수집된 검색 문서(jsonl)** 에 LLM으로 메타 정보를 붙여 검색을 강화한다.
> CEO가 읽어도 "무엇을·왜" 이해되고, 코딩에이전트가 읽으면 추측 없이 끝까지 수행하도록 쓰였다.

너는 지금 검색 코퍼스가 **수집은 끝났지만 LLM 메타가 안 붙은** 상태에 있다.
아래 명세대로 **메타 라벨링 파이프라인을 1개 만들고, 실행해 라벨링된 jsonl을 산출**하라.

이것은 받아쓰기가 아니다. 코드의 표현·구조는 네가 정한다. 단 아래 **0번 절대 규칙·
출력 스키마·LLM 분류 프롬프트·재시도 구조**는 한 줄도 빠뜨리지 말고 구현하라.
글자가 아니라 **계약을 지키는 것**이 합격선이다.

작업 중 사용자에게 질문하지 마라(명세가 완결돼 있다). 단 **0번 5항(LLM 키 부재)**
같은 "진행 불가" 상황만 보고하고 멈춘다. `pwd` 로 프로젝트 루트를 확인하고
그 기준으로 경로를 잡는다.

---

## 0. 절대 규칙 (위반 시 실패 — 한 항목도 어기지 마라)

1. **입력 데이터는 이미 있다 — 재수집 절대 금지.**
   검색 문서는 `poc/data/<domain>/` 아래 `*.jsonl` 로 이미 수집돼 있다.
   도메인은 `sangkwon`(상권/소상공인) · `medical`(의료/제약) · `finance`(금융/연금) ·
   `legal`(법률) · `policy`(정책) 5개. 새로 크롤링·다운로드·수집하는 코드를
   만들지 마라. 있는 jsonl을 **읽어서 메타만 붙인다**.

2. **메타 스키마는 03(메타스키마발굴)이 만든다 — 이 단계에서 즉흥 생성 금지.**
   분류 선택지(`mid_category` 후보 목록 등)는 별도 프롬프트 **03번**이 산출하는
   `poc/data/<domain>/meta_schema.json` 을 **읽기 전용으로 로드**해서 쓴다.
   - `meta_schema.json` 이 있으면: 그 안의 카테고리 목록을 LLM 프롬프트에 주입한다.
   - 없으면(03을 안 돌렸으면): 아래 **사내 기본 mid_category 12개**를 그대로 쓴다.
     이 단계에서 카테고리 체계를 새로 발명하지 마라(즉흥 분류 체계는 도메인마다
     흔들려 검색 부스팅이 무너진다).

   ```
   사내 기본 mid_category 12개 (참조):
   정치/행정/법률, 경제/산업/노동, 사회/인권/젠더,
   보건/의료/복지, 국제/외교/안보, 과학/기술/환경,
   교육/문화/종교, 미디어/언론, 연예/스포츠,
   부동산/재테크/투자, 라이프스타일/소비, 기타
   ```

3. **문서 단위 호출 — 청크별 호출 금지.**
   메타는 **문서 1건당 정확히 1회** LLM을 호출해 뽑는다. 본문을 청크로 쪼개
   청크마다 LLM을 부르지 마라(비용이 N배로 폭증하고 메타가 청크마다 흩어져
   문서 단위 부스팅이 깨진다). 본문이 길면 **정제 후(공백 정리·앞부분 우선)**
   상한 글자수로 잘라 1회 입력한다(상한은 §3에 고정).

4. **캐싱 필수 — 동일 문서 재호출 금지.**
   캐시 키 = `doc_meta_hash = sha256(정제된 문서 본문 텍스트)`.
   `poc/data/<domain>/.meta_cache/<doc_meta_hash>.json` 에 LLM 결과를 저장하고,
   재실행 시 캐시가 있으면 LLM을 다시 부르지 않는다. 본문이 바뀌면 해시가 달라져
   자연히 재분류된다. 비용 최소화는 강의 데모의 전제다(30명이 재현).

5. **LLM 키 부재 시 — 임의 skip 금지, 사용자에게 보고.**
   `OPENAI_API_KEY`(또는 사용 모델의 키)가 환경에 없으면 라벨링을 진행할 수 없다.
   이때 **빈 메타로 채우거나 규칙기반으로 가짜 분류하지 말고**, "LLM 키가 없어
   메타 라벨링을 진행할 수 없습니다. `OPENAI_API_KEY` 설정 후 재실행하세요"라고
   사용자에게 정확히 보고하고 멈춘다. 키가 있으면 질문 없이 끝까지 수행한다.

6. **라벨링된 jsonl은 공개 리포 커밋 금지.**
   `poc/data/` 산출물은 제3자 저작권 본문(의약품 허가상세·법령·정책뉴스 등)을
   포함한다. 작업 전 프로젝트 루트 `.gitignore` 에 `poc/data/` 가 차단돼 있는지
   확인하라(이미 차단돼 있을 것이다). 차단이 없으면 산출 전에 추가한다.
   라벨링 산출물을 git add/commit 하지 마라.

7. **사용자에게 불필요한 질문 금지.**
   명세가 완결돼 있다. 모호하면 명세 문구를 그대로 따른다. 0번 5항(키 부재) 같은
   **진행 불가 상황만** 보고한다. 그 외에는 끝까지 자율 수행한다.

---

## 1. 무엇을 만드나 (WHAT — CEO도 이해할 한 문단)

**검색 문서 한 건 한 건을 LLM에게 보여주고 "이 문서가 무엇에 관한 것인지"를
정형 메타(대분류·중분류·소분류·1줄 요약·키워드·이상감지)로 받아 원본 옆에
붙인다.** 이렇게 붙인 메타는 검색 엔진이 본문만 보던 것을 넘어,
"이 문서는 '조영제 청구' 소분류이고 핵심 키워드가 [조영제, IVP, 삭감]"
같은 압축 신호를 함께 보게 해준다. 검색 결과 정확도를 끌어올리는 1단계 강화다.

이 패턴은 사내 커뮤니티 AI검색(약 69만 게시글 운영 인덱스)의 **1단계 기본 분류**를
강의 코퍼스로 그대로 이식한 것이다. 거기서는 게시글이 올라올 때마다 GPT-4o-mini가
1건씩 분류해 OpenSearch에 같이 인덱싱한다. 같은 구조를 강의 5개 도메인 jsonl에 적용한다.

**산출물**: 입력 `<원본>.jsonl` 마다 메타 6필드가 병합된 `<원본>_labeled.jsonl`.

이 메타가 **01번 프롬프트(검색 인덱싱)** 가 만든 OpenSearch 하이브리드 검색에서
`keywords^3`, `description^3` 로 부스팅된다 — 그래서 이 단계가 검색 품질의
1단계 강화다(시리즈 연결은 맨 끝 참조).

---

## 2. 수행 절차 (이 순서대로 — 건너뛰기 금지)

1. `pwd` 로 프로젝트 루트 확인. `poc/data/` 가 존재하는지, `*.jsonl` 입력이
   실제로 있는지 점검. 없으면 "01/수집 단계 미실행"으로 보고하고 멈춘다.
2. 0번 6항대로 `.gitignore` 의 `poc/data/` 차단을 확인(없으면 추가).
3. 0번 5항대로 LLM 키 존재를 확인. 없으면 보고 후 멈춘다.
4. 라벨링 스크립트 1개를 작성한다(경로·인터페이스는 §4 고정).
5. 도메인 인자를 받아 해당 도메인의 모든 `*.jsonl` 입력을 순회하며 라벨링.
   (도메인 미지정 시 5개 전부 순차 처리. `_labeled.jsonl` · `meta_schema.json` ·
   `_collect_meta.json` 같은 비입력 파일은 §4 규칙으로 건너뛴다.)
6. 문서 1건씩: 본문 정제 → 캐시 조회 → (없으면) LLM 1회 호출 → 6필드 파싱·검증 →
   원본 레코드에 메타 병합 → `<원본>_labeled.jsonl` 에 append.
7. 도메인별 요약 리포트 출력(§6) 후 §7 자가검증을 수행해 표로 보고하고 종료.

---

## 3. LLM 1단계 분류 — 출력 스키마·프롬프트·재시도 (이 계약 고정)

사내 1단계 기본 분류를 그대로 따른다. **문서 1건당 1회 호출, 실패 시 최대 3회 재시도.**

### 3.1 본문 정제 (LLM 입력 만들기)

- 입력 문서에서 제목·본문을 뽑는다. 도메인별 키가 다르므로 아래 매핑을 쓴다
  (없는 키는 건너뛰고 있는 것만 사용):
  - 제목 후보: `title` → `case_name` → `doc_id`/`prec_id` 순으로 첫 번째 존재값
  - 본문 후보: `body` (없으면 제목만)
- 정제: 연속 공백·개행을 단일 공백으로, 양끝 trim.
- **상한 글자수: 정제 본문 4000자**. 초과 시 앞 4000자만 사용(앞부분에
  요지가 몰린 문서 특성 반영). 제목은 자르지 않는다.
- `doc_meta_hash = sha256((제목 + "\n" + 정제본문) UTF-8).hexdigest()` — 캐시 키.

### 3.2 출력 필드 (6필드 — 이름·타입 고정)

| 필드 | 타입 | 설명 | 예시 |
|------|------|------|------|
| `main_category` | string | 대분류 (도메인 성격의 2분법) | `"의료"` / `"비의료"`, `"법령"` / `"비법령"` 등 도메인에 맞게 |
| `mid_category` | string | 중분류 — **반드시 §0-2 후보 목록 중 1개**(목록 외 값 금지) | `"보건/의료/복지"` |
| `sub_category` | string | 소분류 — **15자 이내** 자유 한국어 | `"조영제 청구"` |
| `description` | string | 1줄 요약 (한국어, 한 문장) | `"조영제 사용에 대한 청구 및 정산 관련 질문"` |
| `keywords` | string[] | 핵심 키워드 **3~5개** (한국어 단어) | `["조영제","IVP촬영","삭감"]` |
| `system_alert` | boolean | 이상 문서 감지 (스팸·욕설·무의미·개인정보노출 등) | `false` |

- `mid_category` 가 후보 목록에 없으면 그 결과는 **무효 처리**(§3.4 재시도).
  3회 재시도 후에도 실패하면 `mid_category="기타"` 로 폴백하고 그 문서를
  `meta_fallback=true` 로 표시한다(요약 리포트에 카운트).
- `sub_category` 16자 이상이면 앞 15자로 절단(에러 아님).
- `keywords` 가 3개 미만/5개 초과면 재시도 사유. 폴백 시 가능한 만큼만 채운다.

### 3.3 LLM 분류 프롬프트 (이 골격을 그대로 박아라 — 에이전트가 추측하지 않게)

system / user 2-메시지로 호출한다. `{MID_CATEGORY_LIST}` 자리에 §0-2의
후보 목록(또는 `meta_schema.json` 의 목록)을 콤마로 이어 주입한다.
`{TITLE}` · `{BODY}` 는 §3.1 정제값. **응답은 JSON만** 받는다
(가능하면 `response_format={"type":"json_object"}` 사용).

```text
[SYSTEM]
너는 한국어 문서를 정형 메타로 분류하는 분류기다.
주어진 문서를 읽고 아래 JSON 스키마로만 답한다. 설명·머리말·코드펜스 없이 JSON 객체 하나만 출력한다.

스키마:
{
  "main_category": "문서 성격의 대분류 (한국어 단어 1~4자, 예: 의료/비의료/법령/정책/경제)",
  "mid_category": "아래 후보 중 정확히 하나만 (목록에 없는 값 절대 금지)",
  "sub_category": "구체 소분류, 한국어 15자 이내",
  "description": "문서를 한 문장으로 요약 (한국어, 마침표로 끝냄)",
  "keywords": ["핵심 키워드 3~5개, 한국어 단어"],
  "system_alert": false
}

mid_category 후보 (이 중 하나만):
{MID_CATEGORY_LIST}

규칙:
- mid_category 는 위 후보 목록의 문자열과 글자까지 정확히 일치해야 한다.
- keywords 는 3개 이상 5개 이하. 문서에 실제 등장하거나 핵심을 대표하는 명사.
- 스팸·욕설·광고·무의미·개인정보 과다노출 등 정상 검색 대상이 아니면 system_alert=true.
- 추측으로 사실을 지어내지 말 것. 모르면 일반적·보수적으로 분류한다.

[USER]
제목: {TITLE}

본문:
{BODY}
```

### 3.4 재시도 구조 (최대 3회 — 사내 1단계와 동일)

```text
attempt = 0
while attempt < 3:
    resp = call_llm(messages)            # 문서 1건당 호출
    obj  = json_parse(resp)              # 파싱 실패 → 재시도 사유
    if obj is None: attempt += 1; continue
    if obj.mid_category not in MID_LIST:  # 목록 외 → 재시도 사유
        attempt += 1; continue
    if not (3 <= len(obj.keywords) <= 5): # 개수 위반 → 재시도 사유
        attempt += 1; continue
    return normalize(obj)                 # 통과 (sub_category 15자 절단 등)
# 3회 모두 실패
return fallback(mid_category="기타", meta_fallback=True, 가능한_필드만_채움)
```

- LLM 호출 자체가 예외(타임아웃·429 등)면 그 시도도 attempt로 세고
  짧은 백오프(예: 2초·4초) 후 재시도. 3회 소진 시 위 폴백.
- 재시도·폴백·캐시히트 건수는 §6 요약 리포트에 반드시 집계한다.

---

## 4. 라벨링 스크립트 인터페이스 (경로·동작 고정, 구현 표현은 네 몫)

- 위치: `poc/label_meta.py` (단일 파일. 1000줄 넘으면 모듈 분리 + index re-export).
- 실행: `python poc/label_meta.py <domain>` 또는 `python poc/label_meta.py all`.
  - `<domain>` ∈ {sangkwon, medical, finance, legal, policy}.
- 입력: `poc/data/<domain>/*.jsonl` 중 **다음을 제외한** 모든 파일
  - `*_labeled.jsonl` (이 단계 산출물)
  - `meta_schema.json` · `_collect_meta.json` · `.meta_cache/` 내부 (비입력)
- 출력: 입력 `<name>.jsonl` → 같은 폴더에 `<name>_labeled.jsonl`.
  - 원본 레코드의 모든 키를 보존하고, 메타 6필드 + `doc_meta_hash` +
    (폴백 시) `meta_fallback` 만 추가한다. 원본 필드 삭제·변형 금지.
  - 한 줄에 한 JSON(jsonl 유지). UTF-8, `ensure_ascii=false`.
- 캐시: `poc/data/<domain>/.meta_cache/<doc_meta_hash>.json`.
  존재하면 LLM 미호출(캐시 히트 카운트). 캐시 파일엔 6필드 결과 저장.
- 멱등성: 재실행 시 `<name>_labeled.jsonl` 을 새로 만들되, 문서별로 캐시가
  있으면 LLM을 부르지 않으므로 비용은 0에 수렴한다(결과는 동일).
- 모델: 기본 `gpt-4o-mini`(사내 1단계와 동일). 환경변수 `META_LLM_MODEL`
  로 override 가능. 호출은 동기 1건씩(강의 재현성·비용 예측 우선,
  과한 동시성 금지).

---

## 5. 불변식 (어기면 실패)

1. **문서당 LLM 1회.** 청크 루프 안에서 LLM을 부르지 않는다(§0-3).
2. **mid_category 는 후보 목록 안에서만.** 목록 밖 값이 출력 jsonl에
   하나라도 있으면 실패(폴백 "기타"는 허용 — 그것도 목록 안).
3. **원본 보존.** `_labeled.jsonl` 은 원본 키를 모두 가진 채 메타만 추가.
   원본 본문을 줄이거나 바꾸지 않는다(검색 본문은 그대로여야 01과 호환).
4. **캐시 우선.** 캐시 히트면 LLM 미호출. 비용 폭증은 강의 데모 실패다.
5. **키 없으면 멈춤.** 가짜 메타로 채우지 않는다(§0-5). 정직한 0건 보고.
6. **결정적 단계 자가검증.** 산출 후 파일 존재·라인 수·메타 필드 존재를
   기계로 확인한 뒤에만 "완료"로 보고한다(확인 없이 가정·허위 금지).

---

## 6. 요약 리포트 (도메인별 — stdout 출력)

도메인 처리 끝마다 다음을 출력한다(파일 산출 불필요, 화면만):

```
[<domain>] 입력파일 N개 / 문서 M건
  라벨링 완료: M건  (LLM 호출 X건 / 캐시 히트 Y건)
  재시도 발생: R건   폴백(기타): F건   system_alert=true: A건
  mid_category 분포: { "보건/의료/복지": n1, "경제/산업/노동": n2, ... }
  산출: poc/data/<domain>/<name>_labeled.jsonl  (각 라인 메타 6필드 병합)
```

`all` 실행 시 5개 도메인 블록을 순서대로 출력하고 마지막에 총계 1줄.

---

## 7. 자가검증 (기능 계약 충족도 — 글자가 아니라 계약)

산출 후 아래를 점검해 PASS/FAIL 표로 보고한다. FAIL이면 원인을 고치고
재점검한다(에러를 보고만 하지 말고 먼저 고친다, 최대 3회).

```bash
echo "=== (1) 스크립트 존재 ==="
[ -f poc/label_meta.py ] && echo "OK poc/label_meta.py" || echo "FAIL MISSING"

echo "=== (2) 라벨링 산출물 존재 (처리한 도메인 기준) ==="
ls -1 poc/data/*/*_labeled.jsonl 2>/dev/null | sed 's/^/  /' \
  || echo "  FAIL: _labeled.jsonl 0개"

echo "=== (3) 메타 6필드가 모든 라인에 있는가 (샘플 도메인 1개) ==="
F=$(ls -1 poc/data/*/*_labeled.jsonl 2>/dev/null | head -1)
python3 - "$F" <<'PY'
import sys, json
f=sys.argv[1]; req={"main_category","mid_category","sub_category","description","keywords","system_alert","doc_meta_hash"}
bad=0; n=0
for line in open(f, encoding="utf-8"):
    line=line.strip()
    if not line: continue
    n+=1; d=json.loads(line)
    if not req.issubset(d.keys()): bad+=1
    if not isinstance(d.get("keywords"), list): bad+=1
print(f"  {f}: {n} lines, 필드누락/오류 {bad}건  -> {'OK' if bad==0 else 'FAIL'}")
PY

echo "=== (4) mid_category 가 후보 목록 안인가 ==="
python3 - <<'PY'
import sys, json, glob, os
DEFAULT=["정치/행정/법률","경제/산업/노동","사회/인권/젠더","보건/의료/복지",
"국제/외교/안보","과학/기술/환경","교육/문화/종교","미디어/언론","연예/스포츠",
"부동산/재테크/투자","라이프스타일/소비","기타"]
bad=0; checked=0
for f in glob.glob("poc/data/*/*_labeled.jsonl"):
    dom=os.path.dirname(f)
    schema=os.path.join(dom,"meta_schema.json")
    allow=set(DEFAULT)
    if os.path.exists(schema):
        try:
            js=json.load(open(schema,encoding="utf-8"))
            mids=js.get("mid_category") or js.get("mid_categories") or []
            if mids: allow=set(mids)|{"기타"}
        except Exception: pass
    for line in open(f,encoding="utf-8"):
        line=line.strip()
        if not line: continue
        checked+=1
        if json.loads(line).get("mid_category") not in allow: bad+=1
print(f"  검사 {checked}건, 목록 밖 {bad}건  -> {'OK' if bad==0 else 'FAIL'}")
PY

echo "=== (5) 캐시 디렉터리 생성됐는가 (재실행 비용 0 보장) ==="
ls -d poc/data/*/.meta_cache 2>/dev/null | sed 's/^/  /' \
  || echo "  WARN: 캐시 디렉터리 없음 (LLM 미호출 환경이면 정상)"

echo "=== (6) 입력 원본 보존 (라인 수 = 입력 라인 수) ==="
python3 - <<'PY'
import glob, os
bad=0
for lab in glob.glob("poc/data/*/*_labeled.jsonl"):
    src=lab.replace("_labeled.jsonl",".jsonl")
    if not os.path.exists(src): continue
    a=sum(1 for _ in open(src,encoding="utf-8") if _.strip())
    b=sum(1 for _ in open(lab,encoding="utf-8") if _.strip())
    mark="OK" if a==b else "FAIL"
    if a!=b: bad+=1
    print(f"  {os.path.basename(lab)}: src {a} / labeled {b} -> {mark}")
print("  -> "+("ALL OK" if bad==0 else f"{bad} mismatch"))
PY
```

### 합격 기준

| 검사 | PASS 조건 |
|---|---|
| (1) 스크립트 | `poc/label_meta.py` 존재 |
| (2) 산출물 | 처리 도메인마다 `_labeled.jsonl` 생성 |
| (3) 6필드 | 모든 라인에 메타 6필드 + `doc_meta_hash`, `keywords`는 list |
| (4) mid 목록 | 목록 밖 값 0건 (폴백 "기타" 포함 목록 내) |
| (5) 캐시 | `.meta_cache/` 생성 (LLM 호출이 실제로 일어난 경우) |
| (6) 원본 보존 | labeled 라인 수 = 입력 라인 수 (문서 누락·증식 0) |

6개 전부 PASS면 라벨링 성공. 검사 표 + **"본문 정제·캐싱·재시도·폴백을
명세 어디를 보고 어떻게 구현했는지 1줄 설명"** 을 덧붙여 보고하고 종료한다.
(LLM 키 부재로 §0-5 보고 후 멈춘 경우는 그 사실만 보고 — 그것도 정상 종료다.)

---

## 완료 기준

- `poc/label_meta.py` 가 작성됐고, 키가 있으면 지정 도메인(또는 전체)을
  라벨링해 `<원본>_labeled.jsonl` 을 산출했다.
- 산출 jsonl의 모든 라인이 원본 키 + 메타 6필드(`main_category`,
  `mid_category`, `sub_category`, `description`, `keywords`, `system_alert`)
  + `doc_meta_hash` 를 가진다. `mid_category` 는 후보 목록 안에서만.
- 문서당 LLM 1회·캐시 키 `sha256(본문)`·재시도 3회·폴백 "기타"·
  요약 리포트가 명세대로 동작한다.
- §7 자가검증 6검사 전부 PASS(또는 §0-5 키 부재 보고로 정상 종료).
- 라벨링 산출물은 git에 커밋되지 않는다(`poc/data/` gitignore 확인).

---

## 시리즈 연결 (이 프롬프트는 02번 — 검색 강화 3부작의 가운데)

- **01번 (검색 인덱싱)** 에서 만든 OpenSearch 인덱스에, 여기서 만든
  `_labeled.jsonl` 의 메타를 넣어 **재인덱싱**하면 하이브리드 검색이
  강해진다 — `keywords^3`, `description^3` 부스팅이 이 메타에 직접
  걸리기 때문이다. 01을 먼저 돌렸다면, 01의 인덱싱 입력을
  `_labeled.jsonl` 로 바꿔 다시 인덱싱하라.
- **메타 품질을 끌어올리려면 03번 (메타 스키마 발굴)을 먼저** 돌리는 게
  좋다. 03이 도메인에 맞는 `mid_category` 후보를 데이터에서 발굴해
  `meta_schema.json` 을 만들면, 이 단계가 사내 기본 12개 대신 그
  도메인 맞춤 스키마로 더 정밀하게 분류한다(없으면 기본 12개로도 동작).
- 권장 순서: **03(메타 스키마 발굴) → 02(이 프롬프트, 메타 라벨링) →
  01(검색 인덱싱, `_labeled.jsonl` 로 재인덱싱)**. 03을 건너뛰어도
  02→01 만으로 동작한다(기본 스키마 사용).
