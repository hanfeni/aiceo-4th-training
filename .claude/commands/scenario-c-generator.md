---
description: 수강생 케이스 1개를 받아 시나리오 C(aiceo-4th-agent에 자율형 에이전트 추가, deepagents 기반) 구현 가이드 10섹션 마크다운 1장을 산출. `createDeepAgent` + 도구/서브에이전트 등록 패턴. B와 달리 자율 도구 선택·멀티턴·계획 변경 가능.
argument-hint: <케이스 자연어 설명 또는 구조화 입력>
allowed-tools: Task, Read, Write, Bash, Grep, Glob, AskUserQuestion
---

# /scenario-c-generator (별칭 /scenario-c)

## §0 정체성

### 무엇

수강생 케이스 1개 → **시나리오 C 구현 가이드 1장**.

산출물: `./specs/scenario-c/<slug>/<today>/00_scenario_c.md`

### 두 층위

- 메타 정교 (분업 3종) / 산출물 심플 (도구·서브에이전트 4~7개 추가)

### 산출물 10섹션

```
§1 케이스 한 줄 정의 + C 정당화
§2 에이전트 토폴로지 (도구·서브에이전트·체크포인터·플래닝)
§3 생성·확장할 파일 목록
§4 각 파일의 골격
§5 수강생 사용 가이드 (§5-A 복붙 + §5-B 트리거·배포·멀티턴)
§6 외부 연결 의존성
§7 한계와 우회 (C 특화)
§8 다음 단계 (B 다운그레이드 / 멀티 에이전트 업그레이드)
§9 자율형 LLM 호출 비용·성능 추정 (분포·최악 케이스)
§10 시나리오 B 대비 C의 ROI (B로 충분한지 재평가 강제)
```

### 심플 제약 (불변)

| 항목 | 상한 |
|------|------|
| 추가 파일 (tools·subagents·meta) | 4~7개 |
| 자율 도구 수 | 3~6개 (10개+ → 멀티 에이전트) |
| HITL | 0~2회 (메인 흐름은 자율) |
| **`createDeepAgent` 사용 강제** | 필수 (B와 반대) |
| `@langchain/langgraph` 직접 import | 금지 (R1 - pnpm strict 차단) |
| `NEXT_PUBLIC_` 노출 | 금지 |
| **B 정당화 §10에 임계점 체크 강제** | 필수 |

---

## §1 Step 0 — 명세 정규화 + C 정당화

### 1-1. $ARGUMENTS 평가

```
비어 있음:                          → Full Discovery
케이스 설명만:                      → Mini Discovery (C 정당화만)
구조화 입력:                        → 1-4 바로 진입
시나리오 B 산출물 경로:             → 1-5. B → C 승격 모드
```

### 1-2. Full Discovery

**Q1 — 케이스 한 줄**

**Q2 — C 정당화 (반드시 1개 이상)**
- 분기 10+ 케이스 — 고정 파이프로 커버 불가
- 도구·DB·검색엔진 자율 선택 필요
- 멀티턴 대화 + 계획 동적 변경
- 자율 탐색·리서치 (사람이 미리 정의한 단계 외)
- 자기 응답 reflection·재계획

**Q3 — 멀티 에이전트 필요?**
- 단일 에이전트 + 도구 4~6개 (Recommended)
- 메인 + 서브에이전트 1~2개
- 멀티 에이전트 (이건 시나리오 D — 본 가이드 범위 외)

### 1-3. Mini Discovery
케이스 명세 있음. C 정당화만 확인 (Q2).

### 1-4. 구조화 입력

```yaml
case_name: <slug>
case_description: <2~3줄>
c_justification: <Q2 답변 1개 이상>
input_format: <자연어 질의 / 사용자 명령 / 외부 트리거>
output_format: <대화 응답 / 자율 리서치 보고서 / 액션 시퀀스>
tools_hint: <필요 도구 후보 — DB·WebSearch·외부 API 등 3~6개>
subagent_hint: <서브에이전트 필요? (있으면 역할)>
external_deps_hint: <DB / SaaS / 외부 API>
linked_scenario_b: <B 산출물 경로 — 있으면 ROI 비교용>
```

### 1-5. B → C 승격 모드

`$ARGUMENTS`가 `./specs/scenario-b/<slug>/...`이면:
- B 산출물 Read → 기존 파이프라인·외부 의존성 자동 추출
- §10 ROI 섹션에서 "B로 충분한지" 직접 재검토
- frontmatter `linked_scenario_b` 자동 채움

### 1-6. 사용자 컨펌

```
명세:
- 케이스: <case_name>
- C 정당화: <c_justification>
- 도구 후보: <tools_hint>
- 서브에이전트: <subagent_hint>
- B 산출물 연동: <linked_scenario_b 또는 없음>

⚠️ C는 B 대비 비용 1.5~5배, 비결정성·환각 리스크 높음. B로 충분한지 §10에서 재평가 필수.

산출 경로: ./specs/scenario-c/<slug>/<today>/00_scenario_c.md
진행할까요? (y/n)
```

---

## §2 Step 1 — 분업 추출 (subagent 3종 병렬)

### 2-1. 호출

```
오케스트레이터
    │
    ├──▶ Task(c-structurer)
    │     §2 토폴로지 + §3 파일 목록 + §4 골격
    │
    ├──▶ Task(c-applier)
    │     §5 복붙·트리거 + §6 외부 의존성 + §7 한계 + §8 B/A 트리거
    │
    └──▶ Task(c-cost-estimator)
          §9 자율형 비용 분포 + §10 B 대비 ROI (B로 충분 재평가)
```

**병렬 호출 필수** — 단일 메시지.

### 2-2. Subagent prompt 골격

**c-structurer**:
```text
Task(subagent_type="c-structurer", prompt="""
스펙: .claude/agents/c-structurer.md 정독.
yaml 3섹션(agent_topology · file_list · file_skeletons) 압축 텍스트 반환.

--- aiceo-4th-agent C 컨텍스트 ---
- createDeepAgent({ tools, subagents, instructions, checkpointer, model })
- 도구 등록: src/lib/agent/harness/tools/<>.ts + index.ts HARNESS_TOOLS 배열
- 서브에이전트: src/lib/agent/harness/subagents/<>.ts + index.ts
- registry.ts에서 토글 (R2)
- @langchain/langgraph 직접 import 금지 (R1, pnpm strict)
- globalThis 그래프 싱글톤 (R6)
- checkpointer SQLite + thread_id (R3, 멀티턴)

--- 케이스 명세 ---
<case_name, case_description, c_justification, tools_hint, subagent_hint>

심플 제약:
- 추가 파일 4~7개 (tools·subagents·meta·registry 1줄)
- 자율 도구 3~6개
- 한국어 산출
""")
```

**c-applier**:
```text
Task(subagent_type="c-applier", prompt="""
스펙: .claude/agents/c-applier.md 정독.
yaml 5섹션(copy_paste_prompt · trigger_deploy_multiturn · external_dependencies · limits_workarounds · next_steps_ba) 압축 텍스트 반환.

산출 규칙:
- copy_paste_prompt: 30~40줄, "createDeepAgent 사용", "@langchain/langgraph 직접 import 금지" 명시
- trigger_deploy_multiturn: §5-B 4서브섹션 (UI 챗 / API 호출 / 멀티턴 thread_id / 배포)
- external_dependencies: 4서브섹션 (Easy Path는 도구별로 별도 평가)
- limits_workarounds: C 특화 — 비결정성·환각·테스트 어려움·비용 통제·도구 무한 루프
- next_steps_ba: B 다운그레이드 (분기 5개 이하·고정 파이프 가능 시) / 멀티 에이전트로 (도구 10+ · 협업 필요)
""")
```

**c-cost-estimator**:
```text
Task(subagent_type="c-cost-estimator", prompt="""
스펙: .claude/agents/c-cost-estimator.md 정독.
yaml 2섹션(llm_cost_estimate · roi_vs_scenario_b) 압축 텍스트 반환.

산출 규칙:
- llm_cost_estimate: 자율형 비용은 분포 (p50/p90/p99) — 자율 분기 횟수·도구 호출 횟수 가변
- roi_vs_scenario_b: **B로 충분한지 임계점 재평가 강제** — 4개 임계점 중 1개라도 해당 안 하면 B 권장
""")
```

### 2-3. 산출 검증

```bash
echo "$STRUCTURER_OUT" | grep -qE "agent_topology:|file_list:|file_skeletons:" || RECALL_S=true
echo "$APPLIER_OUT"    | grep -qE "copy_paste_prompt:|trigger_deploy_multiturn:|external_dependencies:" || RECALL_A=true
echo "$COST_OUT"       | grep -qE "llm_cost_estimate:|roi_vs_scenario_b:" || RECALL_C=true
```

---

## §3 Step 2 — 합성

### 3-1. 섹션 매핑

| 섹션 | 소스 |
|------|------|
| §1 케이스 + 정당화 | Step 0 명세 |
| §2 토폴로지 | structurer.agent_topology |
| §3 파일 목록 | structurer.file_list |
| §4 골격 | structurer.file_skeletons |
| §5-A 복붙 | applier.copy_paste_prompt |
| §5-B 트리거·멀티턴 | applier.trigger_deploy_multiturn |
| §6 외부 의존성 | applier.external_dependencies |
| §7 한계 | applier.limits_workarounds |
| §8 B/멀티 트리거 | applier.next_steps_ba |
| §9 비용 분포 | cost-estimator.llm_cost_estimate |
| §10 B 대비 ROI | cost-estimator.roi_vs_scenario_b |

### 3-2. frontmatter (Contract 9키)

```yaml
---
harness: scenario-c-generator
case: <자연어>
slug: <kebab-case>
c_justification: <임계점 1개 이상>
run_at: <ISO8601 KST>
run_id: <epoch>
linked_scenario_b: <경로 또는 null>
agent_pattern: <single | main+sub | multi-agent-out-of-scope>
subagents:
  c_structurer: <ok|recalled|partial>
  c_applier: <ok|recalled|partial>
  c_cost_estimator: <ok|recalled|partial>
---
```

---

## §4 Step 3 — Write + grep 자가검증

### 4-1. 경로

```bash
slug=<kebab>
today=$(date +%Y-%m-%d)
base="./specs/scenario-c/$slug/$today"
mkdir -p "$base"
[ -f "$base/00_scenario_c.md" ] && out="$base/00_scenario_c_<run_id>.md" || out="$base/00_scenario_c.md"
Write "$out"
```

### 4-2. grep 자가검증 (18 체크)

```bash
F="$out"
FAIL=0

# (1) 10개 § 헤딩
for SEC in "§1 케이스" "§2 에이전트 토폴로지" "§3 생성" "§4 각 파일" "§5 수강생" "§6 외부 연결" "§7 한계" "§8 다음 단계" "§9 자율형" "§10 시나리오 B"; do
  grep -qE "^## $SEC" "$F" || { echo "FAIL: 헤딩 $SEC"; FAIL=$((FAIL+1)); }
done

# (2) §5-A/§5-B 분할
for SUB in "5-A" "5-B"; do
  grep -qE "^### §$SUB\." "$F" || { echo "FAIL: §$SUB 분할"; FAIL=$((FAIL+1)); }
done

# (3) §5-B 4서브 + §6 5서브
for SUB in "5B-0" "5B-1" "5B-2" "5B-3"; do
  grep -qE "^#### $SUB\." "$F" || { echo "FAIL: §5-B-$SUB"; FAIL=$((FAIL+1)); }
done
for SUB in "6-0" "6-1" "6-2" "6-3" "6-4"; do
  grep -qE "^### $SUB\." "$F" || { echo "FAIL: §6-$SUB"; FAIL=$((FAIL+1)); }
done

# (4) frontmatter 9키
for K in harness case slug c_justification run_at run_id linked_scenario_b agent_pattern subagents; do
  grep -qE "^$K:" "$F" || { echo "FAIL: fm $K"; FAIL=$((FAIL+1)); }
done

# (5) Easy Path 신호등
grep -qE "(🟢|해당 없음)" "$F" || { echo "FAIL: 신호등"; FAIL=$((FAIL+1)); }

# (6) ASCII 박스
grep -qE "[┌└├│▼─]" "$F" || { echo "FAIL: ASCII"; FAIL=$((FAIL+1)); }

# (7) §9 비용 — 모델·토큰·$ + 분포(p50/p90 또는 평균/최악) 명시
grep -qE "(Sonnet|gpt-|Claude|토큰|\\\$[0-9])" "$F" || { echo "FAIL: §9 비용 단위"; FAIL=$((FAIL+1)); }
grep -qE "(p50|p90|p95|p99|평균|최악|분포|범위)" "$F" || { echo "FAIL: §9 분포 표기 누락"; FAIL=$((FAIL+1)); }

# (8) §10 B 대비
grep -qE "(B 대비|vs B|시나리오 B|B로 충분|B로 가능)" "$F" || { echo "FAIL: §10 B 비교"; FAIL=$((FAIL+1)); }

# (9) C 핵심 — createDeepAgent 코드 사용 (B와 반대 강제)
grep -qE "createDeepAgent\(" "$F" || { echo "FAIL: createDeepAgent 코드 누락 (C 필수)"; FAIL=$((FAIL+1)); }

# (10) @langchain/langgraph 직접 import 금지 (R1)
grep -qE "import.*@langchain/langgraph[^-]" "$F" && { echo "FAIL: @langchain/langgraph 직접 import (R1 위반)"; FAIL=$((FAIL+1)); }

# (11) NEXT_PUBLIC 금지
grep -qE "NEXT_PUBLIC_.*API_KEY" "$F" && { echo "FAIL: NEXT_PUBLIC 노출"; FAIL=$((FAIL+1)); }

# (12) aiceo-4th-agent 경로 패턴 — harness/tools 또는 harness/subagents 등장
grep -qE "harness/(tools|subagents)" "$F" || { echo "FAIL: aiceo-4th-agent harness 경로 누락"; FAIL=$((FAIL+1)); }

# (13) registry 등록 안내
grep -qE "(HARNESS_TOOLS|HARNESS_SUBAGENTS|registry)" "$F" || { echo "FAIL: registry 등록 누락"; FAIL=$((FAIL+1)); }

# (14) checkpointer 멀티턴 안내 (R3)
grep -qE "(checkpointer|thread_id)" "$F" || { echo "FAIL: checkpointer/thread_id 누락 (R3)"; FAIL=$((FAIL+1)); }

# (15) globalThis 싱글톤 (R6)
grep -q "globalThis" "$F" || { echo "FAIL: R6 globalThis 누락"; FAIL=$((FAIL+1)); }

# (16) §10 B로 충분 임계점 체크박스 강제
grep -qE "(\\[ \\] |\\[x\\] )" "$F" || { echo "FAIL: §10 임계점 체크박스 누락"; FAIL=$((FAIL+1)); }

# (17) C 특화 한계 — 비결정성·환각·테스트 어려움
grep -qE "(비결정|환각|hallucination|nondeterm)" "$F" || { echo "FAIL: §7 C 특화 한계(비결정·환각) 누락"; FAIL=$((FAIL+1)); }

# (18) 추가 패키지 — deepagents 자체는 이미 깔려 있으나, 새 패키지 import 시 pnpm add 안내
if grep -qE "from \"(pg|cheerio|mysql2|mongodb)\"" "$F"; then
  grep -qE "pnpm add (pg|cheerio|mysql2|mongodb)" "$F" || { echo "FAIL: 추가 패키지 사용 시 pnpm add 누락"; FAIL=$((FAIL+1)); }
fi

# (19) v1.1 — child_process·네이티브 모듈 사용 시 runtime="nodejs" 명시 강제
if grep -qE "(execFile|child_process|new Pool\(|new Database\()" "$F"; then
  grep -qE "runtime = \"nodejs\"" "$F" || { echo "FAIL: child_process·네이티브 사용 시 runtime=nodejs 명시 누락"; FAIL=$((FAIL+1)); }
fi

# (20) v1.1 — 서브에이전트 tools 필드 사용 시 버전별 실측 안내 강제
if grep -qE "(SubAgent|subagents:|tools: \[\".*\"\])" "$F"; then
  grep -qE "(버전.*실측|버전별 실측|deepagents 버전|.d.ts.*확인)" "$F" || { echo "FAIL: deepagents 버전 실측 안내 누락"; FAIL=$((FAIL+1)); }
fi

# (21) v1.1 — 0/4 임계점 미충족 시 §4 골격 앞에 ⚠️ B 권장 경고 강제
# §10에서 [ ]가 4개 모두면 anti-test → §4에 경고 필수
UNCHECKED_COUNT=$(awk '/^### 10-3/{flag=1; next} /^### 10-4/{flag=0} flag && /^- \[ \]/' "$F" | wc -l | tr -d ' ')
if [ "$UNCHECKED_COUNT" -ge 4 ]; then
  grep -qE "(⚠️|안티 테스트|B 권장|over-engineering)" "$F" || { echo "FAIL: 0/4 임계점인데 B 권장 경고 누락 (anti-test 케이스 의도된 약점 명시 필수)"; FAIL=$((FAIL+1)); }
fi

# (22) v1.1 — 한국 사용자 케이스 표시 시 한국 출처 우선 안내 검증 (case_description에 "사내·국내·매출·한국" 키워드)
if grep -qE "(사내|국내|매출|영업본부|마케팅팀|한국)" "$F"; then
  grep -qE "(네이버|다음|수출입은행|한국|국내)" "$F" || echo "WARN: 한국 케이스인데 한국 출처 명시 없음 (사소)"
fi

[ "$FAIL" -eq 0 ] && echo "✅ ALL PASS" || echo "❌ FAIL=$FAIL"
```

---

## §5 보고

```
✅ 시나리오 C 가이드 생성: <out>
   - 케이스: <case_name>
   - C 정당화: <c_justification>
   - 에이전트 패턴: <single | main+sub>
   - 추가 파일 N개 (tools M·subagents K·meta L·registry 1줄)
   - 자율 도구 수: D
   - 1회 실행 추정 비용: $X.YY (p50) / $Z.WW (p90)
   - B 산출물 연동: <yes/no>
   - subagent: structurer ✓ applier ✓ cost-estimator ✓
   - grep 자가검증 (18 체크) 통과 ✓
```

---

## §6 불변식 (12개)

1. 두 층위 분리
2. 10섹션 골격 + §5 분할 + §6 4서브
3. **§10 B 대비 ROI 임계점 체크박스 강제** — B로 충분한지 재평가
4. **`createDeepAgent` 코드 사용 강제** (B와 반대)
5. **`@langchain/langgraph` 직접 import 금지** (R1 - pnpm strict 차단)
6. **R3 checkpointer + thread_id** 멀티턴 안내 필수
7. **R6 globalThis 싱글톤** 안내 필수
8. `NEXT_PUBLIC_` API 키 노출 금지
9. aiceo-4th-agent harness 경로(`tools/`, `subagents/`) 사용
10. registry.ts 1줄 등록 안내
11. C 특화 한계(비결정·환각) §7 명시
12. grep 18 체크 통과 전 보고 금지

---

## §7 사용 예시

```bash
# 인자 없이
/scenario-c

# 한 줄
/scenario-c 매출 이상치 자율 분석 — DB·뉴스·경쟁사 자율 탐색

# B 승격 모드
/scenario-c ./specs/scenario-b/daily-sales-report/2026-05-24/00_scenario_b.md
```

---

## 끝.
