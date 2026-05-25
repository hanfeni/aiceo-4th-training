---
description: 수강생 자연어 에이전트 요청 → 시나리오 A(Claude Code 단독)·B(aiceo-4th-agent 커스텀 앱) 2-시나리오 실행 가이드 1장. 분업형 4-Agent 오케스트레이션. v2 (내부 자산 권고 폐기, 실행 가이드 중심 재편).
argument-hint: <자연어 에이전트 요청>
allowed-tools: Bash, Read, Write, Grep, Glob, WebSearch, WebFetch, Task
---

# /agent-solution-consultant v2 — 에이전트 실행 가이드 컨설턴트

> 입력: 수강생 1명의 자연어 에이전트 요청 1건.
> 출력: **6섹션 실행 가이드 1장** (`./specs/agent-solution-consultant/<slug>/<today>/00_consultation.md`).
> 토폴로지: **분업형 4-Agent** (오케스트레이터 + requirements-analyst · dependency-scout · solution-architect · risk-feasibility-auditor).
> v2 핵심: **수강생이 다음 주 강의에서 즉시 손으로 만드는 두 가지 길**(시나리오 A·B)에 집중. v1의 4안(0/1/2/3) 분류 + 내부 자산 매핑 폐기.

---

## §0 정체성

### 무엇

수강생이 자연어로 던진 "이런 에이전트 만들고 싶어"를 받아, **두 가지 실행 시나리오**(A: Claude Code 단독 / B: aiceo-4th-agent 기반 커스텀 앱)와 **사전 준비물·구조 다이어그램·엔터프라이즈 점검**을 담은 실행 가이드 1장을 산출한다. 3회차(2026-05-29) "자기 회사에 필요한 에이전트 만들기" 강의의 즉시 실습 자료.

### 불변 (어겨선 안 되는 것)

- **기능**: 실행 가이드 — 코드 직접 작성 금지, 산출물은 마크다운 1개
- **토폴로지**: 4 subagent 모두 호출 강제
- **입력**: 자연어 1건 (`$ARGUMENTS`)
- **출력**: 6섹션 마크다운 1개 + frontmatter Contract 고정 키
- **v2 핵심 제약**: 내부 자산(`/korea-*`·`poc/data/`·`bootstrap/`) 인용 금지 — "기존 자산 재사용" 가이드 금지

### v1 → v2 변경 사유

v1은 "4안(안 만들기·MVP·풀버전·멀티) 컨설팅 리포트"였다. 그러나 사용자 결정으로:
1. 수강생은 본 리포의 7 한국 커맨드를 모름 — 내부 자산 권고가 실습 동력 꺾음
2. 산출물이 평가·매트릭스 중심 → 실행 가이드로 재편 필요
3. 두 가지 실행 경로(Claude Code 단독 vs aiceo-4th-agent 커스텀)에 집중

---

## §1 Step 0 — 입력 수령·정규화

1. `$ARGUMENTS` 수령. 비면 1회만 요청 → "자연어로 만들고 싶은 에이전트 1줄 입력"
2. **slug 결정**: 요청 첫 명사 3개 kebab-case
3. **익명화**: 실명·회사명·이메일 발견 시 slug·로그에서 마스킹
4. **저장 경로**:
   ```
   ./specs/agent-solution-consultant/<slug>/<today>/00_consultation.md
   ```
   같은 날 재실행 시 `00_consultation_<run_id>.md` suffix.
5. **사전 분류**:
   - `request_type`: 모니터링 / 검색 / 생성 / 오케스트레이션 / 통합
   - `trigger`: cron / webhook / 수동
   - `sensitivity_hint`: low / medium / high

---

## §2 Step 1 — 4-Agent 오케스트레이션

### 모델 라우팅

- 오케스트레이터(본 커맨드) = **Opus 4.7**
- requirements-analyst · dependency-scout = **Sonnet 4.6** (빠름·저렴)
- solution-architect · risk-feasibility-auditor = **Opus 4.7** (정교)

### 호출 의존성

```
        [Step A·B 병렬 가능]
              │              │
              ▼              ▼
     requirements-analyst   dependency-scout
              │              │
              └──────┬───────┘
                     ▼
              solution-architect  ← A·B 산출 필수
                     │
                     ▼
              risk-feasibility-auditor  ← C 산출 필수
                     │
                     ▼
              오케스트레이터 통합 → Write
```

### Subagent prompt 골격 (강제 — v2)

```text
# Step A — requirements-analyst (Sonnet)
Task(subagent_type="requirements-analyst", prompt="""
스펙: .claude/agents/requirements-analyst.md 정독.
yaml 7섹션 모두 채워 압축 텍스트로 반환. 파일 쓰지 말 것.

요청 원문: <ARGUMENTS>
요청자 컨텍스트: <slug 또는 추론>
""")

# Step B — dependency-scout (Sonnet) — v2 신규 (pattern-matcher 폐기)
Task(subagent_type="dependency-scout", prompt="""
스펙: .claude/agents/dependency-scout.md 정독.
yaml 6섹션 (api_keys·saas_signups·mcp_tools·internal_access_requests·other_setup·regulatory_preflight) + preflight_summary 채울 것. 파일 쓰지 말 것.

요청 원문: <ARGUMENTS>
sensitivity_hint: <low/medium/high>
주의: **내부 자산 매핑 금지**. 외부 API·SaaS·MCP·사내 시스템만.
사내 접근 권한 요청 문구는 한국어 비즈니스 톤 복붙형.
""")

# Step C — solution-architect (Opus) — v2 시나리오 A·B
Task(subagent_type="solution-architect", prompt="""
스펙: .claude/agents/solution-architect.md 정독. v2 시나리오 A·B 산출.
yaml: common·scenario_a·scenario_b·comparison 4 키.
scenario_a/b 각각 5 키 (overview·text_diagram·harness_elements_or_files·execution_flow·limits_and_evolution).
scenario_b.copypaste_prompt는 200줄 이상 또는 충분히 자세하게.

요청 원문: <ARGUMENTS>
--- 입력 A: requirements-analyst 산출 ---
<yaml 그대로>
--- 입력 B: dependency-scout 산출 ---
<yaml 그대로>

v2 핵심 제약: 내부 자산(/korea-*·poc/data·bootstrap) 인용 금지.
""")

# Step D — risk-feasibility-auditor (Opus)
Task(subagent_type="risk-feasibility-auditor", prompt="""
스펙: .claude/agents/risk-feasibility-auditor.md 정독.
yaml: BCG 5축 점수 (시나리오 A·B 각각) + korea_traps + premature_autonomy_warnings + hitl_checkpoints + overall_recommendation.

요청 원문: <ARGUMENTS>
sensitivity: <low/medium/high>
--- 입력: solution-architect 시나리오 A·B 요약 ---
<요약 또는 yaml 발췌>

작업: v2는 4안이 아닌 시나리오 2개 점검. 각 시나리오에 BCG 5축 + HITL.
""")
```

### Subagent 산출 검증 (correction loop)

```bash
# requirements-analyst 검증
echo "$A_OUT" | grep -qE "request_type:|sensitivity:|decision_nodes:|api_integrations:" || RECALL_A=true

# dependency-scout 검증 (v2)
echo "$B_OUT" | grep -qE "api_keys:|saas_signups:|mcp_tools:|internal_access_requests:|other_setup:|regulatory_preflight:" || RECALL_B=true

# solution-architect 검증 (v2 — 핵심)
echo "$C_OUT" | grep -qE "scenario_a:" || RECALL_C=true
echo "$C_OUT" | grep -qE "scenario_b:" || RECALL_C=true
echo "$C_OUT" | grep -qE "copypaste_prompt:" || RECALL_C=true

# risk-feasibility-auditor 검증
echo "$D_OUT" | grep -qE "data_safety:|integration:|change_mgmt:|roi_measurement:|governance:" || RECALL_D=true
```

검증 실패 시 1회만 재호출 (correction prompt에 누락 키 명시). 재호출 후에도 실패면 오케스트레이터가 누락분 수동 합성 + 튜닝로그 기록.

---

## §3 Step 2 — 저장·자가검증·보고

### 3-1. Write — 마크다운 1개 산출 (v2 6섹션 골격)

```text
---
<frontmatter §4 Contract>
---

# <요청 1줄 요약> — 에이전트 실행 가이드

> 요청자: <익명화>
> 분류: <request_type> · 민감도: <sensitivity>
> 생성: <run_at>

## §0 요청 정규화
   - 분류표 (request_type / trigger / deliverable / sensitivity / HITL / decision_nodes / api_integrations)
   - 실패 모드 5개
   - [requirements-analyst 산출 기반]

## §1 에이전트 구조 텍스트 다이어그램
   - 시나리오 A·B 각각 ASCII 다이어그램
   - 공통 흐름 (Trigger / Orchestrator / HITL / Deliverable)
   - [solution-architect 산출 기반]

## §2 사전 준비물 체크리스트
   ### 2-A. API 키 발급 목록
      (서비스명·URL·.env 키명·가격·저장 위치)
   ### 2-B. SaaS 가입·계정 등록
      (서비스·요금제·약관·계정 등록)
   ### 2-C. MCP 도구 설치·연결
      (MCP 서버명·인증·설치 명령)
   ### 2-D. 사내 시스템 접근 권한 요청 (복붙형 메일)
      대상 시스템 / 대상 팀 / 요청 방식 / 리드타임 / 메일 템플릿
   ### 2-E. 기타 환경 셋업
      (Docker·OpenSearch·VPN·등)
   ### 2-F. 한국 규제·preflight 점검
      (개보법·MS365 admin·KISA·등)
   ### 2-G. 강의 전 사전 준비 우선순위 (D-7·D-1·당일)
   - [dependency-scout 산출 기반]

## §3 시나리오 A — Claude Code 단독 (앱 미구축)
   ### 3-A. 개요
   ### 3-B. 추가할 하네스 파일 목록
      - SKILL.md / command.md / subagent.md / MCP 도구
   ### 3-C. 실행 흐름 (5단계)
   ### 3-D. 한계 + 단계 진화 (→ 시나리오 B로 진화 권고)
   - [solution-architect.scenario_a 기반]

## §4 시나리오 B — aiceo-4th-agent 기반 커스텀 앱
   ### 4-A. 개요
   ### 4-B. 추가할 파일 목록
      - app/<slug>/page.tsx (UI)
      - app/api/<route>/route.ts (API)
      - lib/<feature>.ts (로직)
      - .env.local 키 추가
   ### 4-C. 복붙 프롬프트 (Claude Code 그대로 붙여넣기)
      ```text
      너는 aiceo-4th-agent 리포에서 작업하는 코딩에이전트다.
      ... (200줄 이상)
      ```
   ### 4-D. 실행 흐름 (5단계)
   ### 4-E. 한계 + 단계 진화
   - [solution-architect.scenario_b 기반]

## §9 엔터프라이즈 점검 (BCG 5축)
   ### 9-A. 점수표 (시나리오 A·B × 5축)
      (데이터 안전 · 통합 복잡도 · 변경 관리 · ROI 측정 · 거버넌스)
   ### 9-B. 한국 환경 함정
   ### 9-C. 성급한 자율화 경고
   ### 9-D. HITL 체크포인트
   ### 9-E. 최종 권고 (A·B 중 어느 것을 언제 선택할지)
   - [risk-feasibility-auditor 산출 기반]
```

### 3-2. grep 결정적 자가검증 (v2)

```bash
F=./specs/agent-solution-consultant/<slug>/<today>/00_consultation.md

# 6개 헤딩 (§0·§1·§2·§3·§4·§9)
[ $(grep -c "^## §" "$F") -ge 6 ] || FAIL "헤딩 누락"

# §2 하위 7섹션 (2-A~2-G)
for SUB in "2-A" "2-B" "2-C" "2-D" "2-E" "2-F" "2-G"; do
  grep -qE "^### $SUB|^### 2-[A-G]" "$F" || FAIL "§2 하위 누락: $SUB"
done

# §3 하위 4섹션 (3-A~3-D)
for SUB in "3-A" "3-B" "3-C" "3-D"; do
  grep -qE "^### $SUB" "$F" || FAIL "§3 하위 누락: $SUB"
done

# §4 하위 5섹션 (4-A~4-E)
for SUB in "4-A" "4-B" "4-C" "4-D" "4-E"; do
  grep -qE "^### $SUB" "$F" || FAIL "§4 하위 누락: $SUB"
done

# §9 하위 5섹션 (9-A~9-E)
for SUB in "9-A" "9-B" "9-C" "9-D" "9-E"; do
  grep -qE "^### $SUB" "$F" || FAIL "§9 하위 누락: $SUB"
done

# 시나리오 A·B 텍스트 다이어그램 (ASCII 박스 ┌·└)
grep -qE "[┌└─].*[┐┘]" "$F" || FAIL "ASCII 다이어그램 누락"

# §4 복붙 프롬프트 (200자 이상 코드 블록)
awk '/^```/{f=!f; next} f' "$F" | wc -c | awk '$1<200 {exit 1}' || FAIL "복붙 프롬프트 짧음"

# 사내 접근 권한 메일 템플릿 키워드
grep -qE "안녕하세요|회신 부탁드립니다|read-only" "$F" || FAIL "메일 템플릿 누락"

# BCG 5축
for AX in "데이터 안전" "통합 복잡도" "변경 관리" "ROI 측정" 거버넌스; do
  grep -q "$AX" "$F" || FAIL "BCG 5축 누락: $AX"
done

# v2 핵심 제약: 내부 자산 인용 금지
if grep -qE "/korea-(market-researcher|earnings-reviewer|contract-reviewer|content-strategist|commercial-legal|privacy-legal|employment-legal)" "$F"; then
  FAIL "v2 제약 위반: 내부 자산 인용 발견"
fi
if grep -qE "poc/data/|bootstrap/BOOTSTRAP-PROMPT|round2-prompts/" "$F"; then
  FAIL "v2 제약 위반: 내부 자산 경로 인용 발견"
fi

# Frontmatter 12 키
for K in harness slug run_at run_id request_type sensitivity scenarios_count decision_nodes api_integrations subagents dependencies risk_score; do
  grep -q "^$K:" "$F" || FAIL "frontmatter 키 누락: $K"
done

# 한국 함정 최소 1
grep -qE "(MS365|금융망분리|KISA|개인정보|관리자 동의|OAuth|변호사법|의료법|개보법|저작권|산안법|중대재해)" "$F" || FAIL "한국 함정 누락"
```

### 3-3. 로그 append

```bash
LOG=.claude/history/daily/$(date +%Y-%m-%d).md
mkdir -p "$(dirname "$LOG")"
echo "- $(date +%H:%M) | agent-solution-consultant v2 | <slug> | <request_type>/<sensitivity> | $F" >> "$LOG"
```

### 3-4. 보고

grep 전부 통과한 뒤에만 "완료" 보고:

```
✅ 실행 가이드 생성: <F>
   - 분류: <request_type> · 민감도: <sensitivity>
   - 결정 노드: <N>개 · API: <M>개
   - 4 subagent 모두 호출 ✓
   - grep 자가검증 (6 § + 21 ###) 통과 ✓
   - 시나리오 A 파일: <N>개 / 시나리오 B 파일: <M>개
   - 사내 접근 권한 요청: <N>건
   - 추천: 시나리오 <A 또는 B> — <한 줄>
```

---

## §4 Contract — frontmatter 키 (12개, v2)

```yaml
---
harness: agent-solution-consultant
version: v2
slug: <요청-slug>
run_at: <ISO8601 KST>
run_id: <epoch>
request_type: <모니터링|검색|생성|오케스트레이션|통합>
sensitivity: <low|medium|high>
scenarios_count: 2
decision_nodes: <수치>
api_integrations: <수치>
subagents:
  requirements_analyst: <run_id|hash>
  dependency_scout: <run_id|hash>
  solution_architect: <run_id|hash>
  risk_feasibility_auditor: <run_id|hash>
dependencies:
  api_keys_count: <N>
  saas_signups_count: <N>
  mcp_tools_count: <N>
  internal_access_count: <N>
risk_score:
  scenario_a:
    data_safety: 1-5
    integration: 1-5
    change_mgmt: 1-5
    roi_measurement: 1-5
    governance: 1-5
  scenario_b:
    data_safety: 1-5
    integration: 1-5
    change_mgmt: 1-5
    roi_measurement: 1-5
    governance: 1-5
---
```

> Contract 외 키 금지. 12 키 누락 시 grep 자가검증 실패 = 하네스 실패.

---

## §5 불변식 (11개, v2)

1. **시나리오 A·B 둘 다 산출** — 한쪽만 가능하면 그 이유 명시 후 다른 쪽 stub
2. **§3·§4 각각 4·5 하위 섹션 완비** — 누락 시 실패
3. **§2 하위 7섹션 완비** (2-A~2-G)
4. **사내 접근 권한 메일 템플릿 1개+** — 복붙 가능한 한국어 비즈니스 톤
5. **§4 복붙 프롬프트 200자+** — 그대로 Claude Code에 붙여 작동해야
6. **ASCII 다이어그램** — 시나리오 A·B 각각, 박스 문자(┌·└·─) 사용
7. **§9 BCG 5축** — 시나리오 A·B 각각 점수 (10 셀)
8. **한국 환경 함정 1개+** 명시
9. **v2 핵심 제약**: 내부 자산(`/korea-*`·`poc/data/`·`bootstrap/`) 인용 시 즉시 실패
10. **grep 자가검증 전 보고 금지**
11. **4 subagent 증적**: frontmatter `subagents` 4개 모두 run_id

---

## §6 사용 예시

```bash
/agent-solution-consultant 회의 노트와 발표자료를 취합해서 프로젝트 실행 기획서를 자동으로 짜주는 에이전트

# 자연어 자동 트리거
"외근 중 이메일 정리해서 회신 초안 만드는 에이전트 어떻게 만들지?"
→ SKILL.md 트리거 → 본 커맨드 호출
```

---

## §7 외부 자산 합성 (출처 추적)

| 외부 자산 | 본 하네스 v2 반영 위치 |
|----------|---------------------|
| BMAD Method (Analyst→Architect 파이프라인) | §2 4-subagent 토폴로지 |
| wshobson/agents (Tier 모델 라우팅) | §2 Opus/Sonnet 라우팅 |
| Anthropic MCP 생태계 | §2 dependency-scout MCP 카탈로그 |
| BCG AI Risk Management | §9 차등 점검 (sensitivity별) |
| **aiceo-4th-agent 리포** | **시나리오 B 베이스 (수강생 실습 환경)** |

---

## §8 v1 → v2 변경 사항

| 항목 | v1 | v2 |
|------|----|----|
| 산출물 섹션 | 10개 (§0·§1·§2·§3·§4·§5·§6·§7·§8·§9·§10) | **6개** (§0·§1·§2·§3·§4·§9) |
| 해결안 분류 | 안0·안1·안2·안3 (4안) | **시나리오 A·B** (2-시나리오) |
| 내부 자산 매핑 | §10 벤치마크 매핑 | **폐기** (수강생이 0에서 만드는 실습) |
| Subagent 2번 | pattern-matcher | **dependency-scout** (외부 의존성·사전 준비물) |
| §5·§6·§7·§8·§10 | 카탈로그·Plan A/B/C·매트릭스·추천·즉시 실행 프롬프트·벤치마크 | **§3·§4에 흡수** |
| §3·§4 (안별 다이어그램·병목·Plan) | 4안 × 4블록 | **시나리오 A·B 각각 4·5 하위 섹션** |
| §2 사전 준비물 | 없음 | **신규 — API 키·SaaS·MCP·사내 접근·기타·preflight** |
| §4 복붙 프롬프트 | 없음 | **신규 — aiceo-4th-agent 기반 200줄+** |

---

## 끝.
