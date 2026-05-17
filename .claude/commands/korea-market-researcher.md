---
description: 한국 섹터·발행자(상장사) 뉴스를 KIND/한국 산업연구원/한국 증권사 리서치로 모니터링하고, 리서치 합성 + 중요 발견 에스컬레이션을 담은 섹터 리서치 마크다운 1개를 산출한다 (Anthropic Financial Services "Market Researcher"의 한국형 — 패턴 불변, 데이터·문화 레이어만 치환)
argument-hint: <섹터/산업 또는 발행자 (예: 2차전지 / 반도체 소부장 / 셀트리온)>
allowed-tools: Bash, Read, Write, Grep, Glob, Task, WebSearch, WebFetch
---

# /korea-market-researcher — 한국형 섹터 리서치 하네스

## 0. 정체성 (오리지널 패턴 충실 — 무엇이 불변인가)

이 하네스는 Anthropic Financial Services 라인업의 **Market Researcher**
(agent template, 토폴로지 = Skills + Connectors + **Subagents**)를
**기능·토폴로지·출력 포맷 불변**으로 한국에 이식한 것이다.

**오리지널에서 변하지 않는 것 (절대 변형 금지):**

- **기능 3종**: ① 섹터·발행자 뉴스 **모니터링** ② 리서치 **합성**
  ③ 중요 발견 **에스컬레이션**(주목할 신호를 끌어올림)
- **토폴로지**: 메인이 섹터 신호 수집 sub-task를 **subagent에 위임**
  (분업). 누락 보완형 중복 병렬이 아니다.
- **출력**: 섹터 리서치 리포트(에스컬레이션 맨 앞 → 섹터 동향 합성
  → 발행자별 신호 → 모니터링 로그).

**에스컬레이션은 오리지널의 핵심 동사다 — 평탄화 금지.** 단순 뉴스
나열로 끝내면 패턴 변질이다. 수집·합성한 것 중 **"이건 주목해야
한다"는 발견을 명시적으로 끌어올려** 리포트 맨 앞에 둔다.

**변형되는 것 — 데이터·문화 레이어 단 2개:**

| 레이어 | US 오리지널 | → 한국 |
|---|---|---|
| 데이터 | Guidepoint, Third Bridge, IBISWorld, 브로커 리서치 | KIND 공시, 한국 산업연구원(KIET), 한국 증권사 리서치, 산업·섹터 뉴스 |
| 문화·규제 | 美 섹터 분류(GICS 美 기준), 美 expert network | 한국 산업분류·테마 체계, 공시 기반 한국 섹터 구분 |

**이 하네스가 하지 않는 것:** 매수/매도 권유, 섹터 우열 랭킹,
"이 섹터가 더 낫다"는 판정. 모니터링·합성·에스컬레이션까지가
본분이며, 전망은 인용 형태로만 쓴다.

---

## 1. Step 0 — 공유 메타 산출 + 저장 경로 (오케스트레이터 본체)

대상은 `$ARGUMENTS`(섹터/산업/발행자). **비어 있으면 한 번만 물어**
받고, 채워져 있으면 질문 없이 끝까지.

```bash
now_kst=$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M KST')
today=$(TZ=Asia/Seoul date '+%Y-%m-%d')
run_id=$(TZ=Asia/Seoul date '+%H%M%S')
```

- `subject` — 정규화한 섹터/발행자(예: `2차전지 소재`). 한 번만.
- `slug` — kebab-case(예: `secondary-battery-materials`).

저장 경로(프로젝트 로컬, 전역 vault 미사용):

```bash
base="./specs/claude-for-x-kr/korea-market-researcher/<slug>/<today>"
mkdir -p "$base"
if [ -f "$base/00_market_research.md" ]; then
  out="$base/00_market_research_<run_id>.md"
else
  out="$base/00_market_research.md"
fi
```

---

## 2. Step 1 — 섹터 신호 수집 sub-task를 subagent에 위임

오리지널 분업 패턴대로 **섹터·발행자 뉴스/리서치 1차 신호 수집을
`korea-sector-signal-agent`에 위임**한다. 분업이다 — 오케스트레이터는
합성·에스컬레이션에 집중하고, subagent는 1차 신호 수집만.

subagent 전달 prompt:

```
[메타]
subject: <subject>
now_kst: <now_kst>
today: <today>

위 섹터/발행자의 최근 동향 1차 신호(뉴스·공시·리서치 요지)를
KIND·한국 산업연구원·한국 증권사 리서치·산업 뉴스에서 수집하라.
(korea-sector-signal-agent 정의의 지시를 그대로 수행한다.)
```

subagent는 압축된 1차 신호만 반환(파일 금지).

---

## 3. Step 2 — 오케스트레이터 합성 + 에스컬레이션 (기능 3종)

subagent 반환 신호로 오케스트레이터가 직접:

1. **모니터링 정리** — 수집된 섹터·발행자 신호를 시간순·주제별로
   정리. 각 신호 출처 표기.
2. **리서치 합성** — 개별 신호를 섹터 차원으로 종합(공통 테마,
   수급·정책·실적 흐름). 합성 문장마다 근거 신호 출처.
3. **에스컬레이션** *(핵심)* — 합성 결과 중 **주목해야 할 발견을
   명시적으로 끌어올린다.** 기준: 추세 전환 신호, 정책·규제 변화,
   섹터 모멘텀 변곡, 발행자 중대 이벤트. 각 에스컬레이션 항목에
   "왜 주목인지 + 근거 출처". **판정·권유가 아니라 주의 환기.**

환각 방어: subagent 신호에 **없는 사실을 만들지 않는다.** 출처
미확인 항목 폐기. 0건이면 "윈도우 내 유효 신호 부재"로 정직히.

---

## 4. Step 3 — 마크다운 1개 저장 + 결정적 자가검증 + 로그

§5 Contract대로 **마크다운 1개**를 `$out`에 Write.

결정적 자가검증(기계 확인 후에만 완료 보고):

```bash
test -f "$out" && echo "FILE_OK $out" || echo "FILE_MISSING $out"
for k in harness subject slug run_at run_id signals_count escalation_count; do
  grep -q "^$k:" "$out" && echo "key $k OK" || echo "key $k MISSING"
done
# 에스컬레이션 섹션이 실제로 존재하는지 (평탄화 방지 — 핵심 패턴 검증)
grep -q '에스컬레이션' "$out" && echo "ESCALATION_OK" || echo "ESCALATION_MISSING"
```

검증 통과(파일 + 키 + 에스컬레이션 섹션 존재) **뒤에만** 완료 보고.

로그 1줄 append:

```bash
log=".claude/history/daily/<today>.md"
[ -f "$log" ] || printf '## Claude Code 작업 로그\n\n' > "$log"
# - HH:MM | [<device-label>] | korea-market-researcher | <subject> — 신호 N건, 에스컬레이션 M건
```

사용자 보고: 저장 경로, 섹터 동향 1~2문장, 에스컬레이션 항목 수.

---

## 5. 최종 md Contract (구조 고정 — 표현 자유)

frontmatter에 아래 키 **전부**. Contract 외 키 금지.

```yaml
---
harness: korea-market-researcher
subject: <정규화 섹터/발행자>
slug: <slug>
run_at: <now_kst>
run_id: <run_id>
signals_count: <수집 신호 수>
escalation_count: <에스컬레이션 항목 수>
---
```

본문 섹션(모두 포함, 에스컬레이션 맨 앞):

1. **에스컬레이션** *(맨 앞 · 오리지널 핵심)* — 주목해야 할 발견
   목록. 각 항목: 무엇을 / 왜 주목 / 근거 출처. 0건이면 "주목
   신호 없음"으로 정직히.
2. **섹터 동향 합성** — 신호를 섹터 차원으로 종합한 서술. 근거 표기.
3. **발행자/세부 신호** — 발행자·세부 주제별 신호 정리. 출처 표기.
4. **모니터링 로그·한계** — 수집 소스, 0건 소스, 데이터 한계,
   면책(투자 권유 아님).

---

## 6. 불변식 (어기면 하네스 실패)

1. 오리지널 토폴로지 보존 — 신호 수집 subagent 위임(분업). 누락
   보완형 중복 병렬로 바꾸지 않는다.
2. 기능 3종(모니터링·합성·에스컬레이션) 모두 수행. 에스컬레이션
   평탄화(단순 나열) 금지 — 명시적 끌어올림 필수.
3. subagent는 파일 안 씀. md는 오케스트레이터 1개만.
4. 모든 합성·신호에 출처. 없는 것 생성 금지. 0건은 0건으로.
5. 섹터 우열 랭킹·투자 권유 금지. 전망은 인용 형태만.
6. 저장 후 grep 기계 확인한 뒤에만 완료 보고.
