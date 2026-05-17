---
name: korea-earnings-reviewer
description: 한국 상장사의 분기·반기·사업보고서 실적을 DART/KIND 공시와 한국 IR 자료로 분석해 모델 refresh와 thesis 변화 감지를 담은 실적 리뷰 마크다운 1개를 산출하는 하네스. Anthropic Financial Services "Earnings Reviewer"의 한국형(기능·토폴로지 불변, 데이터·문화 레이어만 치환). 다음 발화에 트리거된다 — "<종목> 실적 리뷰해줘", "<종목> 분기실적 분석", "<종목> 어닝 분석해줘", "DART 실적 공시 분석", "<종목> 컨콜·IR 정리해줘", "이번 분기 실적이 투자 논리에 주는 변화 봐줘". 외부 도구는 WebSearch/WebFetch만 쓴다(API 키 없음, 공개 공시 기반).
---

# korea-earnings-reviewer — 한국형 실적 리뷰 진입점

## 무엇을 하는가

사용자가 **한국 상장사 + 분기**를 주면, 오케스트레이터가 공시·콜
1차 자료 추출 sub-task를 **`korea-earnings-disclosure-agent`에 위임**
(오리지널 분업 토폴로지)한 뒤, 반환된 자료로 **① 공시·콜 분석 ②
모델 refresh ③ thesis 변화 감지** 3종을 수행해 실적 리뷰 마크다운
1개를 `./specs/claude-for-x-kr/korea-earnings-reviewer/<slug>/<today>/`
에 저장한다.

이것은 Anthropic Financial Services의 **Earnings Reviewer** agent
template을 기능·토폴로지·출력 불변으로 한국에 이식한 것이다. 변형은
데이터 레이어(US 공시 DB → DART/KIND)와 문화 레이어(美 어닝 사이클 →
한국 공시 의무·K-IFRS)뿐이다.

## 언제 트리거되는가

- "<종목> 실적/어닝/분기실적 리뷰·분석해줘"
- "DART 공시 분석", "<종목> 컨콜·IR 정리", "이번 실적이 thesis에
  주는 변화 봐줘"

## 트리거되지 않는 경우

- 섹터·산업 동향 모니터링 → `/korea-market-researcher`
- 일반 웹 조사 → 일반 WebSearch 또는 deep-search 계열
- 코드베이스 분석 → `/reverse`

## 어떻게 동작하는가

이 스킬이 트리거되면 **`/korea-earnings-reviewer` 커맨드의 실행
순서를 그대로 수행**한다:

1. **Step 0** — 공유 메타·저장 경로 결정(오케스트레이터).
2. **Step 1** — 공시·콜 추출을 `korea-earnings-disclosure-agent`에
   위임(분업, 누락보완 중복 아님).
3. **Step 2** — 오케스트레이터가 기능 3종(공시분석·모델refresh·
   thesis변화) 수행.
4. **Step 3** — 마크다운 1개 저장 → grep 결정적 자가검증 → 로그
   append → 요약 보고.

대상이 비면 한 번만 묻고, 그 외엔 질문 없이 끝까지. 상세 계약
(Contract·불변식)은 `.claude/commands/korea-earnings-reviewer.md`를
따른다. 투자 권유·목표주가 판정은 하지 않는다.
