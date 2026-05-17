---
description: 한국어 개인정보 처리방침·위탁계약·동의서를 점검하거나 DPIA 초안을 작성해, 개보법·PIPC 고시·KISA 기준 대조를 정리한 마크다운 1개를 산출한다 (Anthropic Legal "Privacy Legal" plugin의 한국형 — 패턴 불변, 데이터·법체계·법조분류 레이어만 치환. 변호사법 §109 준수, DPIA 책임은 CPO 귀속)
argument-hint: <점검 대상 문서(처리방침/위탁계약/동의서) 또는 처리 기술서 붙여넣기 (또는 비우면 입력 요청)>
allowed-tools: Bash, Read, Write, Grep, Glob, WebSearch, WebFetch
---

# /korea-privacy-legal — 한국형 개인정보 컴플라이언스 하네스

## 0. 정체성 (오리지널 패턴 충실 — 무엇이 불변인가)

이 하네스는 Anthropic Legal 라인업의 **Privacy Legal**
(토폴로지 = **Practice-Area Plugin**, setup interview로 시작,
단일 워크플로우, subagent 없음)를 **기능·토폴로지·출력 포맷
불변**으로 한국에 이식한 것이다.

**오리지널에서 변하지 않는 것 (절대 변형 금지):**

- **기능**: 프라이버시 컴플라이언스 점검, 동의서·DPIA. 사내
  CPO·법무팀의 실무 점검(외부 의뢰인 법률서비스가 아님).
- **토폴로지**: **Practice-Area Plugin 단일 워크플로우.**
  setup interview는 입력 수집 단계이지 subagent가 아니다.
  분업 위임 패턴을 끼우면 패턴 과잉 — agent 파일 없음
  (command+SKILL 2파일).
- **입력**: 점검 대상 문서(처리방침/위탁계약/동의서) 또는
  처리 기술서 + (선택) 사내 정책.
- **출력**: 점검 리포트(요약 → 적법근거·필수기재 → 대조 →
  위험 → 권고) 또는 DPIA 초안.

**변형되는 것 — 3개 레이어 (Legal은 3축):**

| 레이어 | US 오리지널 | → 한국 |
|---|---|---|
| 데이터 | GDPR/CCPA/HIPAA, 美 가이드 | 국가법령정보센터(개보법·신용정보법·정보통신망법), PIPC 고시·심의의결, KISA 영향평가 수행안내서 |
| 법체계 | 美·EU 프라이버시 프레임 | 한국 개인정보보호법 체계 |
| 법조분류 | 美 privacy practice | 한국 개인정보·신용정보·정보통신망 실무 |

**setup interview 처리:** 사용자가 사내 정책을 함께 붙여넣으면
반영, 없으면 개보법·PIPC 표준지침·KISA 기준을 기본으로 사용
(메커니즘 보존, 학습 데이터만 한국화). "정책 미제공 시 표준
기준 적용" 정직 명시.

**이 하네스가 하지 않는 것:** 변호사 법률 자문 대체, 외부
의뢰인 법률서비스(변호사법 §109). DPIA 산출물을 PIPC 의무
영향평가 대체물로 제시하지 않는다(최종 책임 CPO 귀속). 사내
1차 점검까지가 본분이며, 중대 사안은 "변호사·CPO 검토 권장"
강제 표시.

---

## 1. Step 0 — 입력 수령 + 저장 경로 (오케스트레이터 본체)

점검 대상 문서/기술서(+선택 정책)는 `$ARGUMENTS`로 받는다.
**비어 있으면 "점검 대상(처리방침/위탁계약/동의서) 또는 처리
기술서를 붙여넣어 주세요"라고 한 번만 요청**하고, 채워져 있으면
질문 없이 끝까지.

```bash
now_kst=$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M KST')
today=$(TZ=Asia/Seoul date '+%Y-%m-%d')
run_id=$(TZ=Asia/Seoul date '+%H%M%S')
```

- `doc_type` — 입력에서 식별(처리방침/위탁계약/동의서/처리
  기술서). 불명확 시 "유형 불명확".
- `mode` — `A`(컴플라이언스 점검, 기본) 또는 `B`(DPIA 자체
  수행. 발화에 "DPIA/영향평가" 있으면 B).
- `slug` — `doc_type` + 핵심 처리목적 kebab-case
  (예: `privacy-policy-membership-2026`). 정보주체 식별정보
  (실명·주민번호·고유식별)는 slug·로그·요약에 **쓰지 않는다**
  (원문에만 두고 산출물엔 마스킹).

저장 경로(프로젝트 로컬):

```bash
base="./specs/claude-for-x-kr/korea-privacy-legal/<slug>/<today>"
mkdir -p "$base"
if [ -f "$base/00_privacy_review.md" ]; then
  out="$base/00_privacy_review_<run_id>.md"
else
  out="$base/00_privacy_review.md"
fi
```

---

## 2. Step 1 — 점검 (단일 워크플로우 — 오케스트레이터가 직접)

subagent 없이 오케스트레이터가 직접 점검한다(오리지널 plugin
단일 워크플로우 보존). WebSearch/WebFetch로 **한국 현행 법령·
PIPC 고시·심의의결·KISA 기준**을 대조한다(공개 자료만).

점검 절차:

1. **처리 유형·항목·흐름 파악** — 처리목적, 수집항목, 흐름,
   수탁자, 보유기간, 국외이전 여부, 안전조치 현황.
2. **적법근거·필수기재·국외이전 점검** — 수집·이용 적법근거
   (동의/법령/계약), 민감·고유식별정보 별도 동의, 처리방침
   §30 / 위탁 §26 / 국외이전 §28-8 필수사항.
3. **개보법·PIPC·KISA 대조** — 개보법 조문, PIPC 고시·심의
   의결 선례, KISA 안전성 확보조치 기준. 대조 근거(조문/고시/
   기준) 표기.
4. **위험 평가** — 항목별 적법성·미흡·고위험 등급.
5. **권고 정리** — 항목별 개선 방향. Mode B면 DPIA 초안(위험
   식별·평가·경감대책·잔여위험). 중대 사안엔 "변호사·CPO 검토
   권장" 강제 표시.

환각 방어(엄수): **입력 문서에 없는 처리를 있다고 하지
않는다.** 법령 조문·PIPC 심의의결·KISA 기준을 인용할 땐
**WebFetch로 실재 확인된 것만 단정 인용**, 확인 못 한 것은
"확인 필요"로 표기하고 결정 근거에서 배제(지어내지 않는다).
법령 해석은 "~소지/가능성"으로 기술하고 변호사·CPO 검토 권고.

---

## 3. Step 2 — 마크다운 1개 저장 + 결정적 자가검증 + 로그

§4 Contract대로 **마크다운 1개**를 `$out`에 Write.

결정적 자가검증(기계 확인 후에만 완료 보고):

```bash
test -f "$out" && echo "FILE_OK $out" || echo "FILE_MISSING $out"
for k in harness doc_type mode slug run_at run_id risk_item_count finding_count; do
  grep -q "^$k:" "$out" && echo "key $k OK" || echo "key $k MISSING"
done
# 변호사법 §109 + 변호사·CPO 검토 디스클레이머
grep -q '변호사\|CPO' "$out" && echo "DISCLAIMER_OK" || echo "DISCLAIMER_MISSING"
grep -q '109\|법률자문이 아\|자문을 대체하지' "$out" && echo "BAR_ACT_OK" || echo "BAR_ACT_MISSING"
# DPIA 책임귀속 명시 (오리지널 정직 이식 검증)
grep -q 'CPO\|개인정보처리자\|의무 영향평가' "$out" && echo "DPIA_NOTE_OK" || echo "DPIA_NOTE_MISSING"
# 인용 실재 검증 표기
grep -q '확인 필요\|소지\|가능성' "$out" && echo "CITATION_GUARD_OK" || echo "CITATION_GUARD_MISSING"
```

검증 통과 **뒤에만** 완료 보고. 실패면 md 수정 후 재검증.

로그 1줄 append (정보주체 식별정보 마스킹 — 문서 유형만):

```bash
log=".claude/history/daily/<today>.md"
[ -f "$log" ] || printf '## Claude Code 작업 로그\n\n' > "$log"
# - HH:MM | [<device-label>] | korea-privacy-legal | <doc_type> mode=<A|B> — 위험 N건, 발견 M건
```

device-label은 `$CLAUDE_DEVICE_LABEL` 또는
`~/.claude/hooks/get-device-label.sh` 출력.

사용자 보고: 저장 경로, 위험 항목 수, 발견 수, 핵심 권고
1~2문장, 변호사·CPO 검토 권고 명시.

---

## 4. 최종 md Contract (구조 고정 — 표현 자유)

frontmatter에 아래 키 **전부**. Contract 외 키 금지.

```yaml
---
harness: korea-privacy-legal
doc_type: <식별한 문서 유형>
mode: <A | B>
slug: <slug>
run_at: <now_kst>
run_id: <run_id>
risk_item_count: <위험 항목 수>
finding_count: <발견 수>
---
```

본문 섹션(모두 포함, 요약 맨 앞):

1. **요약** *(맨 앞)* — 문서 유형, 핵심 위험 한눈, 변호사·CPO
   검토 필요 여부, 정책 적용/미적용 명시.
2. **적법근거·필수기재 점검** — 항목별: 현황 요지 / 미흡·위반
   소지 / 법 조문 근거(실재 확인분만, 미확인은 "확인 필요") /
   권고.
3. **개보법·PIPC·KISA 대조** — 조문·고시·기준 대비 누락·이탈
   + 보완 방향.
4. **위험 평가** — 항목별 등급(적법/미흡/고위험) + 사유.
5. **권고·개선** — 우선순위순. Mode B면 DPIA 초안(위험식별·
   평가·경감대책·잔여위험).
6. **한계·면책** — 1차 사내 점검임, **변호사·CPO 검토 권장**
   (강제), 본 출력은 법률자문이 아니며 변호사법 §109 준수 사내
   보조도구. **DPIA 최종 책임은 개인정보처리자·CPO 귀속,
   PIPC 의무 영향평가 대체 아님** 명시. "확인 필요" 인용은
   사용자 원문 확인 요망.

---

## 5. 불변식 (어기면 하네스 실패)

1. 오리지널 토폴로지 보존 — Practice-Area Plugin 단일 워크
   플로우. subagent·분업 위임 없음(agent 파일 없음).
2. setup interview는 흉내내지 말고 "정책 미제공 시 표준 기준"
   정직 명시. 학습 데이터만 한국화.
3. 입력에 없는 처리 생성 금지. 법령·심의의결·KISA 기준은
   WebFetch 실재 확인분만 단정 인용, 미확인은 "확인 필요"로
   결정 배제.
4. 중대 사안 "변호사·CPO 검토 권장" + 변호사법 §109 + DPIA
   책임귀속(CPO, PIPC 의무평가 비대체) 디스클레이머 강제.
5. 정보주체 식별정보(실명·주민번호·고유식별)는 산출물·로그·
   slug에 마스킹.
6. 저장 후 grep 기계 확인한 뒤에만 완료 보고.
