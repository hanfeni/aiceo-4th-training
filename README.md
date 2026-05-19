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

---

## 10. 사용 안내 — 프롬프트만으로 셀프 하네싱 (메시지 놓친 사람용)

> 이 절은 슬랙·카톡 안내를 못 본 사람이 **이 README만 보고도**
> 사용법을 재현할 수 있도록 남긴 메모다. 코딩 없이 프롬프트만
> 복붙해 하네스를 만드는 두 가지 트랙이 있다.

### 10-A. 트랙 ① — 5개 부트스트랩 프롬프트 (링크 내용을 복붙)

`bootstrap/` 5개 .md는 **그 자체가 "읽은 에이전트가 하네스를
구축하도록" 시키는 메타 프롬프트**다. 링크 참조가 아니라
**파일 본문 전체를 복사해 Claude Code 프롬프트 창에 붙여넣어야**
작동한다.

| 파일 | 유형 | 용도 |
|---|---|---|
| `BOOTSTRAP-PROMPT.md` | 복붙형 | 범용 리뷰 모니터링 (자사/타사 서비스·앱·회사 사용자 리뷰) |
| `BOOTSTRAP-PROMPT-AUTONOMOUS.md` | 자율형 | 위와 동일 목적, 에이전트에 여지를 주는 간결판 |
| `BOOTSTRAP-PROMPT-SAYUWON.md` | 복붙형 | 위를 특정 업체(사유원)에 맞게 출처·단계 튜닝한 사례 |
| `BOOTSTRAP-PROMPT-SEARCH-AUTONOMOUS.md` | 자율형 | 검색 누락방지 (5개 병렬 에이전트 동시 수행) |
| `BOOTSTRAP-PROMPT-CARD-RESEARCH-AUTONOMOUS.md` | 자율형 | 명함 정보 기반 인물 리서치·정보 증강 |

- **복붙형**: 에이전트가 그대로 실행하도록 길고 상세하게 지시.
- **자율형**: 에이전트에 약간의 재량을 주는 간결한 지시.
- 궁극 산출 구조는 둘 다 동일하다.

### 10-B. 트랙 ② — 7개 커맨드 셀프하네싱 (완성품 모방 설치)

`.claude/commands/` 7개는 **이미 완성된 하네스**다. 링크를
에이전트에 주고 "이 구조 그대로 복제·설치"시키면 재현된다.
프롬프트 형식은 §6-1 cp 절차와 동일한 의도 — 차이는
**에이전트가 원격에서 읽어 직접 설치**한다는 점.

7개 커맨드 카탈로그·토폴로지는 §2 표 참조. 설치 프롬프트
공통 골격:

```text
아래 GitHub 링크의 커맨드를 참조해서, 동일한 하네스를
내 전역(~/.claude/)에 설치해줘.

링크: <아래 ⚠️ 주의의 raw URL>

작업 순서:
1. 위 링크 본문을 읽어 커맨드 전체 내용을 파악한다.
2. 같은 리포의 짝 파일도 함께 읽는다:
   - 단일형(2파일): .claude/skills/<H>/SKILL.md
   - 분업형(3파일): + .claude/agents/<H>-agent.md
     (earnings→korea-earnings-disclosure-agent,
      market →korea-sector-signal-agent)
3. 아래 파일을 내용 변경 없이 그대로 생성:
   ~/.claude/commands/<H>.md
   ~/.claude/skills/<H>/SKILL.md
   (분업형이면 ~/.claude/agents/<H>-agent.md 도)
4. 자가검증: grep "^## " ~/.claude/commands/<H>.md 가
   원본과 동일 섹션 구조인지 + (법무 커맨드면 변호사법
   §109 등 디스클레이머 존재) 확인 후 보고.
5. 토폴로지 불변: 단일형에 subagent 끼우지 말 것 /
   분업형 에이전트 누락 말 것. 어떤 재해석·요약·개선도
   하지 말 것.
```

- **설치 레벨**: 기본 전역(`~/.claude/`). 특정 프로젝트만
  원하면 프롬프트의 `~/.claude/` → `./.claude/` 로 치환.

### 10-C. ⚠️ 주의 — 반드시 raw URL을 읽혀라 (검증된 함정)

> 이 머신에서 `korea-employment-legal` 설치를 실제로 검증한
> 결과(2026-05-18): **GitHub blob 링크를 WebFetch로 읽히면
> 보조 모델이 영어로 요약·축약한 변형본을 반환**한다. 그대로
> 설치하면 리포의 핵심 불변식("어떤 재해석·요약·개선도 하지
> 말 것")이 도구 단계에서 깨진다.
>
> **해결**: blob URL을 raw URL로 바꿔, 원문 바이트를 그대로
> 받게 한다 (sha256 원본=설치본 완전 일치 확인됨).

raw URL 변환 규칙:

```text
github.com/hanfeni/aiceo-4th-training/blob/main/<경로>
        ↓ (blob → raw, 호스트 교체)
raw.githubusercontent.com/hanfeni/aiceo-4th-training/main/<경로>
```

- 에이전트에게는 **raw.githubusercontent.com URL**을 주고
  "원문을 변형 없이 그대로 받아 설치"라고 명시한다.
- 설치 후 `grep "^## "` 섹션 수 + (법무는) 디스클레이머
  문구 존재를 기계 확인한 뒤에만 완료로 본다.

---

## 11. 2회차 실습 — 검색 문서 Feasibility PoC

> §1~10은 **1회차(5/15) 사후 보강** 배포물(부트스트랩·7커맨드).
> 아래는 **2회차(5/22) "제작"** 실습 자산이다. 주제가 달라
> 별도 섹션으로 분리한다.

### 11-1. 무엇인가

5개 도메인 각각에 **검색3종(BM25·임베딩·하이브리드) + SQL + 그래프**
실습이 실제로 성립하는지 검증하는 PoC. 데이터셋 선정은
5-에이전트 병렬 조사 6차(라이선스·무인증접근·실 curl 다운로드·
본문품질)로 확정했다.

- 문서: [docs/PRD.md](docs/PRD.md) ·
  [docs/use-cases](docs/use-cases/search-feasibility-poc_use_cases.md) ·
  [docs/qa](docs/qa/search-feasibility-poc_test_cases.md) ·
  [docs/plans](docs/plans/search-feasibility-poc_plan.md)
- 정답지(ground truth) 없이 진행 → **정량(nDCG) 아닌 정성 feasibility**.

### 11-2. 5개 도메인 (구조화 데이터 + 검색 문서 짝)

| 도메인 | 구조화(SQL/그래프) | 검색 문서(임베딩) | 출처 |
|---|---|---|---|
| 상권 | 상가(상권)정보 | 정책뉴스 소상공인 | data.go.kr / korea.kr |
| 의료 | 약가마스터 | 의약품안전나라 허가상세 | data.go.kr / nedrug |
| 금융 | 국민연금 사업장 | 정책뉴스 고용·금융 | data.go.kr / korea.kr |
| 법률 | 법령 메타 CSV | legalize-kr 법령 본문 + 판례참조 | 법제처 CSV / GitHub |
| 정책 | 세출예산(다기관 결합) | 정책브리핑 보도자료 | data.go.kr / korea.kr |

> ⚠️ 함정: korea.kr `pressReleaseView`는 본문이 HWP-iframe에
> 갇혀 40자만 추출됨(검증됨). **`policyNewsView` 또는 RSS
> CDATA 경로**를 써야 한다.

### 11-3. ⚠️ 실데이터는 리포에 없다 (재현으로 확보)

수집한 실데이터(상가·약가·국민연금 CSV, 법령·의약품·정책뉴스
본문)는 **제3자 저작권 본문 + 공개 리포라 `.gitignore`로 전량
제외**된다 (`poc/data/`, `*.jsonl`, 인덱스, legalize-kr clone).

```text
poc/data/<domain>/   ← git 추적 안 됨. 강사 로컬에만 존재.
  ├─ <구조화>.csv     (상가/약가/국민연금/법령메타/세출예산)
  ├─ <검색문서>.jsonl ({doc_id,title,body,url,char_count})
  └─ _collect_meta.json (출처·건수·라이선스·함정노트)
```

- 강의 노트북이 다른 기기면 **재수집 또는 별도 복사** 필요
  (git clone으로는 데이터가 안 따라온다 — 의도된 안전장치).
- 재현: vault 데이터 노트 §6차의 수집 URL/방식을 그대로 사용.
  data.go.kr은 2단계 다운로드(준비 JSON→atchFileId→fileDownload).
- 라이선스: 공공누리 1유형/제한없음/공공저작물·MIT(legalize-kr).
  정책 텍스트만 — 이미지·사진은 제3자 권리라 제외.

### 11-4. 실습 산출물 — 코딩에이전트 프롬프트 3종

> 이 강의는 수강생이 코드를 직접 짜지 않는다. **1회차
> `bootstrap/`와 같은 방식** — 코딩에이전트에 프롬프트를
> 복붙하면 에이전트가 수행한다.

`round2-prompts/` 에 3단계 완성 프롬프트:

| 파일 | 시킬 일 |
|---|---|
| `03-메타스키마발굴-프롬프트.md` | LLM 샘플링 수렴으로 도메인 메타 스키마 발굴 |
| `02-LLM메타라벨링-프롬프트.md` | 검색 문서에 LLM 메타 부착 (사내 1단계 분류 패턴) |
| `01-검색인덱싱-프롬프트.md` | OpenSearch+Nori+OpenAI 하이브리드 검색 구축 |

- 복붙 순서·트랙(풀코스/빠른체험/메타만)·도메인 선택은
  [round2-prompts/README.md](round2-prompts/README.md) 참조.
- 각 프롬프트 `## 0. 절대 규칙`에 6차 검증·architect AI1~AI8
  가드레일이 박혀 있다(데이터 재수집 금지·knn 차원 락인·
  `pressReleaseView` 함정 회피·문서 단위 메타 등).
- `docs/`(PRD·use-cases·QA·plan)는 **프롬프트 설계 근거**로
  보존. plan의 슬라이스/TDD/실행코드 계획은 폐기(이 강의는
  실행 코드가 아니라 프롬프트가 산출물).
- ⚠️ blob→raw URL 함정은 §10-C와 동일하게 적용된다.
