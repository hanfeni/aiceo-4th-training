---
description: 언론사명·기자명을 받아 해당 기자가 다룬 기사들을 주제 클러스터로 묶고, 클러스터별로 5채널(네이버댓글/다음댓글/커뮤니티포럼/SNS/블로그·유튜브) 풀스캔으로 여론 반응을 수집해, 「주제군 여론 반응(메인) + 기자 개인 평판(보조)」 리포트 마크다운 1장 + 채널별 raw yaml 5개 + article_list 1개를 산출하는 하네스. 분업형 subagent 토폴로지(article-collector 1 + review-scout 5병렬), 주제 클러스터링은 오케스트레이터 본체가 담당. HITL 0회 풀자동.
argument-hint: <언론사명> <기자명> [기간(예: 3M, 6M, 1Y) — 기본 3M]
allowed-tools: Bash, Read, Write, Grep, Glob, Task, WebSearch, WebFetch
---

# /reporter-review-scan — 기자 보도 주제군 여론 반응 풀스캔 하네스

## 0. 정체성 (이 하네스가 하는 일·하지 않는 일)

**왜 이렇게 설계됐는가 (실증 기반 재정의):**

초기 설계는 기자 개인의 평판을 추적했으나, 실제 1차 운영(yu-seolhee
케이스, 2026-05-24) 결과 **기자명을 직접 거론한 게시글·댓글은 5채널
전수에서 0건**이라는 한국 뉴스 소비 패턴의 구조적 사실이 발견됐다.
독자는 「기사 주제」에 반응하지 「기자 이름」에 반응하지 않는다.

따라서 본 하네스는 **기자의 보도 주제군을 클러스터로 묶어 여론 반응을
풀스캔**하는 것을 메인으로 하고, 기자 개인 평판은 **보조 항목**으로
편입한다. 입력 인터페이스(언론사+기자명)는 그대로 유지한다.

**하는 일:**
- 입력된 언론사·기자가 기간 내 쓴 기사 N건을 수집
- N건을 **주제 클러스터 3~6개**로 묶기(오케스트레이터 본체)
- 각 클러스터를 5채널에 병렬 위임해 **주제 키워드 기반 풀스캔**
- **메인 산출**: 클러스터별 여론 반응(감성/키워드/대표 인용)
- **보조 산출**: 기자명 직접 거론 게시글(발견 시에만, 0건이면 0건 정직 기재)
- 채널별 raw yaml 5개 + article_list 1개 + 종합 리포트 1개

**하지 않는 일:**
- 기자 개인에 대한 가치 판정·우열 평가·명예훼손성 단정
- 수집된 리뷰 외 추측·해석으로 평판을 만들어내기
- 비공개 게시판·로그인 필요 사이트 스크래핑
- 출처 없는 인용 생성
- 기자명 거론 0건을 "데이터 없음"으로 호도하기 — 정직히 0건 기재

이 하네스는 **수집·클러스터링·여론 종합 자동화**까지가 본분이며,
평판 해석의 최종 책임은 사용자에게 있다.

---

## 1. Step 0 — 입력 파싱 + 메타·경로 (오케스트레이터 본체)

`$ARGUMENTS`를 파싱한다. **비어 있거나 언론사/기자명이 누락이면 한 번만**
물어 받고, 채워져 있으면 질문 없이 끝까지 수행한다.

파싱 규칙:
- 1번째 토큰 → `media` (언론사명, 예: `조선일보`)
- 2번째 토큰 → `reporter` (기자명, 예: `김철수`)
- 3번째 토큰(선택) → `period` (예: `3M` / `6M` / `1Y`). 미지정 시 `3M`.

```bash
now_kst=$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M KST')
today=$(TZ=Asia/Seoul date '+%Y-%m-%d')
run_id=$(TZ=Asia/Seoul date '+%H%M%S')
```

- `target` — `<media> / <reporter> / <period>` (예: `조선일보 / 김철수 / 3M`)
- `slug` — `<reporter>` kebab-case (예: `kim-cheolsoo`). 동명이인은
  뒤에 `-<media>` 붙임(예: `kim-cheolsoo-chosun`).
- `period_start` — `today - period` (KST 기준 ISO 날짜)
- `period_end` — `today`

저장 경로(프로젝트 로컬):

```bash
base="./specs/reporter-review-scan/<slug>/<today>"
mkdir -p "$base"
if [ -f "$base/00_report.md" ]; then
  out="$base/00_report_<run_id>.md"
  suffix="_<run_id>"
else
  out="$base/00_report.md"
  suffix=""
fi
```

산출 파일 7종 경로:
- `$base/00_report${suffix}.md` — 종합 리포트(주제군 메인 + 기자 보조)
- `$base/01_article_list${suffix}.yaml` — 기사 목록 (+ 주제 클러스터 매핑)
- `$base/02_reviews_naver${suffix}.yaml`
- `$base/03_reviews_daum${suffix}.yaml`
- `$base/04_reviews_community${suffix}.yaml`
- `$base/05_reviews_sns${suffix}.yaml`
- `$base/06_reviews_blog${suffix}.yaml`

---

## 2. Step 1 — 기사 목록 수집 sub-task를 subagent에 위임

오케스트레이터는 **기사 URL·제목·발행일·요약·핵심 키워드 수집을
`reporter-article-collector`에 위임**한다. 이것은 분업이다 —
오케스트레이터는 클러스터링·종합·합성에 집중하고, subagent는 기사
목록 추출만 한다.

subagent에 전달할 prompt:

```
[메타]
media: <media>
reporter: <reporter>
period_start: <period_start>
period_end: <period_end>
now_kst: <now_kst>

위 언론사의 해당 기자가 period_start~period_end 사이에 쓴 기사의
URL·제목·발행일·1~2문장 요약·핵심 키워드 3~5개를 언론사 사이트·
네이버뉴스·다음뉴스에서 추출하라.
(reporter-article-collector 정의의 지시를 그대로 수행한다.)
```

subagent는 압축된 article_list만 반환한다(파일 안 씀).

반환 받은 article_list를 잠시 메모리에 보관(Step 2 클러스터링 후 함께 저장).

기사가 0건이면 정직히 0건 리포트로 빠르게 종료(클러스터링·채널
스카우트 스킵).

---

## 3. Step 2 — 주제 클러스터링 (오케스트레이터 본체, 신규 단계)

article_list의 N건 기사를 **3~6개 주제 클러스터**로 묶는다. 이것은
오케스트레이터 본체가 직접 수행하는 단계로, subagent에 위임하지 않는다.

### 클러스터링 규칙

1. 각 기사의 `title` + `summary` + `keywords`를 의미 단위로 묶기.
2. 정치/경제/사회/문화/국제 같은 너무 넓은 분류는 금지 —
   **사건 단위 또는 정책·이슈 단위로 좁게 묶는다**.
   - 좋은 예: "GTX 삼성역 철근 누락", "다주택 양도세 중과 부활",
     "전세사기 대응책", "이란-이스라엘 전쟁 분석" (점선면 시리즈)
   - 나쁜 예: "정치", "경제", "사회"
3. 클러스터당 최소 2건 기사. 1건짜리는 "기타 단건" 클러스터로 묶음.
4. 클러스터 수는 **3~6개**가 적정. 너무 많으면 통합, 너무 적으면 세분.
5. 각 클러스터마다:
   - `cluster_id` — 짧은 kebab-case (예: `gtx-rebar-omission`)
   - `cluster_label` — 한국어 클러스터 이름 (≤30자)
   - `article_count` — 포함 기사 수
   - `article_urls` — 포함 기사 URL 목록
   - `search_keywords` — review-scout가 검색에 쓸 핵심 키워드 5~8개
     (사건명·고유명사·핵심 정책명 포함, 너무 일반적인 단어 제외)
   - `representative_titles` — 대표 기사 제목 2~3개

### 클러스터 후보 발견 안 되면

기사가 매우 다양해 묶이지 않으면(예: 컬럼니스트·뉴스레터 작가):
- 기사 8건 이상의 큰 주제군이 없으면 **2~3개 광역 클러스터**로 묶고
  `note: 기사 다양도 높음 — 광역 클러스터링` 명시.

### article_list yaml 저장 (클러스터 매핑 포함)

```bash
# subagent 반환 + 오케스트레이터 클러스터링 결과를 합쳐
# $base/01_article_list${suffix}.yaml에 Write
```

저장 구조:
```yaml
period: <period>
period_start: <period_start>
period_end: <period_end>
articles_count: <N>
clusters_count: <K (3~6)>
articles:
  - url: ...
    title: ...
    published_at: ...
    summary: ...
    keywords: [...]
    cluster_id: gtx-rebar-omission
clusters:
  - cluster_id: gtx-rebar-omission
    cluster_label: GTX 삼성역 철근 누락 사건
    article_count: 7
    article_urls: [...]
    search_keywords: [GTX 삼성역, 철근 누락, 현대건설, 서울시 보고 지연, ...]
    representative_titles: [...]
```

---

## 4. Step 3 — 5개 review-scout 병렬 위임 (주제 클러스터 기반 풀스캔)

CLAUDE.md `5개 에이전트 병렬 수행` 원칙대로 **5개 인스턴스 동시 호출**.
업무 쪼개기가 아니라 **채널별 풀스캔 분장** — 각 scout는 동일
clusters 입력을 받지만 자기 채널만 풀스캔한다.

**핵심 변경(v2):** scout는 article URL뿐 아니라 **클러스터별
search_keywords로도 검색**한다. 기자명을 직접 거론하지 않은
게시글이 대부분이라는 실증 결과(yu-seolhee 케이스) 때문이다.

5개를 **단일 메시지에 5개 Task 호출**로 병렬 실행:

| scout 인스턴스 | channel | 대상 플랫폼 (예시) |
|---|---|---|
| ① | `naver` | 네이버뉴스 댓글·반응, 네이버 카페 공개글, 지식인 |
| ② | `daum` | 다음뉴스 댓글·추천/반대, 다음 카페 공개글 |
| ③ | `community` | DC인사이드, 클리앙, 뽐뿌, MLB파크, 더쿠, 펨코, 루리웹, 보배드림 등 |
| ④ | `sns` | X(트위터), 스레드, 페이스북 공개 인용·언급 |
| ⑤ | `blog` | 네이버블로그, 티스토리, 브런치, 유튜브 비평 영상, 인디 매체 칼럼 |

각 scout에 전달할 prompt 템플릿:

```
[메타]
channel: <naver|daum|community|sns|blog>
media: <media>
reporter: <reporter>
period_start: <period_start>
period_end: <period_end>
now_kst: <now_kst>

[clusters]
<01_article_list.yaml의 clusters 섹션 inline 전달>

[articles]
<01_article_list.yaml의 articles 섹션 inline 전달 (간략 매핑)>

각 cluster의 search_keywords를 메인 검색축으로 사용해 너의 channel
플랫폼에서 여론 반응을 풀스캔한다. article URL 인용은 보조 검색축이다.
기자명(<reporter>) 직접 거론 게시글은 별도 bucket으로 표시한다.
(reporter-review-scout 정의의 지시를 그대로 수행한다.)
```

각 scout는 압축된 reviews_<channel> 데이터를 반환한다(파일 안 씀).

반환 받은 5개 결과를 각각 yaml 파일로 저장:
- `02_reviews_naver${suffix}.yaml`
- `03_reviews_daum${suffix}.yaml`
- `04_reviews_community${suffix}.yaml`
- `05_reviews_sns${suffix}.yaml`
- `06_reviews_blog${suffix}.yaml`

---

## 5. Step 4 — 오케스트레이터 합성 (주제군 메인 + 기자 보조)

5개 yaml을 병합·합성한다. **HITL 없이 풀자동.**

### 메인 산출: 주제 클러스터별 여론 반응

각 클러스터마다:

1. **중복 제거** — 같은 review_text/source URL 중복 항목 dedup.
2. **클러스터 매핑** — 각 리뷰의 `cluster_id`(scout가 부여) 또는
   `article_url`을 통한 역매핑으로 클러스터 귀속.
3. **클러스터별 감성 분포** — positive / negative / neutral %.
   감성은 각 scout가 명시한 sentiment 필드 기반(임의 재분류 금지).
4. **클러스터별 빈출 키워드 TOP 5~10** — review_text 토큰화·빈도.
5. **클러스터별 대표 인용** — 채널 다양성 고려해 3~5건 발췌.
6. **클러스터별 비판 패턴 / 칭찬 패턴** — 각 패턴 근거 인용 2~3건.

### 보조 산출: 기자 개인 평판

- 모든 채널 결과 중 `reporter_mentioned: true` 표시된 항목만 모음.
- 0건이면 **정직히 0건 기재** — "기자명 직접 거론 게시글 0건.
  평판은 본 리포트 §메인의 주제군 여론으로 갈음."
- 1건 이상이면 인용 + 출처 + 작성일 모두 표기.

### 부가 산출: 채널별 메타

- 채널별 수집 건수·articles_covered·scraping_skipped 사유.

### 환각 방어 (엄수)

- scout 반환 자료에 **없는 인용·URL·감성을 만들지 않는다.**
- 0건 채널·0건 클러스터는 "수집 0건"으로 정직히 기재(채워넣기 금지).
- 모든 인용에 출처 URL·플랫폼명·작성일 표기. 없으면 폐기.
- 기자명 직접 거론 0건을 우회적으로 "있는 것처럼" 표현 금지.

---

## 6. Step 5 — 마크다운 저장 + 결정적 자가검증 + 로그

§7 Contract대로 종합 리포트를 `$out`에 Write. 그 외 md 안 만듦.

저장 직후 **결정적 자가검증**:

```bash
test -f "$out" && echo "FILE_OK $out" || echo "FILE_MISSING $out"
for k in harness media reporter slug period run_at run_id articles_count clusters_count reviews_count sources_count reporter_mentions_count; do
  grep -q "^$k:" "$out" && echo "key $k OK" || echo "key $k MISSING"
done
# 채널별 yaml 6개 모두 존재 확인
for f in 01_article_list 02_reviews_naver 03_reviews_daum 04_reviews_community 05_reviews_sns 06_reviews_blog; do
  test -f "$base/${f}${suffix}.yaml" && echo "yaml $f OK" || echo "yaml $f MISSING"
done
# 출처 표기 존재 확인
grep -qE 'https?://' "$out" && echo "SOURCE_OK" || echo "SOURCE_MISSING"
# 메인 산출(클러스터) 존재 확인 — 0건이라도 섹션은 있어야 함
grep -q "주제 클러스터" "$out" && echo "MAIN_SECTION_OK" || echo "MAIN_SECTION_MISSING"
# 보조 산출(기자 평판) 존재 확인
grep -q "기자 개인 평판" "$out" && echo "AUX_SECTION_OK" || echo "AUX_SECTION_MISSING"
```

검증 통과(파일 + 키 + yaml 6개 + 출처 + 메인/보조 섹션) **뒤에만** 완료 보고.

작업 로그 1줄 append:

```bash
log=".claude/history/daily/<today>.md"
[ -f "$log" ] || printf '## Claude Code 작업 로그\n\n' > "$log"
# - HH:MM | [<device-label>] | reporter-review-scan | <media>/<reporter>/<period> — 기사 N건, 클러스터 K개, 리뷰 M건, 기자 언급 J건
```

사용자 보고: 저장 경로, 기사 수, 클러스터 수, 클러스터별 리뷰 합계,
기자명 직접 언급 건수, 최대 화제 클러스터 1개.

---

## 6. 최종 md Contract (구조 고정 — 표현 자유)

frontmatter 키 **전부** 포함. Contract 외 키 추가 금지.

```yaml
---
harness: reporter-review-scan
media: <언론사명>
reporter: <기자명>
slug: <slug>
period: <period (예: 3M)>
period_start: <YYYY-MM-DD>
period_end: <YYYY-MM-DD>
run_at: <now_kst>
run_id: <run_id>
articles_count: <기사 수>
clusters_count: <주제 클러스터 수 (3~6)>
reviews_count: <전체 리뷰 수>
sources_count: <고유 출처 URL 수>
reporter_mentions_count: <기자명 직접 거론 게시글 수, 0이면 0>
sentiment_pos_pct: <0~100>
sentiment_neg_pct: <0~100>
sentiment_neu_pct: <0~100>
---
```

본문 섹션(모두 포함, 순서 고정):

1. **요약** *(맨 앞)* — 기자 식별·기간·기사 수·클러스터 수·전체 톤·
   기자명 직접 거론 0건 여부 한눈 정리.
2. **기자 프로필** — 언론사·기자명·조회 기간·기사 수·주요 출입처(있다면)·
   기사 클러스터 분포(클러스터별 기사 수 표).
3. **주제 클러스터별 여론 반응** *(메인 산출)* — 클러스터마다 별도 서브섹션:
   - 클러스터명 · 포함 기사 수 · 대표 기사 제목 2~3개
   - 채널별 수집 건수 표 (naver / daum / community / sns / blog)
   - 감성 분포 (pos/neg/neu %)
   - 빈출 키워드 TOP 5~10
   - 대표 인용 3~5건 (URL·플랫폼·작성일)
   - 비판 패턴 / 칭찬 패턴 (있을 시)
4. **기자 개인 평판** *(보조 산출)* — 기자명 직접 거론 게시글만:
   - 0건이면 "기자명 직접 거론 게시글 0건. 평판은 §3 주제군 여론으로
     갈음." 명시.
   - 1건 이상이면 인용 + 출처 + 작성일 모두 표기.
5. **채널별 메타** — 5채널 각각 수집 건수·articles_covered·
   scraping_skipped 사유 요약.
6. **원본 인용 모음** — 채널 무관 상위 인용 10~20건(URL·플랫폼·
   작성일). 클러스터 매핑 함께 표기.
7. **한계·면책** — 스크래핑 불가 사이트, 표본 편향, 명예훼손성
   단정 금지, 평판 해석 책임은 사용자에게 귀속, 기자명 거론 0건은
   도구 한계가 아니라 한국 뉴스 소비 패턴의 사실임을 명시.

---

## 8. 불변식 (어기면 하네스 실패)

1. **분업 토폴로지 보존** — 기사 목록은 article-collector subagent 1개,
   주제 클러스터링은 **오케스트레이터 본체**, 리뷰 수집은 review-scout
   subagent 5인스턴스 병렬. 역할 섞지 않는다.
2. **5채널 풀스캔** — 채널 쪼개기 아닌 **동일 clusters 입력으로
   채널별 풀스캔**. 한 채널이라도 0건이면 0건으로 정직히 기재(다른
   채널로 채우기 금지).
3. **주제 클러스터 메인 + 기자 평판 보조** — 메인/보조 위계를 뒤집지
   않는다. 기자명 거론 게시글이 많아 보여도 메인은 클러스터.
4. **기자명 직접 거론 0건 우회 금지** — 0건은 0건으로 정직히 기재.
   "거의 없다"·"극소수"·"제한적이지만" 같은 우회 표현 금지.
5. **subagent는 파일 안 씀.** yaml 저장은 오케스트레이터만.
6. **모든 인용에 출처 URL·플랫폼·작성일.** 없으면 폐기.
7. **HITL 0회** — 풀자동 진행. 입력이 비어 있을 때만 1회 질문.
8. **평판 단정·명예훼손 표현 금지.** 사실 종합·패턴 식별까지만.
9. 저장 후 grep 기계 확인한 뒤에만 완료 보고.
