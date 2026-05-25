---
name: agent-solution-consultant
description: 수강생 자연어 에이전트 요청 → 시나리오 A(Claude Code 단독)·B(aiceo-4th-agent 커스텀 앱) 2-시나리오 실행 가이드 1장. 분업형 4-Agent 오케스트레이션(requirements-analyst / dependency-scout / solution-architect / risk-feasibility-auditor). v2 (내부 자산 권고 폐기, 실행 가이드 중심 재편). 3회차 강의(2026-05-29 "자기 회사에 필요한 에이전트 만들기") 즉시 실습 자료.
allowed-tools: Bash, Read, Write, Grep, Glob, WebSearch, WebFetch, Task
---

# agent-solution-consultant v2 — 에이전트 실행 가이드 하네스 (진입점)

## 1. 무엇을 하는가

수강생이 자연어로 던진 "이런 에이전트 만들고 싶어"를 받아, **두 가지 실행 시나리오**(A: Claude Code 단독 / B: aiceo-4th-agent 기반 커스텀 앱)와 사전 준비물·엔터프라이즈 점검을 담은 **실행 가이드 1장**을 생성한다.

산출물 위치: `./specs/agent-solution-consultant/<slug>/<today>/00_consultation.md`

### 6섹션 골격 (v2)

- **§0 요청 정규화** — 분류표·실패 모드
- **§1 에이전트 구조 텍스트 다이어그램** — 시나리오 A·B 각각 ASCII
- **§2 사전 준비물 체크리스트** (7 하위) — API 키·SaaS·MCP·사내 접근·기타·preflight
- **§3 시나리오 A** — Claude Code 단독 (앱 미구축)
- **§4 시나리오 B** — aiceo-4th-agent 기반 커스텀 앱 (복붙 프롬프트 포함)
- **§9 엔터프라이즈 점검** (BCG 5축) — 시나리오 A·B 각각 점수

### v2 핵심 제약

- **내부 자산(`/korea-*`·`poc/data/`·`bootstrap/`) 인용 절대 금지** — 수강생이 0에서 만드는 실습. "기존 자산 재사용" 가이드 금지.
- **시나리오 A·B 둘 다 산출** — 한쪽만 가능하면 그 이유 명시.
- **§4 복붙 프롬프트 200자+** — 그대로 Claude Code에 붙여넣어 작동해야.
- **사내 접근 권한 메일 템플릿** — 복붙 가능한 한국어 비즈니스 톤.

---

## 2. 언제 트리거

### 자연어 트리거 어휘
- "이런 에이전트 만들고 싶어"
- "회사에서 ~ 자동화하려는데"
- "에이전트 솔루션 좀 짜줘"
- "이거 어떻게 만들지?"
- "<업무> 같은 거 에이전트로 가능?"
- "<반복 업무> 자동으로 해주는 거 만들어줘"

### 명시 슬래시
```
/agent-solution-consultant <자연어 요청>
```

### 3회차 강의 컨텍스트
3회차(2026-05-29) "자기 회사에 필요한 에이전트 만들기"에서 30명 수강생이 각자 자기 회사 시나리오 1건씩 사전 제출 → 강의 시간 본 하네스로 일괄 컨설팅 → 발표회전(25분, 3-5명) 시 산출물이 발표 골격.

**v1과의 차이**: 산출물이 평가·매트릭스(v1)가 아니라 **즉시 손으로 만드는 실행 가이드**(v2). 시나리오 B 복붙 프롬프트는 Claude Code에 붙여넣으면 aiceo-4th-agent 리포에 신규 메뉴가 추가된다.

---

## 3. 트리거 안 되는 경우

- 이미 만든 에이전트 **디버깅** → `/fix`
- 코드 **직접 작성** 요청 → `/implement`
- 단순 개념 질문 ("MCP가 뭐야?") → 일반 답변
- **기획 문서** 작성 → `/plan` 또는 `/plan-t2`/`/plan-t3`
- **역공학** → `/reverse`

---

## 4. 어떻게 동작하는가

### 4-1. 호출 트리

```
사용자 자연어 "<요청>"
       │
       ▼
SKILL.md (자동 트리거)
       │
       ▼
/agent-solution-consultant <요청>
       │
       ▼
오케스트레이터 (Opus 4.7, command.md)
       │
       ├──▶ requirements-analyst   (Sonnet)
       ├──▶ dependency-scout        (Sonnet, v2 신규)
       ├──▶ solution-architect      (Opus) ◀── A·B 산출 입력
       └──▶ risk-feasibility-auditor (Opus) ◀── C 산출 입력
       │
       ▼
오케스트레이터 통합 → 6섹션 마크다운 Write
       │
       ▼
grep 자가검증 → 통과 시 보고
```

### 4-2. v1 → v2 변경

| 항목 | v1 | v2 |
|------|----|----|
| 산출물 섹션 | 10개 | **6개** |
| 해결안 분류 | 4안(0/1/2/3) | **시나리오 A·B** |
| 2번 subagent | pattern-matcher (내부 자산 매핑) | **dependency-scout** (외부 의존성·사전 준비물) |
| §2 사전 준비물 | 없음 | **신규** (API 키·SaaS·MCP·사내 접근 메일·기타·preflight) |
| §4 복붙 프롬프트 | §8 즉시 실행 (간략) | **§4 시나리오 B 핵심** (200줄+, 그대로 작동) |
| 내부 자산 인용 | "0에서 만들지 마라" 권고 | **인용 금지** (실습 동력 보호) |

### 4-3. 불변

- 시나리오 A·B 둘 다 산출
- §2 하위 7섹션 (2-A~2-G) 완비
- §3·§4 각각 4·5 하위 섹션 완비
- 사내 접근 권한 메일 템플릿 1개+
- §4 복붙 프롬프트 200자+ (코드 블록)
- ASCII 다이어그램 시나리오 A·B 각각
- §9 BCG 5축 시나리오 A·B 각각 점수
- 한국 환경 함정 1개+
- **v2 제약**: 내부 자산 인용 시 즉시 실패

---

## 5. 사용 예시

### 예 1 — 슬래시 명시
```
/agent-solution-consultant 회의 노트와 발표자료를 취합해서 프로젝트 실행 기획서를 자동으로 짜주는 에이전트
```

### 예 2 — 자연어 자동 트리거
```
사용자: "외근 중 받은 이메일에서 To에 내가 들어간 것만 골라 회신 초안 만드는 에이전트 만들고 싶어"
→ SKILL이 트리거 → command 호출
```

### 예 3 — 3회차 강의 일괄 실행
```
사용자: "스크린샷 14개 요청 모두에 컨설팅 돌려서 specs/ 에 저장"
→ SKILL이 14회 반복 호출
```

---

## 6. 부수 산출물 (선택)

수강생 30명 일괄 처리 시:
- `./specs/agent-solution-consultant/_index.md` — 요청자·시나리오 A/B 추천 매트릭스
- `./specs/agent-solution-consultant/_consolidated-deck.md` — 공통 패턴 1-pager

본 SKILL.md 본체에는 포함되지 않으며 별도 후처리.
