---
name: meeting-plan-generator
description: 회의록과 발표자료(로컬 파일/Notion/복붙 등 다양한 소스·형식)를 취합해 프로젝트 실행 기획서(7섹션 마크다운 1장)를 작성한다. 입력이 모호할 때 Discovery 인터뷰로 환경을 좁힌 뒤 처리한다. 다음 발화에 트리거된다 — "회의록 정리해서 기획서 만들어줘", "회의 노트랑 발표자료 합쳐서 실행 계획", "프로젝트 실행 기획서 자동", "meeting plan", "킥오프 자료로 plan 뽑아줘".
base_directory: .claude/skills/meeting-plan-generator
---

# meeting-plan-generator — 회의·발표 → 실행 기획서

## 1. 무엇을 하는가

회의록·발표자료를 입력으로 받아 **프로젝트 실행 기획서 1장**(`specs/meeting-plan-generator/<slug>/<today>/00_plan.md`)을 자동 생성한다.

### 핵심 특성

- **입력 베리에이션이 큰 케이스** — 파일 위치(로컬/Notion/Slack), 형식(MD/PDF/PPTX/복붙), 언어, 민감도가 천차만별
- **Discovery 인터뷰 우선** — 입력 환경이 모호하면 `AskUserQuestion`으로 캐스케이드 질문 후 처리
- **정규화 레이어** — 어떤 입력이 들어와도 공통 중간 포맷(MD)으로 변환한 뒤 단일 로직으로 처리
- **분업 추출** — 회의록·발표자료를 다른 subagent로 병렬 처리 (성격이 다르기 때문)
- **HITL 2회 게이트** — Step 0(입력 환경 파악) + Step 3(민감 정보·모호 항목 검수)

### 산출물 골격 (7섹션)

```
§1 프로젝트 개요 (배경·목적·비전·성공 정의)
§2 범위 (In / Out / 가정)
§3 핵심 결정사항 타임라인 (일자·회의·결정·결정권자)
§4 액션 아이템 (담당자·마감·상태·근거 회의)
§5 일정·마일스톤 (텍스트 간트)
§6 리스크·블로커 (회의 언급 우려 + 보류 결정)
§7 KPI·다음 의사결정 게이트
```

---

## 2. 언제 트리거

### 자연어
- "회의록 정리해서 기획서 만들어줘"
- "킥오프·중간보고 자료 합쳐서 실행 계획 좀"
- "프로젝트 실행 기획서 자동으로 짜줘"
- "회의 노트랑 슬라이드에서 실행 plan 뽑아줘"

### 명시 슬래시
```
/meeting-plan-generator [선택: 입력 경로]
/meeting-plan-generator                        # 인자 없이 호출 → Discovery 인터뷰 진입
/meeting-plan-generator ./meetings/            # 폴더 통째로
/meeting-plan-generator note1.md deck.pdf      # 파일 직접 나열
```

---

## 3. 트리거 안 되는 경우

| 발화 | 라우팅 |
|------|-------|
| "회의록 요약만 해줘" (기획서 아님) | 일반 답변 또는 `/reverse` 없음 — 단순 요약 |
| "PRD 새로 만들고 싶어" (회의 자료 없이) | `/plan` · `/plan-t2` · `/plan-t3` |
| "이 기획서 리뷰해줘" | 코드/문서 리뷰 |
| "회의록 잘 쓰는 법" | 일반 답변 |

---

## 4. 어떻게 동작하는가

### 4-1. 호출 트리

```
사용자 자연어 또는 /meeting-plan-generator
       │
       ▼
SKILL.md (자동 트리거)
       │
       ▼
/meeting-plan-generator [args]
       │
       ▼
오케스트레이터 (command.md, Opus 4.7)
       │
       ├──▶ Step 0: Discovery 인터뷰 (AskUserQuestion 캐스케이드)
       │     - 입력 위치 / 형식 / 민감도 파악
       ├──▶ Step 1: 정규화 (모든 입력 → 공통 MD)
       │     - PDF: Read 직접 / PPTX: unzip+xmllint / MD·TXT: Read
       ├──▶ Step 2: 분업 추출 (2 subagent 병렬)
       │     ▸ meeting-note-extractor (Sonnet)
       │     ▸ deck-content-extractor (Sonnet)
       ├──▶ Step 3: HITL 게이트
       │     - 민감 키워드 매칭 / 모호한 결정 컨펌
       └──▶ Step 4: 7섹션 합성 → Write
              (planner-bmad-pm 재활용 안 함 — command 직접 합성)
       │
       ▼
grep 자가검증 → 통과 시 보고
```

### 4-2. 입력 처리 매트릭스

| 입력 소스 | 처리 방식 | Step 1 도구 |
|----------|----------|-----------|
| 로컬 폴더/파일 (md/txt/pdf) | 직접 Read | Read |
| 로컬 pptx | unzip → ppt/slides/*.xml → 텍스트 추출 | Bash + Grep |
| 로컬 docx | unzip → word/document.xml | Bash + Grep |
| Notion 페이지 URL | MCP Notion 도구 (있으면) | mcp__claude_ai_Notion__notion-fetch |
| 복붙 텍스트 | stdin / 다음 turn 사용자 입력 | — |
| 이메일 첨부 | "다운로드 후 폴더 알려주세요" 안내 | (사용자 매뉴얼) |
| 음성 녹음 | 본 PoC에서 미지원 — STT 외부 처리 안내 | (out of scope) |

### 4-3. 불변

- Step 0 Discovery 인터뷰가 모호도 임계값 이상이면 강제
- 정규화 레이어를 통해 Step 2 이후는 입력 형식 무관
- 추출은 분업 (회의록 ≠ 발표자료)
- 7섹션 골격·Contract frontmatter 9키 강제
- 민감 키워드 매칭 시 자동 처리 금지 (HITL)
- 단일 마크다운 1개 산출 (`00_plan.md`)

---

## 5. 사용 예시

### 예 1 — 자연어 자동 트리거
```
사용자: "지난주 킥오프 회의록 3개랑 발표자료 2개로 실행 기획서 만들어줘.
       파일은 ~/Documents/project-alpha/ 폴더에 있어"
→ SKILL 트리거 → command 호출 → Step 0 일부 스킵(경로 명시됨) → Step 1~4 실행
```

### 예 2 — 인자 없이 호출 (full Discovery)
```
사용자: /meeting-plan-generator
에이전트: AskUserQuestion 1 — "회의자료가 어디 있나요?" (로컬/Notion/복붙/혼합)
사용자: 로컬 + Notion 일부
에이전트: AskUserQuestion 2 — "경로와 Notion URL 알려주세요" + "MCP 연결되어 있나요?"
... 환경 좁힌 뒤 Step 1 진입
```

### 예 3 — 복붙 모드
```
사용자: "회의록 텍스트 붙여넣을게. 이걸로 실행 기획서 만들어줘
       [긴 텍스트...]"
→ Step 0 스킵 (입력 = 본문 그 자체) → Step 2 직행
```

---

## 6. 산출물 경로

```
./specs/meeting-plan-generator/<slug>/<today>/00_plan.md
```

- slug = 첫 회의·발표 제목 첫 명사 3개 kebab-case
- 같은 날 재실행 시 `00_plan_<run_id>.md` suffix
- frontmatter Contract 9키 강제 (자가검증)

---

## 끝.
