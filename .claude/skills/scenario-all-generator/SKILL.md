---
name: scenario-all-generator
description: 수강생 케이스 1개를 받아 시나리오 A·B·C 가이드 + Brief + D(선제 조건)를 한 번에 산출하는 합본 컨설팅 하네스. scenario-a-generator + scenario-b-generator + scenario-c-generator 3개 메타 하네스를 병렬 호출 후 합본 command가 Brief·D를 직접 합성. 산출물 5개 마크다운(00_brief / 01_scenario_a / 02_scenario_b / 03_scenario_c / 04_prerequisites) + 1개 viewer.html (aiceo-4th-agent UI 모방, 브라우저 자동 열림). 다음 발화에 트리거된다 — "4시나리오 합본", "A/B/C/D 가이드 다 만들어줘", "/scenario-all <케이스>".
---

# scenario-all-generator — 4-시나리오 합본 컨설팅 하네스

## 1. 무엇

수강생 케이스 1개 → A·B·C 가이드 3장 + Brief(1장 요약·비교) + D(선제 조건) + viewer.html.

산출물 6개 (specs/scenario-all/<slug>/<today>/):
- `00_brief.md` — 1페이지 요약 + A·B·C 비교 표 + D 사전 조건 요약
- `01_scenario_a.md` — Claude Code 하네스 단독 가이드 (scenario-a-generator 위임)
- `02_scenario_b.md` — aiceo-4th-agent 메뉴 (B 위임)
- `03_scenario_c.md` — 자율 에이전트 (C 위임)
- `04_prerequisites.md` — D: A·B·C 공통 사전 조건 (직접 합성)
- `viewer.html` — aiceo-4th-agent UI 모방, A/B/C/D 좌측 메뉴, 우측 콘텐츠. 브라우저 자동 열림.

## 2. 핵심 토폴로지

```
사용자 케이스 1개
       │
       ▼
오케스트레이터 (scenario-all-generator command)
       │
   ┌───┴───┬───────┐
   ▼ 병렬   ▼       ▼
 /scenario-a  /scenario-b  /scenario-c
 (Task 위임)   (Task 위임)   (Task 위임)
   │            │           │
   └────────────┼───────────┘
                ▼
   command 직접 합성:
   - 00_brief.md (3 산출 비교 요약)
   - 04_prerequisites.md (3 산출의 §6-3·§9 종합)
   - viewer.html (md 5개 + UI 셸)
                ▼
   open viewer.html (macOS 브라우저 자동 열림)
```

## 3. 언제 트리거

### 자연어
- "이 케이스 A·B·C·D 다 만들어줘"
- "4시나리오 합본 컨설팅"
- "Claude Code·aiceo·자율 다 어떻게 만드는지 보여줘"

### 슬래시
```
/scenario-all <케이스>
/scenario-all 일일 매출 보고서 — 사내 DB + 환율
/scenario-all                  # 인자 없으면 Discovery
```

## 4. 트리거 안 되는 경우

| 발화 | 라우팅 |
|------|-------|
| "A만 만들어" | `/scenario-a` |
| "B만" | `/scenario-b` |
| "C만" | `/scenario-c` |

## 5. 어떻게

`/scenario-all-generator` 위임. 핵심 동작:

1. **Step 0**: 케이스 명세 정규화 (Discovery 또는 구조화 입력)
2. **Step 1**: 3개 메타 하네스 **병렬 위임** (단일 메시지 안에서 Task 3건 동시):
   - `/scenario-a-generator <case>`
   - `/scenario-b-generator <case>`
   - `/scenario-c-generator <case>`
3. **Step 2**: 3 산출물 Read 후 합성:
   - 00_brief.md (1페이지 비교)
   - 04_prerequisites.md (D)
4. **Step 3**: viewer.html 생성 (md 5개 + UI 셸)
5. **Step 4**: `open viewer.html` (macOS) — 브라우저 자동 열림
6. **Step 5**: grep 자가검증 + 보고

## 6. 산출물 5+1 정합 규칙

| 파일 | 책임 | 소스 |
|------|------|------|
| 00_brief.md | 1페이지 요약 (A·B·C 비교 + D 요약 + 권장 시나리오) | command 직접 합성 |
| 01_scenario_a.md | A 풀가이드 8섹션 | scenario-a-generator 산출물 그대로 |
| 02_scenario_b.md | B 풀가이드 10섹션 | scenario-b-generator 산출물 그대로 |
| 03_scenario_c.md | C 풀가이드 10섹션 | scenario-c-generator 산출물 그대로 |
| 04_prerequisites.md | D — 사전 결정사항·API 키·사내 권한·환경 세팅·예산 | command 직접 합성 (3 산출의 §6-3·§9 통합) |
| viewer.html | UI 셸 + 5 md 콘텐츠 | command 직접 생성 |

## 7. 불변

- 산출 6개 파일 (5 md + 1 html)
- 3 메타 하네스 **단일 메시지 안에서 병렬 호출**
- viewer.html은 **CDN marked.js**로 md 렌더 (외부 의존 1개)
- viewer.html은 **aiceo-4th-agent UI 토큰 모방** (보라 #8b5cf6 강조 + Pretendard 폰트 + 좌측 사이드바)
- 브라우저 자동 열림 (`open` 명령) — macOS 한정, 다른 OS는 수동
- 한국어 산출, 코드·식별자 영어
- 권장 시나리오 1개 명시 (Brief §최종 권장)
