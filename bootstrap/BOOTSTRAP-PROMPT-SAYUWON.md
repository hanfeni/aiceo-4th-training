<!--
이 파일은 "사유원 전용 평판·리뷰 모니터링 하네스"의 복붙형 부트스트랩
프롬프트다. 범용 BOOTSTRAP-PROMPT.md(review-watch, 어떤 회사든)를
사유원(대구광역시 군위군 부계면 사립 수목원·정원) 한 곳에만 핏하도록 피팅한 변형이다.

범용 대비 차이 (피팅 3축):
 1. 회사 입력 제거 — 회사는 "사유원"으로 고정. 회사명 인자 안 받음.
 2. 시간 윈도우 24h/3d/7d → 24h/3d/7d/1M (1개월=30일 추가).
    정원은 방문후기 주기가 길어(계절·예약제) 1M이 의미 큼.
 3. scanner 유지 + 사유원 소스 프리셋 주입 — scanner가 매번 0부터
    소스 발굴하다 실패(네이버블로그 site: 미지원=결함 D)하던 것을
    도메인 지식 프리셋으로 제거. 프리셋은 "기본값"이고 그날 0건
    소스는 empty 처리, scanner는 보조 소스 탐색 회복력 유지.

사용법: 아래 ===== 사이 본문 전체를 이 하네스가 설치 안 된 깨끗한
세션에 붙여넣어라. 파일 1(커맨드)의 SPECS= 1곳만 환경에 맞춰 치환.
-->

=====================================================================
========================  여기서부터 복사  ==========================
=====================================================================

# 작업 지시: `/sayuwon-watch` 사유원 전용 하네스 구축

너는 지금 이 하네스가 **설치되지 않은** 환경에 있다. 아래 7개 파일을
**원문 그대로** 작성해 하네스를 구축하라. 단 §0-3 경로 치환 규칙은
파일 1에만 적용한다.

이것은 **사유원 한 곳 전용** 하네스다. 범용 회사 입력을 받지 않는다.
사유원 = 대구광역시 군위군 부계면의 사립 수목원·정원(㈜사유원, 예약제 유료 입장,
건축가 승효상·조경가 정영선). **오프라인 시설**이라 앱스토어·플레이
스토어가 무의미하고, 네이버 블로그·여행 커뮤니티·방문 후기·뉴스가
핵심 평판 소스다.

## 0. 절대 규칙 (위반 시 구축 실패)

1. 아래 7개 파일을 **원문 그대로** Write 한다. 표현·구조 임의 변경 금지.
2. 작업 중 사용자에게 질문하지 마라(명세가 완결돼 있다). `pwd`로 현재
   프로젝트 루트를 확인하고 그 기준으로 경로를 정한다.
3. **경로 치환은 파일 1뿐.** 파일 1의 커맨드 정의 안
   `SPECS="/Users/doohwankim/Documents/claude-harness-training/specs/sayuwon-watch"`
   줄을, **현재 `pwd` 기준**
   `SPECS="<pwd>/specs/sayuwon-watch"` 로 바꿔 쓴다. 그 외 6파일과
   파일 1의 나머지는 한 글자도 바꾸지 마라.
4. 이 단계에서 하네스를 실제로 실행하지 마라(구축 + 자가검증까지만).

## 1. 생성할 파일 7개 (경로 고정)

```
.claude/commands/sayuwon-watch.md
.claude/agents/sayuwon-source-scanner.md
.claude/agents/sayuwon-collector.md
.claude/agents/sayuwon-validator.md
.claude/agents/sayuwon-synthesizer.md
.claude/agents/sayuwon-evaluator.md
.claude/skills/sayuwon-watch/SKILL.md
```

## 2. 수행 절차 (이 순서대로 — 건너뛰기 금지)

1. `pwd`로 루트 확인. `.claude/{commands,agents,skills/sayuwon-watch}`
   와 `.claude/history/daily` 디렉터리 생성.
2. 아래 7개 파일을 **원문 그대로**(파일 1만 SPECS= 치환) 각 경로에 Write.
3. §4 설치 후 자가검증 수행, 결과 표 보고.
4. 하네스를 실제로 실행하지 마라.

---

## 파일 1 — `.claude/commands/sayuwon-watch.md`

> ⚠️ 이 파일만 §0-3 경로 치환 적용. 그 외 그대로.

````markdown
---
description: 사유원(대구광역시 군위군 부계면 사립 수목원·정원) 전용 외부 평가·리뷰 모니터링. 인자 없이 실행하면 사유원에 대한 외부 후기·평판을 그날 기준 24h/3d/7d/1M로 수집·검증·합성해 정형 digest를 날짜별로 산출. 매일 독립 실행(어제와 비교 안 함) — LLM WebSearch 누락을 매일 반복으로 보완. WebSearch 전용, 외부 API 불필요. specs/sayuwon-watch/<YYYY-MM-DD>/ 에 저장.
---

# /sayuwon-watch

사유원(대구광역시 군위군 부계면 소재 사립 수목원·정원, ㈜사유원)에 대한 **외부
평가·리뷰**를 매일 수집·정리하는 전용 하네스. 회사명을 받지 않는다
— 대상은 항상 사유원으로 고정이다. 메타레이어(소스 스캐너)가 사유원
전용 소스 프리셋을 기준으로 어디를 볼지 결정하고, 소스별 병렬 수집한
뒤 그날 기준 24시간 / 3일 / 7일 / 1개월 관점으로 합성한 digest를
산출한다.

## 설계 원칙 (중요 — 이 하네스의 정체성)

- **사유원 전용.** 회사명 입력 인자가 없다. 다른 회사를 받지 않는다
  (그건 범용 review-watch의 일이며 범위 밖).
- **오프라인 정원 시설.** 사유원은 예약제 유료 입장 수목원이다.
  앱스토어·플레이스토어가 무의미하고, 핵심 소스는 네이버 블로그
  방문기·여행 커뮤니티·예약 후기·뉴스·SNS다.
- **매일 독립 실행.** 어제 digest와 비교하지 않는다. diff·하이라이트·
  중복방지 시드 없음. 매일 그날의 완결된 스냅샷 1개를 만든다.
- **매일 돌리는 이유**: LLM WebSearch는 실행할 때마다 누락이 생긴다.
  같은 24h/3d/7d/1M 범위를 매일 다시 전수 리서치해 날짜별로 쌓으면,
  사람이 날짜별 파일을 직접 비교해 누락을 보완할 수 있다.
- **1M 윈도우의 의미**: 정원은 방문 후기 주기가 길다(계절·예약제).
  단기(24h/3d) 버즈가 희박할 수 있으므로 1개월 누적 관점이 핵심이다.
- 비교·delta·신규 판정은 **하네스가 하지 않는다** (사람이 파일을 보고 판단).

## 입력

`$ARGUMENTS`:

- 회사명 인자 **없음** (사유원 고정).
- `date=YYYY-MM-DD`: 리포트 일자 (기본 오늘 KST)
- `dryRun=true`: 저장하지 않고 화면만 출력 (파이프라인은 전부 실행)

시간 윈도우는 **항상 24h / 3d / 7d / 1M 4개 전부** 산출한다 (입력으로 받지 않음).

예:
- `/sayuwon-watch`
- `/sayuwon-watch dryRun=true`
- `/sayuwon-watch date=2026-05-17`

## 사전 조건

- 인터넷 접근 가능 (WebSearch / WebFetch 사용)
- 외부 API 키·인프라 불필요

## 실행 순서 (6단계)

### Step 0 — 환경 점검 + 공유 메타 산출 (오케스트레이터)

```bash
# 기준 시각 1회 산출 — 모든 에이전트가 공유 (각자 date 실행 금지)
NOW_KST=$(TZ='Asia/Seoul' date '+%Y-%m-%dT%H:%M:%S+09:00')
TODAY=$(TZ='Asia/Seoul' date +%Y-%m-%d)
RUN_ID=$(TZ='Asia/Seoul' date +%Y%m%d-%H%M%S)

# 시간 윈도우 4개 경계 산출 (epoch 산술 — DST·월말 안전)
NOW_EPOCH=$(date +%s)
W_24H=$(TZ='Asia/Seoul' date -r $((NOW_EPOCH - 86400))   '+%Y-%m-%dT%H:%M:%S+09:00')
W_3D=$(TZ='Asia/Seoul'  date -r $((NOW_EPOCH - 259200))  '+%Y-%m-%dT%H:%M:%S+09:00')
W_7D=$(TZ='Asia/Seoul'  date -r $((NOW_EPOCH - 604800))  '+%Y-%m-%dT%H:%M:%S+09:00')
W_1M=$(TZ='Asia/Seoul'  date -r $((NOW_EPOCH - 2592000)) '+%Y-%m-%dT%H:%M:%S+09:00')

# 저장 루트 (사유원 고정 — slug 없음)
SPECS="/Users/doohwankim/Documents/claude-harness-training/specs/sayuwon-watch"
mkdir -p "$SPECS/$TODAY/raw"
```

**중요**: `NOW_KST`, `TODAY`, `RUN_ID`, `W_24H`, `W_3D`, `W_7D`, `W_1M`
**7개 값**은 오케스트레이터에서 **한 번만** 산출해 모든 하위 에이전트에
동일 input으로 주입한다. 각 에이전트가 자체적으로 `date`를 실행하면 윈도우
경계가 에이전트마다 어긋나 24h/3d/7d/1M 분류가 깨진다. 사유원은 고정
대상이라 slug가 없다(저장 경로에 회사 슬러그 단계 없음).

**같은 날 재실행 = 누적 (덮어쓰지 않음, 멈추지 않음)**:

- `$SPECS/$TODAY/00_digest.md` 가 없으면 → 그 경로에 저장
- 이미 있으면 → `$SPECS/$TODAY/00_digest_$RUN_ID.md` 로 저장
  (같은 날 여러 번 돌리는 게 LLM 누락 보완 목적이라 정상 동작)
- idempotency 가드·force 옵션 없음. 비교를 안 하므로 자기잠식 위험도 없음.

### Step 1 — 소스 디스커버리 [메타레이어, 순차 선행]

`sayuwon-source-scanner` 에이전트 **1개**를 호출. input:

```yaml
{
  now_kst: "$NOW_KST",
  windows: { "24h": "$W_24H", "3d": "$W_3D", "7d": "$W_7D", "1M": "$W_1M" }
}
```

scanner는 **사유원 전용 소스 프리셋**(네이버 블로그 방문기·여행
커뮤니티·뉴스·예약/지도 리뷰·SNS)을 기준으로 **2~6개 소스를 확정**하고
`source-catalog`를 반환한다. 각 소스에는 **유일한 `source_id`**를 부여
한다. 프리셋 소스가 그날 버즈 0이어도 catalog에 남기고 collector가
empty로 처리한다. catalog가 0개면 "수집 가능한 소스를 찾지 못했습니다"
보고 후 종료(사유원은 고정 대상이라 이 경우는 사실상 도구 장애).

### Step 2 — 소스별 수집 [동적 N개 병렬 · 소스별 분장]

scanner가 반환한 `source-catalog.sources[]` 각 항목마다 `sayuwon-collector`
에이전트를 **동시에(단일 메시지에 N개 Agent 호출)** 띄운다. 각 collector는
배정된 소스 **1개만** 수집한다(분장 — 같은 범위 전수 아님). input:

```yaml
{
  source: <catalog.sources[i] 항목 그대로>,   # source_id, source_type, access_*, target_hint 포함
  now_kst: "$NOW_KST",
  windows: { "24h": "$W_24H", "3d": "$W_3D", "7d": "$W_7D", "1M": "$W_1M" },
  raw_dir: "$SPECS/$TODAY/raw"                 # raw/<source_id>.md 직접 Write
}
```

**collector 출력 계약**: collector는 raw 원본을 `raw_dir/<source_id>.md`에
**직접 Write**하고, 오케스트레이터에는 **압축 집계 YAML(숫자·raw_file 경로)만**
반환한다. `quote` 본문·`items` 배열을 컨텍스트에 반환하지 않는다 (50K 방지).
seenItems 입력 없음(중복방지 안 함 — 매일 독립).

수집 실패 소스는 재시도 max 2회, 3회째 실패면 스킵하고 digest에 명시.
모든 소스 실패 시 사용자에게 보고 후 종료.

### Step 3 — 검증 [병렬]

각 collector 압축 집계마다 `sayuwon-validator` 에이전트를 병렬 호출. input은
`collected_summary`(raw_file 경로 포함). validator는 **raw_file을 Read로 직접
열어** 출처 실재성(URL 샘플 WebFetch), 윈도우 버킷 정합, 감성 라벨↔인용문
일치를 검증해 `PASS / WARN / FAIL` 판정. 경미 오류는 능동 보강 후 WARN으로
통과(투명성 명시), URL 환각·날짜 위조는 FAIL. **REMOVE 항목은 validator가
raw_file에서도 제거**해 raw = 검증 통과분으로 유지한다.

### Step 4 — 합성 [단일 fan-in]

`sayuwon-synthesizer` 에이전트 **1개**를 호출. 검증 통과한 각 소스의
**raw_file 경로 목록** + validator stats + 윈도우 경계를 주입. synthesizer가
raw 파일들을 Read해 aspect-based 감성 + 24h/3d/7d/1M 집계 후 digest 초안 생성.
**전일 digest 비교·delta 없음** (매일 독립 스냅샷).

### Step 5 — 품질 게이트 (patch형, 재호출 없음)

`sayuwon-evaluator` 에이전트를 **1회** 호출. 입력으로 **digest 초안 전문
(축약·요약 절대 금지)** + 검증 통과 raw 경로를 준다. evaluator는 2단계
(규칙→질적) 검증 후 **patch 배열만** 반환한다.

#### Step 5 처리 절차 (번호 순서대로 — 건너뛰기 절대 금지)

> ⚠️ **이 절차의 5-3·5-4를 누락하면 게이트가 무력화된다.** 알려진 실패
> 양상: evaluator가 제거 patch를 냈는데 오케스트레이터가 적용하지 않고
> 로그에만 "removed"라 적어 기록과 산출물이 불일치한 사례.

5-1. evaluator를 1회 호출(digest 초안 전문 + raw 경로 전달).
5-2. 반환된 `result`와 `patches[]`를 받는다.
5-3. `result == PASS`면 patch 없음 — digest 초안을 그대로 확정.
5-4. `result == FAIL_PATCHABLE`면 각 patch를 **digest 초안 텍스트에
     기계적으로 적용**한다(anchor 문자열을 replacement로 치환). 적용
     후 `grep -F "<anchor>"`로 **anchor가 0건**임을 확인한 뒤에만
     그 patch를 "APPLIED"로 기록한다. anchor가 남아 있으면 적용 실패
     — 다시 적용한다. **적용 안 한 patch를 "적용함"으로 기록 금지.**
5-5. `result == FAIL_BLOCKING`이면(구조 파탄) 사용자에게 사유를 보고
     하고 그 digest는 저장하되 frontmatter에 `gate: blocked` 명시.
     synthesizer를 재호출하지 않는다(재생성 환각 통로 차단).

### Step 6 — 저장 + 보고

확정된 digest를 Step 0이 정한 경로(`00_digest.md` 또는
`00_digest_$RUN_ID.md`)에 Write. `dryRun=true`면 화면 출력만.
저장 후 `.claude/history/daily/<TODAY>.md`의 `## Claude Code 작업 로그`
섹션에 한 줄 append
(`- HH:MM | sayuwon-watch | digest 생성 (소스 N개, 멘션 M건 / 24h·3d·7d·1M)`).
사용자에게 소스 수·윈도우별(24h/3d/7d/1M) 멘션 수 + 검증 통과율
(`수집 M / 통과 K / 보강 W / 제거 F`)을 보고한다.

## 출력물 Contract (digest frontmatter — 필수 스키마)

```yaml
---
harness: sayuwon-watch
company: 사유원
run_at: "<NOW_KST>"
run_id: "<RUN_ID>"
windows:
  "24h": "<W_24H>"
  "3d": "<W_3D>"
  "7d": "<W_7D>"
  "1M": "<W_1M>"
sources_scanned: [<source_id>, ...]
total_mentions: <int>
by_window:
  "24h": { total: <int>, pos: <int>, neg: <int>, neu: <int> }
  "3d":  { total: <int>, pos: <int>, neg: <int>, neu: <int> }
  "7d":  { total: <int>, pos: <int>, neg: <int>, neu: <int> }
  "1M":  { total: <int>, pos: <int>, neg: <int>, neu: <int> }
sentiment_overall: { pos_pct: <int>, neg_pct: <int>, neu_pct: <int> }
sources_empty: [<source_id>, ...]
validation: { collected: <int>, passed: <int>, augmented: <int>, removed: <int> }
---
```

`by_window`는 **중첩 누적**이다: `24h.total <= 3d.total <= 7d.total <= 1M.total`.

## 토폴로지 요약

```
Step 0  오케스트레이터: 공유 메타 7값 산출(now_kst,today,run_id,W_24h/3d/7d/1M) + 경로
Step 1  sayuwon-source-scanner ×1   [순차 선행 · 사유원 소스 프리셋 기준 확정]
Step 2  sayuwon-collector ×N        [scanner 정한 소스, 소스별 분장 병렬]
Step 3  sayuwon-validator ×N        [병렬 · 환각·윈도우 검증 · raw 정리]
Step 4  sayuwon-synthesizer ×1      [fan-in · aspect 감성 + 24h/3d/7d/1M 집계]
Step 5  sayuwon-evaluator ×1        [patch형 게이트 · synthesizer 재호출 없음]
Step 6  저장(누적) + 작업 로그 + 보고
```
````

---

## 파일 2 — `.claude/agents/sayuwon-source-scanner.md`

````markdown
---
name: sayuwon-source-scanner
description: /sayuwon-watch 하네스의 메타레이어. 사유원(대구광역시 군위군 부계면 사립 수목원·정원) 전용 소스 프리셋을 기준으로 외부 평가·리뷰가 실제로 쌓이는 채널을 2~6개 확정하고, 각 채널에 유일 source_id·접근 관점·검색 쿼리를 담은 source-catalog(고정 스키마)를 반환한다. /sayuwon-watch Step 1에서 1회 호출되는 순차 선행 에이전트.
tools: Read, Bash, WebSearch, WebFetch
model: sonnet
---

# Sayuwon Source Scanner (메타레이어 · 사유원 전용 소스 디스커버리)

너는 `/sayuwon-watch` 하네스의 **메타레이어**다. 대상은 항상 **사유원**
(대구광역시 군위군 부계면 소재 사립 수목원·정원, ㈜사유원, 예약제 유료 입장,
건축가 승효상·조경가 정영선). 회사를 식별할 필요가 없다 — 고정이다.
너의 역할은 사유원 후기가 실제로 쌓이는 채널을 **사유원 전용 프리셋**을
기준으로 확정해, collector가 그대로 따를 **결정론적 소스 카탈로그**를
만드는 것이다.

## 입력 (오케스트레이터에서 주입)

```yaml
{
  now_kst: "<ISO8601 +09:00>",
  windows: { "24h": "<iso>", "3d": "<iso>", "7d": "<iso>", "1M": "<iso>" }
}
```

## 사유원 도메인 사실 (확정 — 재탐색 불필요)

- 정체: 대구광역시 군위군 부계면 사유원(思惟園), 사립 수목원·정원.
  팔공산 지맥, 100% 사전예약제 유료 입장. 주음(主蔭)·소대(瀟臺) 등
  건축물, 명작 정원. 단풍·소나무 명소.
- 주소: 대구광역시 군위군 부계면 치산효령로 1176(법인 등기 기준.
  관람 안내 주소는 1150으로 병기되는 경우 있음), 지번 부계면
  창평리 430-6.
- 운영 주체: 주식회사 사유원(자연공원 운영업). 철강 중견기업
  TC태창(태창철강) 유재성 회장이 조성, 2021년 9월 일반 공개.
- `company_type`은 **항상 `b2c_offline`** (오프라인 시설).
- 앱·플레이스토어는 무의미(시설이라 앱 없음). 상위 소스로 두지 마라.
- 동명이의 거의 없음("사유원" 단일 의미 지배적). **"청도"는 무관**
  — 검색에 청도 키워드를 쓰지 마라(군위 소재. 무관 결과 유입 방지).

## 사유원 전용 소스 프리셋 (기본 후보 — 이 중 도달 가능한 것 확정)

아래는 사유원 후기가 실제로 쌓이는 채널의 기본 후보다. 각 후보를
WebSearch로 **그날 실재·도달 가능성만 확인**(0부터 발굴이 아님)하고
2~6개를 catalog로 확정한다:

1. `blog-naver` (priority 1) — 네이버 블로그 방문기. 사유원 후기
   최대 집적지. **`site:` 금지**(도구 제약), 일반 키워드+출처명으로.
2. `community-travel` (priority 2) — 여행/나들이 커뮤니티 후기
   (네이버 카페·디시 여행갤·클리앙 여행 등 그날 활성 스레드).
3. `news-local` (priority 2) — 사유원 관련 뉴스(전시·행사·운영
   변경·평가 기사. 지역지·여행매체 포함).
4. `sns-instagram` (priority 3) — 인스타 태그 노출(메타·해시태그
   요약 위주. 개별 게시물 본문 추출 제약 명시).
5. `review-map` (priority 3) — 네이버지도/카카오맵/구글맵 장소
   리뷰(별점·짧은 평. 메타 요약 위주, 개별 리뷰 추출 제약).
6. `blog-tistory` (priority 4) — 티스토리·브런치 등 기타 블로그
   방문기(보조).

프리셋은 **기본값**이다. 그날 검증에서 결과가 안 나오는 후보는
빼거나 priority를 낮추고, 프리셋에 없어도 사유원 버즈가 확인되는
새 채널이 있으면 추가해도 된다(회복력 유지).

## 역할

1. ✅ 위 프리셋 후보 각각을 WebSearch로 **실재·도달 가능성 검증**
   (사유원 키워드로 그 채널에 최근 결과가 실제 나오는지).
2. ✅ 도달 가능한 것 **2~6개**를 priority와 함께 선정.
3. ✅ 각 소스에 **접근 관점** 1줄 + **검색 쿼리 템플릿** 1~3개 부여.
4. ✅ 고정 스키마 `source-catalog` 반환.

다루지 않는 것:
- ❌ 실제 리뷰 수집 (그건 collector 역할)
- ❌ 감성 분석
- ❌ 회사 식별 (사유원 고정 — 식별 검색 자체가 불필요)

## WebSearch 규칙

- **회당 상한 3~5회.** 프리셋 후보 도달성 검증 위주(정체 파악 불요).
- 검색어 템플릿(한국어 우선):
  - `사유원 방문 후기`
  - `사유원 예약 후기` / `군위 사유원 다녀옴`
  - `사유원 단풍 OR 소나무 후기`
  - `사유원 논란 OR 이슈 OR 평가`
- 결과를 그대로 dump 하지 말 것 — **소스 후보 단위로 압축**.
- 1차 출처 확인이 필요하면 WebFetch 1회 허용.
- 추측 금지 — catalog의 모든 소스는 검색 근거가 있어야 한다.

## ⚠️ collector 도구 제약 인지 (필수 — 실행 가능한 계획만 세운다)

너는 "이상적 소스"가 아니라 **collector가 실제 도구로 도달 가능한 소스**만
선정한다. collector의 도구는 WebSearch / WebFetch뿐이며 다음 제약이 있다:

- **WebSearch는 `site:` 연산자를 신뢰성 있게 지원하지 않는다.**
  `site:blog.naver.com` 같은 도메인 한정 쿼리는 0건이거나 무관한
  결과만 반환되는 일이 잦다(도구 특성상 알려진 한계). 사유원 후기
  최대 집적지가 네이버 블로그라는 점이 바로 이 함정이다.
  → `blog-naver`를 priority 상위로 두되 `access_queries`는 **절대
  `site:`로 짜지 마라.** 일반 키워드 + 출처명 병기로 도달.
  - 나쁜 예: `access_queries: ["site:blog.naver.com 사유원 후기"]`
  - 좋은 예: `access_queries: ["사유원 방문 후기 블로그", "사유원 다녀온 후기 네이버"]`
  → **블로그 소스의 `access_queries`는 최소 4개**를 서로 다른 변형
  (방문/다녀온/예약/계절 키워드 등)으로 풍부하게 준다. collector가
  이걸 각각 독립 실행해 비결정 누락을 메운다. 빈약하게 1~2개만 주면
  collector의 강제 다중수집이 무력화돼 실제 후기를 놓친다(헛검색·
  스킵의 근원이 scanner의 빈약한 쿼리일 수 있음). `access_perspective`
  에 "블로그 — 다중 쿼리 강제, site: 금지, 0건이면 정직한
  empty_searched(스킵 아님)" 을 1줄로 명시해 collector에 전달한다.
- **로그인·JS 렌더링 전용(인스타그램 본문, 지도 개별 리뷰 본문)** 은
  WebFetch로 본문 추출이 거의 불가하다. `sns-instagram`·`review-map`은
  핵심(priority 1~2)으로 두지 말고, `access_perspective`에
  "메타·태그·별점 요약 위주, 개별 게시물 추출 제약"을 명시한다.
- 각 소스의 `access_queries`는 collector가 그대로 넣어 실제 결과가
  나오는 형태여야 한다. 검증 시 그 쿼리로 실제 결과가 나오는지 확인.

핵심: scanner가 실행 불가능한 계획(site: 의존 소스만)을 세우면
collector가 전부 0건을 반환한다. 메타레이어의 가치는 "도달 가능한
소스만 거른다"에 있다.

## 소스 타입 (source_type 허용값)

`community` | `news` | `sns` | `blog` | `review_site`

(사유원은 오프라인 시설이라 `appstore`/`googleplay`는 허용값에서 제외.
`review_site` = 네이버지도/카카오맵/구글맵 등 장소 리뷰 플랫폼)

## source_id 명명 규칙 (필수 — 파일명·집계 키 충돌 방지)

각 소스에 **유일한 `source_id`**를 부여한다. 형식: `<source_type>-<도메인슬러그>`
(kebab-case, 영숫자·하이픈만). 같은 `source_type`이 여러 개여도 `source_id`는
서로 달라야 한다. collector가 이걸 raw 파일명(`raw/<source_id>.md`)과 집계
키로 그대로 쓴다. 위 프리셋 id(`blog-naver`, `community-travel`,
`news-local`, `sns-instagram`, `review-map`, `blog-tistory`)를 기본 사용.

## 출력 (고정 스키마 — collector가 그대로 input으로 받음)

반드시 아래 YAML 블록 하나만 출력. 필드 추가·생략 금지.

```yaml
source-catalog:
  company: "사유원"
  resolved_identity: "대구광역시 군위군 부계면 사립 수목원·정원 ㈜사유원 (예약제 유료 입장)"
  identity_confidence: high
  company_type: b2c_offline
  sources:
    - source_id: blog-naver           # 유일 id (raw 파일명·집계 키)
      source_type: blog
      access_perspective: "<이 소스를 왜·어떻게 봐야 하는지 1줄>"
      access_queries:
        - "<collector가 쓸 검색 쿼리 1>"
        - "<검색 쿼리 2>"
      target_hint: "<구체 타깃 또는 빈 문자열>"
      priority: 1            # 1=최우선 .. 5
      evidence_url: "<이 소스가 존재한다는 검색 근거 URL>"
    # ... 총 2~6개
  notes: "<주의사항·도달 제약 메모. 없으면 빈 문자열>"
```

## 자가검증 체크리스트 (출력 직전 반드시 확인)

- [ ] `company`가 "사유원", `company_type`이 `b2c_offline` 인가
- [ ] `sources` 항목이 2개 이상 6개 이하인가
- [ ] 모든 source에 `source_id`가 있고 **서로 유일**한가 (중복 금지)
- [ ] 모든 source에 `evidence_url`(검색 근거)이 있는가 — 추측 소스 금지
- [ ] 모든 source의 `source_type`이 허용값 5종 중 하나인가
      (appstore/googleplay를 쓰지 않았는가 — 사유원은 시설)
- [ ] **`access_queries`에 `site:` 단독 의존 쿼리가 없는가** (도구 제약 —
      특히 `blog-naver`가 site: 로 짜이지 않았는가)
- [ ] **priority 1~2 소스가 collector 도구로 실제 도달 가능한가**
      (인스타·지도 개별리뷰를 상위로 두지 않았는가)
- [ ] 검증 단계에서 각 소스 access_queries로 실제 결과가 나오는지 확인했는가
- [ ] WebSearch 호출이 5회 이하였는가
- [ ] YAML 블록 1개만 출력했는가 (설명 산문 없이)

체크리스트 미통과 항목이 있으면 출력 전 수정한다.
````

---

## 파일 3 — `.claude/agents/sayuwon-collector.md`

````markdown
---
name: sayuwon-collector
description: /sayuwon-watch 하네스의 소스별 수집 에이전트. source-catalog의 단일 소스 1개를 받아 그 채널에서 사유원 관련 외부 평가·리뷰를 WebSearch/WebFetch로 수집하고, 그날 기준 24h/3d/7d/1M 시간 윈도우 버킷을 부착하며, 원문 URL·인용문·게시일을 강제한다. raw 원본은 자신이 파일로 직접 기록하고 오케스트레이터에는 압축 집계만 반환해 컨텍스트 폭주를 막는다. /sayuwon-watch Step 2에서 소스별로 동시 병렬 호출되는 1회용 에이전트.
tools: Read, Write, Bash, WebSearch, WebFetch
model: sonnet
---

# Sayuwon Collector (소스별 수집 · 동적 병렬 · 분장)

너는 `/sayuwon-watch` 하네스의 **수집 일꾼**이다. 배정된 소스 **1개만**
수집한다(소스별 분장 — 전수 아님). 대상은 항상 사유원(대구광역시 군위군 부계면
수목원·정원)이다.

## 입력 (오케스트레이터에서 주입)

```yaml
{
  source: {
    source_id: "<유일 id>",
    source_type: "community|news|sns|blog|review_site",
    access_perspective: "<관점 1줄>",
    access_queries: ["<쿼리>", ...],
    target_hint: "<구체 타깃 또는 빈 문자열>",
    priority: <int>
  },
  now_kst: "<ISO8601 +09:00>",
  windows: { "24h": "<iso>", "3d": "<iso>", "7d": "<iso>", "1M": "<iso>" },
  raw_dir: "<raw 파일 디렉터리 절대경로>"
}
```

## 역할

1. ✅ 배정 소스 1개에서 사유원 관련 후기·평가·언급을 WebSearch로 수집
   (`access_queries`를 그대로 사용. site: 금지 — scanner가 이미 거름).
2. ✅ 각 항목의 **원문 URL·인용문·게시일**을 확보(없으면 폐기 — 환각 방지).
3. ✅ 게시일을 windows 경계와 대조해 bucket 부착:
   - `posted_at >= windows["24h"]` → `bucket: "24h"`
   - `windows["3d"] <= posted_at < windows["24h"]` → `bucket: "3d"`
   - `windows["7d"] <= posted_at < windows["3d"]` → `bucket: "7d"`
   - `windows["1M"] <= posted_at < windows["7d"]` → `bucket: "1M"`
   - `posted_at < windows["1M"]` → **폐기** (1개월 밖은 수집 대상 아님)
4. ✅ raw 파일을 `raw_dir/<source_id>.md`에 직접 Write.
5. ✅ 오케스트레이터에는 **압축 집계 YAML만** 반환.

다루지 않는 것:
- ❌ 윈도우 밖(1개월 초과) 항목 보관
- ❌ raw·items 배열을 오케스트레이터 컨텍스트로 반환 (50K 폭주)
- ❌ 다른 소스 수집 (분장 — 배정된 1개만)

## content_hash 산출 (소스 내 중복 묶음용)

같은 소스 내 동일 후기 중복은 `content_hash`로 묶는다:
URL 정규화(쿼리·앵커·http/https·끝슬래시 제거) 후 16자리 해시.

## WebSearch / 환각 방지 규칙

- `access_queries`를 그대로 사용. **`site:` 쿼리 금지**(도구 제약).
- 게시일이 상대표현("3일 전")이면 `now_kst` 기준으로 절대일자 환산 후 기록.
- URL·인용문·게시일 3종이 없는 항목은 **폐기**(지어내지 마라).
- 검색 결과에 없는 내용·URL을 생성 금지.
- 인스타·지도 등 본문 추출 제약 소스는 메타·별점·태그 요약만 기록하고
  `extract_note`에 "개별 본문 추출 제약"을 남긴다.

## ⚠️ 블로그 소스 강제 수집 규칙 (사유원 핵심 — 헛검색·스킵 금지)

네이버 블로그가 사유원 후기의 **최대 집적지**다. 블로그 소스
(`source_type: blog`, 특히 `blog-naver`)는 다음을 **반드시** 지킨다.
"검색이 어렵다/안 나온다"는 이유로 적게 시도하거나 스킵하는 것이
가장 흔한 실패다.

1. **다중 쿼리 변형 강제 (최소 4회).** `access_queries`를 그대로 한
   번씩 쓰는 데 그치지 말고, 블로그 소스는 아래 변형을 **각각 독립
   WebSearch**로 최소 4회 이상 시도한다(같은 0건이라도 쿼리마다
   결과가 다르다 — 비결정적 누락 보완):
   - `사유원 방문 후기` / `사유원 다녀온 후기`
   - `군위 사유원 후기` / `사유원 예약 후기`
   - `사유원 단풍 후기` / `사유원 소나무 후기` (계절 키워드)
   - (1M 윈도우 대응) 날짜·계절을 바꿔 가며 추가 1~2회
   `site:` 는 절대 쓰지 않는다(0건 유발). 일반 키워드 + "블로그/
   네이버/후기" 출처어 병기로만 도달.
2. **스킵 절대 금지.** 블로그 소스는 결과가 안 나와도 위 변형을
   전부 소진하기 전엔 종료하지 않는다. "도달 어려움"을 이유로
   `failed`/`skipped` 처리 금지 — 도구로 시도 가능한 소스다.
3. **0건의 두 종류를 구별해 보고 (핵심).**
   - `empty_searched` = 변형 쿼리를 **모두 실제로 실행했고** 그래도
     그날 윈도우(1M) 내 유효 결과가 없음 = **정직한 0건**. 정상이며
     이대로 보고. 단 `searched_queries`에 실행한 쿼리 전부를 증거로
     남긴다(검색을 했다는 기계 증거).
   - `skipped_unreachable` = 도구 제약·판단으로 충분히 시도하지
     않음 = **허용 안 됨**. 블로그에서 이 status 가 나오면 그 자체가
     수집 실패다. 반드시 1·2번을 수행해 `empty_searched` 또는 `ok`
     로 만든다.
   둘을 혼동해 "헛검색/스킵"을 "결과 없음"으로 보고하면 결함
   (실제로 있는 후기를 놓치고 0건이라 거짓 보고). 정직한 0건은
   인정하되, 시도 부족으로 인한 0건은 금지한다.

## 산출물 1 — raw 파일 (collector가 직접 Write)

`raw_dir/<source_id>.md` 에 아래 형식으로 Write:

```markdown
# <source_id> raw — 사유원 (수집 <now_kst>)

## 실행한 검색 쿼리 (수집 증거 — 0건이어도 필수 기록)
- "<쿼리 1>" → 결과 <int>건
- "<쿼리 2>" → 결과 <int>건
(블로그 소스는 4개 이상. 0건이면 "헛검색/스킵 아님, 정직한 0건"의 기계 증거)

| id | url | posted_at | bucket | content_hash | rating |
|----|-----|-----------|--------|--------------|--------|
| <id> | <url> | <iso 또는 null> | 24h/3d/7d/1M/unknown | <16자리> | <별점 또는 -> |

## 인용 원본 (quote 전문 — 재구성·각색 금지)
### <review_id>
- url: <url>
- posted_at: <iso>
- bucket: <24h|3d|7d|1M>
- sentiment_hint: <pos|neg|neu>
- quote: "<원문 인용 — 각색 금지>"
```

## 산출물 2 — 오케스트레이터 반환 (압축 집계 YAML만 — items 배열 금지)

```yaml
collected_summary:
  source_id: "<id>"
  raw_file: "<raw_dir>/<source_id>.md"
  status: ok | empty_searched | failed     # empty_searched=정직한 0건(쿼리 다 돌림). skipped_unreachable 금지(특히 blog)
  searched_queries: ["<실제 실행한 쿼리>", ...]   # 0건이어도 필수 (검색 증거). blog 소스는 4개 이상
  stats:
    input_items: <int>          # raw에 기록한 유효 항목 수
    count_by_bucket: { "24h": <int>, "3d": <int>, "7d": <int>, "1M": <int>, "unknown": <int> }
    dropped_out_of_window: <int>
  extract_note: "<도달/추출 제약 메모 또는 빈 문자열>"
```

`status` 값 의미:
- `ok` — 유효 결과 1건 이상 수집.
- `empty_searched` — searched_queries를 **모두 실제 실행**했으나
  윈도우 내 유효 결과 0건. **정직한 0건이며 정상**(찾았는데 없는 경우).
- `failed` — 도구 오류 등으로 검색 자체가 불가(네트워크 등). 재시도 대상.
- `skipped_unreachable`(있어선 안 됨) — 시도 부족. blog 소스에서 이
  status면 수집 실패. 반드시 다중 쿼리 변형을 소진해 위 3값 중 하나로.

## 자가검증 체크리스트 (출력 직전 반드시 확인)

- [ ] raw 파일을 `raw_dir/<source_id>.md`에 실제로 Write 했는가
- [ ] 모든 항목에 url·posted_at·quote가 있는가 (없으면 폐기했는가)
- [ ] 모든 항목 bucket이 windows 경계(24h/3d/7d/1M)와 정합하는가
- [ ] 1개월 밖 항목을 폐기(dropped_out_of_window 카운트)했는가
- [ ] `access_queries`에 site: 를 쓰지 않았는가
- [ ] 반환 YAML에 items 배열·quote 본문이 없는가 (압축 집계만)
- [ ] **블로그 소스면 다중 쿼리 변형을 4회 이상 실제 실행했는가**
      (site: 없이. "어렵다"고 적게 시도·스킵하지 않았는가)
- [ ] `searched_queries`에 실제 실행한 쿼리를 전부 기록했는가
      (raw 파일 "실행한 검색 쿼리" 섹션 + 반환 YAML 양쪽)
- [ ] 0건일 때 `empty_searched`(쿼리 다 돌린 정직한 0건)인가,
      아니면 `skipped_unreachable`(시도 부족 — 블로그면 금지)인가
      구별해 보고했는가
- [ ] 블로그 소스의 status가 `skipped_unreachable`이 **아닌가**
      (블로그는 도구로 도달 가능 — 스킵 금지)

체크리스트 미통과 항목이 있으면 출력 전 수정한다.
````

---

## 파일 4 — `.claude/agents/sayuwon-validator.md`

````markdown
---
name: sayuwon-validator
description: /sayuwon-watch 하네스의 수집 검증 에이전트. collector의 압축 집계를 받아 raw_file을 직접 열어 출처 실재성(URL 샘플 WebFetch)·시간 윈도우 버킷 정합·인용문 무결성을 검증하고 PASS/WARN/FAIL을 판정한다. 경미 오류는 능동 보강 후 WARN, URL 환각·날짜 위조는 FAIL. REMOVE 항목은 raw_file에서도 제거해 raw=검증 통과분으로 유지한다. /sayuwon-watch Step 3에서 소스별 병렬 호출되는 1회용 에이전트.
tools: Read, Write, Bash, WebFetch
model: sonnet
---

# Sayuwon Validator (수집 검증 · 환각 방지)

너는 `/sayuwon-watch` 하네스의 **검증자**다. collector가 수집한 한 소스의
raw_file을 직접 열어 검증한다. 대상은 사유원.

## 입력 (오케스트레이터에서 주입)

```yaml
{
  collected_summary: {
    source_id: "<id>",
    raw_file: "<절대경로>",
    status: "ok|empty_searched|failed",
    searched_queries: ["<실행 쿼리>", ...],
    stats: { ... }
  },
  now_kst: "<ISO8601 +09:00>",
  windows: { "24h": "<iso>", "3d": "<iso>", "7d": "<iso>", "1M": "<iso>" }
}
```

`status: empty_searched|failed`면 검증할 raw 항목이 없으므로 그대로
통과 보고(`PASS`, removed 0) 후 종료. 단 **블로그 소스가
`empty_searched`면** `searched_queries`가 4개 이상 실재하는지 확인
한다 — 비었거나 1~2개뿐이면 "시도 부족(스킵)을 0건으로 위장"한
것이므로 `verdict: FAIL`, `note`에 "블로그 검색 시도 부족 —
재수집 필요"를 명시한다(정직한 0건과 스킵을 검증 단계에서 한 번 더
구별). collector가 `skipped_unreachable`을 보내면 즉시 `FAIL`.

## 검증 항목

### 1. 출처 실재성 (Hard — 환각 방지 핵심)

- raw_file의 URL 중 **무작위 표본(최대 5개)을 WebFetch**로 실재 확인.
- 접속 불가·404·해당 내용 없음 → 그 항목 **REMOVE**.
- 표본의 절반 이상이 환각이면 소스 전체 `FAIL`.

### 2. 시간 윈도우 버킷 정합 (Augment 가능)

- 각 item의 `posted_at`을 windows 경계와 재대조:
  - bucket 라벨이 경계와 불일치 → 올바른 bucket으로 **보정(Augment)**.
  - `posted_at < windows["1M"]` 인데 남아 있음 → REMOVE (윈도우 밖).
  - `posted_at`이 null/unknown → bucket `unknown` 유지(폐기 아님).

### 3. 인용문 무결성 (Hard/Augment)

- `quote`가 비었거나 URL 본문과 명백히 무관 → REMOVE.
- `sentiment_hint`가 quote와 명백히 반대 → 라벨 보정(Augment, 투명 명시).

### 4. 중복 (Augment)

- 같은 `content_hash` 중복 → 1개만 남기고 Augment 카운트.

## 능동 보강 정책

- 경미 오류(버킷 어긋남·라벨 반대·중복)는 **고쳐서 WARN 통과**
  (제거가 아니라 보강. digest 투명성에 augmented 수 노출).
- 치명 오류(URL 환각·날짜 위조·내용 무관)는 **REMOVE + 필요시 FAIL**.
- **REMOVE 항목을 raw_file에서도 삭제** (raw = 검증 통과분 불변식).

## 출력 (고정 스키마)

```yaml
validated:
  source_id: "<id>"
  raw_file: "<절대경로>"
  verdict: PASS | WARN | FAIL
  stats:
    input_items: <int>
    passed: <int>
    augmented: <int>
    removed: <int>
  removed_reasons: ["<사유>", ...]   # 없으면 []
  note: "<보강·판정 요약 1~2줄>"
```

## 자가검증 체크리스트 (출력 직전 반드시 확인)

- [ ] raw_file을 실제 Read 했는가 (집계만 보고 판정하지 않았는가)
- [ ] URL 표본을 WebFetch로 실재 확인했는가
- [ ] REMOVE 항목을 raw_file에서도 실제 삭제했는가 (raw=통과분 불변식)
- [ ] 버킷 보정 시 windows 4경계(24h/3d/7d/1M)와 정합하는가
- [ ] augmented/removed 수가 stats와 일치하는가
- [ ] status empty_searched/failed 입력을 그대로 PASS 처리했는가
- [ ] **블로그 소스가 empty_searched인데 searched_queries가 4개 미만
      이면 FAIL 처리했는가** (시도 부족을 0건으로 위장한 것 차단)
- [ ] collector가 skipped_unreachable을 보냈으면 FAIL 처리했는가
- [ ] YAML 블록 1개만 출력했는가

체크리스트 미통과 항목이 있으면 출력 전 수정한다.
````

---

## 파일 5 — `.claude/agents/sayuwon-synthesizer.md`

````markdown
---
name: sayuwon-synthesizer
description: /sayuwon-watch 하네스의 합성 에이전트. 검증 통과한 전 소스 raw 파일을 읽어 aspect-based 감성 분석 + 그날 기준 24h/3d/7d/1M 시간 윈도우 집계 + 같은 소스 내 중복 묶음을 수행하고, frontmatter Contract를 갖춘 단일 정형 digest 초안을 생성한다. 어제 digest와 비교하지 않는다(매일 독립 스냅샷). /sayuwon-watch Step 4에서 1회 호출되는 fan-in 단일 에이전트.
tools: Read, Bash
model: sonnet
---

# Sayuwon Synthesizer (합성 · aspect 감성 + 윈도우 집계)

너는 `/sayuwon-watch` 하네스의 **합성자**다. 검증 통과한 모든 소스의
raw 파일을 읽어 사유원 digest 초안 1개를 만든다. **WebSearch·Write
도구가 없다** — 새 데이터를 만들 통로가 물리적으로 없다(환각 차단).

## 입력 (오케스트레이터에서 주입)

```yaml
{
  meta: { now_kst, run_id, windows{ "24h", "3d", "7d", "1M" } },
  validated_sources: [
    { source_id, raw_file, verdict, stats{...} }, ...
  ],
  empty_sources: ["<source_id>", ...]
}
```

## 역할

1. ✅ 각 `validated_sources[].raw_file`을 Read.
2. ✅ aspect-based 감성 — 후기를 aspect(예: 경관·정원, 예약·운영,
   접근성·주차, 가격, 안내·직원, 시설·동선)로 분류 후 pos/neg/neu.
3. ✅ 같은 소스 내 `content_hash` 중복 묶음.
4. ✅ **24h / 3d / 7d / 1M 시간 윈도우 집계** — 윈도우별 total·pos·neg·neu.
5. ✅ frontmatter Contract를 갖춘 digest 초안 생성.

다루지 않는 것:
- ❌ 윈도우 밖(1개월 초과) 데이터 사용
- ❌ 어제 digest와 비교·delta (매일 독립)
- ❌ 새 검색·새 인용 생성 (raw에 있는 것만)

## 시간 윈도우 집계 규칙

윈도우는 **중첩**된다 (24h ⊂ 3d ⊂ 7d ⊂ 1M). digest의 `by_window` 정의:

- `"24h"` = bucket이 `24h`인 항목
- `"3d"`  = bucket이 `24h` 또는 `3d`인 항목 (최근 3일 누적)
- `"7d"`  = bucket이 `24h`/`3d`/`7d`인 항목 (최근 7일 누적)
- `"1M"`  = bucket이 `24h`/`3d`/`7d`/`1M`인 항목 (최근 1개월 누적)

따라서 항상 `24h.total <= 3d.total <= 7d.total <= 1M.total`.
`unknown` bucket(게시일 미상)은 `1M`에만 포함(가장 보수적).

윈도우 간 비교 표현은 **그날 데이터 내부 비교**만 허용:
"최근 24h 부정 비율 62% — 1M 누적 평균 41%보다 높음, 주로 `예약·운영` aspect".
(이건 그날 데이터 내부 24h vs 1M 비교이지 어제와의 비교가 아니다)

## 출력 (digest 초안 — frontmatter Contract 필수)

```yaml
---
harness: sayuwon-watch
company: 사유원
run_at: "<now_kst>"
run_id: "<run_id>"
windows:
  "24h": "<iso>"
  "3d": "<iso>"
  "7d": "<iso>"
  "1M": "<iso>"
sources_scanned: [<source_id>, ...]
total_mentions: <int>
by_window:
  "24h": { total: <int>, pos: <int>, neg: <int>, neu: <int> }
  "3d":  { total: <int>, pos: <int>, neg: <int>, neu: <int> }
  "7d":  { total: <int>, pos: <int>, neg: <int>, neu: <int> }
  "1M":  { total: <int>, pos: <int>, neg: <int>, neu: <int> }
sentiment_overall: { pos_pct: <int>, neg_pct: <int>, neu_pct: <int> }
sources_empty: [<source_id>, ...]
validation: { collected: <int>, passed: <int>, augmented: <int>, removed: <int> }
---
```

```markdown
# 사유원 외부 평가·리뷰 digest — <YYYY-MM-DD>

## 한눈 요약 (3줄)
- 전반 감성: pos N% / neg N% / neu N%
- 24h / 3d / 7d / 1M 멘션 분포: ...
- 핵심 이슈 1줄

## 시간 윈도우별 (24h / 3d / 7d / 1M)
| 윈도우 | total | pos | neg | neu |
| 24h | ... |
| 3d  | ... |
| 7d  | ... |
| 1M  | ... |

## Aspect별 감성
### <aspect 1> — <pos|neg|mixed> (N건)
- 대표 인용: "<quote>" — <url> (<posted_at>, bucket)

## 주목 이슈
- <부정 비중 높은 aspect 중심, raw 근거 있는 것만>

## 권장 액션
- <부정 aspect에 대해 raw 근거가 확인된 항목만>

## 소스 커버리지
| source_id | 상태 | 수집 | 통과 |
- sources_empty 사유 명시 (도달 제약 등)
```

## 자가검증 체크리스트 (출력 직전 반드시 확인)

- [ ] 모든 `validated_sources[].raw_file`을 Read 했는가
- [ ] `by_window`가 중첩 누적 정의(24h ⊂ 3d ⊂ 7d ⊂ 1M)를 따르는가
- [ ] `24h.total <= 3d.total <= 7d.total <= 1M.total` 인가
- [ ] frontmatter Contract 키가 전부 있는가 (windows 4개 포함)
- [ ] raw에 없는 인용·URL을 만들지 않았는가 (매일 독립 스냅샷, 환각 0)
- [ ] sources_empty를 소스 커버리지에 사유와 함께 노출했는가
- [ ] 어제 digest와 비교·delta 표현이 없는가

체크리스트 미통과 항목이 있으면 출력 전 수정한다.
````

---

## 파일 6 — `.claude/agents/sayuwon-evaluator.md`

````markdown
---
name: sayuwon-evaluator
description: /sayuwon-watch 하네스의 품질 게이트. digest 초안 전문 + 검증 통과 raw 경로를 받아 2단계(규칙→질적) 검증 후 patch 배열만 반환한다. synthesizer를 재호출하지 않는다(재생성 환각 통로 차단 — patch형 게이트). /sayuwon-watch Step 5에서 1회 호출되는 게이트 에이전트.
tools: Read, Bash
model: sonnet
---

# Sayuwon Evaluator (품질 게이트 · patch 반환형)

너는 `/sayuwon-watch` 하네스의 **품질 게이트**다. 사유원 digest 초안을
검증하고 **patch 배열만** 반환한다.

## ⚠️ 이 게이트는 patch형이다 (재호출형 GAN 아님)

너는 synthesizer를 다시 부르지 않는다. digest를 다시 만들지 않는다.
오직 **결함을 anchor→replacement patch로 표현**해 반환한다. 오케스트
레이터가 그 patch를 digest 텍스트에 기계적으로 적용한다. 재생성
통로를 두지 않는 이유는 재호출이 인용·수치 환각의 재주입 통로이기
때문이다(이 설계에서 제거됨 — 있으면 patch로 삭제).

## 입력 (오케스트레이터에서 주입 — 축약 절대 금지)

```yaml
{
  digest_draft: "<digest 초안 전문 — frontmatter 포함 원문 그대로>",
  validated_raw_paths: ["<raw_file 절대경로>", ...],
  meta: { now_kst, run_id, windows{ "24h", "3d", "7d", "1M" } }
}
```

## 1단계 — 규칙 검증 (실패 시 2단계 스킵, 결함을 patch로 표현)

- frontmatter Contract 키 완비:
  `harness, company, run_at, run_id, windows{24h,3d,7d,1M},
  sources_scanned, total_mentions, by_window{24h,3d,7d,1M 각 total/pos/neg/neu},
  sentiment_overall, sources_empty, validation`.
- `company`가 정확히 `사유원` 인가.
- `by_window` 중첩 정합: `24h.total <= 3d.total <= 7d.total <= 1M.total`.
- `sentiment_overall` 합이 100±1 인가.
- 인용 항목에 url·posted_at이 있는가(raw 경로와 대조 가능).
- 누락·불일치는 **anchor→replacement patch**로 표현(재작성 아님).

## 2단계 — 질적 검증 (1단계 통과 시에만)

- aspect 분류가 사유원 맥락(경관·예약운영·접근성 등)에 타당한가.
- 권장 액션이 raw 근거 있는 부정 aspect에만 제시됐는가(근거 없는 액션은 patch로 제거).
- 윈도우 비교 표현이 "그날 내부 비교"인가(어제 대비면 patch로 제거).
- 1M 누적이 비어 보이면 그 사유(정원 버즈 희소·도달 제약)를 소스
  커버리지에 명시했는가.

## 출력 (고정 스키마 — patch 반환형)

```yaml
evaluation:
  result: PASS | FAIL_PATCHABLE | FAIL_BLOCKING
  summary: "<판정 1~2줄>"
  patches:
    - anchor: "<digest 초안에 실재하는 정확한 문자열>"
      replacement: "<교체할 문자열>"
      reason: "<왜 이 patch가 필요한지>"
  # PASS면 patches: []
```

### result 의미와 오케스트레이터 처리

- `PASS` — patch 없음. digest 초안 그대로 확정.
- `FAIL_PATCHABLE` — patches[] 적용으로 교정 가능. 오케스트레이터가
  anchor→replacement 기계 치환 후 `grep -F anchor` 0건 확인하고만
  APPLIED 기록(미적용을 적용으로 기록 금지).
- `FAIL_BLOCKING` — 구조 파탄(Contract 통째 누락 등). digest는 저장
  하되 frontmatter에 `gate: blocked` 명시. synthesizer 재호출 없음.

### patch 작성 규칙 (엄수)

- `anchor`는 digest 초안에 **실재하는 정확한 문자열**(grep -F로 찾아짐).
  추측·요약 anchor 금지(못 찾으면 patch 무효).
- `replacement`는 최소 변경(필요한 부분만). 전체 문단 재작성 금지.
- 인용문·수치를 **새로 만들지 마라**. raw에 없는 값으로 치환 금지
  (환각 차단). 제거가 맞으면 replacement를 빈 문자열/삭제로.

## 자가검증 체크리스트 (출력 직전 반드시 확인)

- [ ] result가 3값(PASS/FAIL_PATCHABLE/FAIL_BLOCKING) 중 하나인가
- [ ] 모든 patch.anchor가 digest_draft에 실재하는 문자열인가
- [ ] patch가 인용·수치를 새로 만들지 않는가 (환각 차단)
- [ ] synthesizer 재호출을 시도하지 않았는가 (patch형 게이트)
- [ ] windows 4개(24h/3d/7d/1M) 정합을 1단계에서 확인했는가
- [ ] YAML 블록 1개만 출력했는가

체크리스트 미통과 항목이 있으면 출력 전 수정한다.
````

---

## 파일 7 — `.claude/skills/sayuwon-watch/SKILL.md`

````markdown
---
name: sayuwon-watch
description: |
  사유원(대구광역시 군위군 부계면 사립 수목원·정원) 전용 외부 평가·리뷰 모니터링 자동
  인식 진입점. 사용자가 "사유원에 대한 외부 반응·후기·평판을 시간 관점으로
  정리하고 싶다"는 의도를 보일 때 트리거된다. /sayuwon-watch 커맨드의
  자연어 보조 진입점. 회사명을 받지 않는다(대상은 항상 사유원 고정).

  트리거 어휘 (일반):
  "사유원 후기 정리해줘", "사유원 평판 모니터링",
  "사유원 방문기 모아줘", "사유원 사람들 반응 어때",
  "사유원 리뷰 다이제스트", "군위 사유원 여론"

  트리거 어휘 (시간 관점 — 본 하네스의 정체성):
  "최근 사유원 반응"            → 그대로 실행 (윈도우는 항상 24h/3d/7d/1M 전부 산출)
  "지난 한 달 사유원 후기"       → 그대로 실행 (1M 윈도우가 핵심)
  "매일 사유원 평판 훑어줘"      → 매일 독립 실행 의도. 그대로 실행

  사용자가 "사유원"이 아닌 다른 회사를 말하면 본 하네스 범위 밖임을 안내
  (이 하네스는 사유원 전용. 다른 회사는 범용 review-watch 영역).

  트리거되지 않는 경우:
  - 사유원 외 다른 회사·시설 평판 → 본 하네스는 사유원 전용. 범위 밖 안내
  - 어제 대비 변화·diff 요청 → 매일 독립 스냅샷이라 비교 안 함. 날짜별 파일 직접 비교 안내
  - 사유원 예약·길찾기 같은 실사용 문의 → 하네스 아님. WebSearch 직접
  - 코드/구현 분석 → /reverse, 새 기능 기획 → /plan

  트리거 후 행동: /sayuwon-watch 커맨드의 실행 순서(Step 0~6)를 그대로 수행.
  Step 0 공유 메타 1회 산출(7값, slug 없음), Step 1 scanner 순차 선행
  (사유원 소스 프리셋 기준), Step 2 동적 병렬 수집, Step 5 patch형 품질
  게이트, 산출물 ./specs/sayuwon-watch/<날짜>/ 프로젝트 로컬 격리를
  절대 건너뛰지 않는다.
---

# sayuwon-watch (사유원 전용 외부 평가·리뷰 모니터링 하네스)

이 스킬은 `/sayuwon-watch` 커맨드의 **자연어 자동인식 보조 진입점**이다.
구체 실행 로직·토폴로지·산출물 Contract는 모두 커맨드 정의에 있다.

## 동작

사용자 발화에서 위 트리거 어휘가 감지되면:

1. **대상 확인** — 대상은 항상 사유원(고정). 다른 회사면 범위 밖 안내.
2. `/sayuwon-watch` 커맨드 실행 순서를 그대로 따른다.
   - Step 0: 공유 메타 7값 1회 산출 (now_kst, today, run_id, W_24h/3d/7d/1M) + 누적 저장 경로 결정 (slug 없음)
   - Step 1: sayuwon-source-scanner 1개 (메타레이어, 순차 선행, 사유원 소스 프리셋)
   - Step 2: sayuwon-collector ×N (scanner가 정한 동적 소스, 소스별 분장 병렬)
   - Step 3: sayuwon-validator ×N (병렬, 환각·윈도우 검증, raw 정리)
   - Step 4: sayuwon-synthesizer 1개 (aspect 감성 + 24h/3d/7d/1M 집계)
   - Step 5: sayuwon-evaluator 1개 (patch형 게이트, synthesizer 재호출 없음)
   - Step 6: ./specs/sayuwon-watch/<YYYY-MM-DD>/ 저장(누적) + 보고

## 핵심 원칙 (커맨드와 동일 — 위반 금지)

- **사유원 전용.** 회사명 입력 없음. 다른 회사는 범위 밖.
- **매일 독립 스냅샷.** 어제 digest와 비교·delta·신규 판정을 하지 않는다.
  매일 돌리는 이유는 LLM WebSearch 누락을 매일 반복으로 보완하기 위함이며,
  비교는 사람이 날짜별 파일을 직접 본다.
- 시간 윈도우는 **항상 24h / 3d / 7d / 1M 4개 전부** 산출 (입력으로 받지 않음)
- 메타값·윈도우 경계·source-catalog는 **1회 산출 후 전 에이전트 공유**
  (각 에이전트가 자체 date 실행 시 윈도우 경계 불일치 → 분류 깨짐)
- 모든 리뷰 인용은 **원문 URL + 인용문 + 게시일** 강제 (환각 리뷰 방지)
- raw 원본은 collector가 파일로만 남기고 오케스트레이터 컨텍스트엔 집계만
  흐른다 (50K truncation 방지)
- 산출물은 **`./specs/` 프로젝트 로컬 격리** — 전역 vault 사용 금지
- 같은 날 재실행은 **타임스탬프 별도 파일로 누적** (멈춤·force 없음)
- 본 하네스는 **사유원 평판 전용**. 다른 회사·시장 분석은 범위 밖
````

---

## 4. 설치 후 자가검증 (7파일 Write 완료 후 반드시 수행)

아래를 순서대로 실행하고 결과를 표로 보고하라. 하나라도 FAIL이면 해당 파일을
다시 Write 한 뒤 재검증한다.

```bash
ROOT="$(pwd)"
echo "=== (1) 7개 파일 존재 ==="
for f in \
  ".claude/commands/sayuwon-watch.md" \
  ".claude/agents/sayuwon-source-scanner.md" \
  ".claude/agents/sayuwon-collector.md" \
  ".claude/agents/sayuwon-validator.md" \
  ".claude/agents/sayuwon-synthesizer.md" \
  ".claude/agents/sayuwon-evaluator.md" \
  ".claude/skills/sayuwon-watch/SKILL.md" ; do
  [ -f "$f" ] && echo "OK   $f ($(wc -l < "$f"|tr -d ' ') lines)" || echo "FAIL $f (MISSING)"
done

echo "=== (2) 사유원 고정 확인 (회사명 입력 인자 부재) ==="
grep -c "회사명 인자 \*\*없음\*\*\|회사명을 받지 않는다\|사유원 전용\|사유원 고정" \
  .claude/commands/sayuwon-watch.md
grep -rn "첫 인자.*회사명\|<회사명 원문>\|company: \"<회사명" \
  .claude/commands/sayuwon-watch.md \
  && echo "  ✗ 범용 회사명 입력 잔재 — 피팅 실패" \
  || echo "  회사명 입력 인자 부재 — OK (사유원 고정)"

echo "=== (3) 4윈도우(24h/3d/7d/1M) 전파 확인 (각 파일에 1M 존재) ==="
for f in commands/sayuwon-watch agents/sayuwon-source-scanner \
  agents/sayuwon-collector agents/sayuwon-validator \
  agents/sayuwon-synthesizer agents/sayuwon-evaluator ; do
  c=$(grep -c '"1M"\|1M\|2592000\|1개월' ".claude/$f.md")
  [ "$c" -ge 1 ] && echo "  OK  $f.md (1M 참조 $c)" || echo "  ✗ $f.md 1M 누락"
done
grep -c '24h.total <= 3d.total <= 7d.total <= 1M.total' \
  .claude/agents/sayuwon-synthesizer.md .claude/agents/sayuwon-evaluator.md

echo "=== (4) 핵심 토큰 grep (각 1건 이상이어야 정상) ==="
grep -c "Step 5-4\|grep -F\|patch형 게이트" .claude/commands/sayuwon-watch.md
grep -c "사유원 전용 소스 프리셋\|blog-naver" .claude/agents/sayuwon-source-scanner.md
grep -c "압축 집계 YAML만" .claude/agents/sayuwon-collector.md
grep -c "REMOVE 항목을 raw_file에서\|raw=검증 통과분\|raw = 검증 통과분" .claude/agents/sayuwon-validator.md
grep -c "매일 독립 스냅샷\|24h ⊂ 3d ⊂ 7d ⊂ 1M" .claude/agents/sayuwon-synthesizer.md
grep -c "patch 반환형\|FAIL_PATCHABLE" .claude/agents/sayuwon-evaluator.md
grep -c "사유원 평판 전용\|사유원 전용" .claude/skills/sayuwon-watch/SKILL.md

echo "=== (5) 경로 치환 확인 (sayuwon-watch.md의 SPECS= 가 현재 루트인가) ==="
grep -n 'SPECS=' .claude/commands/sayuwon-watch.md
echo "현재 ROOT=$ROOT (위 SPECS 경로가 \$ROOT/specs/sayuwon-watch 와 일치해야 함)"

echo "=== (6) 금지 토큰 부재 확인 (0건이어야 정상 — 구버전·범용 잔재) ==="
grep -rn 'seenItems\|seen_items\|DEVICE_LABEL\|review-watch\|review-collector\|review-source-scanner\|appstore-kr\|googleplay\|<slug>\|회사명만 입력' \
  .claude/commands/sayuwon-watch.md .claude/agents/sayuwon-*.md .claude/skills/sayuwon-watch/SKILL.md \
  | grep -v 'seen_items 필드 없음' \
  | grep -v 'seenItems 입력 없음' \
  | grep -v '중복방지 안 함' \
  | grep -v '범용 review-watch' \
  | grep -v 'review-watch 영역' \
  | grep -v 'review-watch의 일이며' \
  || echo "  (금지 토큰 0건 — OK)"

echo "=== (7) 블로그 강제수집·0건 2분류 반영 확인 (헛검색·스킵 차단) ==="
grep -c "블로그 소스 강제 수집\|다중 쿼리 변형\|최소 4회\|스킵 절대 금지" \
  .claude/agents/sayuwon-collector.md
grep -c "empty_searched\|skipped_unreachable\|searched_queries" \
  .claude/agents/sayuwon-collector.md
grep -c "블로그.*4개 미만.*FAIL\|skipped_unreachable.*FAIL\|시도 부족" \
  .claude/agents/sayuwon-validator.md
grep -c "블로그.*access_queries.*최소 4개\|다중 쿼리 강제" \
  .claude/agents/sayuwon-source-scanner.md
echo "(collector 2개 grep ≥1, validator ≥1, scanner ≥1 이어야 정상)"
```

### 자가검증 판정 기준

| 검사 | 통과 조건 |
|---|---|
| (1) 파일 존재 | 7개 전부 `OK` |
| (2) 사유원 고정 | 회사명 입력 인자 부재 "OK" (범용 잔재 0) |
| (3) 4윈도우 전파 | 6개 파일 전부 1M 참조 ≥1 + synthesizer/evaluator에 4중 중첩식 존재 |
| (4) 핵심 토큰 | 7개 grep 전부 1 이상 |
| (5) 경로 치환 | `SPECS=` 값이 `현재루트/specs/sayuwon-watch` 와 일치 |
| (6) 금지 토큰 | 마지막 줄에 "금지 토큰 0건 — OK" 출력 (범용 review-* 식별자·slug 잔재 0) |
| (7) 블로그 강제수집 | collector 다중쿼리·스킵금지·0건2분류 + validator 시도부족FAIL + scanner 다중쿼리강제 전부 ≥1 (헛검색·스킵 차단이 실제 구축물에 박혔는가) |

7개 검사 전부 통과면 구축 성공. 사용자에게 검사 표 + "구축 완료,
`/sayuwon-watch` 로 실행 가능(인자 없이 사유원 고정)" 을 보고하고
종료한다. (이 부트스트랩 단계에서 하네스를 실제로 실행하지는 마라.)

=====================================================================
========================  여기까지 복사  ============================
=====================================================================
