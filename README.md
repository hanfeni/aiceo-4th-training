# aiceo-4th-training — claude-for-x 한국 미러 커맨드 하네스

> AI CEO 4기 교육 과정 리포지토리.
> Anthropic 산업별 Claude 라인업(Financial Services / Small Business
> / Legal)의 agent template·plugin·skill을 **기능·토폴로지·출력
> 불변**으로 한국에 이식한 **7개 슬래시 커맨드 하네스**를 담는다.
> 변형은 데이터·문화(Legal은 +법체계·법조분류) 레이어만 한다.

---

## 1. 핵심: 하네스 = 슬래시 커맨드

이 리포의 단위는 **`.claude/commands/<harness>.md` 슬래시 커맨드
7개**다. 각 커맨드가 하네스의 실제 실행 계약(6섹션)을 담는다.
스킬·에이전트는 커맨드를 보조하는 부속이다.

```text
하나의 하네스 =
  .claude/commands/<harness>.md   ← [본체·필수] 슬래시 커맨드. 6섹션 Contract
  .claude/skills/<harness>/SKILL.md ← [진입점·필수] 자연어 자동 트리거 → 커맨드로 라우팅
  .claude/agents/<harness>-agent.md ← [선택] 분업형 커맨드만. 1차 자료 추출 위임
```

- **커맨드**가 진짜다 — 실행 순서·Contract·불변식이 여기 있다.
- **스킬**은 얇은 진입점 — "이 발화면 그 커맨드를 수행하라"는 라우팅.
- **에이전트**는 분업형 2개 커맨드만 가짐.

> 복사할 때는 **커맨드 파일을 먼저 보고**, 짝이 되는 스킬(+분업형은
> 에이전트)을 함께 가져간다. §6 참조.

---

## 2. 7개 커맨드라인 카탈로그

| # | 슬래시 커맨드 | 한 줄 기능 | 오리지널 (Anthropic) | 토폴로지 | 인자 |
|---|---|---|---|---|---|
| 1 | `/korea-earnings-reviewer` | 한국 상장사 실적 리뷰 (DART/KIND, thesis 변화) | Financial — Earnings Reviewer | **분업형** (3파일) | `<종목+분기>` |
| 2 | `/korea-market-researcher` | 한국 섹터 뉴스 모니터링·합성·에스컬레이션 | Financial — Market Researcher | **분업형** (3파일) | `<섹터/산업>` |
| 3 | `/korea-contract-reviewer` | 계약서 1차 리스크·독소·누락 조항 검토 | Small Business — Contract Reviewer | 단일형 (2파일) | `<계약서 텍스트>` |
| 4 | `/korea-content-strategist` | 한국 마케팅 메시지 전략(기둥·채널·아이디어) | Small Business — Content Strategist | 단일형 (2파일) | `<사업주제+타깃>` |
| 5 | `/korea-commercial-legal` | 사내 법무 — 강행규정·약관규제법·협상 메모 | Legal — Commercial Legal | 단일형 (2파일) | `<계약서+playbook>` |
| 6 | `/korea-privacy-legal` | 개인정보 처리방침·위탁 점검 / DPIA 초안 | Legal — Privacy Legal | 단일형 (2파일) | `<처리방침/기술서>` |
| 7 | `/korea-employment-legal` | 근로계약·취업규칙 점검 / 노무 분쟁 대응 | Legal — Employment Legal | 단일형 (2파일) | `<규칙/사실관계>` |

분업형(1·2)만 에이전트 보유:
`korea-earnings-disclosure-agent` / `korea-sector-signal-agent`.

호출: 슬래시 직접(`/korea-commercial-legal <텍스트>`) 또는 자연어
(스킬이 자동 트리거 — 각 SKILL.md "언제 트리거" 절 참조).

---

## 3. 두 가지 토폴로지 (복사 시 반드시 구분)

오리지널 라인업의 토폴로지를 **그대로** 상속한다. 바꾸면 패턴 변질.

### 3-A. 단일형 — 커맨드 2파일 (Small Business / Legal)

```text
SKILL.md (진입점)  →  command.md (6섹션 본체)
                       └ 오케스트레이터가 단일 워크플로우로 직접 수행
                         subagent 없음
```

해당 커맨드: `/korea-contract-reviewer` `/korea-content-strategist`
`/korea-commercial-legal` `/korea-privacy-legal`
`/korea-employment-legal` (5개).

### 3-B. 분업형 — 커맨드 3파일 (Financial Services)

```text
SKILL.md  →  command.md (오케스트레이터)
              └ Step 1에서 <harness>-agent.md 에 1차 자료 추출 위임
                (분업 — 누락보완 중복 아님)
```

해당 커맨드: `/korea-earnings-reviewer` `/korea-market-researcher`
(2개). 오리지널 Financial이 subagent를 명세에 박았으므로 보존.

> ⚠️ 단일형 커맨드에 subagent를 끼우거나, 분업형에서 subagent를
> 빼면 **오리지널 토폴로지 위반**. 복사 시 §2 표의 토폴로지 칸을
> 먼저 확인한다.

---

## 4. 커맨드 6섹션 표준 (7개 모두 동일)

`.claude/commands/<harness>.md` 는 항상 이 6섹션 — 복사 후
`grep "^## " <커맨드>` 로 6개 다 보이면 구조 보존 OK:

| 섹션 | 내용 |
|---|---|
| **§0 정체성** | 오리지널이 무엇인가 + 불변(기능·토폴로지·입력·출력) + **변형 레이어 표** (US→KR. SmallBusiness=2축 데이터·문화 / Legal=3축 +법체계·법조분류) |
| **§1 Step 0** | 입력 수령(`$ARGUMENTS`, 비면 1회만 요청) + slug·저장경로 결정 + 개인정보 마스킹 |
| **§2 Step 1** | 핵심 워크플로우 (단일형=직접 / 분업형=에이전트 위임) + 환각 방어 |
| **§3 Step 2** | 마크다운 1개 Write → **grep 결정적 자가검증** → daily 로그 append → 보고 |
| **§4 Contract** | frontmatter 키 고정 (harness·slug·run_at·run_id + 하네스별 카운트). Contract 외 키 금지 |
| **§5 불변식** | 어기면 하네스 실패하는 규칙 6개 (토폴로지·환각·디스클레이머·마스킹·grep) |

커맨드 frontmatter: `description` `argument-hint`
`allowed-tools: Bash, Read, Write, Grep, Glob, WebSearch, WebFetch`.

짝 SKILL.md 는 항상 4섹션: `무엇을 하는가 / 언제 트리거 /
트리거 안 되는 경우 / 어떻게 동작하는가`.

---

## 5. 공통 규칙 (전 커맨드 불변)

- **외부 도구**: WebSearch / WebFetch 만. API 키·유료 커넥터 없음
  (오리지널 FactSet/DocuSign 등은 "미연결" 정직 명시).
- **산출물**: `./specs/claude-for-x-kr/<harness>/<slug>/<today>/00_*.md`
  마크다운 **1개**. 같은 날 재실행 시 `_<run_id>` suffix.
- **환각 방어**: 입력에 없는 것 생성 금지. 법령·판례·공시는 실재
  확인분만 단정, 미확인은 "확인 필요"로 결정 배제.
- **자가검증**: 저장 후 `grep` 으로 frontmatter 키·디스클레이머
  존재를 기계 확인한 **뒤에만** 완료 보고.
- **개인정보 마스킹**: 실명·주민번호·계좌는 slug·로그·요약에서
  마스킹 (원문에만).
- **전문가 디스클레이머**: 법률 커맨드(5·6·7)는 변호사법 §109
  (employment는 +공인노무사법) 강제. 자문 대체 아님.
- **로그**: `.claude/history/daily/<today>.md` 1줄 append.

---

## 6. 커맨드 복사·이식 절차

### 6-1. 기존 커맨드 복사 (가장 쉬움)

```bash
# 1) §2 표에서 토폴로지 확인 — 단일형 2파일 / 분업형 3파일
H=korea-commercial-legal   # 예: 가져갈 커맨드

# 2) 커맨드 + 짝 스킬 복사
mkdir -p <대상>/.claude/skills/$H <대상>/.claude/commands
cp .claude/commands/$H.md          <대상>/.claude/commands/
cp .claude/skills/$H/SKILL.md      <대상>/.claude/skills/$H/

# 3) 분업형(earnings/market)이면 에이전트도:
# cp .claude/agents/korea-earnings-disclosure-agent.md <대상>/.claude/agents/

# 4) (선택) 테스트 픽스처
cp -r test-fixtures/$H             <대상>/test-fixtures/

# 5) 산출물 경로는 코드에 상대경로(./specs/...)라 수정 불요.
#    대상 리포를 cwd로 두면 Claude Code가 자동 인식.
```

검증: `grep "^## " <대상>/.claude/commands/$H.md` → §0~§5
6섹션 보이면 OK.

### 6-2. 새 오리지널을 한국화 (신규 커맨드 작성)

같은 토폴로지 기존 커맨드를 **벤치마크 템플릿**으로:

| 새 커맨드가 ~ 라인업 | 벤치마크 |
|---|---|
| Small Business / Legal (단일 워크플로우) | `/korea-contract-reviewer` (단일형 기준) |
| Financial Services (분업 위임) | `/korea-earnings-reviewer` + 그 agent |

1. 벤치마크의 command.md(6섹션)·SKILL.md(4섹션) 복사
2. §0 정체성의 **변형 레이어 표**만 새 도메인으로 치환
   (기능·토폴로지·출력 문장은 그대로 — 데이터·문화만 바꿈)
3. §2 워크플로우 절차를 새 도메인 검토 단계로 치환
4. §3 grep 자가검증의 도메인 디스클레이머 키워드 치환
5. §4 Contract frontmatter 카운트 키를 도메인에 맞게
6. test-fixtures/ 에 샘플+ANSWER-KEY 쌍 (의도적 결함 +
   false positive 함정 동시 심기 — `test-fixtures/korea-*-legal/`
   참조)
7. 기계 대조: 커맨드 6헤딩·SKILL 4헤딩이 벤치마크와 1:1
   (`grep "^## "`)

### 6-3. 절대 하지 말 것

- 단일형↔분업형 토폴로지 변경 (오리지널 라인업 무시)
- 다른 커맨드·에이전트를 "재사용 패턴"으로 끼움 → pattern bleed
- 변형 레이어 2~3개 외의 기능·단계·출력 변경
- grep 자가검증 없이 완료 보고
- 외부 유료 커넥터 연동 흉내 (미연결 정직 명시 위반)

---

## 7. 디렉토리 맵

```text
aiceo-4th-training/
├── README.md                              ← 본 문서 (커맨드 중심 구조·복사 가이드)
├── .claude/
│   ├── commands/<harness>.md              ← [본체] 슬래시 커맨드 7개. 6섹션 Contract
│   ├── skills/<harness>/SKILL.md          ← [진입점] 자동 트리거 7개
│   ├── agents/<harness>-agent.md          ← [분업형 전용] 2개
│   └── history/
│       ├── daily/<YYYY-MM-DD>.md          ← 커맨드 실행 로그 (1줄 append)
│       └── themes/                        ← 리서치 박제
├── specs/claude-for-x-kr/<harness>/<slug>/<today>/00_*.md  ← 산출물
└── test-fixtures/<harness>/
    ├── sample-*.txt                       ← 가상 입력 (의도적 결함 + 함정)
    └── ANSWER-KEY.md                      ← 채점 정답지 (TDD)
```

---

## 8. 테스트 방법

`test-fixtures/<harness>/` 에 가상 입력 + 정답지 보유
(현재: contract-reviewer, commercial/privacy/employment-legal 4종).

```bash
# 1) 커맨드 실행
/korea-commercial-legal <test-fixtures/korea-commercial-legal/sample-service-agreement.txt 내용>

# 2) 출력을 ANSWER-KEY.md 와 대조 채점
#    - 高 심각도 위반 모두 잡았나? (식별력)
#    - false positive 함정을 오탐했나? (환각 방어)
#    - 자격사법 디스클레이머·Contract 키 있나? (불변식)
```

ANSWER-KEY.md = 의도적으로 심은 위반·근거·심각도 + **잡으면 안 되는
함정** + 채점 기준(우수/양호/미흡) + 불변식 대조 포인트를 미리 정의한
정답지(TDD).

---

## 9. 출처·배경

- 오리지널 라인업 분석·한국 수요 5-에이전트 종합·전수 현지화 매핑:
  옵시디언 vault `Themes/claude-harness-training/`
  (`claude-for-x-series-localization-mapping.md` 33개 전수 매핑,
  `claude-for-x-series-kr-demand.md` 한국 수요 우선순위)
- 본 README = 그 매핑의 **구현체(7 커맨드 하네스)** 구조·복사 가이드.
