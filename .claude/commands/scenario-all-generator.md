---
description: 수강생 케이스 1개를 받아 시나리오 A·B·C 가이드 + Brief + D(선제 조건) + viewer.html을 한 번에 산출. 3개 메타 하네스(scenario-a/b/c-generator)를 단일 메시지 병렬 위임 후 Brief·D 합성 + viewer.html + 브라우저 자동 열림.
argument-hint: <케이스 자연어 설명>
allowed-tools: Task, Read, Write, Bash, Grep, Glob, AskUserQuestion
---

# /scenario-all-generator (별칭 /scenario-all)

## §0 정체성

### 무엇
수강생 케이스 1개 → 6개 산출물.

산출 경로: `./specs/scenario-all/<slug>/<today>/`
- `00_brief.md`
- `01_scenario_a.md`
- `02_scenario_b.md`
- `03_scenario_c.md`
- `04_prerequisites.md`
- `viewer.html`

### 핵심 토폴로지

```
오케스트레이터 (이 command)
    │
    ├──▶ Task(scenario-a-generator)
    ├──▶ Task(scenario-b-generator)   ← 단일 메시지 병렬
    └──▶ Task(scenario-c-generator)
            │
            ▼
    command 직접 합성:
    - 00_brief.md (3 산출 종합 + 권장)
    - 04_prerequisites.md (3 산출의 §6-3·§9 통합)
    - viewer.html
            │
            ▼
    open viewer.html (macOS)
```

### 불변

1. 6 파일 산출 (5 md + 1 html)
2. 3 메타 하네스 단일 메시지 병렬
3. viewer.html은 aiceo-4th-agent UI 토큰 모방 + CDN marked.js
4. Brief §최종 권장에 1개 시나리오 명시
5. D는 직접 합성 (별도 subagent 없음 — 토큰 절약)
6. 한국어 산출

---

## §1 Step 0 — 케이스 명세 정규화

### 1-1. $ARGUMENTS 평가

```
비어 있음:                  → Full Discovery
케이스 한 줄 명시:          → 바로 진입
구조화 입력 (4필드):        → 바로 진입
```

### 1-2. Full Discovery

```
AskUserQuestion:
"4시나리오 합본 컨설팅용 케이스를 한 줄로 알려주세요."
- 회의록 → Slack 변환
- 일일 매출 보고서 (DB + 환율)
- 경쟁사 비교 정기 모니터링
- 매출 이상치 자율 분석
- 직접 입력
```

### 1-3. 명세 정규화

```yaml
case_name: <slug>
case_description: <2~3줄>
```

이걸 그대로 3 메타 하네스에 인자로 전달.

### 1-4. 사용자 컨펌

```
4시나리오 합본 생성 시작:
- 케이스: <case_name>
- 산출: 6 파일 (5 md + 1 html)
- 예상 소요: 60~90초 (3 메타 하네스 + viewer.html 합성)
- 브라우저 자동 열림 (macOS)

진행할까요? (y/n)
```

---

## §2 Step 1 — 3 메타 하네스 병렬 위임

**단일 메시지 안에서 Task 3건 동시 호출**:

```
Task(subagent_type="general-purpose", prompt="""
너는 scenario-a-generator 메타 하네스를 호출하는 역할이다.

먼저 .claude/commands/scenario-a-generator.md 스펙을 정독해 그 산출 규칙을 완전히 이해하라.
그 후 .claude/agents/scenario-a-structurer.md, scenario-a-applier.md도 함께 정독해 분업 패턴을 이해.

다음 케이스에 대해 시나리오 A 가이드를 8섹션 마크다운으로 산출하라:

case_name: <case_name>
case_description: <case_description>

산출 형식: scenario-a-generator의 출력 마크다운 그대로 (frontmatter + §1~§8 + §5-A/§5-B 분할 + §6 4서브섹션).
""")

Task(subagent_type="general-purpose", prompt="""
너는 scenario-b-generator 메타 하네스를 호출하는 역할이다.

먼저 .claude/commands/scenario-b-generator.md, .claude/agents/b-structurer.md, b-applier.md, b-cost-estimator.md 정독.

case_name: <case_name>
case_description: <case_description>

산출: scenario-b-generator의 10섹션 마크다운 (§1~§10 + §5-A/§5-B + §6 4서브).
""")

Task(subagent_type="general-purpose", prompt="""
너는 scenario-c-generator 메타 하네스를 호출하는 역할이다.

먼저 .claude/commands/scenario-c-generator.md, c-structurer.md, c-applier.md, c-cost-estimator.md 정독.

case_name: <case_name>
case_description: <case_description>

산출: scenario-c-generator의 10섹션 마크다운 (§1~§10 + §10-3 임계점 4개 체크박스 강제).
""")
```

**병렬 호출 필수** — 단일 메시지에서 3건 동시. 직렬 호출 금지 (시간 3배).

### 2-1. 산출 보존

각 산출을 변수로:
- `A_OUT` = scenario-a 산출 텍스트
- `B_OUT` = scenario-b 산출 텍스트
- `C_OUT` = scenario-c 산출 텍스트

### 2-2. 검증

```bash
echo "$A_OUT" | grep -qE "## §1 케이스 한 줄 정의" || RECALL_A=true
echo "$B_OUT" | grep -qE "## §10 시나리오 A 대비" || RECALL_B=true
echo "$C_OUT" | grep -qE "## §10 시나리오 B 대비" || RECALL_C=true
```

실패 시 1회 재호출. 재호출 후도 실패면 부분 산출 진행.

---

## §3 Step 2 — Write 3개 산출 그대로 + Brief + D 합성

### 3-1. 경로 결정

```bash
slug=<case_name kebab-case>
today=$(date +%Y-%m-%d)
base="./specs/scenario-all/$slug/$today"
mkdir -p "$base"
```

### 3-2. 01·02·03 Write (3 메타 산출 그대로)

```bash
Write "$base/01_scenario_a.md" $A_OUT
Write "$base/02_scenario_b.md" $B_OUT
Write "$base/03_scenario_c.md" $C_OUT
```

### 3-3. 00_brief.md 합성 (command 직접)

**Brief 6섹션 골격**:

```markdown
---
harness: scenario-all-generator
case: <자연어>
slug: <kebab>
run_at: <ISO8601 KST>
run_id: <epoch>
recommended_scenario: <A | B | C>
recommendation_reason: <1줄>
---

# <case_name> — 4시나리오 합본 컨설팅 Brief

> <case_description 2~3줄>

## §1 케이스 개요
**무엇** / **왜** / **입력·출력** (3 산출 §1 종합)

## §2 시나리오 3안 비교 표

| 항목 | A (Claude Code) | B (aiceo-4th-agent 메뉴) | C (자율 에이전트) |
|------|----------------|-------------------------|------------------|
| 환경 | 1인 CLI | 웹앱 (팀 공유) | 웹앱 (자율) |
| 자율성 | 단일·분업 호출 | 고정 파이프 | createDeepAgent |
| 파일 수 | <A §3 카운트> | <B §3 카운트> | <C §3 카운트> |
| 외부 의존 | <A §6-1 필수> | <B §6-1 필수> | <C §6-1 필수> |
| 1회 실행 비용 | (대부분 무료, Claude Code 구독) | <B §9-2 1회> | <C §9-1 p50> |
| 월간 예상 | — | <B §9-2 월간> | <C §9-2 월간> |
| 자동화 | macOS 매크로 | cron | API + thread_id |
| 멀티턴 | 약함 | 약함 | 강함 |
| 권장 사용자 | 1인 PoC | 팀 3~30명 | 멀티턴 + 자율 탐색 |

## §3 권장 시나리오 (단일 답)

**👉 시나리오 <X> 권장**

이유:
- <C 정당화 임계점 체크 결과 기반>
- B의 ROI 임계점 체크 결과 기반
- A는 PoC·1인용 단계에서만 권장

대안 검토:
- <X 외 다른 시나리오를 선택하면 어떤 손익?>

## §4 다음 단계 (3안 중 선택 후)

선택한 시나리오의 가이드 (01/02/03)를 참조해 실제 구현 진입.
**선제 조건은 04_prerequisites.md** 먼저 확인.

## §5 학습 경로 추천

수강생 입장에서:
1. PoC 단계 → A로 빠르게 검증 (1시간)
2. 팀 공유 결정 → B로 메뉴 추가 (1~3일)
3. 분기 폭증·자율 탐색 필요 → C로 승격 (5일+, 주의: 비결정성·환각)

## §6 산출물 인덱스

- [00_brief.md](./00_brief.md) — 이 문서
- [01_scenario_a.md](./01_scenario_a.md) — A 풀가이드
- [02_scenario_b.md](./02_scenario_b.md) — B 풀가이드
- [03_scenario_c.md](./03_scenario_c.md) — C 풀가이드
- [04_prerequisites.md](./04_prerequisites.md) — D 선제 조건
- [viewer.html](./viewer.html) — 브라우저 뷰어 (자동 열림)
```

### 3-3-bis. 권장 시나리오 자동 선정 규칙

C 정당화 임계점 4개 (C 산출물 §10-3에서 추출):
- 4/4 충족 → **C 권장**
- 2~3/4 충족 → **B 권장** (C는 향후 옵션)
- 0~1/4 충족 → **A 권장** (PoC 단계, 또는 B로 점진 승격)

특수 케이스:
- A의 외부 의존성 0 + 1회성 → **A 권장** (PoC)
- B의 ROI 임계점 (사용자 3+ / 자동 실행 / 이력 관리) 2개+ 충족 → **B 권장**

### 3-4. 04_prerequisites.md 합성 (command 직접)

A·B·C 산출의 §6-3 권한 요청 + §9 비용 + 사전 결정사항을 통합.

**D 5섹션 골격**:

```markdown
---
harness: scenario-all-generator
case: <자연어>
slug: <kebab>
covers: [A, B, C]
run_at: <ISO8601>
---

# <case_name> — 선제 조건 (시나리오 A·B·C 공통)

> 이 문서는 A·B·C 어느 시나리오로 가더라도 미리 확보·결정해야 할 사전 조건을 모은다.

## §1 필수 결정사항 (5분 안에 답할 것)

- [ ] 누가 사용할 것인가? (본인 1인 / 팀 N명 / 사내 전사)
- [ ] 자동 실행 필요? (수동 매번 / cron 자동 / 외부 트리거)
- [ ] 결과 이력 보관? (필요 / 휘발성 OK)
- [ ] 멀티턴 대화 필요? (단발 / 후속 질문 가능해야 함)
- [ ] 예산? (월 ₩X 이내)

답에 따라:
- 1인 + 수동 + 휘발성 → A
- 팀 + 자동 + 이력 → B
- 멀티턴 + 자율 분기 → C

## §2 API 키·외부 SaaS 발급 절차

### 2-1. LLM API 키 (3 시나리오 공통)
- **Anthropic**: https://console.anthropic.com → API Keys → "Create Key"
- 단가 확인: https://www.anthropic.com/pricing
- (선택) OpenAI: https://platform.openai.com/api-keys

### 2-2. 외부 SaaS·API
<A·B·C 산출의 §6 의존성 인벤토리에서 외부 API 종합>
- 환율: 한국수출입은행 https://www.koreaexim.go.kr/ir/HPHKIR020M01
- 뉴스: 네이버 검색 API https://developers.naver.com/products/service-api/search/search.md
- Slack Webhook: 워크스페이스 설정 → Incoming Webhooks
- (기타 케이스 특화 항목)

### 2-3. 사내 SaaS·DB
<A·B·C 산출의 §6-3 사내 권한 요청 문구를 통합>

**DBA팀 권한 요청 문구** (B·C 공통):
> <case 별 templated message>

**IT팀 (Outlook/Notion 등 OAuth)**:
> <필요 시>

## §3 개발 환경 세팅

### 3-1. 시나리오 A 환경 — Claude Code
- 설치: https://claude.com/claude-code
- `.claude/skills/`·`.claude/commands/`·`.claude/agents/` 폴더에 산출물 복사
- 첫 실행: `claude --version` 확인

### 3-2. 시나리오 B·C 환경 — aiceo-4th-agent
- repo clone: `git clone <aiceo-4th-agent-repo>`
- `pnpm install`
- `.env.local` 작성:
  ```
  ANTHROPIC_API_KEY=sk-ant-...
  (케이스별 외부 API 키)
  ```
- `pnpm dev` 실행 → http://localhost:3000

### 3-3. 추가 패키지 (케이스별)
<3 산출의 §5-B 배포 절차에서 pnpm add 명령 종합>

## §4 예상 비용 + 운영 일정

### 4-1. 시나리오별 비용 비교

| 시나리오 | 개발 시간 | 월 LLM 비용 | 월 인프라 비용 | 6개월 누적 |
|---------|----------|-----------|-------------|-----------|
| A | <시간> | (Claude Code 구독에 포함) | 0 | ₩0 (구독료 sunk) |
| B | <시간> | <B §9-2 월간> | 0 (사내) / Vercel | <누적> |
| C | <시간> | <C §9-2 월간> | 0 (사내) / Vercel | <누적> |

### 4-2. 학습·개발 일정

- D 사전 조건 확인: 0.5일 (이 문서)
- A PoC: 1시간 (수강생 입장 빠른 검증)
- B 메뉴 추가: 1~3일
- C 자율 에이전트: 5~10일 (테스트·튜닝 포함)

## §5 권장 진행 순서

1. **이 D 문서 먼저 읽고 결정사항 5개 답하기**
2. PoC → A로 빠른 검증
3. 효과 확인되면 → B 또는 C 선택 (Brief §3 권장 참조)
4. 6개월 운영 후 멀티 에이전트로 승격 검토 (C+ 단계)
```

### 3-5. Write Brief + D

```bash
Write "$base/00_brief.md" $BRIEF_CONTENT
Write "$base/04_prerequisites.md" $D_CONTENT
```

---

## §4 Step 3 — viewer.html 생성

aiceo-4th-agent UI 토큰 모방:
- 보라 강조: `#8b5cf6` (--agent-500)
- 푸른 강조: `#2194f3` (--blue-500)
- 폰트: Pretendard (Google Fonts CDN)
- 좌측 사이드바 + 메인 콘텐츠 2단

**HTML 골격**:

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title><case_name> — 시나리오 합본 컨설팅</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css">
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
  :root {
    --agent-500: #8b5cf6;
    --agent-50: #f5f3ff;
    --blue-500: #2194f3;
    --gray-50: #f7f7f7;
    --gray-100: #f2f2f2;
    --gray-200: #e6e6e6;
    --gray-800: #1a1a1a;
    --neutral-600: #6d767f;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Pretendard', sans-serif; background: var(--gray-50); color: var(--gray-800); }
  .layout { display: flex; min-height: 100vh; }
  .sidebar {
    width: 260px; background: white; border-right: 1px solid var(--gray-200);
    padding: 24px 16px; flex-shrink: 0;
  }
  .sidebar h1 {
    font-size: 16px; font-weight: 700; margin-bottom: 24px;
    color: var(--gray-800);
  }
  .sidebar .group-title {
    font-size: 12px; font-weight: 600; color: var(--neutral-600);
    text-transform: uppercase; margin: 20px 0 8px;
  }
  .sidebar nav a {
    display: block; padding: 8px 12px; border-radius: 8px;
    color: var(--gray-800); text-decoration: none; font-size: 14px;
    margin-bottom: 4px; cursor: pointer;
  }
  .sidebar nav a:hover { background: var(--gray-100); }
  .sidebar nav a.active {
    background: var(--agent-50); color: var(--agent-500); font-weight: 600;
    border-left: 3px solid var(--agent-500);
  }
  .main {
    flex: 1; padding: 32px 48px; overflow-y: auto;
    max-width: calc(100vw - 260px);
  }
  .content { max-width: 880px; }
  .content h1 { font-size: 24px; margin-bottom: 16px; }
  .content h2 { font-size: 20px; margin: 24px 0 12px; padding-bottom: 8px; border-bottom: 1px solid var(--gray-200); }
  .content h3 { font-size: 16px; margin: 16px 0 8px; color: var(--agent-500); }
  .content p { margin: 8px 0; line-height: 1.7; }
  .content ul, .content ol { margin: 8px 0 8px 24px; line-height: 1.7; }
  .content code {
    background: var(--gray-100); padding: 2px 6px; border-radius: 4px;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px;
  }
  .content pre {
    background: var(--gray-800); color: #f0f0f0; padding: 16px;
    border-radius: 8px; overflow-x: auto; margin: 12px 0;
  }
  .content pre code { background: transparent; color: inherit; padding: 0; }
  .content table {
    border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 14px;
  }
  .content th, .content td {
    border: 1px solid var(--gray-200); padding: 8px 12px; text-align: left;
  }
  .content th { background: var(--gray-100); font-weight: 600; }
  .content blockquote {
    border-left: 4px solid var(--agent-500); background: var(--agent-50);
    padding: 12px 16px; margin: 12px 0; border-radius: 4px;
  }
  .header-bar {
    display: flex; align-items: center; gap: 16px;
    padding-bottom: 16px; margin-bottom: 24px;
    border-bottom: 1px solid var(--gray-200);
  }
  .badge {
    display: inline-block; padding: 2px 8px; border-radius: 4px;
    background: var(--agent-50); color: var(--agent-500); font-size: 12px; font-weight: 600;
  }
</style>
</head>
<body>
<div class="layout">
  <aside class="sidebar">
    <h1>4-시나리오 합본 컨설팅</h1>
    <div class="group-title">개요</div>
    <nav>
      <a data-md="00_brief.md" class="active">📋 Brief (1페이지 요약)</a>
    </nav>
    <div class="group-title">시나리오 가이드</div>
    <nav>
      <a data-md="01_scenario_a.md">🅰️ A — Claude Code 하네스</a>
      <a data-md="02_scenario_b.md">🅱️ B — aiceo-4th-agent 메뉴</a>
      <a data-md="03_scenario_c.md">🅲 C — 자율 에이전트</a>
    </nav>
    <div class="group-title">사전 조건</div>
    <nav>
      <a data-md="04_prerequisites.md">⚙️ D — 선제 조건</a>
    </nav>
  </aside>
  <main class="main">
    <div class="header-bar">
      <h1 id="case-title"><case_name></h1>
      <span class="badge">scenario-all-generator</span>
    </div>
    <div id="content" class="content">로딩 중...</div>
  </main>
</div>
<script>
  const links = document.querySelectorAll('.sidebar nav a');
  const content = document.getElementById('content');

  // 5개 md 콘텐츠를 HTML 안에 임베드 (오프라인 동작)
  const mdContents = {
    "00_brief.md": `<<BRIEF_MD_ESCAPED>>`,
    "01_scenario_a.md": `<<A_MD_ESCAPED>>`,
    "02_scenario_b.md": `<<B_MD_ESCAPED>>`,
    "03_scenario_c.md": `<<C_MD_ESCAPED>>`,
    "04_prerequisites.md": `<<D_MD_ESCAPED>>`,
  };

  function render(mdName) {
    const md = mdContents[mdName] || "콘텐츠 없음";
    content.innerHTML = marked.parse(md);
    links.forEach(a => a.classList.toggle('active', a.dataset.md === mdName));
  }

  links.forEach(a => {
    a.addEventListener('click', (e) => {
      e.preventDefault();
      render(a.dataset.md);
    });
  });

  // 초기 렌더: Brief
  render('00_brief.md');
</script>
</body>
</html>
```

### 4-1. md 콘텐츠 임베드

`<<BRIEF_MD_ESCAPED>>` 등 자리표시자는 JS 문자열 안전 escape 후 치환:
- `` ` `` → `\``
- `${` → `\${`
- `\\` → `\\\\`

또는 더 안전하게 base64 인코딩 후 atob 디코드:
```javascript
const mdContents = {
  "00_brief.md": atob("<<BRIEF_MD_BASE64>>"),
  ...
};
```

base64 권장 — 한국어 escape 안전 + 코드블록 ` ` 충돌 없음.

### 4-2. Write viewer.html

```bash
Write "$base/viewer.html" $HTML_WITH_EMBEDS
```

---

## §5 Step 4 — 브라우저 자동 열림

```bash
# macOS
open "$base/viewer.html"
```

다른 OS:
- Windows: `start viewer.html`
- Linux: `xdg-open viewer.html`

명령 실패 시 경로만 보고 (수동 열기).

---

## §6 Step 5 — grep 자가검증 + 보고

### 6-1. 자가검증 (8 체크)

```bash
F_DIR="$base"

# (1) 6 파일 모두 존재
for F in 00_brief.md 01_scenario_a.md 02_scenario_b.md 03_scenario_c.md 04_prerequisites.md viewer.html; do
  [ -f "$F_DIR/$F" ] || { echo "FAIL: $F 없음"; FAIL=$((FAIL+1)); }
done

# (2) Brief에 권장 시나리오 1개 명시
grep -qE "(시나리오 [ABC] 권장|👉 시나리오 [ABC])" "$F_DIR/00_brief.md" || { echo "FAIL: Brief 권장 누락"; FAIL=$((FAIL+1)); }

# (3) Brief에 frontmatter recommended_scenario
grep -qE "^recommended_scenario:" "$F_DIR/00_brief.md" || { echo "FAIL: recommended_scenario 누락"; FAIL=$((FAIL+1)); }

# (4) viewer.html에 marked.js CDN
grep -q "marked.min.js" "$F_DIR/viewer.html" || { echo "FAIL: marked.js CDN 누락"; FAIL=$((FAIL+1)); }

# (5) viewer.html에 보라 강조 (--agent-500 또는 #8b5cf6)
grep -qE "(8b5cf6|--agent-500)" "$F_DIR/viewer.html" || { echo "FAIL: aiceo UI 토큰 누락"; FAIL=$((FAIL+1)); }

# (6) viewer.html에 5개 메뉴
for M in "00_brief.md" "01_scenario_a.md" "02_scenario_b.md" "03_scenario_c.md" "04_prerequisites.md"; do
  grep -q "$M" "$F_DIR/viewer.html" || { echo "FAIL: viewer 메뉴 $M 누락"; FAIL=$((FAIL+1)); }
done

# (7) D에 5섹션 모두
for SEC in "§1 필수 결정사항" "§2 API 키" "§3 개발 환경" "§4 예상 비용" "§5 권장 진행"; do
  grep -qE "^## $SEC" "$F_DIR/04_prerequisites.md" || { echo "FAIL: D 섹션 $SEC 누락"; FAIL=$((FAIL+1)); }
done

# (8) A·B·C 산출이 정상 형식
grep -qE "^harness: scenario-a-generator" "$F_DIR/01_scenario_a.md" || { echo "FAIL: A frontmatter"; FAIL=$((FAIL+1)); }
grep -qE "^harness: scenario-b-generator" "$F_DIR/02_scenario_b.md" || { echo "FAIL: B frontmatter"; FAIL=$((FAIL+1)); }
grep -qE "^harness: scenario-c-generator" "$F_DIR/03_scenario_c.md" || { echo "FAIL: C frontmatter"; FAIL=$((FAIL+1)); }

[ "$FAIL" -eq 0 ] && echo "✅ ALL PASS" || echo "❌ FAIL=$FAIL"
```

### 6-2. 보고

```
✅ 4시나리오 합본 컨설팅 생성: <out_dir>
   - 케이스: <case_name>
   - 권장 시나리오: <X>
   - 산출: 5 md + 1 html
   - 3 메타 하네스 병렬 위임: a ✓ / b ✓ / c ✓
   - Brief·D: command 직접 합성
   - viewer.html: aiceo UI 토큰 모방 + marked.js CDN + 5 md 임베드
   - 브라우저 자동 열림 (macOS open)
   - grep 자가검증 (8 체크) 통과 ✓

다음:
- viewer.html에서 좌측 메뉴 클릭으로 A/B/C/D 전환
- 1개 시나리오 결정 후 해당 가이드(01/02/03) 참조해 구현 진입
```

---

## §7 사용 예시

```bash
/scenario-all
/scenario-all 일일 매출 보고서 자동 생성 (사내 DB + 환율)
/scenario-all 매출 이상치 자율 분석
```

---

## 끝.
