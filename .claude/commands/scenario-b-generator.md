---
description: 수강생 케이스 1개를 받아 시나리오 B(aiceo-4th-agent 메뉴 추가, 고정 파이프라인) 구현 가이드 10섹션 마크다운 1장을 산출. Next.js 16 + LangChain ChatAnthropic/ChatOpenAI 직접 invoke 패턴. deepagents·자율형 SDK 사용 금지.
argument-hint: <케이스 자연어 설명 또는 구조화 입력>
allowed-tools: Task, Read, Write, Bash, Grep, Glob, AskUserQuestion
---

# /scenario-b-generator (별칭 /scenario-b)

## §0 정체성

### 무엇

수강생 케이스 1개 → **시나리오 B 구현 가이드 1장**.

산출물: `./specs/scenario-b/<slug>/<today>/00_scenario_b.md`

### 두 층위 구분 (불변)

- **메타 하네스 (이 command)** = 정교: 분업 subagent 3종, HITL, 검증 풍부
- **수강생용 가이드 (산출물)** = 심플: aiceo-4th-agent 메뉴 1개를 4~7파일로 추가

### 산출물 10섹션 골격 (불변)

```
§1 케이스 한 줄 정의
§2 파이프라인 다이어그램
§3 생성할 파일 목록 (aiceo-4th-agent 경로)
§4 각 파일의 골격
§5 수강생 사용 가이드
  §5-A 복붙 프롬프트
  §5-B 메뉴 트리거 + 배포 방법
§6 외부 연결 의존성 (Easy Path + 인벤토리 + 옵션 A/B/C + 권한 요청 + 신호등)
§7 한계와 우회
§8 다음 단계 (A 다운그레이드 / C 업그레이드)
§9 LLM 호출 비용·성능 추정
§10 시나리오 A 대비 B의 비용·가치 (ROI)
```

### 심플 제약 (불변)

| 항목 | 상한 |
|------|------|
| 메뉴당 파일 개수 | 4~7개 |
| LLM 호출 단계 | 2~5개 (자율 분기 금지) |
| HITL | 최대 2회 |
| deepagents·LangGraph 그래프 사용 | **절대 금지** (C와 구분) |
| API 키 NEXT_PUBLIC_ 노출 | **절대 금지** |
| 산출 언어 | 한국어 (코드·식별자만 영어) |

---

## §1 Step 0 — 케이스 명세 정규화

### 1-1. $ARGUMENTS 평가

```
비어 있음 / 5단어 이하:        → 1-2. Full Discovery (3회 캐스케이드)
케이스 한 줄 명시:              → 1-3. Mini Discovery
구조화 입력:                    → 1-4. 바로 진입
시나리오 A 산출물 경로 지정:    → 1-5. A 산출물 베이스 모드 (B로 승격)
```

### 1-2. Full Discovery (3회)

**Q1 — 케이스 한 줄 설명**
- 일일 매출 보고서 (사내 DB + 환율 API)
- 경쟁사 페이지 정기 모니터링
- GEO 콘텐츠 자동 발행
- 직접 입력

**Q2 — 입력·출력 형식**
- 사용자 입력(폼) → 결과 화면
- 스케줄 트리거 → DB 저장 + 알림
- API 호출 → JSON 응답
- 기타

**Q3 — B를 선택한 이유 (분기 결정)**
- 팀 공유·다중 사용자
- 자동 게시·스케줄
- 이력 관리·diff
- 외부 API 통합 (OAuth·과금)
- 위 중 2개 이상

### 1-3. Mini Discovery
케이스 충분, 입력·출력만 확인.

### 1-4. 구조화 입력 형식

```yaml
case_name: <slug>
case_description: <2~3줄>
input_format: <폼 / 스케줄 / API / 파일 업로드 / 혼합>
output_format: <화면 표시 / DB 저장 / 외부 게시 / 파일 다운로드>
b_choice_reason: <팀공유 / 자동게시 / 이력관리 / API통합 / 복합>
external_deps_hint: <DB / SaaS API / 외부 공개 API / 사내 시스템>
linked_scenario_a: <A 산출물 경로 (있으면)>
```

### 1-5. A 산출물 베이스 모드

`$ARGUMENTS`가 `./specs/scenario-a/<slug>/...` 경로면:
- A 산출물 Read → case_description·input·output·external_deps 자동 추출
- frontmatter에 `linked_scenario_a` 자동 채움
- §10 ROI 섹션에서 A 대비 직접 비교 가능

### 1-6. 사용자 컨펌

```
명세:
- 케이스: <case_name>
- B 선택 이유: <b_choice_reason>
- 입력→출력: <input> → <output>
- 외부 의존: <hint>
- A 산출물 연동: <linked_scenario_a 또는 없음>

산출 경로: ./specs/scenario-b/<slug>/<today>/00_scenario_b.md
진행할까요? (y/n)
```

---

## §2 Step 1 — 분업 추출 (subagent 3종 병렬)

### 2-1. 호출 토폴로지

```
오케스트레이터 (이 command)
    │
    ├──▶ Task(b-structurer)
    │     §2 파이프라인 + §3 파일 목록 + §4 골격
    │
    ├──▶ Task(b-applier)
    │     §5 복붙·트리거 + §6 외부 의존성 + §7 한계 + §8 A·C 트리거
    │
    └──▶ Task(b-cost-estimator)
          §9 LLM 비용·성능 + §10 A 대비 ROI
```

**병렬 호출 필수** — 단일 메시지 안에서 3건 동시.

### 2-2. Subagent prompt 골격

**b-structurer**:
```text
Task(subagent_type="b-structurer", prompt="""
스펙: .claude/agents/b-structurer.md 정독.
yaml 3섹션(pipeline_diagram · file_list · file_skeletons) 압축 텍스트로 반환.
파일 쓰지 말 것.

--- aiceo-4th-agent 컨텍스트 ---
스택: Next.js 16 App Router + React 19 + TS + LangChain
경로 패턴:
- src/app/(main)/<slug>/page.tsx (UI)
- src/app/api/<slug>/route.ts (API)
- src/components/<slug>/<C>.tsx
- src/lib/<slug>/<helper>.ts
- src/app/(main)/AgentNav.tsx 등록 필수
LLM 호출: ChatAnthropic / ChatOpenAI 직접 invoke (deepagents 금지)

--- 케이스 명세 ---
<case_name, case_description, input_format, output_format, external_deps_hint>

심플 제약:
- 메뉴당 파일 4~7개
- LLM 호출 단계 2~5개 (직렬 또는 fan-out/in, 자율 분기 금지)
- 한국어 산출
""")
```

**b-applier**:
```text
Task(subagent_type="b-applier", prompt="""
스펙: .claude/agents/b-applier.md 정독.
yaml 5섹션(copy_paste_prompt · menu_trigger_deploy · external_dependencies · limits_workarounds · next_steps_ac) 압축 텍스트로 반환.
파일 쓰지 말 것.

--- 케이스 명세 ---
<동일>

산출 규칙:
- copy_paste_prompt: 30~40줄 (B는 A보다 길어도 OK), aiceo-4th-agent 메뉴 추가 명령
- menu_trigger_deploy: §5-B 4서브섹션 (메뉴 URL 접근 / API 직접 호출 / 스케줄러 / 배포 절차)
- external_dependencies: §6 4서브섹션 (Easy Path / 인벤토리 / 옵션 A/B/C / 권한 요청 / 신호등)
- limits_workarounds: B 특화 한계 (deepagents 안 써서 못하는 것: 자율 판단·분기 폭증 → C 트리거)
- next_steps_ac: A로 다운그레이드 / C로 업그레이드 양방향 트리거
""")
```

**b-cost-estimator**:
```text
Task(subagent_type="b-cost-estimator", prompt="""
스펙: .claude/agents/b-cost-estimator.md 정독.
yaml 2섹션(llm_cost_estimate · roi_vs_scenario_a) 압축 텍스트로 반환.
파일 쓰지 말 것.

--- 케이스 명세 + structurer 산출 (LLM 호출 패턴) ---
<...>

산출 규칙:
- llm_cost_estimate: 단계별 호출 횟수 × 평균 토큰 × 모델별 단가 = 1회 실행 비용 + 월간 추정
  - 모델: Claude Sonnet 4.6 입력 $3/1M·출력 $15/1M, OpenAI gpt-4o-mini 입력 $0.15/1M·출력 $0.60/1M (2026-05 기준)
  - 호출 지연 추정 (p50, p95)
- roi_vs_scenario_a: A로 못하는 가치 + B로 추가 비용 vs C로 가는 임계점
""")
```

### 2-3. Subagent 산출 검증

```bash
echo "$STRUCTURER_OUT" | grep -qE "pipeline_diagram:|file_list:|file_skeletons:" || RECALL_S=true
echo "$APPLIER_OUT"    | grep -qE "copy_paste_prompt:|menu_trigger_deploy:|external_dependencies:" || RECALL_A=true
echo "$COST_OUT"       | grep -qE "llm_cost_estimate:|roi_vs_scenario_a:" || RECALL_C=true
```

검증 실패 시 1회 재호출. 재호출 후 실패면 부분 합성.

---

## §3 Step 2 — 10섹션 합성

### 3-1. 합성 규칙

| 섹션 | 소스 |
|------|------|
| §1 케이스 한 줄 정의 | Step 0 명세 정리 |
| §2 파이프라인 다이어그램 | structurer.pipeline_diagram |
| §3 파일 목록 | structurer.file_list |
| §4 파일 골격 | structurer.file_skeletons |
| §5-A 복붙 프롬프트 | applier.copy_paste_prompt |
| §5-B 메뉴 트리거·배포 | applier.menu_trigger_deploy |
| §6 외부 연결 의존성 | applier.external_dependencies |
| §7 한계·우회 | applier.limits_workarounds |
| §8 A·C 트리거 | applier.next_steps_ac |
| §9 LLM 비용·성능 | cost-estimator.llm_cost_estimate |
| §10 A 대비 ROI | cost-estimator.roi_vs_scenario_a |

### 3-2. 산출물 frontmatter (Contract 8키)

```yaml
---
harness: scenario-b-generator
case: <case_name 자연어>
slug: <kebab-case>
b_choice_reason: <팀공유 | 자동게시 | 이력관리 | API통합 | 복합>
run_at: <ISO8601 KST>
run_id: <epoch>
linked_scenario_a: <경로 또는 null>
subagents:
  b_structurer: <ok | recalled | partial>
  b_applier: <ok | recalled | partial>
  b_cost_estimator: <ok | recalled | partial>
---
```

---

## §4 Step 3 — Write + grep 자가검증

### 4-1. 경로 결정

```bash
slug=<case_name kebab-case>
today=$(date +%Y-%m-%d)
base="./specs/scenario-b/$slug/$today"
mkdir -p "$base"

if [ -f "$base/00_scenario_b.md" ]; then
  out="$base/00_scenario_b_<run_id>.md"
else
  out="$base/00_scenario_b.md"
fi
Write "$out"
```

### 4-2. grep 자가검증 (확장)

```bash
F="$out"
FAIL=0

# (1) 10개 § 헤딩
for SEC in "§1 케이스 한 줄 정의" "§2 파이프라인 다이어그램" "§3 생성할 파일 목록" "§4 각 파일의 골격" "§5 수강생 사용 가이드" "§6 외부 연결 의존성" "§7 한계와 우회" "§8 다음 단계" "§9 LLM 호출 비용" "§10 시나리오 A 대비"; do
  grep -qE "^## $SEC" "$F" || { echo "FAIL: 헤딩 $SEC"; FAIL=$((FAIL+1)); }
done

# (2) §5-A / §5-B 분할
for SUB in "5-A" "5-B"; do
  grep -qE "^### §$SUB\." "$F" || { echo "FAIL: §$SUB 분할 누락"; FAIL=$((FAIL+1)); }
done

# (3) §6 4서브섹션
for SUB in "6-0" "6-1" "6-2" "6-3" "6-4"; do
  grep -qE "^### $SUB\." "$F" || { echo "FAIL: §6 서브섹션 누락 $SUB"; FAIL=$((FAIL+1)); }
done

# (4) frontmatter 8키
for K in harness case slug b_choice_reason run_at run_id linked_scenario_a subagents; do
  grep -qE "^$K:" "$F" || { echo "FAIL: fm $K"; FAIL=$((FAIL+1)); }
done

# (5) Easy Path 신호등
grep -qE "(🟢|해당 없음)" "$F" || { echo "FAIL: 신호등"; FAIL=$((FAIL+1)); }

# (6) 파이프라인 다이어그램 ASCII 박스
grep -qE "[┌└├│▼─]" "$F" || { echo "FAIL: ASCII"; FAIL=$((FAIL+1)); }

# (7) §9 비용 — 모델명·달러 또는 토큰 단위 등장
grep -qE "(Sonnet|gpt-|Claude|토큰|tokens|\\\$[0-9])" "$F" || { echo "FAIL: §9 비용 단위 누락"; FAIL=$((FAIL+1)); }

# (8) §10 ROI — "A 대비" 또는 "vs A" 등장
grep -qE "(A 대비|vs A|시나리오 A)" "$F" || { echo "FAIL: §10 A 비교 누락"; FAIL=$((FAIL+1)); }

# (9) B 안전 — deepagents·createDeepAgent **코드로 사용** 금지 (있으면 fail)
# 안내문("deepagents 쓰지 마")은 OK. 실제 import·호출 코드만 금지.
grep -qE "(import.*deepagents|createDeepAgent\()" "$F" && { echo "FAIL: B에서 deepagents 코드 사용 위반"; FAIL=$((FAIL+1)); }

# (10) NEXT_PUBLIC_ + API_KEY 동시 등장 시 fail (보안)
if grep -qE "NEXT_PUBLIC_.*API_KEY" "$F"; then
  echo "FAIL: API 키 NEXT_PUBLIC_ 노출 위반"; FAIL=$((FAIL+1))
fi

# (11) aiceo-4th-agent 경로 패턴 등장
grep -qE "src/app/\(main\)/" "$F" || { echo "FAIL: aiceo-4th-agent 경로 누락"; FAIL=$((FAIL+1)); }

# (12) AgentNav 등록 안내
grep -qE "AgentNav" "$F" || { echo "FAIL: AgentNav 등록 누락"; FAIL=$((FAIL+1)); }

# (13) v1.1 — §3 파일 목록 카운트 상한 7개 (메뉴 등록 제외)
FILE_COUNT=$(awk '/^## §3 생성할 파일 목록/{flag=1; next} /^## §4/{flag=0} flag' "$F" | grep -cE "^\| \`src/")
[ "$FILE_COUNT" -le 7 ] || { echo "FAIL: §3 파일 $FILE_COUNT개 > 상한 7개"; FAIL=$((FAIL+1)); }

# (14) v1.1 — R6 globalThis 싱글톤 패턴 — DB Pool/Database 사용 시 강제
if grep -qE "new (Pool|Database)\(" "$F"; then
  grep -q "globalThis" "$F" || { echo "FAIL: R6 globalThis 싱글톤 패턴 누락 (Pool/Database 사용 시)"; FAIL=$((FAIL+1)); }
fi

# (15) v1.1 — JSON.parse(await invoke...) 직접 호출 금지 (zod 검증 필요)
grep -qE "JSON\.parse\(await invoke" "$F" && { echo "FAIL: LLM 반환을 JSON.parse 직접 호출 (zod safeParse 강제)"; FAIL=$((FAIL+1)); }

# (16) v1.1 — 추가 패키지 사용 시 pnpm add 명시
if grep -qE "from \"(pg|cheerio|mysql2|mongodb)\"" "$F"; then
  grep -qE "pnpm add (pg|cheerio|mysql2|mongodb)" "$F" || { echo "FAIL: 추가 패키지 사용 시 pnpm add 명령 누락"; FAIL=$((FAIL+1)); }
fi

# (17) v1.1 — §5-B 모델 ID 최신 확인 안내 (학습 지식 단정 금지)
grep -qE "(최신 단가|최신 모델|npm view|docs.anthropic|anthropic.com/pricing|anthropic.com/en/docs/about-claude/models)" "$F" || { echo "FAIL: §5-B 모델·API 최신 확인 안내 누락"; FAIL=$((FAIL+1)); }

[ "$FAIL" -eq 0 ] && echo "✅ ALL PASS" || echo "❌ FAIL=$FAIL"
```

자가검증 통과 전 보고 금지.

---

## §5 Step 4 — 보고

```
✅ 시나리오 B 가이드 생성: <out>
   - 케이스: <case_name>
   - B 선택 이유: <b_choice_reason>
   - 파일 N개 (UI M·API K·helper L)
   - LLM 호출 단계: D
   - 1회 실행 추정 비용: $X.YY
   - A 산출물 연동: <yes/no>
   - subagent 호출: structurer ✓, applier ✓, cost-estimator ✓
   - grep 자가검증 (12 체크) 통과 ✓
```

---

## §6 불변식 (10개)

1. **두 층위 분리** — 메타 정교 / 산출물 심플
2. **10섹션 골격** — §1~§10 모두 산출
3. **§5-A/§5-B 분할** — 만들기·쓰기 가이드 페어
4. **§6 4서브섹션** — Easy Path + 인벤토리 + 옵션 A/B/C + 권한 요청 + 신호등
5. **§9·§10 강제** — B의 차별가치(비용·ROI), 누락 시 자가검증 실패
6. **deepagents·createDeepAgent 사용 금지** — C와 명확히 구분
7. **API 키 NEXT_PUBLIC_ 노출 금지** — aiceo-4th-agent 보안 규칙
8. **분업 subagent 3종 병렬** — 단일 메시지 동시 호출
9. **합성은 command 직접** — 별도 합성 subagent 없음
10. **grep 자가검증 12 체크 통과 전 보고 금지**

---

## §7 사용 예시

```bash
# 인자 없이 → Full Discovery
/scenario-b

# 한 줄
/scenario-b 일일 매출 보고서 메뉴, 사내 DB + 환율 API

# A 산출물 베이스
/scenario-b ./specs/scenario-a/daily-sales-report/2026-05-24/00_scenario_a.md

# 자연어 트리거
"이 일일 매출 보고서 케이스 aiceo-4th-agent 메뉴로 만들면 어떻게?"
```

---

## 끝.
