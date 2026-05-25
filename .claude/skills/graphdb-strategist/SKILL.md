---
name: graphdb-strategist
description: 사용자가 가진 데이터(자연어 설명·RDBMS DDL·CSV 헤더·기존 문서 무엇이든)를 받아 GraphDB·온톨로지 도입 컨설팅 5파일(00_brief·01_graph_proposals·02_benefit_cases·03_user_tasks·viewer.html)을 산출하는 하네스. 비기술 야심가에게 적합성 신호등(GREEN/YELLOW/RED) + 구조 제안 3종(보수·표준·야심) + Competency Questions + PoC 가짜데이터+실행가능 Cypher + 안티패턴 경고 + 사용자 TASK 분해(조직·데이터·기술 3축)를 제공한다. viewer.html은 Mermaid + vis-network 인터랙티브 그래프 포함, 브라우저 자동 열림. 분업형 subagent 토폴로지(domain-extractor + fit-auditor + benefit-caster 단일 메시지 병렬). 다음 발화에 트리거된다 — "GraphDB 컨설팅해줘", "우리 데이터 그래프DB로 옮기면", "이 스키마 온톨로지로 짜줘", "지식그래프 도입 검토", "GraphRAG 도입할까", "이 데이터 그래프로 만들면 뭐가 좋아", "/graphdb-strategist <데이터 설명>", "/graphdb <데이터 설명>".
---

# graphdb-strategist — GraphDB·온톨로지 도입 컨설팅 하네스

## 무엇을 하는가

사용자가 보유한 데이터(자연어 설명·RDBMS DDL·CSV 헤더·기존 문서 무엇이든)를 받아, 비기술 야심가도 즉시 의사결정에 쓸 수 있는 GraphDB·온톨로지 도입 컨설팅 5파일을 자동 생성한다:

1. **00_brief.md** — 신호등 진단(GREEN/YELLOW/RED) + 핵심 권고 1페이지
2. **01_graph_proposals.md** — 구조 제안 3종(보수·표준·야심) + Mermaid + Competency Questions
3. **02_benefit_cases.md** — "이것도 가능?" 베네핏 케이스 5~7건 + PoC 가짜데이터 + 실행 가능 Cypher 3~5개
4. **03_user_tasks.md** — 사용자가 해야 할 TASK 분해 (조직·데이터·기술 3축)
5. **viewer.html** — Pretendard + marked.js + Mermaid + vis-network 인터랙티브 뷰어 (브라우저 자동 열림)

산출 경로: `./specs/graphdb-strategist/<slug>/<today>/`

## 언제 트리거되는가

직접 트리거:
- `/graphdb-strategist <데이터 설명>`
- `/graphdb <데이터 설명>` (별칭)

자연어 트리거:
- "GraphDB 컨설팅해줘"
- "우리 데이터로 그래프DB 만들면 뭐가 좋을까"
- "이 스키마를 그래프로 옮기면"
- "온톨로지 짜줘", "지식그래프 도입 검토"
- "GraphRAG 도입할까", "Neo4j 쓸 가치가 있나"
- "이 데이터 구조를 그래프로 그려줘"

## 트리거되지 않는 경우

- 신규 LLM 에이전트 컨설팅 → `/consult-agent` 또는 `/scenario-all-generator`
- 기존 코드 역공학 → `/reverse`
- 신규 기능 기획 → `/plan` (Tier 1/2/3)
- 그래프 알고리즘 이론 질문 → 그냥 대화

## 어떻게 동작하는가

이 스킬이 트리거되면 `/graphdb-strategist` 커맨드의 실행 순서를 그대로 수행한다:

1. **Step 0 — 입력 정규화** — Discovery 인터뷰 (입력이 모호하면 AskUserQuestion 캐스케이드로 데이터 형태·비즈니스 목표 1줄 확인)
2. **Step 1 — 사전 리서치** — 도메인별 KG 벤치마크 사례 1~2건 WebSearch (consult-agent 패턴)
3. **Step 2 — 분업 추출 (3 subagent 단일 메시지 병렬)**:
   - `graphdb-domain-extractor` — 엔티티·관계·속성·모호성·도메인 신호 6섹션 yaml
   - `graphdb-fit-auditor` — 5축 적합성(연결성·쿼리패턴·진화성·set-aggregation·규모) 점수 + 신호등 + 안티패턴 + "쓰지 마라" 케이스
   - `graphdb-benefit-caster` — "이것도 가능?" 베네핏 케이스 5~7건 + wow factor Top 3 + GraphRAG 진화 경로
4. **Step 3 — command 직접 합성** — 4 md 파일 작성 (subagent 위임 금지)
5. **Step 4 — viewer.html 생성** — Pretendard + marked + Mermaid + vis-network. md는 base64 임베드, 인터랙티브 그래프는 extractor 산출 → vis-network nodes/edges 변환
6. **Step 5 — 브라우저 자동 열림** (macOS `open`)
7. **Step 6 — 자가검증 7체크** — 신호등 일관성, CQ 5+개, Cypher 3+개, TASK 3축, vis-network·mermaid 로드 등

입력이 비어 있으면 Discovery 인터뷰(데이터 형태·비즈니스 목표·실제 입력)로 3회 물어본 뒤, 채워지면 질문 없이 끝까지 진행한다.

## 핵심 설계 원칙

- **신호등 게이트 강제** — "그래프 쓰지 마라"를 정직하게 말해주는 게 이 하네스의 가장 큰 가치
- **CQ(Competency Questions) 5~10개** — NeOn 온톨로지 방법론 표준
- **PoC 목업 3 필수 조건**:
  1. 입력 도메인 용어 그대로 사용 (일반 dummy 금지)
  2. 한국어 로컬라이제이션 (이름·주소·회사명 한국식)
  3. 베네핏 Cypher가 실제 결과 반환하도록 CREATE 데이터 의도 설계
- **3 subagent 단일 메시지 병렬** — 직렬 호출 금지

## 다른 하네스와의 관계

| 하네스 | 역할 |
| --- | --- |
| `/consult-agent` | 에이전트 요청 컨설팅 (그래프 아님) |
| `/scenario-all-generator` | 4-시나리오 합본 (LLM 에이전트 구현) |
| `/reverse` | 기존 코드 역공학 |
| `/plan-t1/t2/t3` | 신규 기능 기획 |
| **/graphdb-strategist** | **데이터 → GraphDB 도입 컨설팅** (이 하네스) |

연계 사용 시나리오:
- `/graphdb-strategist`로 표준 구조 채택 → 그 결과를 `/scenario-b-generator`에 입력 → aiceo-4th-agent에 GraphRAG 메뉴 추가

상세 계약은 `.claude/commands/graphdb-strategist.md`를 따른다.
