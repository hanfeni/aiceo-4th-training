---
description: 사용자가 가진 데이터(자연어 설명·RDBMS 스키마·CSV 헤더·기존 문서)를 받아 GraphDB/온톨로지 도입 컨설팅 5파일(00_brief·01_graph_proposals·02_benefit_cases·03_user_tasks·viewer.html)을 산출하는 메타 하네스. 비기술 야심가에게 적합성 신호등(GREEN/YELLOW/RED) + 구조 제안 3종(보수·표준·야심) + Competency Questions + PoC 가짜데이터+Cypher + 안티패턴 + 사용자 TASK 분해를 제공한다. 분업형 subagent 토폴로지(domain-extractor + fit-auditor + benefit-caster 단일 메시지 병렬). viewer.html은 Mermaid + vis-network 인터랙티브 그래프 포함.
argument-hint: <데이터 설명: 자연어 / DDL / CSV 헤더 / 문서 본문 / 혼합>
allowed-tools: Bash, Read, Write, Grep, Glob, Task, AskUserQuestion, WebSearch, WebFetch
---

# /graphdb-strategist — GraphDB·온톨로지 도입 컨설팅 하네스

## §0 정체성

### 무엇
사용자가 보유한 데이터(스키마·CSV·문서·자연어 설명 무엇이든)를 받아 **GraphDB/온톨로지 컨설팅 리포트 4장 + viewer.html 1장**을 산출.

산출 경로: `./specs/graphdb-strategist/<slug>/<today>/`
- `00_brief.md` — 신호등 진단 + 핵심 권고 1페이지
- `01_graph_proposals.md` — 구조 제안 3종(보수/표준/야심) + Mermaid + CQ
- `02_benefit_cases.md` — "이것도 가능?" 베네핏 케이스 5~7건 + PoC Cypher
- `03_user_tasks.md` — 사용자 TASK 분해 (조직·데이터·기술 3축)
- `viewer.html` — Pretendard + marked.js + Mermaid + vis-network 인터랙티브

### 핵심 설계 원칙

이 하네스의 본질은 **"비기술 야심가에게 그래프의 가치와 숙제를 동시에 정직하게 보여주는 것"**이다.

1. **Step 0 = 입력 정규화 + 비즈니스 목표 1줄** — 야심가는 "왜 그래프를 보고 있는가"가 핵심. 입력 데이터보다 목표가 먼저
2. **Step 1 = 사전 리서치** — 도메인 KG 벤치마크 1~2건 (consult-agent 패턴 답습)
3. **Step 2 = 분업 추출 (3 subagent 단일 메시지 병렬)** — extractor / fit-auditor / benefit-caster
4. **Step 3 = command 직접 합성** — 4 md 작성을 별도 subagent에 위임하지 않음
5. **Step 4 = viewer.html** — Mermaid(구조 다이어그램) + vis-network(드래그 가능 인터랙티브)
6. **Step 5 = 브라우저 자동 열림** (macOS `open`)

### 불변

1. 산출 5파일 (4 md + 1 html), `frontmatter` 8키 Contract 강제
2. **신호등 진단**(GREEN/YELLOW/RED) 반드시 §1에 포함 — "쓰지 마라"를 정직하게 말할 것
3. **구조 제안 3종 분량 균형**: 각 200~400자 + Mermaid 1개 + CQ 매핑 + 트레이드오프
4. **Competency Questions 5~10개** 반드시 도출
5. **PoC Cypher 쿼리 3~5개** 실행 가능 형태 (가짜데이터 CREATE + MATCH)
6. **안티패턴 섹션** 필수 — "이 케이스에서 조심할 함정 + RDBMS가 더 나은 경우"
7. **사용자 TASK는 3축**(조직 / 데이터 준비 / 기술 셋업)으로 분해, 각 축 3~5개
8. subagent 3개 모두 단일 메시지 안에서 Task로 병렬 호출
9. viewer.html은 오프라인 동작 (md base64 임베드, CDN은 폰트/marked/mermaid/vis-network만)
10. 한국어 산출

---

## §1 Step 0 — 입력 정규화 + 비즈니스 목표 확인

### 1-1. `$ARGUMENTS` 평가

```
비어 있음:                  → Full Discovery (3회 캐스케이드)
짧은 텍스트 (~50자):        → 보강 Discovery (목표·도메인만 확인)
긴 텍스트 (스키마/문서):    → 바로 진입 + 비즈니스 목표만 1회 확인
```

### 1-2. Full Discovery (3회 캐스케이드)

**Q1 — 무엇을 보고 있는가**
```
AskUserQuestion:
"GraphDB로 풀고 싶은 데이터를 어떤 형태로 가지고 있나요?"
- 자연어 설명만 (스키마 모름)
- RDBMS 스키마 (DDL/ERD 있음)
- 엑셀/CSV 헤더 샘플
- 기존 문서 (위키/노션)
- 여러 개 혼합
```

**Q2 — 비즈니스 목표 (가장 중요)**
```
AskUserQuestion:
"그래프로 무엇을 얻고 싶으신가요? (가장 가까운 1개)"
- 추천/연관 (사람·콘텐츠·상품 연결)
- 사기/이상 탐지 (수상한 패턴 찾기)
- 360도 뷰 (고객/제품의 전체 맥락)
- LLM 결합 (GraphRAG으로 챗봇 정확도↑)
- 규제/감사 추적 (계보·영향도 분석)
- 아직 명확하지 않음 (탐색 중)
```

**Q3 — 데이터 입력**
```
Q1 답변에 따라 분기:
- 자연어/CSV/문서: "데이터 설명을 자유롭게 적어주세요" (자유 텍스트)
- DDL: "CREATE TABLE 문 또는 ERD 텍스트를 붙여넣어주세요"
- 혼합: 가장 핵심인 것 하나만 우선
```

### 1-3. 입력 정규화 — 공통 yaml 스키마

어떤 형태로 들어오든 아래 yaml로 정리:

```yaml
case_name: <kebab-case-slug>          # 예: hospital-emr-graph
case_one_liner: <한 줄 요약>           # 예: "병원 EMR을 그래프로 옮겨 약물상호작용 탐지"
business_goal: <Q2 답변>               # 예: customer-360 / fraud / graphrag / ...
input_format: <Q1 답변>                # 예: rdbms-ddl / natural-language / csv-headers / docs
raw_input: |
  <원문 전체 — 정제 없이 그대로>
sensitivity:                          # 자동 추출
  - PII / financial / medical / none
known_systems:                        # 자동 추출 (있을 때만)
  - 예: Oracle, SAP, Salesforce
```

### 1-4. 사용자 컨펌

```
GraphDB 컨설팅 시작:
- 케이스: <case_one_liner>
- 비즈니스 목표: <business_goal>
- 입력: <input_format> (<원문 글자 수>자)
- 산출: 5파일 (4 md + viewer.html)
- 예상 소요: 90~120초 (3 subagent 병렬 + 합성 + viewer)
- 브라우저 자동 열림 (macOS)

진행할까요? (y/n)
```

---

## §2 Step 1 — 사전 리서치 (필수, 30~60초)

비기술 야심가에게 신뢰감을 주는 핵심 단계. 건너뛰지 않는다.

### 2-1. 리서치 항목 (모두 WebSearch)

해당 도메인의 **킬러 KG 사례**를 찾아 §4 베네핏 케이스의 신빙성을 보강한다.

```
검색 쿼리 (business_goal에 따라 분기):

[customer-360]
- "customer 360 knowledge graph case study <도메인>"
- "<업종> graph database 360 view ROI"

[fraud]
- "fraud detection knowledge graph <업종> 2025"
- "anti money laundering graph database case"

[recommendation]
- "recommendation graph database Cypher pattern <도메인>"

[graphrag]
- "GraphRAG <업종> LLM hallucination reduction 2025"
- "Microsoft GraphRAG enterprise case"

[compliance]
- "regulatory lineage graph database <업종>"

[탐색 중]
- "knowledge graph use case <도메인 키워드>"
```

### 2-2. 결과 사용처

- 02_benefit_cases.md의 각 케이스에 1줄 "유사 사례 출처" 인용
- 00_brief.md §최종 권고에 "동종 업계 사례 X건 발견"

리서치 결과는 별도 파일 저장 없이 본문에 인용.

---

## §3 Step 2 — 분업 추출 (3 subagent 병렬)

**단일 메시지 안에서 Task 3건을 동시 호출**한다. 직렬 호출 금지.

### 3-1. Task A — graphdb-domain-extractor

```
Task(subagent_type="graphdb-domain-extractor", prompt="""
입력 데이터에서 그래프 도메인 모델을 추출하라.

case_name: <case_name>
business_goal: <business_goal>
input_format: <input_format>
raw_input: |
  <raw_input>

산출 yaml 6섹션 (압축 텍스트):
1. entities — 엔티티 후보 5~12개 (이름·핵심속성·예상레코드수)
2. relationships — 관계 후보 5~15개 (from·to·동사·카디널리티·시간성)
3. attributes_to_lift — 노드로 승격할 속성 후보 (이유 1줄)
4. ambiguities — 모호한 부분 3~5개 (어떻게 처리할지 분기 옵션)
5. data_quality_risks — 입력 데이터 자체의 품질 리스크 (중복·결측·일관성)
6. domain_signals — 이 도메인에서 그래프가 빛날 신호 (핵심 관계 트리플 3~5개)
""")
```

### 3-2. Task B — graphdb-fit-auditor

```
Task(subagent_type="graphdb-fit-auditor", prompt="""
GraphDB 도입 적합성을 5축으로 1~5점 평가하라.

case_name: <case_name>
business_goal: <business_goal>
raw_input: |
  <raw_input>

평가 5축 (각 1~5점 + 근거 1~2줄):
A. 연결성 — 관계의 깊이·다중경로 패턴 빈도
B. 쿼리패턴 — 다단계 traversal / 패턴매칭 / 영향분석 비중
C. 진화성 — 스키마가 자주 바뀔 가능성 (그래프는 유리, RDBMS는 불리)
D. set-aggregation — 대규모 집계·OLAP 비중 (높으면 그래프 불리)
E. 규모 — 노드/엣지 예상 규모와 단일 머신 한계

산출 yaml 4섹션:
1. axis_scores — A~E 각 점수 + 근거 (총점 25점 만점)
2. signal — GREEN(20~25) / YELLOW(13~19) / RED(0~12)
3. anti_patterns_to_avoid — 이 케이스에서 빠질 함정 3~5개 (Neo4j 안티패턴 매핑)
4. when_not_to_use — RDBMS/DW/Document DB가 더 나은 케이스 명시 (있다면)
""")
```

### 3-3. Task C — graphdb-benefit-caster

```
Task(subagent_type="graphdb-benefit-caster", prompt="""
"이것도 가능해?" 베네핏 케이스 5~7건을 발굴하라.

case_name: <case_name>
business_goal: <business_goal>
raw_input: |
  <raw_input>

각 케이스는 비기술 야심가가 "와 이게 되네?" 할 만한 것.
GraphRAG / Fraud / Customer360 / Recommendation / Compliance / Lineage / Centrality 7 카테고리 매칭.

산출 yaml 3섹션:
1. benefit_cases — 5~7건 (각: 케이스명·"이것도 가능?" 1줄·왜 그래프여야 하는가·예상 Cypher 1줄·동종 사례 유무)
2. wow_factor_ranking — 비기술 의사결정자에게 가장 임팩트 클 케이스 3건 순위
3. graphrag_path — GraphRAG로 진화시 추가 가치 (LLM 환각 60%↓ 등 2025 트렌드 기반)
""")
```

### 3-4. 3 산출물 수신 + 합치

세 결과를 yaml로 모은다. 길면 `./specs/graphdb-strategist/<slug>/<today>/_raw/`에 임시 저장.

---

## §4 Step 3 — command 직접 합성 (4 md)

오케스트레이터가 직접 작성. subagent 위임 금지.

### 4-1. `00_brief.md` (1페이지 진단)

```markdown
---
slug: <case_name>
generated_at: <now_kst>
business_goal: <business_goal>
signal: <GREEN|YELLOW|RED>
total_score: <0~25>
recommended_proposal: <보수|표준|야심>
estimated_effort: <PoC X주 / 본구현 X개월>
generator: graphdb-strategist
---

# <case_name> — GraphDB 도입 진단 Brief

## §1 한 줄 진단
> <적합성 한 줄 — 예: "환자-약물-상호작용 그래프는 GreenLight. 단, 청구 집계는 그래프 밖에 둬야 함.">

## §2 신호등 (5축 평가)
| 축 | 점수 | 근거 |
| --- | --- | --- |
| 연결성 | X/5 | ... |
| 쿼리패턴 | X/5 | ... |
| 진화성 | X/5 | ... |
| set-aggregation | X/5 | ... |
| 규모 | X/5 | ... |
| **합계** | **XX/25** | **<signal>** |

## §3 핵심 권고
1. 추천 구조: <보수|표준|야심> (이유 1~2줄)
2. 첫 PoC 범위: <2주 안에 만들 수 있는 최소>
3. 절대 그래프에 넣지 말 것: <set-aggregation 등>

## §4 비즈니스 가치 Top 3
- 🥇 <wow_factor 1>
- 🥈 <wow_factor 2>
- 🥉 <wow_factor 3>

## §5 다음 행동 (사용자가 오늘 시작할 것)
- [ ] 03_user_tasks.md 읽고 데이터 담당자 정하기
- [ ] PoC용 샘플데이터 1만건 추출
- [ ] Neo4j Desktop 또는 AuraDB Free 가입

## §6 동종 업계 사례 (사전 리서치)
- <사례 1 + URL>
- <사례 2 + URL>
```

### 4-2. `01_graph_proposals.md` (구조 제안 3종)

```markdown
---
slug: <case_name>
generated_at: <now_kst>
generator: graphdb-strategist
proposals: 3
---

# 구조 제안 3종

## §1 도메인 모델 (공통 베이스)

extractor가 뽑은 entities·relationships 표.

| 엔티티 | 핵심 속성 | 예상 규모 |
| --- | --- | --- |

| 관계 | from → to | 카디널리티 | 시간성 |
| --- | --- | --- | --- |

## §2 Competency Questions (5~10개)

비기술 사용자가 "이 그래프로 이런 질문에 답할 수 있어야 한다"를 명시.

1. CQ1: ...
2. CQ2: ...
...

## §3 제안 1 — 보수 (Minimal LPG)

**컨셉**: 핵심 5~6개 노드 + 핵심 관계만. RDBMS와 병용.

**Mermaid**:
\`\`\`mermaid
graph LR
  A[Entity1] -->|REL| B[Entity2]
  ...
\`\`\`

**커버하는 CQ**: 1, 3, 5

**트레이드오프**:
- ✅ 학습 1주, PoC 2주 가능
- ✅ 기존 RDBMS 그대로 + 그래프는 "관계 인덱스" 역할
- ❌ GraphRAG·복잡 추론 불가
- 💰 인프라: Neo4j Community 무료 / AuraDB Free

## §4 제안 2 — 표준 (Domain Ontology)

**컨셉**: 도메인 온톨로지 수준. 8~12 노드 라벨 + 속성 노드 분리.

**Mermaid**: ...

**커버하는 CQ**: 1~7

**트레이드오프**:
- ✅ Customer 360 / 영향도 분석 / 추천 모두 가능
- ✅ 운영팀 1~2명 필요
- ❌ 스키마 거버넌스 필요 — 온톨로지 위원회 구성 필수
- 💰 인프라: Neo4j Enterprise (월 $X) 또는 AuraDB Professional

## §5 제안 3 — 야심 (GraphRAG-Ready Ontology + RDF 진화 경로)

**컨셉**: 표준 + GraphRAG 인덱스 + RDF/OWL 마이그레이션 옵션 + 추론 규칙.

**Mermaid**: ...

**커버하는 CQ**: 1~10 + "LLM이 답할 수 있는 자연어 질문"

**트레이드오프**:
- ✅ LLM 챗봇이 자연어로 질문 가능 (환각 60%↓)
- ✅ 컴플라이언스·추론 가능
- ❌ 학습곡선 가파름 (3~6개월 + 외부 컨설팅 권장)
- ❌ Day 1 ROI 안 나옴. 6~12개월 뷰
- 💰 인프라: Neo4j Enterprise + 벡터 DB(또는 Neo4j 5.x 벡터 인덱스) + LLM API

## §6 추천 매트릭스

| 조건 | 추천 |
| --- | --- |
| PoC 2주 안에 보여줘야 함 | 보수 |
| 운영팀 2명 확보 가능 | 표준 |
| LLM 챗봇 목표 + 6개월 여유 | 야심 |
```

### 4-3. `02_benefit_cases.md` (이것도 가능?)

```markdown
---
slug: <case_name>
generated_at: <now_kst>
generator: graphdb-strategist
benefit_cases: <N>
---

# 베네핏 케이스 — "이것도 가능해?"

## §1 베네핏 케이스 5~7건

각 케이스 형식:

### 케이스 N: <케이스명>

> 💬 **이것도 가능해?** "<자연어 질문 1줄>"

**왜 그래프여야 하는가**: RDBMS로는 N-hop JOIN이 폭발하지만 그래프는 O(N) traversal.

**작동 원리**: 1~2 문장.

**예상 Cypher**:
\`\`\`cypher
MATCH (a:Patient)-[:TAKES]->(:Drug)-[:INTERACTS_WITH]->(:Drug)<-[:TAKES]-(a)
RETURN a.id AS at_risk_patient
\`\`\`

**동종 사례**: <사전 리서치에서 찾은 URL 또는 회사명>

**비즈니스 임팩트**: "<수치>" (사례 출처 명시 또는 "추정")

---

(케이스 5~7건 반복)

## §2 PoC 가짜데이터 + 실행 가능 Cypher 3~5개

비기술 사용자가 Neo4j Browser에 그대로 붙여넣어 즉시 실행 가능한 코드.

### 목업 설계 원칙 (3 필수 조건 — 절대 깨지 말 것)

1. **입력 도메인 용어 그대로 사용** — extractor가 뽑은 엔티티명·관계명을 그대로. 일반 dummy(foo/bar/Entity1) 절대 금지
2. **한국어 로컬라이제이션** — 이름은 한국 성씨+이름(김환자·이의사), 주소는 한국 행정구역(서울 강남구), 회사는 한국 법인명. Faker ko_KR 감각
3. **베네핏 쿼리가 실제 결과를 반환하도록 설계** — §1 각 베네핏 케이스의 Cypher가 빈 결과가 아닌 구체적 매치를 반환해야 함. CREATE 데이터를 일부러 그렇게 짠다 (예: 약물상호작용 케이스는 실제로 상호작용 페어를 CREATE에 심어둠)

### Setup (CREATE) — 20행 기준 예시 (의료 도메인)
\`\`\`cypher
// 1) 베네핏 쿼리가 hit하도록 의도 설계된 가짜데이터
CREATE
  (p1:Patient {id: 'P001', name: '김환자', age: 67, region: '서울 강남구'}),
  (p2:Patient {id: 'P002', name: '이지영', age: 54, region: '서울 송파구'}),
  (d1:Drug {code: 'D-WAR', name: 'Warfarin', class: '항응고제'}),
  (d2:Drug {code: 'D-ASP', name: 'Aspirin', class: '항혈소판제'}),
  (d3:Drug {code: 'D-AMO', name: 'Amoxicillin', class: '항생제'}),
  (doc1:Doctor {license: 'L-12345', name: '박의사', dept: '심장내과'}),
  // 2) 베네핏 쿼리 #1(약물상호작용 환자)가 P001을 잡도록 의도
  (p1)-[:PRESCRIBED_BY {date: '2026-04-01'}]->(doc1),
  (p1)-[:TAKES {start: '2026-04-01'}]->(d1),
  (p1)-[:TAKES {start: '2026-04-15'}]->(d2),
  (d1)-[:INTERACTS_WITH {severity: 'high', evidence: 'KFDA-2024-381'}]->(d2),
  // 3) P002는 의도적으로 상호작용 없게 — 쿼리가 정확히 P001만 반환하도록
  (p2)-[:TAKES]->(d3);
\`\`\`

> 위 데이터로 §1의 베네핏 쿼리 #1 "약물상호작용 위험 환자 찾기"가 실행되면 정확히 `김환자(P001)` 1명이 반환된다. 사용자는 "어 이게 실제로 나오네!" 체감.

### Query 1 — <CQ1 매핑>
\`\`\`cypher
MATCH ...
RETURN ...;
\`\`\`

(Query 5개까지 반복)

## §3 GraphRAG 진화 시 추가 가치

2025-26 핵심 트렌드. Microsoft GraphRAG 등 사례 기반.

- LLM 환각 60% 감소 (Gartner 2025)
- 자연어 질문 → 자동 Cypher 변환 → 정확한 답변
- ...
```

### 4-4. `03_user_tasks.md` (사용자 TASK 분해)

```markdown
---
slug: <case_name>
generated_at: <now_kst>
generator: graphdb-strategist
axes: 3
---

# 사용자 TASK 분해 — 그래프 도입을 위한 숙제

비기술 야심가도 따라할 수 있도록 3축으로 분해.

## §1 조직 축 (사람과 역할)

| # | TASK | 누가 | 언제 | 산출물 |
| --- | --- | --- | --- | --- |
| O-1 | 그래프 챔피언 1명 지정 (도메인 전문가) | C-level | 2주 | 임명장 |
| O-2 | 데이터 오너 매핑 (각 엔티티별 책임자) | 챔피언 | 4주 | RACI 표 |
| O-3 | 외부 자문 결정 (Neo4j Pro Services 또는 사내 학습) | C-level | 6주 | 견적서 |
| O-4 | 온톨로지 위원회 구성 (제안 2·3 선택 시) | 챔피언 | 2개월 | 운영 규칙 |

## §2 데이터 축 (데이터 준비)

| # | TASK | 누가 | 언제 | 산출물 |
| --- | --- | --- | --- | --- |
| D-1 | 입력 데이터 1만건 샘플 추출 (PoC용) | 데이터팀 | 1주 | CSV |
| D-2 | PII/민감정보 마스킹 정책 | 보안팀 | 2주 | 정책 문서 |
| D-3 | 엔티티 ID 통합 (마스터 데이터) | 데이터팀 | 4주 | 통합 키 매핑 |
| D-4 | 관계 카디널리티 검증 (1:N? M:N?) | 도메인 전문가 | 4주 | 검증 리포트 |

## §3 기술 축 (인프라·툴)

| # | TASK | 누가 | 언제 | 산출물 |
| --- | --- | --- | --- | --- |
| T-1 | Neo4j AuraDB Free 가입 + PoC 데이터 적재 | 엔지니어 1명 | 1주 | Neo4j Browser 스샷 |
| T-2 | LOAD CSV 또는 APOC import 스크립트 | 엔지니어 | 2주 | import.cypher |
| T-3 | 모니터링·백업 정책 (본구현 시) | DevOps | 2개월 | 운영 가이드 |
| T-4 | 시각화 도구 선택 (Bloom / NeoDash) | 엔지니어 | 2개월 | 데모 대시보드 |

## §4 우선순위 추천 (첫 4주)

1. **Week 1**: O-1(챔피언) + D-1(샘플 추출) + T-1(AuraDB 가입)
2. **Week 2**: D-2(마스킹) + T-2(import) + 첫 Cypher 쿼리 실행
3. **Week 3**: §02의 PoC Cypher 5개 모두 실행 → 동료에게 시연
4. **Week 4**: GO/NO-GO 결정 → 본구현 또는 보류

## §5 안티패턴 경고 (조심할 함정)

extractor·auditor가 발견한 함정 + Neo4j 안티패턴 매핑.

1. **BLOB 저장 금지** — 파일·이미지는 S3/스토리지에 두고 URL만 노드 속성으로
2. **노드 ID 직접 노출 금지** — Neo4j 내부 ID는 재사용됨. 비즈니스 키 별도 운영
3. **거대 집계 쿼리 금지** — "월별 매출 합계" 같은 OLAP는 DW에 두고 그래프는 관계 탐색 전용
4. **노드 폭발 금지** — 하나의 엔티티를 수십만 노드로 잘게 쪼개지 말 것 (성능 저하)
5. (이 케이스 특화 함정 1~2개)

## §6 RDBMS가 더 나은 경우 (정직한 조언)

> auditor signal == RED 또는 YELLOW일 때만 이 섹션 출력.

- 안정적이고 단순한 분석 쿼리 → 데이터 웨어하우스가 ROI 우월
- 트랜잭션 ACID가 핵심 → RDBMS
- 단일 엔티티 CRUD만 많음 → Document DB
```

---

## §5 Step 4 — viewer.html 생성

### 5-1. HTML 골격

aiceo-4th-agent UI 토큰 답습 + Mermaid + vis-network 추가:

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title><case_name> — GraphDB 컨설팅</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css">
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>
  :root {
    --agent-500: #8b5cf6;
    --agent-50: #f5f3ff;
    --blue-500: #2194f3;
    --green-500: #16a34a;
    --green-50: #f0fdf4;
    --yellow-500: #ca8a04;
    --yellow-50: #fefce8;
    --red-500: #dc2626;
    --red-50: #fef2f2;
    --gray-50: #f7f7f7;
    --gray-100: #f2f2f2;
    --gray-200: #e6e6e6;
    --gray-800: #1a1a1a;
    --neutral-600: #6d767f;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Pretendard', sans-serif; background: var(--gray-50); color: var(--gray-800); }
  .layout { display: flex; min-height: 100vh; }
  .sidebar {
    width: 280px; background: white; border-right: 1px solid var(--gray-200);
    padding: 24px 16px; flex-shrink: 0;
  }
  .sidebar h1 { font-size: 16px; font-weight: 700; margin-bottom: 8px; }
  .sidebar .subtitle { font-size: 12px; color: var(--neutral-600); margin-bottom: 24px; }
  .signal {
    display: inline-block; padding: 6px 12px; border-radius: 6px;
    font-weight: 700; font-size: 13px; margin-bottom: 16px;
  }
  .signal-GREEN { background: var(--green-50); color: var(--green-500); border: 1px solid var(--green-500); }
  .signal-YELLOW { background: var(--yellow-50); color: var(--yellow-500); border: 1px solid var(--yellow-500); }
  .signal-RED { background: var(--red-50); color: var(--red-500); border: 1px solid var(--red-500); }
  .sidebar .group-title {
    font-size: 12px; font-weight: 600; color: var(--neutral-600);
    text-transform: uppercase; margin: 20px 0 8px;
  }
  .sidebar nav a {
    display: block; padding: 8px 12px; border-radius: 8px;
    color: var(--gray-800); text-decoration: none; font-size: 14px;
    margin-bottom: 4px; cursor: pointer;
  }
  .sidebar nav a:hover { background: var(--gray-100); }
  .sidebar nav a.active {
    background: var(--agent-50); color: var(--agent-500); font-weight: 600;
    border-left: 3px solid var(--agent-500);
  }
  .main {
    flex: 1; padding: 32px 48px; overflow-y: auto;
    max-width: calc(100vw - 280px);
  }
  .content { max-width: 920px; }
  .content h1 { font-size: 24px; margin-bottom: 16px; }
  .content h2 { font-size: 20px; margin: 24px 0 12px; padding-bottom: 8px; border-bottom: 1px solid var(--gray-200); }
  .content h3 { font-size: 16px; margin: 16px 0 8px; color: var(--agent-500); }
  .content p { margin: 8px 0; line-height: 1.7; }
  .content ul, .content ol { margin: 8px 0 8px 24px; line-height: 1.7; }
  .content code {
    background: var(--gray-100); padding: 2px 6px; border-radius: 4px;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px;
  }
  .content pre {
    background: var(--gray-800); color: #f0f0f0; padding: 16px;
    border-radius: 8px; overflow-x: auto; margin: 12px 0;
  }
  .content pre code { background: transparent; color: inherit; padding: 0; }
  .content table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 14px; }
  .content th, .content td { border: 1px solid var(--gray-200); padding: 8px 12px; text-align: left; }
  .content th { background: var(--gray-100); font-weight: 600; }
  .content blockquote {
    border-left: 4px solid var(--agent-500); background: var(--agent-50);
    padding: 12px 16px; margin: 12px 0; border-radius: 4px;
  }
  .header-bar {
    display: flex; align-items: center; gap: 16px;
    padding-bottom: 16px; margin-bottom: 24px;
    border-bottom: 1px solid var(--gray-200);
  }
  .badge {
    display: inline-block; padding: 2px 8px; border-radius: 4px;
    background: var(--agent-50); color: var(--agent-500); font-size: 12px; font-weight: 600;
  }
  #graph-canvas {
    width: 100%; height: 480px; border: 1px solid var(--gray-200); border-radius: 8px;
    background: white; margin: 16px 0;
  }
  .graph-hint { font-size: 12px; color: var(--neutral-600); margin-top: 4px; }
</style>
</head>
<body>
<div class="layout">
  <aside class="sidebar">
    <h1>GraphDB 컨설팅</h1>
    <div class="subtitle"><case_one_liner></div>
    <div class="signal signal-<SIGNAL>"><SIGNAL_LABEL> · <TOTAL>/25점</div>

    <div class="group-title">진단</div>
    <nav>
      <a data-md="00_brief.md" class="active">📋 Brief (1페이지)</a>
    </nav>

    <div class="group-title">구조 제안</div>
    <nav>
      <a data-md="01_graph_proposals.md">🔀 제안 3종 + CQ</a>
      <a data-action="graph">🌐 인터랙티브 그래프</a>
    </nav>

    <div class="group-title">베네핏</div>
    <nav>
      <a data-md="02_benefit_cases.md">💡 이것도 가능?</a>
    </nav>

    <div class="group-title">실행</div>
    <nav>
      <a data-md="03_user_tasks.md">✅ 사용자 TASK</a>
    </nav>
  </aside>

  <main class="main">
    <div class="header-bar">
      <h1 id="case-title"><case_name></h1>
      <span class="badge">graphdb-strategist</span>
    </div>
    <div id="content" class="content">로딩 중...</div>
  </main>
</div>

<script>
  // mermaid 초기화
  mermaid.initialize({ startOnLoad: false, theme: 'default' });

  const links = document.querySelectorAll('.sidebar nav a');
  const content = document.getElementById('content');

  // md 콘텐츠 base64 임베드 (오프라인 동작)
  const mdContents = {
    "00_brief.md": atob("<<BRIEF_B64>>"),
    "01_graph_proposals.md": atob("<<PROPOSALS_B64>>"),
    "02_benefit_cases.md": atob("<<BENEFITS_B64>>"),
    "03_user_tasks.md": atob("<<TASKS_B64>>"),
  };

  // 표준 제안의 그래프 데이터 (extractor 산출 → command가 채움)
  const graphData = {
    nodes: <<NODES_JSON>>,
    edges: <<EDGES_JSON>>,
  };

  async function renderMd(mdName) {
    let md = mdContents[mdName] || "콘텐츠 없음";
    // marked 파싱
    let html = marked.parse(md);
    content.innerHTML = html;
    // mermaid 코드 블록 후처리
    const mermaidBlocks = content.querySelectorAll('pre code.language-mermaid');
    let idx = 0;
    for (const block of mermaidBlocks) {
      const code = block.textContent;
      const id = 'mmd-' + (++idx);
      const { svg } = await mermaid.render(id, code);
      block.parentElement.outerHTML = '<div class="mermaid-rendered">' + svg + '</div>';
    }
    links.forEach(a => a.classList.toggle('active', a.dataset.md === mdName));
  }

  function renderGraph() {
    content.innerHTML = `
      <h1>인터랙티브 도메인 그래프 (표준 제안)</h1>
      <p class="graph-hint">노드를 드래그하면 이동, 스크롤로 줌. extractor가 추출한 엔티티·관계.</p>
      <div id="graph-canvas"></div>
    `;
    const container = document.getElementById('graph-canvas');
    const data = {
      nodes: new vis.DataSet(graphData.nodes),
      edges: new vis.DataSet(graphData.edges),
    };
    const options = {
      nodes: {
        shape: 'dot', size: 24,
        font: { size: 14, face: 'Pretendard' },
        color: { background: '#8b5cf6', border: '#7c3aed', highlight: { background: '#a78bfa', border: '#7c3aed' } },
      },
      edges: {
        arrows: 'to',
        font: { size: 11, face: 'Pretendard', align: 'middle' },
        color: { color: '#94a3b8', highlight: '#8b5cf6' },
        smooth: { type: 'continuous' },
      },
      physics: { stabilization: { iterations: 200 } },
      interaction: { hover: true, navigationButtons: true, zoomView: true },
    };
    new vis.Network(container, data, options);
    links.forEach(a => a.classList.remove('active'));
    const graphLink = document.querySelector('[data-action="graph"]');
    if (graphLink) graphLink.classList.add('active');
  }

  links.forEach(a => {
    a.addEventListener('click', (e) => {
      e.preventDefault();
      if (a.dataset.action === 'graph') {
        renderGraph();
      } else if (a.dataset.md) {
        renderMd(a.dataset.md);
      }
    });
  });

  // 초기 렌더
  renderMd('00_brief.md');
</script>
</body>
</html>
```

### 5-2. 치환 자리표시자

| 자리표시자 | 채울 값 |
| --- | --- |
| `<case_one_liner>` | §1-3에서 정규화한 케이스 한 줄 |
| `<case_name>` | slug |
| `<SIGNAL>` | GREEN / YELLOW / RED (대문자) |
| `<SIGNAL_LABEL>` | "🟢 GREEN" / "🟡 YELLOW" / "🔴 RED" |
| `<TOTAL>` | 5축 합계 점수 (0~25) |
| `<<BRIEF_B64>>` | `00_brief.md`을 base64 인코딩 |
| `<<PROPOSALS_B64>>` | `01_graph_proposals.md` |
| `<<BENEFITS_B64>>` | `02_benefit_cases.md` |
| `<<TASKS_B64>>` | `03_user_tasks.md` |
| `<<NODES_JSON>>` | extractor entities → vis-network nodes (id·label·group) |
| `<<EDGES_JSON>>` | extractor relationships → vis-network edges (from·to·label) |

**vis-network 데이터 변환 규칙**:

```javascript
// extractor가 반환한 yaml:
//   entities: [{name: 'Patient', ...}, {name: 'Drug', ...}]
//   relationships: [{from: 'Patient', to: 'Drug', verb: 'TAKES'}]

// 변환:
nodes = entities.map((e, idx) => ({
  id: e.name,
  label: e.name,
  title: e.핵심속성?.join(', ') || '',
}));
edges = relationships.map(r => ({
  from: r.from,
  to: r.to,
  label: r.verb,
  arrows: 'to',
}));
```

### 5-3. Base64 인코딩 (Bash)

```bash
BRIEF_B64=$(base64 < "$base/00_brief.md" | tr -d '\n')
PROPOSALS_B64=$(base64 < "$base/01_graph_proposals.md" | tr -d '\n')
BENEFITS_B64=$(base64 < "$base/02_benefit_cases.md" | tr -d '\n')
TASKS_B64=$(base64 < "$base/03_user_tasks.md" | tr -d '\n')
```

치환 후 `Write "$base/viewer.html"`.

---

## §6 Step 5 — 브라우저 자동 열림

```bash
# macOS
open "$base/viewer.html"

# 사용자에게 안내
echo "📊 컨설팅 리포트 5파일 생성 완료"
echo "📁 경로: $base/"
echo "🌐 viewer.html이 기본 브라우저에서 열렸습니다."
```

---

## §7 자가검증 체크리스트

산출 완료 보고 전 반드시 grep으로 확인.

```bash
# 1. 5파일 존재
ls "$base"/{00_brief,01_graph_proposals,02_benefit_cases,03_user_tasks}.md "$base/viewer.html"

# 2. 신호등 일관성
brief_signal=$(grep '^signal:' "$base/00_brief.md" | awk '{print $2}')
viewer_signal=$(grep -o 'signal-[A-Z]*' "$base/viewer.html" | head -1)
[[ "$viewer_signal" == "signal-$brief_signal" ]] || echo "FAIL: signal 불일치"

# 3. 구조 제안 3개 모두 존재
grep -c '^## §[3-5] 제안' "$base/01_graph_proposals.md"   # 3이어야 함

# 4. CQ 5개 이상
grep -c '^[0-9]*\. CQ' "$base/01_graph_proposals.md"      # ≥5

# 5. PoC Cypher 블록 3개 이상
grep -c '^```cypher' "$base/02_benefit_cases.md"          # ≥3

# 6. 사용자 TASK 3축 모두 존재
grep -c '^## §[1-3] .축' "$base/03_user_tasks.md"         # 3

# 7. viewer.html에 vis-network·mermaid 모두 로드
grep -q "vis-network" "$base/viewer.html" || echo "FAIL: vis-network 누락"
grep -q "mermaid" "$base/viewer.html" || echo "FAIL: mermaid 누락"

# 8. RED 신호일 때 §6 RDBMS 권고 섹션 존재
if [[ "$brief_signal" == "RED" ]]; then
  grep -q "RDBMS가 더 나은" "$base/03_user_tasks.md" || echo "FAIL: RED인데 대안 권고 누락"
fi
```

7개 항목 모두 통과해야 사용자에게 완료 보고.

---

## §8 완료 보고 템플릿

```
✅ GraphDB 컨설팅 완료

🚦 진단: <SIGNAL> (<TOTAL>/25점)
🎯 추천 구조: <보수|표준|야심>
📋 베네핏 케이스: <N>건 발굴
✅ 사용자 TASK: <조직 N + 데이터 N + 기술 N>건

📁 산출물 5파일:
  - 00_brief.md (1페이지 진단)
  - 01_graph_proposals.md (구조 3종 + CQ)
  - 02_benefit_cases.md (이것도 가능? + Cypher)
  - 03_user_tasks.md (TASK 분해)
  - viewer.html (인터랙티브 뷰어 — 브라우저 자동 열림)

🌐 viewer.html이 기본 브라우저에서 열렸습니다. 사이드바에서 항목 전환 + "인터랙티브 그래프" 메뉴로 노드 드래그·줌 가능합니다.

다음 단계 권장:
1. Brief §3 핵심 권고 확인
2. 03_user_tasks.md의 Week 1 항목부터 시작
3. PoC Cypher를 Neo4j AuraDB Free에서 직접 실행해보기
```

---

## §9 트리거 발화 매핑 (skill에서 자동 트리거)

다음 발화에 이 command 트리거:

- "GraphDB 컨설팅해줘"
- "우리 데이터 그래프DB로 옮기면"
- "이 스키마 온톨로지로 짜줘"
- "지식그래프 도입 검토"
- "GraphRAG 도입할까"
- "이 데이터 그래프로 만들면 뭐가 좋아"
- "/graphdb-strategist <데이터 설명>"
- "/graphdb <데이터 설명>" (별칭)

---

## §10 다른 하네스와의 관계

| 하네스 | 역할 분담 |
| --- | --- |
| /consult-agent | 에이전트 요청 컨설팅 (그래프 아님) |
| /scenario-all-generator | 4-시나리오 합본 (LLM 에이전트 구현) |
| /reverse | 기존 코드 역공학 |
| /plan-t1/t2/t3 | 신규 기능 기획 |
| **/graphdb-strategist** | **데이터 → GraphDB 도입 컨설팅** (이 하네스) |

겹치는 영역: 없음. 이 하네스는 "데이터 구조 컨설팅" 전용.

연계 사용 시나리오:
- 사용자가 `/graphdb-strategist`로 표준안 채택 → 그 결과를 `/scenario-b-generator`에 입력 → aiceo-4th-agent에 GraphRAG 메뉴 추가
