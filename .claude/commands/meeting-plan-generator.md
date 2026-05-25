---
description: 회의록·발표자료(로컬/Notion/복붙 등 다소스·다형식)를 취합해 프로젝트 실행 기획서 7섹션 마크다운 1장을 작성한다. 입력이 모호하면 Discovery 인터뷰로 환경을 좁힌 뒤 정규화→분업 추출→HITL→합성 순으로 처리한다.
argument-hint: <선택: 폴더경로 | 파일목록 | URL>
allowed-tools: Bash, Read, Write, Grep, Glob, Task, AskUserQuestion
---

# /meeting-plan-generator — 회의·발표 → 실행 기획서

## §0 정체성

### 무엇

회의 노트와 발표자료를 받아 **프로젝트 실행 기획서 1장**을 작성한다.

산출물: `./specs/meeting-plan-generator/<slug>/<today>/00_plan.md`

### 핵심 설계 원칙

이 케이스의 본질은 **"입력의 불확실성이 크다"**는 것이다. 그래서 다른 하네스와 달리:

1. **Step 0 = Discovery 인터뷰**가 가장 무겁다 — 인자 없이 호출 가능, AskUserQuestion 캐스케이드로 환경 좁힘
2. **Step 1 = 정규화** 레이어 — 어떤 입력이 들어와도 공통 MD로 변환한 뒤 단일 로직
3. **Step 2 = 분업 추출** — 회의록(시간순 결정·액션)과 발표자료(논리·수치·도식)는 성격이 달라 분리
4. **Step 3 = HITL 게이트** — 민감 정보 + 추출 결과 모호 항목 검수
5. **Step 4 = command 직접 합성** — 7섹션 작성을 별도 subagent 위임하지 않고 오케스트레이터가 종합 (subagent 1개 줄여 단순화)

### 불변

- 산출물 1개 마크다운 (`00_plan.md`)
- 7섹션 골격 (§1~§7) 모두 포함
- frontmatter 9키 Contract 강제
- 추출 subagent 2개 모두 호출 (회의록·발표자료가 둘 다 있을 때) — 한쪽만 있으면 그 한쪽만
- 민감 키워드 매칭 시 HITL 없이 자동 진행 금지
- grep 자가검증 통과 전 "완료" 보고 금지

---

## §1 Step 0 — Discovery 인터뷰 (입력 환경 파악)

### 1-1. 인자 평가

```
$ARGUMENTS가 비어 있음:           → 1-2. Full Discovery (3회 캐스케이드)
$ARGUMENTS = 폴더 경로 1개:        → 1-3. Scan + 부분 Discovery (민감도만 확인)
$ARGUMENTS = 파일 목록 2개 이상:   → 1-3. Scan + 부분 Discovery
$ARGUMENTS = URL (Notion 등):     → 1-4. URL 모드
$ARGUMENTS = 긴 텍스트 (복붙):     → 1-5. Paste 모드 (Discovery 스킵)
```

### 1-2. Full Discovery (3회 캐스케이드)

**Q1 — 입력 위치**
```
AskUserQuestion:
"회의자료가 어디 있나요?"
- 로컬 폴더 또는 파일 (경로 알려주세요)
- Notion / Confluence 페이지 (URL)
- Slack / Teams 메시지 (복붙)
- 일부는 여기, 일부는 저기 (혼합)
```

**Q2 — 형식 및 추가 정보 (Q1 답변에 따라 분기)**

답변이 "로컬"이면:
```
"폴더 경로 또는 파일 목록을 한 줄에 알려주세요. 예: ~/Documents/project-alpha/"
(자유 텍스트)
```

답변이 "Notion"이면:
```
AskUserQuestion:
"Notion MCP 연결 상태는?"
- 연결됨 (자동 fetch 시도)
- 미연결 (URL 알려주시면 수동 fetch 안내)
- 모름 (확인 방법 안내)
```

답변이 "복붙"이면 → 1-5. Paste 모드로 점프.

답변이 "혼합"이면 → 각 소스별로 위 분기 반복.

**Q3 — 민감도**
```
AskUserQuestion:
"회의 내용에 민감 정보(인사·재무·계약·고객 정보) 포함 가능성?"
- 없음 (자동 처리 OK)
- 있을 수 있음 (Recommended) — 민감 키워드 매칭 시 컨펌 모달
- 모름 (보수적 처리 = 있을 수 있음과 동일)
```

### 1-3. Scan + 부분 Discovery

```bash
# 1) 경로 스캔
for path in $ARGUMENTS; do
  if [ -d "$path" ]; then
    find "$path" -maxdepth 3 -type f \( -name "*.md" -o -name "*.txt" -o -name "*.pdf" -o -name "*.pptx" -o -name "*.docx" \) | head -50
  elif [ -f "$path" ]; then
    echo "$path"
  fi
done > /tmp/mpg_input_files.txt

# 2) 형식별 카운트
md_count=$(grep -cE '\.(md|txt)$' /tmp/mpg_input_files.txt)
pdf_count=$(grep -cE '\.pdf$' /tmp/mpg_input_files.txt)
pptx_count=$(grep -cE '\.pptx$' /tmp/mpg_input_files.txt)
docx_count=$(grep -cE '\.docx$' /tmp/mpg_input_files.txt)
total=$((md_count + pdf_count + pptx_count + docx_count))

# 3) 사용자에게 보고
"발견: MD/TXT $md_count개, PDF $pdf_count개, PPTX $pptx_count개, DOCX $docx_count개 (총 $total)"
```

스캔 결과 0개면 → 1-2. Full Discovery로 fallback.
스캔 결과 50개 초과면 → "범위가 큽니다. 회의록·발표자료를 폴더로 분리해주시거나 키워드로 좁혀주세요" 안내 후 중단.

이후 Q3 민감도만 묻고 진행.

### 1-4. URL 모드 (Notion 등)

MCP 연결 상태 확인:
```
Notion MCP가 ToolSearch로 로드 가능하면 → mcp__claude_ai_Notion__notion-fetch
없으면 → "URL을 본문 텍스트로 복붙해주세요" 안내 후 1-5로 전환
```

### 1-5. Paste 모드

`$ARGUMENTS` 또는 사용자 추가 입력이 100자 이상의 자유 텍스트면 그것을 회의록 본문으로 간주.

Discovery 스킵하고 Step 2 직행 (단, 민감도는 한 번만 물음 — 정책상 high로 가정해도 무방).

### 1-6. Discovery 산출 — 처리 계획 텍스트

Step 1 끝에 사용자에게 1줄 요약:
```
처리 계획: 회의록 $N개 + 발표자료 $M개 → 정규화 → 분업 추출 (병렬) → HITL → 7섹션 합성
민감도 정책: <자동 / HITL>
저장 경로: ./specs/meeting-plan-generator/<slug>/<today>/00_plan.md
진행할까요? (y/n)
```

`n` 이면 중단. `y`이면 Step 2 진입.

---

## §2 Step 1 — 정규화 (모든 입력 → 공통 MD)

목표: Step 2 이후가 입력 형식과 무관하도록 모든 입력을 **공통 중간 포맷(`/tmp/mpg_<run_id>/normalized/<name>.md`)** 으로 변환.

### 2-1. MD/TXT
```bash
# 그대로 복사 (또는 Read)
cp "$src" "/tmp/mpg_$run_id/normalized/$(basename $src .${src##*.}).md"
```

### 2-2. PDF
```
Read 도구가 PDF 직접 지원 → 텍스트만 추출해 MD로 저장.
페이지 20+ PDF는 `pages: "1-20"` 분할 Read 권장.
```

### 2-3. PPTX (외부 dep 없는 추출)
```bash
# pptx = zip 압축이므로 unzip + grep으로 텍스트만 발췌
mkdir -p "/tmp/mpg_$run_id/pptx_$(basename $src .pptx)"
unzip -q "$src" -d "/tmp/mpg_$run_id/pptx_$(basename $src .pptx)"
# 슬라이드별 텍스트 추출 (간이 — <a:t>...</a:t> 매칭)
for slide in /tmp/mpg_$run_id/pptx_*/ppt/slides/slide*.xml; do
  num=$(echo "$slide" | grep -oE 'slide[0-9]+' | head -1)
  echo "## $num"
  grep -oE '<a:t[^>]*>[^<]*</a:t>' "$slide" | sed 's/<[^>]*>//g'
  echo ""
done > "/tmp/mpg_$run_id/normalized/$(basename $src .pptx).md"
```

### 2-4. DOCX (선택)
```bash
# 동일 원리 — word/document.xml에서 <w:t> 추출
unzip -p "$src" word/document.xml | grep -oE '<w:t[^>]*>[^<]*</w:t>' | sed 's/<[^>]*>//g' > out.md
```

### 2-5. Notion URL (MCP)
```
mcp__claude_ai_Notion__notion-fetch(url=...)
→ 반환된 마크다운/텍스트를 /tmp/mpg_$run_id/normalized/ 에 저장
```

### 2-6. 복붙 텍스트
이미 텍스트 → 그대로 저장.

### 2-7. 정규화 후 분류

각 파일을 **회의록(meeting)** vs **발표자료(deck)** 로 분류:

```
heuristic:
- 파일명에 "meeting|회의|note|minutes|회의록" → meeting
- 파일명에 "deck|slide|발표|presentation|.pptx" → deck
- 본문에 "참석자|결정사항|액션아이템" 키워드 高 → meeting
- 본문에 "## slide|페이지 1|목차" 키워드 高 → deck
- 분류 불확실하면 사용자에게 1회 물음 (AskUserQuestion: 파일별 다중 선택)
```

분류 결과를 `/tmp/mpg_$run_id/classification.json` 에 저장.

---

## §3 Step 2 — 분업 추출 (subagent 병렬)

### 3-1. 호출 토폴로지

```
오케스트레이터
    │
    ├──▶ Task(subagent_type="meeting-note-extractor", ...)   [회의록만]
    │
    └──▶ Task(subagent_type="deck-content-extractor", ...)   [발표자료만]
```

회의록만 있으면 첫 번째만, 발표자료만 있으면 두 번째만 호출. 둘 다 있으면 **병렬 호출**.

### 3-2. Subagent prompt 골격

**meeting-note-extractor**
```text
Task(subagent_type="meeting-note-extractor", prompt="""
스펙: .claude/agents/meeting-note-extractor.md 정독.
yaml 5섹션 (meta·decisions·actions·blockers·open_questions) 채워 압축 텍스트로 반환.
파일 쓰지 말 것.

--- 입력 회의록 파일 목록 (정규화 완료) ---
- /tmp/mpg_<run_id>/normalized/note_2025-12-01.md
- /tmp/mpg_<run_id>/normalized/note_2025-12-08.md
- /tmp/mpg_<run_id>/normalized/note_2025-12-15.md

각 회의에서 일자·참석자·결정사항·액션아이템(Owner·Due)·블로커·미결 질문을 추출.
""")
```

**deck-content-extractor**
```text
Task(subagent_type="deck-content-extractor", prompt="""
스펙: .claude/agents/deck-content-extractor.md 정독.
yaml 4섹션 (meta·key_messages·metrics_and_targets·logic_flow) 채워 압축 텍스트로 반환.
파일 쓰지 말 것.

--- 입력 발표자료 파일 목록 (정규화 완료) ---
- /tmp/mpg_<run_id>/normalized/kickoff_deck.md
- /tmp/mpg_<run_id>/normalized/midterm_deck.md

각 자료에서 핵심 메시지·수치·목표·논리 흐름을 추출.
""")
```

### 3-3. Subagent 산출 검증

```bash
echo "$MEETING_OUT" | grep -qE "decisions:|actions:|blockers:" || RECALL_MEETING=true
echo "$DECK_OUT"    | grep -qE "key_messages:|metrics_and_targets:" || RECALL_DECK=true
```

검증 실패 시 1회만 재호출 (correction prompt에 누락 키 명시). 재호출 후 실패면 오케스트레이터가 부분 합성.

---

## §4 Step 3 — HITL 게이트

### 4-1. 민감 키워드 매칭

```bash
SENSITIVE_KEYWORDS="연봉|급여|계약|해지|해고|법무|법적|인사고과|M&A|인수합병|징계|노조|소송|감사|내부고발|보안사고|개인정보 유출|영업비밀|단가|마진"
hit_count=$(grep -oE "$SENSITIVE_KEYWORDS" "$MEETING_OUT" "$DECK_OUT" | wc -l)
```

`hit_count >= 1` 이면:
```
AskUserQuestion:
"민감 키워드 $hit_count건 감지됨. 처리 방식:"
- 마스킹 후 진행 (Recommended) — 해당 라인을 [REDACTED]로 치환
- 해당 회의·자료 제외하고 진행
- 전체 중단
```

### 4-2. 모호 항목 검수 (선택)

추출된 결정사항·액션 중 다음 조건 해당 시 1회 컨펌:
- Owner 또는 Due가 비어 있는 액션 3개 이상
- 결정 사항 중 "TBD", "미정", "추후 논의" 표기 다수
- 발표자료 수치가 회의록 수치와 불일치

```
"다음 항목은 확인이 필요합니다. 진행 방식?"
- 그대로 산출물에 '확인 필요' 플래그로 포함 (Recommended)
- 사용자가 수동으로 채우게 빈칸 유지
- 산출물에서 제외
```

---

## §5 Step 4 — 7섹션 합성 (command 직접)

### 5-1. 합성 규칙

오케스트레이터가 추출 결과(`MEETING_OUT` + `DECK_OUT` yaml)를 입력으로 받아 **직접 7섹션 마크다운을 작성**한다. 별도 subagent 위임 없음.

**섹션별 데이터 소스**:

| 섹션 | 주 소스 | 보조 소스 |
|------|--------|----------|
| §1 프로젝트 개요 | deck.key_messages | meeting.meta (초기 회의 배경) |
| §2 범위 (In/Out) | deck.key_messages + meeting.decisions | meeting.open_questions (Out 판단) |
| §3 결정사항 타임라인 | meeting.decisions | — |
| §4 액션 아이템 | meeting.actions | — |
| §5 일정·마일스톤 | deck (있으면) + meeting 일정 결정 | — |
| §6 리스크·블로커 | meeting.blockers + meeting.open_questions | deck (논리 흐름의 가정) |
| §7 KPI·다음 게이트 | deck.metrics_and_targets | meeting.decisions (지표 합의) |

### 5-2. Write — 마크다운 산출

```markdown
---
<frontmatter Contract §6>
---

# <프로젝트명> — 프로젝트 실행 기획서

> 생성: <run_at>
> 입력: 회의록 N개 + 발표자료 M개
> 추출 subagent: meeting-note-extractor, deck-content-extractor

## §1 프로젝트 개요
### 배경
### 목적
### 비전
### 성공 정의

## §2 범위
### In (포함)
### Out (미포함)
### 가정 / 전제

## §3 핵심 결정사항 타임라인
| 일자 | 회의/자료 | 결정 | 결정권자 | 근거 |

## §4 액션 아이템
### 담당자별 그루핑
- **<이름>**
  - [ ] <액션> — Due: <YYYY-MM-DD> — 근거: <회의명>

### 마감일순 정렬
| Due | Owner | Action | Status |

## §5 일정·마일스톤
```text
[ Phase 0 ] 킥오프              ████              [Done 2025-12-01]
[ Phase 1 ] 설계·구조 합의      ░░░██████░░       [2025-12-08 ~ 2026-01-05]
[ Phase 2 ] 구현·통합           ░░░░░░░░░████░░   [2026-01-06 ~ 2026-02-20]
...
```

## §6 리스크·블로커
| 항목 | 영향 | 대응 | 책임자 | 상태 |

## §7 KPI·다음 의사결정 게이트
### KPI
| 지표 | 목표 | 측정 방법 | 측정 주기 |

### 다음 의사결정 게이트
| 일자 | 회의 | 안건 | 필요 인풋 |
```

### 5-3. 저장

```bash
base="./specs/meeting-plan-generator/<slug>/<today>"
mkdir -p "$base"
if [ -f "$base/00_plan.md" ]; then
  out="$base/00_plan_<run_id>.md"
else
  out="$base/00_plan.md"
fi
Write "$out"
```

---

## §6 Contract — frontmatter 키 (9개)

```yaml
---
harness: meeting-plan-generator
slug: <kebab-case>
run_at: <ISO8601 KST>
run_id: <epoch>
sources_meetings:
  - path: <경로>
    date: <회의 일자 추정>
sources_decks:
  - path: <경로>
    title: <자료 제목>
decisions_count: <N>
actions_count: <M>
risk_flags:
  - <블로커 1줄>
sensitivity_handling: <auto | hitl_masked | hitl_excluded>
subagents:
  meeting_note_extractor: <run_id|hash|skipped>
  deck_content_extractor: <run_id|hash|skipped>
---
```

> Contract 외 키 금지. 9키 누락 시 grep 자가검증 실패 = 하네스 실패.

---

## §7 grep 자가검증

```bash
F="$out"
FAIL_COUNT=0

# 7개 § 헤딩 모두 존재
for SEC in "§1 프로젝트 개요" "§2 범위" "§3 핵심 결정사항 타임라인" "§4 액션 아이템" "§5 일정·마일스톤" "§6 리스크·블로커" "§7 KPI"; do
  grep -qE "^## $SEC" "$F" || { echo "FAIL: 헤딩 누락 $SEC"; FAIL_COUNT=$((FAIL_COUNT+1)); }
done

# Frontmatter 9키
for K in harness slug run_at run_id sources_meetings sources_decks decisions_count actions_count risk_flags sensitivity_handling subagents; do
  grep -qE "^$K:" "$F" || { echo "FAIL: frontmatter 누락 $K"; FAIL_COUNT=$((FAIL_COUNT+1)); }
done

# §3 타임라인 표 (일자 컬럼)
grep -qE "\| *[0-9]{4}-[0-9]{2}-[0-9]{2}" "$F" || { echo "FAIL: §3 일자 누락"; FAIL_COUNT=$((FAIL_COUNT+1)); }

# §4 액션 아이템에 Owner·Due 컬럼 존재
grep -qE "Owner|담당자" "$F" && grep -qE "Due|마감" "$F" || { echo "FAIL: §4 Owner/Due 누락"; FAIL_COUNT=$((FAIL_COUNT+1)); }

# §5 텍스트 간트 (블록 문자)
grep -qE "█|░|▓" "$F" || { echo "FAIL: §5 간트 블록 누락"; FAIL_COUNT=$((FAIL_COUNT+1)); }

# Subagent 증적
grep -qE "meeting_note_extractor:|deck_content_extractor:" "$F" || { echo "FAIL: subagent 증적 누락"; FAIL_COUNT=$((FAIL_COUNT+1)); }

[ "$FAIL_COUNT" -eq 0 ] && echo "✅ ALL PASS" || echo "❌ 재작업 필요 ($FAIL_COUNT)"
```

---

## §8 로그·보고

### 로그 append
```bash
LOG=.claude/history/daily/$(date +%Y-%m-%d).md
mkdir -p "$(dirname "$LOG")"
echo "- $(date +%H:%M) | meeting-plan-generator | <slug> | meetings=$N decks=$M decisions=$D actions=$A | $out" >> "$LOG"
```

### 보고
grep 통과 후에만:
```
✅ 실행 기획서 생성: <out>
   - 입력: 회의록 N개 + 발표자료 M개
   - 결정사항 D건, 액션 A건, 리스크 R건
   - 민감도 처리: <auto|hitl_masked|hitl_excluded>
   - 추출 subagent 호출: ✓
   - grep 자가검증 (7 § + 9키 + 5 패턴) 통과 ✓
```

---

## §9 불변식 (8개)

1. **Step 0 Discovery 인터뷰** — 인자 모호 시 강제, 사용자 컨펌 후 진행
2. **정규화 레이어 통과** — Step 2 이후는 입력 형식 무관
3. **추출 subagent 분업** — 회의록/발표자료 각각 다른 subagent (있는 것만)
4. **HITL 게이트** — 민감 키워드 매칭 시 자동 진행 금지
5. **7섹션 골격** — § 1~7 모두 산출, 빈 섹션은 "정보 부족" 명시
6. **Contract frontmatter 9키** — 누락 시 자가검증 실패
7. **grep 자가검증 전 보고 금지**
8. **합성은 command 직접** — 별도 subagent 위임 없음 (단순화 결정)

---

## §10 사용 예시

```bash
# 인자 없이 → Full Discovery
/meeting-plan-generator

# 폴더
/meeting-plan-generator ~/Documents/project-alpha/

# 파일 직접
/meeting-plan-generator note1.md note2.md kickoff.pptx

# Notion URL (MCP 필요)
/meeting-plan-generator https://www.notion.so/...

# 자연어 트리거 (SKILL.md 경유)
"지난주 회의록 3개 + 킥오프 자료로 실행 기획서 만들어줘. ~/Documents/project-alpha/"
```

---

## 끝.
