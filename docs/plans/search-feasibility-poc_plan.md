# 구현 계획: 검색 문서 Feasibility PoC

> ⚠️ **2026-05-19 — 이 슬라이스/TDD 실행 계획은 폐기(SUPERSEDED).**
> 사용자 결정: 이 강의는 수강생이 코드를 직접 짜는 게 아니라
> **"코딩에이전트에게 시키는" 패러다임**이다. 따라서 산출물은
> `poc/*.py` 실행 코드·S0~S5 슬라이스·TDD가 아니라 **코딩에이전트에
> 복붙하는 완성 프롬프트 3종**(bootstrap/ 형식)이다.
> 폐기 대상은 §2 슬라이스 분해·TDD·1슬라이스=1커밋·실행 코드 계획.
> 보존 대상(프롬프트 설계 근거로 격하)은 §1 불변식(architect
> AI1~AI8), PRD §1의 6차 데이터 검증·라이선스·함정·차원 락인
> 리스크 — 이것들은 "프롬프트에 박을 가드레일"의 출처로 살아있다.
> 강의 노출 산출물은 `bootstrap/` 옆 3단계 프롬프트뿐이며, 아래
> 원문은 프롬프트가 명령해야 할 제약의 근거로만 참조한다.

> Based on `docs/PRD.md` §1 v1.0 / `docs/use-cases/search-feasibility-poc_use_cases.md` UC-1~10 / `docs/qa/search-feasibility-poc_test_cases.md` 67 TC.
> Architect: **PASS** (1회 재제출) + AI1~AI4 STRUCTURAL + 보안 사전리뷰 슬라이스 삽입 명령.
> (인덱싱 스택 OpenSearch 재정의로 AI5~AI8 + S3 3분할 추가됨 — PRD v1.1 참조)
> 작성: 2026-05-18 KST / D-4 (강의 2026-05-22).
> 브랜치: `feat/search-feasibility-poc`.

## 1. 불변식 (모든 슬라이스 준수 — architect AI1~AI4)

| ID | 불변식 | 적용 |
|----|--------|------|
| **AI1** | UC-1-X2 백엔드 전환 = gate→orchestrator 경로로만, indexer/search 독자 fallback 금지, `poc/README.md` 명문화 | S0, S3, S5 |
| **AI2** | 보안 사전리뷰 슬라이스(S0b)를 S0 직후·collect 착수 전 배치, `.gitignore` vs 실 산출물 경로 정합 + 리포트 인용 길이상한 | S0b (collect 차단 게이트) |
| **AI3** | `Chunk.text_hash` 입력 = 정제 후 본문, collect→정제→spec→chunk 순서 불변식 | S1, S2 |
| **AI4** | `report.py` 600줄 접근 시 `report/{spec_table,matrix,verdict}.py` 분할 | S4 |
| 전역 | 1슬라이스=1커밋 / TDD(tests→impl→verify) / 1000줄 금지 / type hints·f-string / `[FX]` CI·`[NET]` 라이브 스모크 분리 | 전 슬라이스 |
| 부록 B | 정량지표(nDCG/MRR/Recall@k) 금지 / 정성 한계 문구 종결조건 / 부정 결과 왜곡·은폐 금지 | S3b·S4·S5 |

## 2. 구현 슬라이스 (8개) — 의존성 순서

순서: **S0 → S0b → S1 → S2 → S3 → S3b → S4 → S5**

### S0 — 임베딩 키 게이트 + 모델 + 5수집기 10건 스파이크
- 파일: `poc/models.py`, `poc/embedding.py`(OpenAI/Claude/bge-m3), `poc/gate.py`(전역단일 1회결정), `poc/collectors/base.py`(ABC `collect(spike=False)`), `poc/collectors/{sangkwon,medical,finance,legal,policy}.py`(스파이크만), `poc/run_feasibility.py`(스켈레톤), `poc/README.md`(AI1 명문화), `requirements.txt`, `run_poc.sh`(루트)
- UC/AC: UC-1 P1~5/A1/E1/E2/X1, UC-6 P1·7 → AC-4, AC-1(부분)
- TC(P0): TC-1.1, TC-1.2, TC-1.3, TC-1.8
- TDD: `[FX] test_gate.py`, `test_models.py`(GateDecision 키값 미포함), `test_collectors_spike.py`
- 사전리뷰: 🔴 security 필수 / 시간 3~4h / 병렬 ❌ 기반

### S0b — 배포 안전 보안 사전리뷰 게이트 (collect 전 — AI2)
- 파일: `poc/security_gate.py`(`.gitignore` vs 산출물 경로 정합 + 스테이징 스캔 + `clip_quote`), `poc/report.py`(스텁 — 인용 상한 상수만), `poc/README.md`(AI2 명문화)
- UC/AC: UC-10 P1~4/E1/X1/X2, UC-7-E1 → AC-8, NFR-5
- TC(전부 P0): TC-10.1, TC-10.2, TC-10.4, TC-10.5, TC-10.3, TC-7.3, TC-11.1
- TDD: `[FX] test_security_gate.py`
- 완료: 미통과 시 오케스트레이터가 collect 진입 차단 (S0→S0b→collect 강제)
- 사전리뷰: 🔴 security 필수 (AI2 직접 명령) / 시간 2~3h / 병렬 ❌

### S1 — 5수집기 본수집 + 정제(UC-7/8) + collect→정제 불변식
- 파일: `poc/collectors/{sangkwon,medical,finance,legal,policy}.py` 본수집, `poc/cleaner.py`(HTML+캡션 정규식, policyNewsView 강제·pressReleaseView 금지)
- UC/AC: UC-6·7·8 전부, UC-1-A2 → AC-1, FR-1.x, NFR-1/6, AI3
- TC(P0): TC-6.2, TC-6.7, TC-7.1, TC-7.2, TC-7.4, TC-7.5, TC-8.1, TC-8.2, TC-8.3 / `[NET]`: TC-6.1, TC-6.4
- TDD: `[FX] test_cleaner.py`, `test_collect_policy_news.py`, `test_collect_filter.py`
- 완료: 정제 후 본문만 S2 입력(AI3) / collect 후 `git status --ignored` S0b 재검증
- 사전리뷰: 🔴 security 필수 (S0b PASS 선결) / 시간 **6~8h 최장 NET** / 병렬 ✅ **5-에이전트 병렬 (D-4 핵심)**

### S2 — 3축 스펙 + 청킹(1000/overlap100) + text_hash (AI3 뒷단계)
- 파일: `poc/spec.py`(글자/토큰/형태소 평균·총규모·버전·이상치·총청크), `poc/chunker.py`(1000토큰 슬라이딩 overlap100, text_hash=정제 후 본문, 통짜벡터 금지, single_chunk_reason)
- UC/AC: UC-2·5 전부 → AC-2, AC-3, FR-2/3.x, NFR-3/4, AI3
- TC(P0): TC-2.1, TC-2.2, TC-5.1, TC-5.2, TC-5.4, TC-5.5, TC-5.6
- TDD: `[FX] test_spec.py`(known-answer), `test_chunker.py`(text_hash 정제후 회귀)
- 사전리뷰: 🟡 architect 권장 (AI3) / 시간 4~5h / 병렬 🟡 2-에이전트 부분

### S3 — 인덱싱(BM25 kiwi + 임베딩) + 검색
- 파일: `poc/indexer.py`(BM25 rank-bm25+kiwi + 임베딩 embedding.py 호출 AI1, text_hash 캐싱), `poc/search.py`, `poc/queries/{5도메인}.py`(설계형 절반 + 자연어형 절반)
- UC/AC: UC-1 P9, UC-3 P1~3/A2/E2/X3, UC-1-X2 → AC-4, AC-5(부분), FR-4.1/4.2, FR-5.1/5.3
- TC(P0): TC-3.2 / P1: TC-1.6(키재검증→bge-m3 AI1 경로), TC-3.5, TC-3.7, TC-3.10, TC-1.11
- TDD: `[FX] test_indexer.py`(indexer 독자 백엔드 선택 안 함 단언 AI1), `test_search.py`, `test_queries.py`, `test_key_revalidate.py`
- 사전리뷰: 🟡 architect 권장 (AI1) / 시간 4~5h / 병렬 🟡 부분(queries 5병렬)

### S3b — 하이브리드 RRF (k·정규화 grid 전용)
- 파일: `poc/hybrid.py`(RRF, k·정규화 grid 순회, best 선택, "무의미" 결론 — 억지 best 금지)
- UC/AC: UC-3 P4~6/A1/X5 → AC-5, FR-5.2
- TC(P0): TC-3.3, TC-3.9(의도 반대 왜곡없이 부록B-3) / P1: TC-3.4, TC-3.12, TC-11.3
- TDD: `[FX] test_hybrid.py`(known-answer RRF·왜곡없이·무의미 결론)
- 사전리뷰: ⚪ 불요 / 시간 2~3h FX / 병렬 ✅ S3와 병렬

### S4 — 매트릭스 + 정성 리포트 + 정성 한계 문구 게이트 (AI4)
- 파일: 600줄 접근 시 `poc/report/{__init__,spec_table,matrix,verdict}.py` 분할(AI4) + 정성 한계 문구 게이트(UC-9) + 인용 길이상한
- UC/AC: UC-3 P6~8, UC-4·9 전부, 부록B → AC-5, AC-6, AC-7, FR-5.4/6.x
- TC(P0): TC-3.1, TC-4.1~4.4, TC-4.8, TC-4.9, TC-4.10, TC-9.1~9.4, TC-11.x / 수동: TC-4.5(체크리스트 내장)
- TDD: `[FX] test_report_matrix.py`, `test_report_verdict.py`, `test_report_gate.py`, `test_report_filesize.py`(≤1000줄·분할 AI4)
- 사전리뷰: 🟡 architect 권장 (AI4 + 부록B) / 시간 4~5h / 병렬 🟡 3-에이전트 부분

### S5 — 오케스트레이터 E2E + 캐시/HITL + 부록 B 통합 회귀
- 파일: `poc/run_feasibility.py`(전 단계 조정, 캐시/재사용 NFR-4, HITL, 백엔드 전환 여기서만 AI1, 순서 불변식 AI3), `poc/tests/test_e2e.py`, `test_invariants_b.py`
- UC/AC: UC-1 P4~12 E2E/X1/X2/X3, 부록B → AC-1~8 전반, NFR-4, AI1/AI3
- TC(P0): TC-1.7, TC-11.1, TC-11.2, TC-11.3 / 수동: TC-4.5(`[NET]` 강사 체크리스트)
- TDD: `[FX] test_e2e.py`(순서 위반 차단 AI3·백엔드 단일 경로 사후단언 AI1), `test_invariants_b.py`
- 완료: 최종 `git status --ignored`로 코퍼스·인덱스·.env 미추적·코드+리포트만 추적(AC-8)
- 사전리뷰: 🟡 architect + 🔴 머지 전 S0b security 게이트 최종 재실행 필수 / 시간 4~5h / 병렬 ❌ 최종

## 3. 슬라이스 요약 표

| 슬라이스 | 핵심 모듈 | UC | AC | 사전리뷰 | 시간 | 병렬 |
|---|---|---|---|---|---|---|
| S0 키게이트+모델+스파이크 | models, embedding, gate, collectors/base+5스텁 | UC-1, UC-6 P1·7 | AC-4, AC-1부분 | 🔴 security | 3~4h | ❌ |
| S0b 보안 사전리뷰 게이트 | security_gate, report스텁 | UC-10, UC-7-E1 | AC-8, NFR-5 | 🔴 security(AI2) | 2~3h | ❌ |
| S1 5수집기+정제 | collectors/{5}, cleaner | UC-6·7·8 | AC-1 | 🔴 security | **6~8h** | ✅ 5-에이전트 |
| S2 3축스펙+청킹 | spec, chunker | UC-2·5 | AC-2·3 | 🟡 architect(AI3) | 4~5h | 🟡 2 |
| S3 인덱싱+검색 | indexer, search, queries | UC-1 P9, UC-3 P1~3 | AC-4, AC-5부분 | 🟡 architect(AI1) | 4~5h | 🟡 |
| S3b 하이브리드 RRF | hybrid | UC-3 P4~6 | AC-5 | ⚪ 불요 | 2~3h | ✅ S3∥ |
| S4 매트릭스+리포트 | report/{spec_table,matrix,verdict} | UC-3 P6~8, UC-4·9 | AC-5·6·7 | 🟡 architect(AI4) | 4~5h | 🟡 3 |
| S5 오케스트레이터 E2E | run_feasibility, test_e2e | UC-1 E2E, 부록B | AC-1~8 | 🟡+🔴 S0b재실행 | 4~5h | ❌ |

**총 29~38h 순차. S1 5-에이전트 병렬 + S3b∥S3 시 D-4(~24h) 완주 가능.**
임계 경로: S0 → S0b → **S1(병렬 필수)** → S2 → S3 → S4 → S5.

## 4. 실행 순서 불변식

```
S0(gate·models·spike)
 └ S0b(보안 게이트 — collect 차단, AI2)  ◀ PASS 전 collect 미착수
   └ S1(collect→정제, AI3 앞)  ◀ 5-에이전트 병렬, 최장
     └ S2(정제후본문→spec→chunk, AI3 뒤, text_hash 캐시키)
       └ S3(index→search BM25/임베딩, AI1 백엔드경로)
         ├ S3b(hybrid RRF grid — S3와 병렬 가능)
         └ S4(matrix·report·문구게이트, AI4 분할)
           └ S5(orchestrator E2E·부록B 사후단언·S0b 최종 재실행)
```

## 5. 의존성

- 라이브러리: `kiwipiepy`, `rank-bm25`, `openai`, `anthropic`, `sentence-transformers`(bge-m3), `tiktoken`, `httpx`, `pytest`/`pytest-mock`/`responses`, `numpy`
- 외부 소스: OpenAI/Claude 임베딩 API(미가용 시 bge-m3 비용0) / data.go.kr 무인증 2단계 / korea.kr policyNewsView(pressReleaseView 금지) / nedrug(봇차단) / GitHub legalize-kr clone(sparse, force-push)
- 데이터 소스 근거: vault `Themes/lectures/2026-05-aiceo-data-connection-samples.md` §6차

## 6. 정성 PoC 정체성 (부록 B — 절대 위반 금지)

- 정량지표(nDCG/MRR/Recall@k) 산출 **금지** — 정답지 없음, 의도된 스코프
- 모든 산출물에 "정성 판정, 정량 검증 아님" 종결 문구 필수
- 검색3종이 의도와 반대로 갈려도 **있는 그대로 기록** (왜곡·은폐 금지)
- "세 방식이 안 갈림"은 이 PoC가 잡으려는 바로 그 결과 — FAIL이 아니라 valid 산출물
