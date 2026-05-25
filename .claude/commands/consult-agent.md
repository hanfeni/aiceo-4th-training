---
description: 수강생 LLM 에이전트 요청 사항을 분석하여 구조 다이어그램(ASCII) + 필요 도구/API 목록 + 페인 포인트 + 대안/난이도를 담은 컨설팅 마크다운을 docs/consulting/에 저장한다
argument-hint: <수강생 요청 사항 텍스트 또는 요청자명>
allowed-tools: Bash, Read, Write, Grep, Glob, WebSearch, WebFetch
---

# /consult-agent — 에이전트 요청 컨설팅 하네스

## 0. 입력 수신

`$ARGUMENTS`에 수강생 요청 사항 텍스트가 온다.
**비어 있으면 한 번만** 아래를 물어 받고, 그 뒤는 질문 없이 끝까지.

필요 정보:
- 요청 사항 전문 (에이전트가 무엇을 해야 하는가)
- 요청자 이름 (없으면 `unknown`)

---

## 1. Step 0 — 메타 산출 + 저장 경로

```bash
now_kst=$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M KST')
today=$(TZ=Asia/Seoul date '+%Y-%m-%d')
run_id=$(TZ=Asia/Seoul date '+%H%M%S')
```

- `requestor` — 요청자 이름 (kebab-case, 예: `kim-dohwan`)
- `slug` — 요청 핵심 키워드 kebab-case (예: `pdm-multi-agent`)
- `title` — 요청 제목 한 줄 요약

저장 경로:

```bash
base="./docs/consulting/<requestor>"
mkdir -p "$base"
if [ -f "$base/<slug>.md" ]; then
  out="$base/<slug>_<run_id>.md"
else
  out="$base/<slug>.md"
fi
```

---

## 2. Step 0.5 — 사전 리서치 (필수 — 최신 정보 기반 컨설팅)

요청이 짧더라도 **건너뛰지 않는다.** 컨설팅의 품질은 이 단계에 달려 있다.

요청 사항에서 **핵심 기술 키워드**를 3~5개 추출한 뒤, 아래 순서로 WebSearch를 수행한다.

### 리서치 항목 (해당되는 것만)

#### 1. 관련 도구/API 현황

- 요청에 등장하는 외부 서비스(Outlook, LinkedIn, Google 등)의 공식 API 존재 여부 및 접근 방식
- 검색 쿼리 예: `"<서비스명> API 2024 rate limit"`, `"<서비스명> MCP server"`

#### 2. Claude/LLM 에이전트 구현 패턴

- 유사한 에이전트를 구현한 사례, 오픈소스 레퍼런스
- 검색 쿼리 예: `"<기능> LLM agent implementation site:github.com"`, `"<기능> Claude agent tool use"`

#### 3. 비용/제약 최신 현황

- API 비용, Rate Limit, 무료 티어 한도
- 검색 쿼리 예: `"<API명> pricing 2025"`, `"<서비스명> API free tier limits"`

#### 4. 알려진 기술적 장벽

- 비슷한 시도에서 발생한 문제, Stack Overflow/GitHub Issues 패턴
- 검색 쿼리 예: `"<기능> automation challenge"`, `"<서비스명> API limitation"`

### 리서치 결과 처리

- 수집한 정보는 별도 파일로 저장하지 않고 **컨설팅 내용에 직접 반영**
- 각 페인 포인트와 대안 제안에 **리서치 출처** 명시 (예: `출처: OpenAI 공식 문서, 2025-01`)
- 정보가 오래됐거나 불확실하면 "확인 필요" 표기

---

## 3. Step 1 — 에이전트 구조 파악 + ASCII 다이어그램

요청 사항에서 아래를 추출한다:

- **에이전트 종류** (단일 에이전트 / 멀티 에이전트 / 파이프라인)
- **입력** (사용자가 무엇을 주는가)
- **처리 단계** (어떤 에이전트/도구가 무슨 역할인가)
- **출력** (최종 결과물)
- **트리거 방식** (수동 호출 / 자동 스케줄 / 이벤트 기반)

ASCII 다이어그램 작성 규칙:
- 박스: `[에이전트명 또는 도구명]`
- 화살표: `-->` (단방향), `<-->` (양방향)
- 병렬 처리: 같은 레벨에 나란히
- 외부 시스템/API: `((시스템명))` 또는 `{시스템명}`
- 최대 너비 60자 이내

예시 패턴:

```
단일 에이전트:
사용자 입력
    │
    ▼
[메인 에이전트]
  ├─→ [웹검색 도구]
  ├─→ ((외부 API))
    │
    ▼
결과 출력

멀티 에이전트:
사용자 입력
    │
    ▼
[Orchestrator]
  ├─→ [Agent A: 역할]
  ├─→ [Agent B: 역할]
  └─→ [Agent C: 역할]
    │
    ▼
[결과 통합]
    │
    ▼
최종 출력
```

---

## 3. Step 2 — 필요 도구/API 목록 분류

### 분류 기준

**A. 기본 제공 (Claude Code 하네스 내장)**
- 웹검색 (WebSearch/WebFetch)
- 파일 읽기/쓰기 (Read/Write)
- 코드 실행 (Bash)
- 텍스트 처리

**B. MCP 확장 (설치 필요, 무료 또는 저비용)**
- Notion MCP
- Google Drive MCP
- Gmail MCP
- Playwright MCP (웹 자동화)

**C. 별도 API 키 + 비용 발생**
| API/서비스 | 용도 | 월 예상 비용 |
|------------|------|-------------|
| ...        | ...  | ...         |

**D. 기업 내부 접근 권한 필요 (가장 큰 페인 포인트)**
- 사내 문서 시스템 (SharePoint, Confluence 등)
- 사내 DB 직접 접근
- ERP/CRM 시스템
- 이메일 계정 (Outlook, Gmail 기업용)

각 항목에 **획득 난이도** 표기: 쉬움 / 보통 / 어려움

---

## 4. Step 3 — 페인 포인트 분석

아래 5가지 차원에서 분석한다:

### 4.1 인증/권한 제약
- 어떤 시스템에 누가 접근 권한을 줄 수 있는가
- OAuth, API 키, SSO 중 어떤 방식이 필요한가
- 기업 보안 정책 충돌 가능성

### 4.2 데이터 접근성
- 필요한 데이터가 공개 데이터인가 / 사내 데이터인가
- 실시간 필요 여부 vs 배치 처리 가능 여부
- 데이터 형식 (정형/비정형, PDF/웹/DB)

### 4.3 비용 및 규모
- LLM API 호출 비용 (토큰 소모량 추정)
- 외부 API 비용
- 운영 지속성 (누가 관리하는가)

### 4.4 기술적 안정성
- 외부 서비스 의존도 (장애 시 전체 중단 위험)
- 에러 핸들링 복잡도
- 멀티 에이전트의 경우 오케스트레이션 복잡도

### 4.5 규제/컴플라이언스
- 개인정보 처리 (고객 데이터가 포함되는가)
- 사내 데이터를 외부 LLM API로 전송 시 보안 정책
- 법적 제약 (저작권, 개인정보보호법 등)

---

## 5. Step 4 — 대안/우회 방법 + 구현 난이도

### 전체 구현 난이도: 상/중/하

| 접근법 | 설명 | 특수 API 필요 여부 | 난이도 |
|--------|------|-------------------|--------|
| 완전 구현 | 요청 그대로 구현 | ... | ... |
| 1단계 MVP | 핵심 기능만 우선 | ... | ... |
| 우회 방법 | 특수 API 없이 유사 구현 | 불필요 | ... |

### 추천 구현 전략
(어디서 시작하고, 어떤 순서로 확장하면 좋은지 1~3줄)

### 빠른 검증 방법 (PoC)
(실제 구현 전 24시간 내 테스트 가능한 방법)

---

## 6. Step 5 — 마크다운 저장 + 자가검증

§7 Contract대로 마크다운 1개를 `$out`에 Write.

자가검증:

```bash
test -f "$out" && echo "FILE_OK" || echo "FILE_MISSING"
for k in harness requestor slug title run_at difficulty; do
  grep -q "^$k:" "$out" && echo "key $k OK" || echo "key $k MISSING"
done
grep -q '페인 포인트' "$out" && echo "PAIN_POINT_OK" || echo "PAIN_POINT_MISSING"
grep -q '필요 도구' "$out" && echo "TOOLS_OK" || echo "TOOLS_MISSING"
```

검증 통과 뒤에만 완료 보고.

---

## 7. 최종 md Contract

frontmatter 필수 키 (전부 포함, 추가 키 금지):

```yaml
---
harness: consult-agent
requestor: <요청자>
slug: <slug>
title: <한 줄 요약>
run_at: <now_kst>
run_id: <run_id>
difficulty: 상|중|하
special_api_required: true|false
---
```

본문 섹션 (순서 고정):

1. **요청 요약** — 원문 요청을 1~3문장으로 압축
2. **에이전트 구조 다이어그램** (ASCII)
3. **필요 도구 / API 목록** (A/B/C/D 분류)
4. **페인 포인트 분석** (5가지 차원)
5. **대안/우회 방법 & 구현 난이도** (테이블 + 추천 전략)

---

## 8. 불변식

1. 요청 내용이 불명확해도 **추측해서 채우지 않는다** — 모호한 부분은 페인 포인트에 "요구사항 불명확" 항목으로 명시.
2. 웹검색/하네스 기본 도구로 해결 가능한 것과 **별도 권한이 필요한 것을 반드시 구분**한다.
3. 구현 난이도 평가 시 **"쉽다"고 과소평가 금지** — 실제 기업 환경의 인증/보안 제약을 반영.
4. 추천 전략은 **최소 동작 가능한 MVP부터** 시작하는 방향으로.
5. 저장 후 grep 기계 확인 뒤에만 완료 보고.
