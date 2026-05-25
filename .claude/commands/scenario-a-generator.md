---
description: 수강생 케이스 1개를 받아 시나리오 A(Claude Code 하네스 단독) 구현 가이드 7섹션 마크다운 1장을 산출. 산출물은 심플 제약(파일 4개 이하·subagent 2종 이하·HITL 2회 이하)을 강제한다.
argument-hint: <케이스 자연어 설명 또는 구조화 입력>
allowed-tools: Task, Read, Write, Bash, Grep, Glob, AskUserQuestion
---

# /scenario-a-generator (별칭 /scenario-a)

## §0 정체성

### 무엇

수강생이 만들고 싶은 에이전트 케이스 1개 → **시나리오 A 구현 가이드 1장**.

산출물: `./specs/scenario-a/<slug>/<today>/00_scenario_a.md`

### 두 층위 구분 (불변)

- **메타 하네스 (이 command)** = 정교: 분업 subagent 2종, HITL, 검증 풍부
- **수강생용 하네스 (산출물 §2~§4 내용)** = 심플: 파일 2~4개, 분기 최소

### 산출물 8섹션 골격 (불변, §5는 §5-A/§5-B 분할)

```
§1 케이스 한 줄 정의
§2 하네스 토폴로지 (ASCII 다이어그램)
§3 생성할 파일 목록 (경로·책임·줄 수)
§4 각 파일의 골격 (SKILL/command/subagent 등)
§5 수강생 사용 가이드
  §5-A 코딩에이전트에 던질 복붙 프롬프트 (만들기 가이드)
  §5-B 트리거 환경 가이드 (쓰기 가이드 — 만든 후 어떻게 켜고 실행하나)
§6 외부 연결 의존성 (Easy Path + 인벤토리 + 옵션 A/B/C + 권한 요청 + 신호등)
§7 한계와 우회
§8 다음 단계 (B/C로 넘어갈 트리거)
```

**§6 신설 이유**: 수강생은 기술 이해도가 낮아 "내가 우리 회사 데이터에 접근할 수 있나?"가 가장 큰 장벽이다. SaaS 앱·사내 API·DB·파일시스템·인증/권한 등 모든 외부 연결 의존성에 대해 (a) 가장 쉬운 시작점 (Easy Path) (b) 풀 옵션 A/B/C (c) 권한 요청 문구 복붙용 템플릿 (d) 신호등 한눈 요약 4서브섹션을 강제 산출한다. 외부 의존이 0개여도 §6은 생략 불가 — "해당 없음" 명시 필수.

**§5-B 신설 이유**: 수강생이 하네스를 다 만든 뒤 "이걸 어떻게 켜는 거지?"에서 막힌다. 케이스 특성에 따라 (1) Claude Code 자연어 채팅 (2) 슬래시 커맨드 (3) `claude --print` CLI (4) launchd/cron 자동 실행 (5) macOS Folder Action·Mail Rule 외부 트리거 등 권장 트리거가 다르다. HITL 필수 케이스에 `--print`를 추천하면 안 되는 등 안전 규칙도 있다. 산출물 §5-B에서 권장 트리거 1개 + 옵션 매트릭스 + 자동화 가이드 + 사전 준비 체크리스트 4서브섹션을 강제한다.

### 심플 제약 (산출물에 강제 — 위반 시 자가검증 실패)

| 항목 | 난이도 하 | 난이도 중 | 난이도 상 |
|------|----------|----------|----------|
| 파일 개수 | 2개 (SKILL+command) | 3개 (+subagent 1종) | 4개 (+subagent or hook or MCP) |
| subagent 종 수 | 0 | 1 | 1~2 |
| HITL 게이트 | 0 | 1 | 1~2 |
| 외부 의존 | 0 | 1 | 2 |

위 표를 넘으면 산출물이 "수강생용 심플" 원칙을 어긴 것 — §7 자가검증에서 fail.

---

## §1 Step 0 — 케이스 명세 정규화

### 1-1. $ARGUMENTS 평가

```
비어 있음 / 5단어 이하:        → 1-2. Full Discovery (3회 캐스케이드)
케이스 한 줄 명시 (10~30단어): → 1-3. Mini Discovery (난이도만 확인)
구조화 입력 (4필드 모두):       → 1-4. 바로 진입
```

### 1-2. Full Discovery (3회 캐스케이드)

**Q1 — 케이스 한 줄 설명**
```
AskUserQuestion:
"어떤 에이전트를 만들고 싶으신가요? 한 줄로 알려주세요."
- 회의록 → Slack 포맷 변환기
- 경쟁사 페이지 비교 리포트
- 사내 위키 + 코드 교차 검색 답변기
- 직접 입력 (자유 텍스트)
```

**Q2 — 입력·출력 형식**
```
AskUserQuestion:
"이 에이전트의 입력·출력은?"
- 텍스트 in → 텍스트 out (가장 단순)
- 파일/URL in → 리포트 out
- 질문 in → 검색 결과 종합 out
- 기타 (자유 텍스트)
```

**Q3 — 난이도 추정**
```
AskUserQuestion:
"수강생 입장에서 난이도는?"
- 하 (단일 LLM 호출, 외부 의존 없음)
- 중 (병렬 분업, 외부 의존 1개)
- 상 (MCP·hook·분기 HITL 포함)
- 자동 추정 (제가 명세에서 판단)
```

### 1-3. Mini Discovery

명세는 충분, 난이도만 확인:
```
"이 케이스의 난이도를 정해주세요."
- 하 / 중 / 상 / 자동 추정
```

### 1-4. 자동 난이도 추정 규칙

명세 텍스트에서 다음 키워드 매칭:
- "병렬"·"여러 URL"·"분업"·"subagent" → 중 이상
- "MCP"·"Notion"·"외부 API"·"hook"·"트리거"·"분기" → 상
- "단일"·"하나"·"간단"·"요약"·"변환" → 하
- 매칭 없으면 → 중

### 1-5. 명세 정규화 산출

다음 4필드를 텍스트로 정리 (이후 subagent에 전달):
```yaml
case_name: <한 줄, kebab-case slug용>
case_description: <2~3줄, 무엇을 왜>
input_format: <텍스트 / 파일 / URL / 질문 / 혼합>
output_format: <마크다운 1장 / 리포트 / 응답 / 알림>
difficulty: <하 | 중 | 상>
external_deps_hint: <없음 | WebFetch | MCP명 | 기타>
```

### 1-6. 사용자 컨펌

```
명세 확인:
- 케이스: <case_name>
- 설명: <case_description>
- 난이도: <difficulty> (파일 N개, subagent M종 상한)
- 입력→출력: <input_format> → <output_format>

산출 경로: ./specs/scenario-a/<slug>/<today>/00_scenario_a.md
진행할까요? (y/n)
```

`n`이면 중단. `y`이면 §2 진입.

---

## §2 Step 1 — 분업 추출 (subagent 2종 병렬)

### 2-1. 호출 토폴로지

```
오케스트레이터 (이 command)
    │
    ├──▶ Task(subagent_type="scenario-a-structurer", ...)
    │     역할: §2 토폴로지 + §3 파일 목록 + §4 골격
    │
    └──▶ Task(subagent_type="scenario-a-applier", ...)
          역할: §5 복붙 프롬프트 + §6 한계·우회 + §7 다음 단계
```

**병렬 호출 필수** — 단일 메시지 안에서 동시 호출. 직렬 금지.

### 2-1-bis. 신규 등록 fallback (튜닝)

`scenario-a-structurer` / `scenario-a-applier` 두 subagent가 런타임에 아직 등록 안 됐을 수 있다 (새로 만든 직후). 그럴 때:

1. 우선 정상 이름으로 `Task(subagent_type="scenario-a-structurer", ...)` 시도.
2. "Agent type not found" 에러 반환되면 즉시 `general-purpose`로 fallback:
   ```
   Task(subagent_type="general-purpose", prompt="""
   너는 지금 scenario-a-structurer subagent 역할을 한다.
   먼저 이 파일을 정독해 너의 역할·제약·출력 규칙을 완전히 이해하라:
   .claude/agents/scenario-a-structurer.md

   그 후 아래 케이스에 대해 yaml 3섹션만 반환하라. 파일 쓰지 마라.
   --- 입력 케이스 명세 ---
   <명세>
   """)
   ```
3. applier도 동일하게 fallback.
4. fallback 사용 시 frontmatter `subagents:` 필드에 `recalled_via_general_purpose` 플래그 추가.

### 2-2. Subagent prompt 골격

**scenario-a-structurer**
```text
Task(subagent_type="scenario-a-structurer", prompt="""
스펙: .claude/agents/scenario-a-structurer.md 정독.
yaml 3섹션(topology_ascii · file_list · file_skeletons) 압축 텍스트로 반환.
파일 쓰지 말 것.

--- 입력 케이스 명세 ---
case_name: <slug>
case_description: <설명>
input_format: <...>
output_format: <...>
difficulty: <하|중|상>
external_deps_hint: <...>

심플 제약 강제:
- 파일 개수: 하 2개 / 중 3개 / 상 4개 (이하)
- subagent 종 수: 하 0 / 중 1 / 상 1~2
- 모든 산출 한국어, 코드·식별자는 영어
""")
```

**scenario-a-applier**
```text
Task(subagent_type="scenario-a-applier", prompt="""
스펙: .claude/agents/scenario-a-applier.md 정독.
yaml 3섹션(copy_paste_prompt · limits_workarounds · next_steps_bc) 압축 텍스트로 반환.
파일 쓰지 말 것.

--- 입력 케이스 명세 ---
(동일)

산출 규칙:
- §5 복붙 프롬프트는 30줄 이내, 수강생이 그대로 붙여넣어 작동
- §6 한계는 5~7개 (표 형식)
- §7 트리거는 3~5개 (B/C로 이주 시점)
- 한국어 산출
""")
```

### 2-3. Subagent 산출 검증 + 재호출

```bash
echo "$STRUCTURER_OUT" | grep -qE "topology_ascii:|file_list:|file_skeletons:" || RECALL_S=true
echo "$APPLIER_OUT"    | grep -qE "copy_paste_prompt:|limits_workarounds:|next_steps_bc:" || RECALL_A=true
```

검증 실패 시 1회만 재호출 (누락 키 명시). 재호출 후에도 실패면 오케스트레이터가 빠진 섹션 직접 작성.

---

## §3 Step 2 — 7섹션 합성 (command 직접)

### 3-1. 합성 규칙

오케스트레이터가 두 subagent yaml을 받아 7섹션 마크다운을 작성. 별도 합성 subagent 없음.

**충돌 시 정본 정책** (튜닝):
- subagent·파일 **이름**이 둘 사이에 다르면 → **structurer 산출이 정본**, applier 본문의 이름을 structurer 이름으로 일괄 치환.
- 같은 사실 다른 표현은 둘 다 살리되 중복 제거.
- 한 쪽만 누락한 항목은 그대로 채택.

**경로 정책 분리** (튜닝):
- **메타 산출 경로** (이 하네스의 출력): `./specs/scenario-a/<slug>/<today>/00_scenario_a.md`
- **수강생용 가이드 안의 권장 경로** (산출물 §4·§5 안에서 수강생에게 추천): 수강생 자유 선택 — `./specs/<harness>/<slug>/<date>/` 또는 `./docs/<harness>/` 중 케이스에 맞게. structurer/applier가 한쪽을 추천하면 그대로 유지.
- 두 경로를 혼동하지 말 것.

**섹션 매핑**:

| 섹션 | 소스 |
|------|------|
| §1 케이스 한 줄 정의 | Step 0의 case_description + 무엇/왜/입출력 정리 |
| §2 하네스 토폴로지 | structurer.topology_ascii |
| §3 파일 목록 | structurer.file_list |
| §4 파일 골격 | structurer.file_skeletons |
| §5-A 복붙 프롬프트 | applier.copy_paste_prompt |
| §5-B 트리거 환경 가이드 | applier.trigger_methods (4서브섹션: 권장 트리거 + 옵션 매트릭스 + 자동화 가이드 + 사전 준비 체크리스트) |
| §6 외부 연결 의존성 | applier.external_dependencies (4서브섹션: Easy Path + 인벤토리 + 옵션 A/B/C + 권한 요청 + 신호등) |
| §7 한계·우회 | applier.limits_workarounds |
| §8 B/C 트리거 | applier.next_steps_bc |

### 3-2. 산출물 frontmatter (Contract 6키)

```yaml
---
harness: scenario-a-generator
case: <case_name 자연어>
slug: <kebab-case>
difficulty: <하 | 중 | 상>
run_at: <ISO8601 KST>
run_id: <epoch>
subagents:
  scenario_a_structurer: <ok | recalled | partial>
  scenario_a_applier: <ok | recalled | partial>
---
```

### 3-3. 출력 마크다운 템플릿

```markdown
---
<frontmatter §3-2>
---

# <case_name> (시나리오 A)

> <case_description 2~3줄>

---

## §1 케이스 한 줄 정의

**무엇** — ...
**왜** — ...
**입력** — ...
**출력** — ...

---

## §2 하네스 토폴로지

```
<ASCII 다이어그램 — structurer 산출>
```

---

## §3 생성할 파일 목록

| 경로 | 책임 | 줄 수 |
|------|------|-------|
| ... | ... | ... |

---

## §4 각 파일의 골격

### §4-1. <파일 1 경로>
```markdown
<골격>
```

### §4-2. <파일 2 경로>
...

---

## §5 수강생 사용 가이드

### §5-A. 코딩에이전트에 던질 복붙 프롬프트 (만들기 가이드)

```text
<applier.copy_paste_prompt — 30줄 이내>
```

### §5-B. 트리거 환경 가이드 (만든 후 어떻게 켜고 실행하나)

#### 5B-0. 🟢 권장 트리거
<applier.trigger_methods — 1~2줄, 가장 적합한 트리거 1개 + 이유>

#### 5B-1. 트리거 방법 옵션 매트릭스
| 트리거 방법 | 명령 예시 | 적합 상황 | HITL | 자동화 |
|------------|----------|----------|------|--------|
| ... |

#### 5B-2. 자동화 트리거 가이드
<자동화 가능 시: launchd/Folder Action/Mail Rule 등 1~2개; HITL 필수면 "자동화 불가, B로 승격 시 가능" 1줄>

#### 5B-3. 트리거 환경 사전 준비 체크리스트
- [ ] Claude Code CLI 설치 확인
- [ ] 본 하네스 파일이 .claude/ 아래 있는지
- [ ] (CLI 트리거 시) PATH·환경변수
- [ ] (외부 의존 있을 때) §6 Easy Path 사전 준비

---

## §6 외부 연결 의존성

### 6-0. 🟢 Easy Path (가장 쉬운 시작)
<applier.external_dependencies — 1순위 옵션만 추려 1~3줄, 외부 의존 0이면 "해당 없음">

### 6-1. 의존성 인벤토리
<표 — 단계·의존 대상·종류·필수도·Easy Path 채택 옵션>

### 6-2. 의존성별 옵션 A/B/C 풀 가이드
<의존성마다 1개 블록 — 옵션 A/B/C 절차·소요·막힐 때>

### 6-3. 사내 권한 요청 문구 (복붙용)
<옵션 A 이상 선택 의존성마다 1개씩 — 안녕하세요 ~ 부탁드립니다 템플릿>

### 6-4. 신호등 요약
<표 — 의존성별 🟢/🟡/🔴 분류>

---

## §7 한계와 우회

| 한계 | 우회 |
|------|------|
| ... | ... |

---

## §8 다음 단계 (B/C로 넘어갈 때의 트리거)

- 트리거 1: ...
- 트리거 2: ...
...

---

## 끝.
```

---

## §4 Step 3 — Write + grep 자가검증

### 4-1. 경로 결정

```bash
slug=<case_name 첫 명사 3개 kebab-case>
today=$(date +%Y-%m-%d)
base="./specs/scenario-a/$slug/$today"
mkdir -p "$base"

if [ -f "$base/00_scenario_a.md" ]; then
  out="$base/00_scenario_a_<run_id>.md"
else
  out="$base/00_scenario_a.md"
fi
Write "$out"
```

### 4-2. grep 자가검증 (8 체크)

```bash
F="$out"
FAIL=0

# (1) 8개 § 헤딩 모두 존재
for SEC in "§1 케이스 한 줄 정의" "§2 하네스 토폴로지" "§3 생성할 파일 목록" "§4 각 파일의 골격" "§5 수강생 사용 가이드" "§6 외부 연결 의존성" "§7 한계와 우회" "§8 다음 단계"; do
  grep -qE "^## $SEC" "$F" || { echo "FAIL: 헤딩 누락 $SEC"; FAIL=$((FAIL+1)); }
done

# (1-a) §5-A / §5-B 분할 존재
for SUB in "5-A" "5-B"; do
  grep -qE "^### §$SUB\." "$F" || { echo "FAIL: §$SUB 분할 누락"; FAIL=$((FAIL+1)); }
done

# (1-b) §5-B 4서브섹션 (5B-0 ~ 5B-3)
for SUB in "5B-0" "5B-1" "5B-2" "5B-3"; do
  grep -qE "^#### $SUB\." "$F" || { echo "FAIL: §5-B 서브섹션 누락 $SUB"; FAIL=$((FAIL+1)); }
done

# (1-bis) §6 4서브섹션 모두 존재
for SUB in "6-0" "6-1" "6-2" "6-3" "6-4"; do
  grep -qE "^### $SUB\." "$F" || { echo "FAIL: §6 서브섹션 누락 $SUB"; FAIL=$((FAIL+1)); }
done

# (1-ter) §6-0 Easy Path 신호등(🟢) 또는 "해당 없음" 명시
grep -qE "(🟢|해당 없음)" "$F" || { echo "FAIL: §6-0 Easy Path 신호등/해당없음 누락"; FAIL=$((FAIL+1)); }

# (1-quater) §5-B 권장 트리거에 claude 명령 또는 자연어 트리거 키워드 포함
grep -qE "(claude|채팅|슬래시|/<slug>)" "$F" || { echo "FAIL: §5-B 트리거 키워드 누락"; FAIL=$((FAIL+1)); }

# (2) frontmatter 6키
for K in harness case slug difficulty run_at run_id subagents; do
  grep -qE "^$K:" "$F" || { echo "FAIL: frontmatter 누락 $K"; FAIL=$((FAIL+1)); }
done

# (3) §2 ASCII 다이어그램 (박스 문자)
grep -qE "[┌└├│▼─]" "$F" || { echo "FAIL: §2 ASCII 박스 누락"; FAIL=$((FAIL+1)); }

# (4) §3 파일 목록 표
grep -qE "^\| .* \| .* \|" "$F" || { echo "FAIL: §3 표 누락"; FAIL=$((FAIL+1)); }

# (5) §5 복붙 프롬프트 코드블록
grep -qE '^```text' "$F" || echo "WARN: §5 코드블록 'text' 표기 누락 (선택)"

# (6) 심플 제약 — 파일 개수 상한 검사
DIFFICULTY=$(grep -oE "^difficulty: [하중상]" "$F" | awk '{print $2}')
FILE_COUNT=$(grep -cE "^\| \`\\.claude/" "$F")
case "$DIFFICULTY" in
  하) MAX=2 ;;
  중) MAX=3 ;;
  상) MAX=4 ;;
esac
[ "$FILE_COUNT" -le "$MAX" ] || { echo "FAIL: 파일 $FILE_COUNT개 > $DIFFICULTY 상한 $MAX"; FAIL=$((FAIL+1)); }

# (7) 한국어 산출 확인 (한글 500자 이상)
# macOS Bash 환경에서 한글 카운트가 빈 값으로 출력되는 이슈 회피
HANGUL=$(LC_ALL=ko_KR.UTF-8 grep -oE "[가-힣]" "$F" 2>/dev/null | wc -l | tr -d ' ')
HANGUL=${HANGUL:-0}
[ "$HANGUL" -ge 500 ] || { echo "FAIL: 한국어 산출 부족 ($HANGUL자)"; FAIL=$((FAIL+1)); }

# (8) §5 복붙 프롬프트 30줄 이내
PROMPT_LINES=$(awk '/^## §5/{flag=1; next} /^## §6/{flag=0} flag && /^```/{c++} flag && c==1' "$F" | wc -l)
[ "$PROMPT_LINES" -le 35 ] || echo "WARN: §5 복붙 프롬프트 $PROMPT_LINES줄 > 30 권장"

[ "$FAIL" -eq 0 ] && echo "✅ ALL PASS ($FAIL fail)" || echo "❌ 재작업 필요 ($FAIL fail)"
```

자가검증 통과 전 보고 금지.

---

## §5 Step 4 — 보고

### 5-1. 로그

```bash
LOG=.claude/history/daily/$(date +%Y-%m-%d).md
mkdir -p "$(dirname "$LOG")"
echo "- $(date +%H:%M) | scenario-a-generator | $slug | $DIFFICULTY | $out" >> "$LOG"
```

### 5-2. 사용자 보고

```
✅ 시나리오 A 가이드 생성: <out>
   - 케이스: <case_name>
   - 난이도: <difficulty> (파일 상한 N개, 실제 M개)
   - subagent 호출: structurer ✓, applier ✓
   - grep 자가검증 (8 체크) 통과 ✓

다음:
- 산출물 검토 → 미세 조정 → 수강생에 배포
- 다른 케이스도 만들려면 /scenario-a <다음 케이스>
```

---

## §6 불변식

1. **두 층위 분리** — 메타 정교 / 산출물 심플
2. **8섹션 골격** — §1~§8 모두 산출
3. **§6 4서브섹션 강제** — Easy Path + 인벤토리 + 옵션 A/B/C + 권한 요청 + 신호등. 외부 의존 0개여도 "해당 없음" 명시 필수
4. **Easy Path 1순위 규칙** — 권한 신청 0건 + 기술 설정 0건 옵션 우선. 권한 신청 필요한 것을 1순위로 추천 금지
5. **frontmatter 6키 Contract** — 누락 시 검증 실패
6. **분업 subagent 2종 병렬 호출** — 단일 메시지 안에서 동시
7. **심플 제약 강제** — 파일 개수·subagent 종·HITL·외부 의존 모두 상한 준수
8. **합성은 command 직접** — 별도 합성 subagent 없음
9. **grep 자가검증 통과 전 보고 금지** (8 § 헤딩 + §6 4서브섹션 + frontmatter + 추가 체크)
10. **한국어 산출** — 코드·식별자만 영어

---

## §7 사용 예시

```bash
# 인자 없이 → Full Discovery
/scenario-a

# 한 줄 명시
/scenario-a 회의록을 Slack 포맷으로 변환하는 에이전트, 난이도 하

# 구조화 입력
/scenario-a case=competitor-compare difficulty=중 input=URL output=리포트

# 자연어 트리거 (SKILL.md 경유)
"경쟁사 페이지 비교 리포트 만드는 에이전트, Claude Code 하네스로 어떻게 짜지?"
```

---

## 끝.
