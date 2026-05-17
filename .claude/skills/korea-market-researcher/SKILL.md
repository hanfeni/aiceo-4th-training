---
name: korea-market-researcher
description: 한국 섹터·발행자(상장사) 뉴스를 KIND/한국 산업연구원/한국 증권사 리서치로 모니터링하고 리서치 합성 + 중요 발견 에스컬레이션을 담은 섹터 리서치 마크다운 1개를 산출하는 하네스. Anthropic Financial Services "Market Researcher"의 한국형(기능·토폴로지 불변, 데이터·문화 레이어만 치환). 다음 발화에 트리거된다 — "<섹터> 동향 정리해줘", "<산업> 시장 리서치", "<섹터> 모니터링해줘", "이 섹터 뭐가 중요한지 봐줘", "<산업> 최근 신호 합성", "주목할 섹터 이슈 끌어올려줘". 외부 도구는 WebSearch/WebFetch만 쓴다(API 키 없음, 공개 데이터 기반).
---

# korea-market-researcher — 한국형 섹터 리서치 진입점

## 무엇을 하는가

사용자가 **섹터/산업/발행자**를 주면, 오케스트레이터가 섹터 신호
수집 sub-task를 **`korea-sector-signal-agent`에 위임**(오리지널 분업
토폴로지)한 뒤, 반환 신호로 **① 모니터링 ② 리서치 합성 ③ 에스컬
레이션** 3종을 수행해 섹터 리서치 마크다운 1개를
`./specs/claude-for-x-kr/korea-market-researcher/<slug>/<today>/`에
저장한다.

이것은 Anthropic Financial Services의 **Market Researcher** agent
template을 기능·토폴로지·출력 불변으로 한국에 이식한 것이다. 변형은
데이터 레이어(US expert network/IBISWorld → KIND/한국 산업연구원/
한국 증권사 리서치)와 문화 레이어(美 섹터 분류 → 한국 산업분류·
테마 체계)뿐이다.

**에스컬레이션**(주목할 발견 끌어올림)이 오리지널의 핵심 동사다 —
단순 뉴스 나열로 평탄화하지 않는다.

## 언제 트리거되는가

- "<섹터/산업> 동향·시장 리서치·모니터링해줘"
- "이 섹터 뭐가 중요한지 봐줘", "주목할 이슈 끌어올려줘"
- "<섹터> 최근 신호 합성"

## 트리거되지 않는 경우

- 단일 상장사 분기실적 deep-dive → `/korea-earnings-reviewer`
- 일반 웹 조사 → 일반 WebSearch 또는 deep-search 계열
- 코드베이스 분석 → `/reverse`

## 어떻게 동작하는가

이 스킬이 트리거되면 **`/korea-market-researcher` 커맨드의 실행
순서를 그대로 수행**한다:

1. **Step 0** — 공유 메타·저장 경로 결정(오케스트레이터).
2. **Step 1** — 섹터 신호 수집을 `korea-sector-signal-agent`에
   위임(분업, 누락보완 중복 아님).
3. **Step 2** — 오케스트레이터가 기능 3종(모니터링·합성·에스컬
   레이션) 수행. 에스컬레이션 평탄화 금지.
4. **Step 3** — 마크다운 1개 저장 → grep 결정적 자가검증(에스컬
   레이션 섹션 존재 포함) → 로그 append → 요약 보고.

대상이 비면 한 번만 묻고, 그 외엔 끝까지. 상세 계약은
`.claude/commands/korea-market-researcher.md`를 따른다. 섹터 우열
랭킹·투자 권유는 하지 않는다.
