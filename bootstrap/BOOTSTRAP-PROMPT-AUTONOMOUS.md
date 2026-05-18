# 작업 지시: `/review-watch` 하네스 자율 구축

너는 지금 `/review-watch` 하네스가 **설치되지 않은** 환경에 있다. 아래는
이 하네스가 **만족해야 하는 설계 명세**다. 원문 파일은 주어지지 않는다.
**명세를 이해하고, 네가 직접 7개 파일을 작성해** 하네스를 구축하라.

이것은 받아쓰기가 아니다. 표현·문장·구조는 네가 정한다. 단, 아래
**기능 계약**과 **불변식**과 **결함 처방**은 한 줄도 빠뜨리지 말고 구현해야
한다. 글자가 아니라 **계약을 지키는 것**이 합격선이다.

작업 중 사용자에게 질문하지 마라(명세가 완결돼 있다). `pwd`로 현재
프로젝트 루트를 확인하고 그 기준으로 경로를 정한다.

---

## 1. 하네스의 목적 (WHY)

B2C 서비스 운영사가 **회사명만** 입력하면, 자사에 대한 **외부 평가·리뷰**를
**그날 기준 24시간 / 3일 / 7일** 관점으로 수집·검증·합성해 **정형 digest**를
날짜별로 산출한다. WebSearch/WebFetch만 쓴다(외부 API·키 없음).

**정체성 원칙 (반드시 구현):**

- **매일 독립 스냅샷.** 어제 digest와 비교하지 않는다. diff·하이라이트·
  중복방지 시드(seenItems) 없음. 매일 그날의 완결된 스냅샷 1개.
- 매일 돌리는 이유: LLM WebSearch는 실행마다 누락이 생긴다. 같은 범위를
  매일 재수집해 날짜별로 쌓으면 사람이 파일을 직접 비교해 누락을 보완한다.
- 비교·delta·신규 판정은 하네스가 **하지 않는다**(사람 몫).

## 2. 만들 7개 파일과 각 책임 (WHAT — 구현은 네 몫)

`.claude/` 하위에 커맨드 1 + 에이전트 5 + 스킬 1 = 7파일. 경로:

| 파일 | 역할 (이 책임을 네 표현으로 구현) |
|---|---|
| `.claude/commands/review-watch.md` | 오케스트레이터. 6단계 파이프라인 정의 + frontmatter Contract + 토폴로지 |
| `.claude/agents/review-source-scanner.md` | 메타레이어. 회사명 → 소스 2~6개 동적 발굴 + source_id 부여 |
| `.claude/agents/review-collector.md` | 소스별 수집(분장). raw 파일 직접 Write, 오케스트레이터엔 집계만 |
| `.claude/agents/review-validator.md` | 검증. 출처 실재성·윈도우·인용 무결성, REMOVE를 raw에 반영 |
| `.claude/agents/review-synthesizer.md` | 합성(fan-in 1개). aspect 감성 + 24h/3d/7d 집계 + digest 초안 |
| `.claude/agents/review-evaluator.md` | 품질 게이트(patch형). 2단계 검증 후 patch만 반환 |
| `.claude/skills/review-watch/SKILL.md` | 자연어 자동인식 진입점. 커맨드 실행순서로 연결 |

에이전트 정의는 Claude Code subagent 형식(YAML frontmatter `name`/
`description`/`tools`/`model` + 본문)을 따른다. 각 에이전트의 `tools`는
그 책임 수행에 필요한 최소 도구로 네가 판단해 부여한다(예: collector는
파일을 직접 써야 하니 Write 포함, evaluator는 검사만 하니 Read/Grep 등).

## 3. 6단계 파이프라인 (TOPOLOGY — 순서·병렬성 고정, 서술은 네 몫)

```
Step 0  오케스트레이터: 공유 메타 7값 1회 산출 + 저장 경로 결정
Step 1  scanner ×1        [순차 선행 · 메타레이어]
Step 2  collector ×N      [동적 N개 병렬 · 소스별 분장]
Step 3  validator ×N      [병렬]
Step 4  synthesizer ×1    [단일 fan-in]
Step 5  evaluator ×1      [patch형 게이트]
Step 6  저장(누적) + 보고
```

- **Step 0 공유 메타 7값**: `now_kst`, `today`, `run_id`, `W_24H`,
  `W_3D`, `W_7D`, `slug`. **오케스트레이터가 한 번만** 산출(epoch 산술로
  윈도우 경계 계산 — DST·월말 안전)해 **모든 하위 에이전트에 동일 input
  주입**. 각 에이전트가 자체 `date`를 실행하면 윈도우 경계가 어긋나
  24h/3d/7d 분류가 깨진다 — 이게 정합성의 핵심.
- **Step 1 scanner**: 회사 성격을 WebSearch로 탐색(추측 금지) → 외부
  평가가 실제 쌓이는 채널 2~6개 동적 선정 → 각 소스에 **유일 source_id**
  부여. catalog 0개면 사유 보고 후 종료.
- **Step 2 collector**: scanner가 정한 소스마다 1개씩, **단일 메시지에
  N개 동시 호출**(병렬). 각 collector는 배정된 **소스 1개만** 수집(분장 —
  같은 범위 전수 아님).
- **Step 3 validator**: collector 산출마다 병렬. raw 파일을 직접 열어
  검증, 제거 항목을 raw에서도 삭제.
- **Step 4 synthesizer**: 검증 통과 raw들을 모아 1개가 합성.
- **Step 5 evaluator**: digest 초안을 2단계 검증, patch만 반환(§6 처방).
- **Step 6**: 저장. 같은 날 `00_digest.md` 있으면 `00_digest_<run_id>.md`로
  누적(덮어쓰기·멈춤·force 없음). 산출물은 `./specs/review-watch/<slug>/
  <YYYY-MM-DD>/` (프로젝트 로컬, 전역 vault 금지). 작업 로그는
  `./.claude/history/daily/<today>.md` 에 한 줄 append.

## 4. frontmatter Contract (digest 필수 스키마 — 키 누락 금지)

synthesizer가 만드는 digest 최상단 YAML frontmatter는 **다음 키를 전부**
포함해야 한다(키 이름·구조 고정, 값은 실행마다 다름):

```
harness, company, slug, run_at, run_id,
windows{ "24h", "3d", "7d" },
sources_scanned[],
total_mentions,
by_window{ "24h":{total,pos,neg,neu}, "3d":{...}, "7d":{...} },
sentiment_overall{ pos_pct, neg_pct, neu_pct },
top_aspects[]{ aspect, sentiment, mentions },
sources_empty[],
validation{ collected, passed, augmented, removed }
```

- Contract에 **없는 키를 추가하지 않는다**(특히 `seen_items`·`device`는
  이 설계에 없다 — 매일 독립이라 중복방지 시드 불필요).
- `by_window`는 **중첩 누적**: 24h ⊂ 3d ⊂ 7d (3d total ≥ 24h total,
  7d total ≥ 3d total).
- `collected` = 모든 소스의 "수집 성공해 raw에 기록한 항목 수"의 합
  (수집 *시도* 수 아님). 0건 소스는 collected에 0으로 들어가고
  `sources_empty`에 명기.
- digest 본문에 필수 섹션: 한눈 요약 / 시간 윈도우별 / Aspect별 감성 /
  권장 액션 / 소스 커버리지.

## 5. 불변식 (INVARIANTS — 어기면 하네스 실패)

1. **공유 메타 단일 산출**: 윈도우 경계는 Step 0에서 1회만. 어느
   에이전트도 자체 `date`로 윈도우를 재계산하지 않는다.
2. **raw = 검증 통과분**: collector가 쓴 raw 파일을 validator가 직접
   수정해 제거 항목을 빼므로, raw 파일은 항상 "검증 통과한 것만" 담는다.
   synthesizer는 raw를 그대로 신뢰해 인용한다.
3. **컨텍스트 격리**: collector·validator는 raw 본문·인용문 배열을
   오케스트레이터에 반환하지 않는다. **숫자·파일경로 집계만** 반환한다.
   원문은 파일에만 산다(이유는 §6-B).
4. **인용 무결성**: 모든 리뷰 인용은 `원문 URL + 인용문(원문 발췌) +
   게시일` 3종을 갖춘다. 셋 중 하나라도 없으면 그 항목은 버린다.
   raw에 없는 인용을 synthesizer가 만들지 않는다.
5. **source_id 유일**: scanner가 각 소스에 유일 id 부여
   (형식 `<source_type>-<도메인슬러그>`). 같은 source_type이 여럿이어도
   id는 서로 다르다. collector는 이 id를 raw 파일명·집계 키로 쓴다.

## 6. 결함 처방 (이미 비싸게 학습된 함정 — 반드시 회피 설계)

아래는 이 하네스를 여러 번 돌려 발견한 실패 양상의 **일반 원리**다.
구체 사례·고유명은 의도적으로 뺐다(처방만 구현하라).

- **A. 자기오염 회피 → patch형 게이트**: evaluator가 FAIL일 때
  synthesizer를 **재호출하지 않는다**. 재호출형(재생성)은 검증 통과
  데이터를 통째로 다시 만들며 인용을 날조하는 환각 폭주를 일으킨다.
  대신 evaluator는 결함을 **patch(앵커 원문 → 치환 텍스트)로만** 표현하고
  오케스트레이터가 그 patch를 **기계적 문자열 치환**으로 적용한다. LLM이
  데이터를 재생성할 통로 자체를 없앤다.
- **A'. patch 적용 누락 회피 → 번호화 절차 + grep 자가검증**: 오케스트
  레이터가 patch를 "적용했다고 가정"하고 건너뛰는 비결정적 누락이
  알려져 있다. Step 5를 번호화된 강제 절차로 만들고, **patch 적용 후
  anchor를 grep으로 재검색해 0건임을 확인한 뒤에만 "적용함"으로 기록**
  (검증 없이 허위 기록 금지). 미적용 시 경고 배너로 노출.
- **B. 컨텍스트 폭주 회피 → 파일 경유**: 다소스 raw가 오케스트레이터
  컨텍스트로 모이면 출력이 잘린다(50K). collector가 raw를 파일로 직접
  쓰고 컨텍스트엔 집계만 흐르게 한다(불변식 3).
- **D. 도구 능력 오해 회피**: scanner는 "이상적 소스"가 아니라
  "collector가 WebSearch/WebFetch로 실제 도달 가능한 소스"만 고른다.
  WebSearch는 `site:` 단독 쿼리를 신뢰성 있게 지원하지 않으므로,
  site: 단독 의존 소스를 priority 상위로 두지 않는다. 로그인·JS 전용
  (앱스토어 개별 리뷰 등)은 메타·평점 요약 위주로만.
- **F. 비결정 단계 누락 회피**: 결정적 단계(파일 치환·검증)는 정의에
  "하라"만 적지 말고 번호화 + 수행 후 기계 재검증하게 한다(A'와 동형).
- **G. 이식 이력 누출 회피**: 너가 작성하는 7파일에 개발 이력·고유
  사례명·"재구축/복제" 같은 표현을 넣지 마라. 규칙의 **정당성 근거**는
  적되 "언제 누가 발견했는가"는 적지 않는다. 이 하네스는 이식 가능한
  산출물이어야 한다.
- **환각 방어 3중**: ① collector가 url/인용/날짜 없는 항목 폐기
  ② validator가 URL 샘플을 실제 WebFetch해 실재 확인(없으면 제거,
  소스 다수 날조면 소스 FAIL) ③ evaluator가 본문 인용이 raw에 실재
  하는지 대조. 데이터가 없으면 **0건으로 정직하게** 보고(지어내지 말 것).

## 7. 수행 절차

1. `pwd`로 프로젝트 루트 확인. `.claude/{commands,agents,skills/
   review-watch}` 와 `.claude/history/daily` 디렉터리 생성.
2. §1~6을 충족하는 7개 파일을 **네 표현으로 작성**해 각 경로에 Write.
   - 원문을 받지 않았으므로 베낄 것이 없다. 명세를 구현하라.
   - 각 에이전트 정의 말미에 "출력 직전 자가검증 체크리스트"를 네가
     설계해 넣어라(그 에이전트가 자기 계약을 어기지 않았는지 스스로
     점검하도록).
3. 7파일을 다 쓴 뒤 §8 자가검증을 수행하고 결과를 표로 보고.
4. 이 단계에서 하네스를 **실제로 실행하지는 마라**(구축까지만).

## 8. 자가검증 (기능 계약 충족도 — 글자가 아니라 계약)

원본과 1:1 비교는 하지 않는다(자율 작성이라 글자가 다른 게 정상).
대신 아래를 점검하고 PASS/FAIL을 보고한다. 하나라도 FAIL이면 해당
파일을 계약에 맞게 고친 뒤 재점검한다.

```bash
echo "=== (1) 7파일 존재 ==="
for f in .claude/commands/review-watch.md \
  .claude/agents/review-source-scanner.md \
  .claude/agents/review-collector.md \
  .claude/agents/review-validator.md \
  .claude/agents/review-synthesizer.md \
  .claude/agents/review-evaluator.md \
  .claude/skills/review-watch/SKILL.md ; do
  [ -f "$f" ] && echo "OK $f" || echo "FAIL $f MISSING"
done

echo "=== (2) 각 파일이 자기 책임 개념을 담는가 (개념 존재 — 글자 아님) ==="
echo "아래는 grep 힌트일 뿐. 핵심은 '이 개념이 구현됐는가'를 너가 판단:"
grep -l "공유 메타\|7.*값\|1회 산출"        .claude/commands/review-watch.md && echo "  cmd: 공유메타 단일산출 개념 O"
grep -l "source_id"                          .claude/agents/review-source-scanner.md && echo "  scanner: source_id 개념 O"
grep -l "raw.*직접 Write\|raw.*파일\|집계만"  .claude/agents/review-collector.md && echo "  collector: 파일경유+집계반환 개념 O"
grep -l "REMOVE\|제거.*raw\|검증 통과분"      .claude/agents/review-validator.md && echo "  validator: raw=통과분 불변식 O"
grep -l "24h.*3d.*7d\|중첩\|aspect"          .claude/agents/review-synthesizer.md && echo "  synthesizer: 윈도우집계+aspect O"
grep -l "patch\|재호출.*않\|재생성.*없"       .claude/agents/review-evaluator.md && echo "  evaluator: patch형(재호출X) O"
grep -l "review-watch\|트리거"                .claude/skills/review-watch/SKILL.md && echo "  skill: 진입점 O"

echo "=== (3) frontmatter Contract 키 완비 (커맨드 또는 synthesizer에) ==="
for k in harness company slug run_at run_id windows sources_scanned \
  total_mentions by_window sentiment_overall top_aspects sources_empty validation ; do
  grep -rq "$k" .claude/commands/review-watch.md .claude/agents/review-synthesizer.md \
    && echo "  key $k O" || echo "  key $k MISSING ✗"
done

echo "=== (4) 금지 개념 부재 (이 설계에 없어야) ==="
grep -rn "seen_items\|seenItems\|중복방지 시드\|어제.*비교\|delta 계산\|재호출형 게이트" \
  .claude/commands/review-watch.md .claude/agents/review-*.md \
  | grep -v "안 함\|없다\|없음\|하지 않\|아니다\|금지" \
  && echo "  ✗ 금지 개념이 긍정적으로 구현됨 — 계약 위반" \
  || echo "  금지 개념 부재 — OK"

echo "=== (5) 이식 이력 누출 부재 (결함 G — 0건이어야) ==="
grep -rn "재구축\|정밀 복제\|4차\|6차\|토스 실측\|미래에셋\|사유원 실측" \
  .claude/commands/review-watch.md .claude/agents/review-*.md .claude/skills/review-watch/SKILL.md \
  && echo "  ✗ 개발이력/고유사례 누출 — 결함 G" \
  || echo "  이력 누출 0건 — OK"
```

### 합격 기준

| 검사 | PASS 조건 |
|---|---|
| (1) 파일 존재 | 7개 전부 OK |
| (2) 책임 개념 | 7파일 각각 자기 책임 개념을 **실제 구현**(grep은 힌트, 최종 판단은 너) |
| (3) Contract 키 | 13개 키 전부 O |
| (4) 금지 개념 | "금지 개념 부재 — OK" 출력 (seen_items·어제비교·재호출형이 긍정 구현 안 됨) |
| (5) 이력 누출 | "이력 누출 0건 — OK" (결함 G 회피) |

5개 검사 전부 PASS면 자율 구축 성공. 사용자에게 검사 표 + **"각 파일을
명세 어디를 보고 어떻게 구현했는지 1줄 설명"** 을 덧붙여 보고하라
(받아쓰기가 아니라 이해 기반 구현임을 보이기 위함). 그 후 종료한다.
(이 단계에서 하네스를 실제 실행하지는 마라.)
