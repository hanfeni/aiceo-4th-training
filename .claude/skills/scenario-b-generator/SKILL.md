---
name: scenario-b-generator
description: 수강생이 만들고 싶은 에이전트 케이스 1개를 받아 "aiceo-4th-agent에 메뉴 추가 — 고정 파이프라인 구현 가이드(시나리오 B)" 10섹션 마크다운 1장을 산출하는 메타 하네스. 자율형(Claude Agent SDK·LangGraph DeepAgents) 사용 안 함, 개별 LLM 호출을 고정 파이프라인으로 엮는다. aiceo-4th-agent 코드베이스(Next.js 16 + React 19 + TypeScript + LangChain ChatAnthropic/ChatOpenAI + better-sqlite3) 컨텍스트를 사전 인지하고 메뉴 1개를 정확히 추가하는 가이드를 작성. 다음 발화에 트리거된다 — "시나리오 B 가이드 만들어줘", "이 케이스 aiceo-4th-agent 메뉴로 추가하면", "/scenario-b <케이스 설명>".
---

# scenario-b-generator — 시나리오 B 가이드 생성기

## 1. 무엇

수강생 케이스 1개 → 시나리오 B(aiceo-4th-agent 메뉴 추가, 고정 파이프라인) 구현 가이드 1장.

산출물: `./specs/scenario-b/<slug>/<today>/00_scenario_b.md`

## 2. 두 시나리오 비교 (A와 B의 본질적 차이)

| 항목 | 시나리오 A | 시나리오 B (본 하네스) |
|------|----------|---------------------|
| 사용자 환경 | Claude Code (1인용 CLI) | aiceo-4th-agent 웹앱 (팀 공유) |
| AI 호출 방식 | Claude Code 내장 LLM | LangChain ChatAnthropic/ChatOpenAI 직접 invoke |
| 자율성 | 단일·분업 LLM 호출 | **고정 파이프라인** (자율 판단 없음) |
| 자율형 SDK | 사용 X | **Claude Agent SDK·LangGraph DeepAgents 사용 안 함** (C와의 차이) |
| 트리거 | 슬래시·CLI·자연어 | 웹 UI 버튼·API 호출·스케줄러 |
| 상태 저장 | 로컬 파일 (specs/) | SQLite·Neo4j·OpenSearch (사내 DB 가능) |
| 다중 사용자 | 불가 | 가능 (인증·세션) |
| 배포 | 없음 (로컬 only) | next build → 사내 호스팅 |

**B 선택 시점**: 팀 공유·자동 게시·이력 관리·API 통합·SLA가 필요할 때. 단, 자율 판단·분기 폭증·도구 자율 선택이 필요하면 C로.

## 3. aiceo-4th-agent 프로젝트 컨텍스트 (메타가 알고 있는 정보)

**스택**:
- Next.js 16 (App Router) + React 19 + TypeScript + Tailwind 4
- LangChain (`@langchain/anthropic`, `@langchain/openai`, `@langchain/core`)
- zustand (상태), better-sqlite3 (저장), Neo4j (그래프), OpenSearch (검색)
- 패키지 매니저: pnpm

**디렉터리 구조**:
```
src/app/(main)/<menu-slug>/page.tsx       — UI 페이지
src/app/api/<menu-slug>/route.ts          — API 라우트
src/components/<menu-slug>/<Component>.tsx — UI 컴포넌트
src/lib/<menu-slug>/<helper>.ts           — 비즈니스 로직
src/store/<menu-slug>Store.ts             — zustand 스토어 (선택)
```

**메뉴 추가 시 필수 등록**:
- `src/app/(main)/AgentNav.tsx` 에 메뉴 항목 추가 (좌측 네비)

**기존 메뉴 (참고)**: chat, custom-agent, dart, data-load, graph-lab, harness, index-lab, meta-lab, search-lab, store-explorer, workspace

**중요 규칙 (CLAUDE.md 발췌)**:
- API 키는 서버 전용, `NEXT_PUBLIC_` 접두사 절대 금지
- route.ts 상단에 `export const runtime = "nodejs"` + `export const dynamic = "force-dynamic"`
- 1파일 1000줄 초과 금지
- 시나리오 B는 **deepagents 사용 안 함**, ChatAnthropic/ChatOpenAI 직접 invoke

## 4. 언제 트리거

### 자연어
- "이 케이스 aiceo-4th-agent 메뉴로 만들면?"
- "시나리오 B 가이드 만들어줘"
- "고정 파이프라인으로 [케이스] 메뉴 추가하는 방법"

### 슬래시
```
/scenario-b <케이스 설명>
/scenario-b 일일 매출 보고서 메뉴, 사내 DB + 환율 API
/scenario-b                  # 인자 없으면 AskUserQuestion으로 좁힘
```

## 5. 트리거 안 되는 경우

| 발화 | 라우팅 |
|------|-------|
| "Claude Code 하네스로 만들면?" | 시나리오 A (`/scenario-a`) |
| "자율 에이전트로 만들면?" | 시나리오 C (`/scenario-c`) |
| "에이전트 4안 비교 컨설팅" | `/agent-solution-consultant` |
| "PRD 작성" | `/plan` |

## 6. 어떻게

`/scenario-b-generator` 커맨드 위임. 핵심 동작:
1. Step 0 — 케이스 명세 정규화 (필요 시 AskUserQuestion 1~2회)
2. Step 1 — 분업 subagent 3종 병렬 호출:
   - b-structurer (파이프라인 다이어그램 + 컴포넌트 파일 목록 + 골격)
   - b-applier (복붙 프롬프트 + 메뉴 트리거/배포 + 외부 의존성 + 한계 + A·C 트리거)
   - b-cost-estimator (LLM 호출 패턴 분석 → 비용·지연 추정 + A 대비 ROI)
3. Step 2 — command 직접 10섹션 합성
4. Step 3 — grep 자가검증 + Write

## 7. 산출물 골격 (10섹션, A의 8섹션 + 2개 신설)

```
§1 케이스 한 줄 정의
§2 파이프라인 다이어그램 (LLM 노드·DB·UI 컴포넌트)
§3 생성할 파일 목록 (aiceo-4th-agent 경로)
§4 각 파일의 골격 (page/api route/LLM caller/prompt)
§5 수강생 사용 가이드
  §5-A 코딩에이전트 복붙 프롬프트
  §5-B 메뉴 트리거 + 배포 방법
§6 외부 연결 의존성 (Easy Path + 옵션 A/B/C + 권한 요청 + 신호등)
§7 한계와 우회
§8 다음 단계 (A 다운그레이드 / C 업그레이드 양방향)
§9 LLM 호출 비용·성능 추정 (신설)
§10 시나리오 A 대비 B의 비용·가치 (신설, ROI)
```

§9·§10이 B의 차별 가치. 비용·ROI 명시 없이 B를 권하면 수강생이 과도 엔지니어링.

## 8. 심플 제약 (산출물에 항상 강제)

- 메뉴당 파일 개수: **4~7개** (page.tsx + api route.ts + 1~3 helper + 0~2 component)
- LLM 호출 단계: **2~5개** (자율 분기 금지, 고정 순서)
- HITL: 최대 2회 (UI 단계로)
- 외부 의존: 케이스에 따라 (필수만 카운트)
- 산출 한국어, 코드·식별자 영어
- **deepagents·LangGraph 그래프 사용 금지** (C와 명확히 구분)
- API 키는 서버 전용, `NEXT_PUBLIC_` 금지
