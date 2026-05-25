---
name: scenario-c-generator
description: 수강생이 만들고 싶은 에이전트 케이스 1개를 받아 "aiceo-4th-agent에 자율형 에이전트 구성 가이드(시나리오 C)" 10섹션 마크다운 1장을 산출하는 메타 하네스. LangGraph DeepAgents(`createDeepAgent`) 또는 Claude Agent SDK 사용. aiceo-4th-agent 기존 deepagents 하네스(`src/lib/agent/harness/`)에 도구·서브에이전트를 추가하는 패턴을 강제한다. B와 달리 자율 분기·도구 동적 선택·멀티턴·계획 변경 가능. 다음 발화에 트리거된다 — "시나리오 C 가이드 만들어줘", "이 케이스 자율 에이전트로 만들면", "/scenario-c <케이스 설명>".
---

# scenario-c-generator — 시나리오 C 가이드 생성기

## 1. 무엇

수강생 케이스 1개 → 시나리오 C(자율형 에이전트, deepagents 기반) 구현 가이드 1장.

산출물: `./specs/scenario-c/<slug>/<today>/00_scenario_c.md`

## 2. 세 시나리오 비교

| 항목 | A (Claude Code) | B (aiceo-4th-agent 고정 파이프) | **C (자율 에이전트)** |
|------|----------------|------------------------------|---------------------|
| 사용자 환경 | Claude Code CLI | aiceo-4th-agent 웹앱 | aiceo-4th-agent 웹앱 |
| AI 호출 | 내장 LLM | ChatAnthropic 직접 invoke | **createDeepAgent 그래프** |
| 자율성 | 단일·분업 호출 | 고정 파이프라인 | **자율 도구 선택·계획 변경** |
| 자율 SDK | X | X | **deepagents / Claude Agent SDK** |
| 멀티턴 | 약함 | 약함 | **checkpointer + thread_id** |
| 도구 동적 선택 | X | X | **LLM 판단** |
| 분기 폭증 대응 | 어려움 | 어려움 (5+면 한계) | **강함** |
| 비결정성 | 낮음 | 낮음 | **높음 — 같은 입력도 다른 경로** |
| 비용 | 낮음 | 중간 | **높음 (1.5~5배)** |
| 테스트 난이도 | 낮음 | 중간 | **높음 — 모킹 필수, 환각 리스크** |

**C 선택 시점**: B가 분기 폭증·도구 자율 선택·멀티턴 대화·자율 탐색을 못 따라갈 때. **그 외 모든 경우는 B 권장** (over-engineering 방지).

## 3. aiceo-4th-agent C 관련 컨텍스트 (메타가 인지)

### 자율 에이전트 코어

```typescript
import { createDeepAgent } from "deepagents";
// createDeepAgent({ tools, subagents, instructions, checkpointer, model }) → 컴파일된 LangGraph 그래프
const graph = createDeepAgent({...});
await graph.stream(input, { configurable: { thread_id }, streamMode: ["messages", "tools"] });
```

### 디렉터리 패턴 (이미 깔린 구조 확장)

```
src/lib/agent/harness/
├── registry.ts                    — 토글의 단일 지점 (CLAUDE.md R2)
├── checkpointer.ts                — sqlite checkpointer (멀티턴)
├── tools/
│   ├── <newTool>.ts               — 새 도구 모듈 (1파일 = 1요소)
│   ├── <newTool>.meta.ts          — 도구 메타데이터
│   └── index.ts                   — HARNESS_TOOLS 배열에 1줄 등록
└── subagents/
    ├── <newSub>.ts                — 새 서브에이전트
    ├── <newSub>.meta.ts
    └── index.ts                   — HARNESS_SUBAGENTS 배열에 1줄 등록
```

### CLAUDE.md 절대 규칙 (C 구현 시 필수)

- **R1**: `@langchain/core` 버전 단일 정렬 (서로 다른 클래스 정체성 방지)
- **R2**: 하네스 토글은 `registry.ts`에서만, agent.ts·route.ts에 `if(toolEnabled)` 분기 금지
- **R3**: 멀티턴 = checkpointer + thread_id (수동 history 금지)
- **R4**: streamMode `"messages"` (텍스트 토큰용)
- **R5**: thinking·subagent 출력 본문 누출 차단 (chunkFilter.ts 격리)
- **R6**: globalThis 싱글톤 (HMR 시 그래프 재생성 방지)
- **R7**: route.ts에 `runtime = "nodejs"` (SQLite/네이티브)
- **R8**: 학습 지식 API 단정 금지 — pnpm install 후 실측·docs/notes 기록

### B와의 차이 — C에서만 가능한 4가지

1. **도구 동적 선택**: LLM이 `tools` 배열에서 상황에 맞는 도구 자율 선택
2. **서브에이전트 위임**: 메인 에이전트가 task를 서브에이전트에 위임
3. **계획 동적 변경**: 첫 결과 보고 다음 단계를 LLM이 결정
4. **멀티턴 reflection**: checkpointer로 대화 이력 누적, 자기 응답 reflection

## 4. 언제 트리거

### 자연어
- "이 케이스 자율 에이전트로 만들면?"
- "시나리오 C 가이드 만들어줘"
- "deepagents로 [케이스] 구현 방법"

### 슬래시
```
/scenario-c <케이스 설명>
/scenario-c 매출 이상치 자율 분석 — DB·뉴스·경쟁사 자율 탐색
/scenario-c                  # 인자 없으면 Discovery
```

## 5. 트리거 안 되는 경우

| 발화 | 라우팅 |
|------|-------|
| "Claude Code 하네스로 만들면?" | 시나리오 A |
| "고정 파이프라인 메뉴 추가하면?" | 시나리오 B |
| "에이전트 3안 비교" | `/agent-solution-consultant` |
| "PRD" | `/plan` |

## 6. 어떻게

`/scenario-c-generator` 위임. 핵심:
1. Step 0 — 명세 정규화 + **C 정당화 확인** (B로 안 되는 이유 명시 필수)
2. Step 1 — 분업 subagent 3종 병렬:
   - c-structurer (에이전트 토폴로지 + tools/subagents 파일 목록 + 골격)
   - c-applier (복붙·트리거+배포·외부 의존성·한계·B/A 다운그레이드)
   - c-cost-estimator (자율형 비용 분포 + 비결정성·환각 리스크 + B 대비 ROI)
3. Step 2 — command 10섹션 합성
4. Step 3 — grep 자가검증 + Write

## 7. 산출물 골격 (10섹션, B와 동일 + 일부 의미 차이)

```
§1 케이스 한 줄 정의 (+ C 정당화)
§2 에이전트 토폴로지 (도구·서브에이전트·메모리·체크포인터)
§3 생성·확장할 파일 목록 (registry.ts 1줄, tools/<>.ts, subagents/<>.ts)
§4 각 파일의 골격
§5 수강생 사용 가이드
  §5-A 코딩에이전트 복붙 프롬프트
  §5-B 트리거 + 배포 + 멀티턴 대화 진입 방법
§6 외부 연결 의존성 (Easy Path + 옵션 A/B/C + 권한 + 신호등)
§7 한계와 우회 (C 특화: 비결정성·환각·테스트·비용 통제)
§8 다음 단계 (B로 다운그레이드 / 더 강한 자율형 — 멀티 에이전트 등)
§9 자율형 LLM 호출 비용·성능 추정 (분포·최악 케이스 포함)
§10 시나리오 B 대비 C의 비용·가치 (ROI, B로 충분한지 재평가)
```

## 8. 심플 제약 (산출물에 강제)

- 추가 파일 4~7개 (도구 1~3 + 서브에이전트 1~2 + meta + registry 1줄)
- **deepagents·createDeepAgent 사용 강제** (B와 반대 — C의 차별)
- 자율 도구 수 3~6개 (10개 초과 시 분기 폭증 → 멀티 에이전트로)
- HITL: UI에서 0~2회 (메인 흐름은 자율)
- API 키 서버 전용, `NEXT_PUBLIC_` 금지
- R1~R8 모두 준수
- 한국어 산출, 코드·식별자 영어
- **B로 충분한지 재평가 강제** — §10에 "B로 가능" 임계점 체크 필수
