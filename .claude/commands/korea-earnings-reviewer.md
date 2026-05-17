---
description: 한국 상장사 분기·반기·사업보고서 실적을 DART/KIND 공시 + 한국 IR 자료로 분석해, 모델 refresh와 thesis 변화 감지를 담은 실적 리뷰 마크다운 1개를 산출한다 (Anthropic Financial Services "Earnings Reviewer"의 한국형 — 패턴 불변, 데이터·문화 레이어만 치환)
argument-hint: <종목명 또는 종목코드 / 분기 (예: 삼성전자 2026 1Q)>
allowed-tools: Bash, Read, Write, Grep, Glob, Task, WebSearch, WebFetch
---

# /korea-earnings-reviewer — 한국형 실적 리뷰 하네스

## 0. 정체성 (오리지널 패턴 충실 — 무엇이 불변인가)

이 하네스는 Anthropic Financial Services 라인업의 **Earnings Reviewer**
(agent template, 토폴로지 = Skills + Connectors + **Subagents**)를
**기능·토폴로지·출력 포맷 불변**으로 한국에 이식한 것이다.

**오리지널에서 변하지 않는 것 (절대 변형 금지):**

- **기능 3종**: ① 컨퍼런스콜 전사·공시 분석 ② 금융 모델 refresh
  ③ thesis(투자 논리) 변화 감지
- **토폴로지**: 메인(오케스트레이터)이 sub-task를 **subagent에 위임**
  한다. 이 subagent는 특정 sub-task 전담이다(공시 본문 추출·콜 전사
  요지화). 누락 보완형 중복 병렬이 아니다 — **분업 위임**이다.
- **출력**: 실적 분석 리포트 1개(요약 → 실적 수치 → 모델 변화 →
  thesis 변화 → 리스크).

**변형되는 것 — 데이터·문화 레이어 단 2개:**

| 레이어 | US 오리지널 | → 한국 |
|---|---|---|
| 데이터 | Financial Modeling Prep, 공시 DB, 콜 전사 서비스 | DART(전자공시), KIND(거래소공시), 한국 증권사 리포트, 한국 IR/콜 자료 |
| 문화·규제 | 美 분기 어닝 사이클(10-Q/10-K), GAAP | 한국 공시 의무(분기 45일·반기·사업보고서 90일), K-IFRS, 연결/별도 |

**이 하네스가 하지 않는 것:** 매수/매도 투자 권유, 목표주가 판정,
"이 종목이 더 낫다"는 우열 판단. 사실 종합·thesis 변화 **감지**까지가
본분이며, 전망은 "어느 출처가 그렇게 봤다"는 인용 형태로만 쓴다.

---

## 1. Step 0 — 공유 메타 산출 + 저장 경로 (오케스트레이터 본체)

대상은 `$ARGUMENTS`(종목명/코드 + 분기). **비어 있으면 한 번만 물어**
받고, 채워져 있으면 질문 없이 끝까지 수행한다.

```bash
now_kst=$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M KST')
today=$(TZ=Asia/Seoul date '+%Y-%m-%d')
run_id=$(TZ=Asia/Seoul date '+%H%M%S')
```

- `target` — 정규화한 대상(예: `삼성전자(005930) 2026 1Q`). 정규화는
  오케스트레이터가 한 번만.
- `slug` — `target`을 kebab-case로 (예: `samsung-005930-2026-1q`).

저장 경로(프로젝트 로컬, 전역 vault 미사용):

```bash
base="./specs/claude-for-x-kr/korea-earnings-reviewer/<slug>/<today>"
mkdir -p "$base"
if [ -f "$base/00_earnings_review.md" ]; then
  out="$base/00_earnings_review_<run_id>.md"
else
  out="$base/00_earnings_review.md"
fi
```

---

## 2. Step 1 — 공시 sub-task를 subagent에 위임 (오리지널 분업 패턴)

오리지널 토폴로지대로 **공시·콜 본문 추출 sub-task를
`korea-earnings-disclosure-agent`에 위임**한다. 이것은 분업이다 —
오케스트레이터는 분석·종합에 집중하고, subagent는 1차 자료 추출만 한다.

subagent에 전달할 prompt:

```
[메타]
target: <target>
now_kst: <now_kst>
today: <today>

위 대상의 직전 분기/반기/사업보고서 실적 공시와 IR/콜 자료의
1차 자료를 DART·KIND·한국 증권사·IR 페이지에서 추출하라.
(korea-earnings-disclosure-agent 정의의 지시를 그대로 수행한다.)
```

subagent는 압축된 1차 자료(공시 수치·콜 발언 요지·출처 URL)만
반환한다. 파일을 쓰지 않는다(최종 md는 오케스트레이터 1개).

---

## 3. Step 2 — 오케스트레이터 분석 (기능 3종 수행)

subagent가 반환한 1차 자료를 근거로 오케스트레이터가 직접 분석한다.
**오리지널 기능 3종을 순서대로:**

1. **공시·콜 분석** — 매출/영업이익/순이익, 연결·별도 구분, 전년동기·
   전분기 대비(YoY/QoQ), 세그먼트별 실적. **모든 수치에 출처 표기.**
2. **모델 refresh** — 직전 추정 대비 실제 차이(컨센서스 surprise),
   가이던스 변화. 컨센서스 데이터가 공개 범위에서 없으면 "공개 범위
   내 컨센서스 부재"로 정직히 기재(추정치 지어내기 금지).
3. **thesis 변화 감지** — 이번 실적·콜이 기존 투자 논리에 주는 변화
   신호만 **감지·기술**(예: 마진 추세 전환, 가이던스 하향, 신사업
   기여 시작). **판정·권유 아님.** 변화 신호마다 근거 출처를 단다.

환각 방어(엄수): subagent 반환 자료에 **없는 수치·발언을 만들지
않는다.** 출처 URL·발표 주체가 확인 안 되는 항목은 폐기. 0건이면
"해당 분기 공시 미확인"으로 정직히 보고.

---

## 4. Step 3 — 마크다운 1개 저장 + 결정적 자가검증 + 로그

§5 Contract대로 **마크다운 1개**를 `$out`에 Write. 그 외 md 안 만듦.

저장 직후 **결정적 자가검증**(기계 확인 후에만 완료 보고):

```bash
test -f "$out" && echo "FILE_OK $out" || echo "FILE_MISSING $out"
for k in harness target slug run_at run_id quarter sources_count thesis_change_count; do
  grep -q "^$k:" "$out" && echo "key $k OK" || echo "key $k MISSING"
done
# 모든 핵심 수치에 출처가 달렸는지 표본 확인 (수치 섹션에 URL/매체 0건이면 실패)
grep -qE 'https?://|DART|KIND' "$out" && echo "SOURCE_OK" || echo "SOURCE_MISSING"
```

검증 통과(파일 존재 + 키 완비 + 출처 표기 존재) **뒤에만** 완료 보고.
실패면 md 수정 후 재검증.

작업 로그 1줄 append:

```bash
log=".claude/history/daily/<today>.md"
[ -f "$log" ] || printf '## Claude Code 작업 로그\n\n' > "$log"
# - HH:MM | [<device-label>] | korea-earnings-reviewer | <target> — thesis변화 N건, 출처 M건
```

device-label은 `$CLAUDE_DEVICE_LABEL` 또는
`~/.claude/hooks/get-device-label.sh` 출력.

사용자 보고: 저장 경로, 핵심 실적 1~2문장, thesis 변화 신호 수,
출처 수.

---

## 5. 최종 md Contract (구조 고정 — 표현 자유)

frontmatter에 아래 키 **전부** 포함. Contract 외 키 추가 금지.

```yaml
---
harness: korea-earnings-reviewer
target: <정규화 대상>
slug: <slug>
run_at: <now_kst>
run_id: <run_id>
quarter: <분기 식별 예: 2026-1Q>
sources_count: <인용 출처 수>
thesis_change_count: <감지된 thesis 변화 신호 수>
---
```

본문 섹션(모두 포함, 요약 맨 앞):

1. **요약** *(맨 앞)* — 이번 실적 핵심과 thesis 변화 한눈 정리.
   근거 출처 표기.
2. **실적 수치** — 매출/영업이익/순이익(연결·별도), YoY/QoQ,
   세그먼트. 표 형태. 모든 수치 출처 표기.
3. **모델 변화** — 컨센서스 대비 surprise, 가이던스 변화. 공개 범위
   부재 시 정직 기재.
4. **thesis 변화 신호** — 감지된 변화만 목록. 신호별 근거 출처.
   판정·권유 없음.
5. **리스크·한계** — 미확인 공시, 데이터 한계, 면책(투자 권유 아님).

---

## 6. 불변식 (어기면 하네스 실패)

1. 오리지널 토폴로지 보존 — 공시 추출은 subagent 위임(분업). 누락
   보완형 중복 병렬로 바꾸지 않는다.
2. 기능 3종(공시분석·모델refresh·thesis변화) 모두 수행. 하나라도
   누락하면 실패.
3. subagent는 파일 안 씀. md는 오케스트레이터 1개만.
4. 모든 수치·발언에 출처. 없는 것 생성 금지. 0건은 0건으로.
5. 투자 권유·목표주가 판정·우열 판단 금지. 전망은 인용 형태만.
6. 저장 후 grep 기계 확인한 뒤에만 완료 보고.
