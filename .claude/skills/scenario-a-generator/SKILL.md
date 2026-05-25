---
name: scenario-a-generator
description: 수강생이 만들고 싶은 에이전트 케이스 1개를 받아 "Claude Code 하네스 요소만으로 구현하는 가이드(시나리오 A)" 7섹션 마크다운 1장을 산출하는 메타 하네스. 산출물은 항상 심플하게 떨어지도록 제약을 강제한다(파일 4개 이하, subagent 2종 이하, HITL 2회 이하). 다음 발화에 트리거된다 — "시나리오 A 가이드 만들어줘", "이 케이스 Claude Code 하네스로 구현하면", "/scenario-a <케이스 설명>".
---

# scenario-a-generator — 시나리오 A 가이드 생성기

## 1. 무엇

수강생 케이스 1개 → 시나리오 A(Claude Code 하네스 단독) 구현 가이드 1장.

산출물: `./specs/scenario-a/<slug>/<today>/00_scenario_a.md`

## 2. 핵심 구분 (두 층위)

| 층위 | 누가 쓰나 | 정교함 |
|------|---------|-------|
| **메타 하네스** (이 하네스 자체) | 강사 — 산출물 생성 도구 | 정교 — 분업·HITL·검증 풍부 |
| **수강생에게 제안하는 하네스** (산출물 §2~§4 내용) | 수강생 — 자기 회사에서 굴릴 것 | **심플** — 파일 2~4개 |

→ 메타가 산출하는 §2 토폴로지·§3 파일 목록은 **항상 단순한 형태**로 떨어진다.

## 3. 언제 트리거

### 자연어
- "이 케이스 Claude Code 하네스로 어떻게 만들지?"
- "시나리오 A 가이드 만들어줘"
- "회의록 Slack 변환기 Claude Code로 짜는 방법"

### 슬래시
```
/scenario-a <케이스 설명>
/scenario-a 회의록을 Slack 포맷으로 변환하는 에이전트, 난이도 하
/scenario-a                  # 인자 없으면 AskUserQuestion으로 좁힘
```

## 4. 트리거 안 되는 경우

| 발화 | 라우팅 |
|------|-------|
| "aiceo-4th-agent 메뉴 추가" | 시나리오 B/C (별도 하네스) |
| "에이전트 4안 비교 컨설팅" | /agent-solution-consultant |
| "단순 PRD 작성" | /plan |
| "회의록 정리 자체" | /meeting-plan-generator |

## 5. 어떻게

`/scenario-a` 커맨드 위임. 자세한 처리는 command.md 참조.

핵심 동작:
1. Step 0 — 케이스 명세 정규화 (필요 시 AskUserQuestion 1~2회)
2. Step 1 — 분업 subagent 2종 병렬 호출 (structurer + applier)
3. Step 2 — command 직접 합성 (7섹션)
4. Step 3 — grep 자가검증 + Write

## 6. 심플 제약 (산출물에 항상 강제)

- 파일 개수 상한: 하 2개 / 중 3개 / 상 4개
- subagent 종 수: 최대 2종 (인스턴스 병렬은 OK)
- HITL 게이트: 최대 2회 (하는 0회)
- 외부 의존: 하 0개 / 중 1개 / 상 2개
- §5 복붙 프롬프트: 30줄 이내
- 산출 언어: 한국어 (코드·식별자는 영어)
