---
description: 사내 법무팀 관점에서 한국어 상거래 계약서를 검토하거나 협상 메모를 작성해, 강행규정·약관규제법·표준계약서 대조와 협상 라인을 정리한 마크다운 1개를 산출한다 (Anthropic Legal "Commercial Legal" plugin의 한국형 — 패턴 불변, 데이터·법체계·법조분류 레이어만 치환. 변호사법 §109 준수 사내 보조도구)
argument-hint: <검토할 계약서 텍스트 (+ 선택 사내 playbook) 붙여넣기 (또는 비우면 입력 요청)>
allowed-tools: Bash, Read, Write, Grep, Glob, WebSearch, WebFetch
---

# /korea-commercial-legal — 한국형 사내 상사 법무 검토 하네스

## 0. 정체성 (오리지널 패턴 충실 — 무엇이 불변인가)

이 하네스는 Anthropic Legal 라인업의 **Commercial Legal**
(토폴로지 = **Practice-Area Plugin**, setup interview로 시작,
단일 워크플로우, subagent 없음)를 **기능·토폴로지·출력 포맷
불변**으로 한국에 이식한 것이다.

**오리지널에서 변하지 않는 것 (절대 변형 금지):**

- **기능**: 일반 상거래 계약·딜 워크플로우 — 계약서 작성·검토,
  협상 메모, 위험 검토. 사내 법무팀의 실무 검토(외부 의뢰인
  법률서비스가 아님).
- **토폴로지**: **Practice-Area Plugin 단일 워크플로우.**
  setup interview(팀 playbook·risk calibration·house style)로
  시작하나 그 자체가 입력 수집 단계이지 subagent가 아니다.
  Financial 분업 위임 패턴을 끼우면 패턴 과잉 — agent 파일을
  만들지 않는다(command+SKILL 2파일).
- **입력**: 계약서 텍스트 + (선택) 사내 playbook.
- **출력**: 검토 리포트(요약 → 강행규정·약관규제 → 표준 대조 →
  협상 라인 → 권고) 또는 협상 메모.

**변형되는 것 — 3개 레이어 (Legal은 2축이 아니라 3축):**

| 레이어 | US 오리지널 | → 한국 |
|---|---|---|
| 데이터 | FactSet·Westlaw·美 표준 조항 | 국가법령정보센터, 대법원 종합법률정보, 공정위 표준약관·표준계약서 |
| 법체계 | common law 판례법 | 한국 성문법(민법·상법) + 판례 |
| 법조분류 | 美 commercial practice | 한국 상사·약관규제법·하도급법·표준계약서 실무 |

**setup interview 처리:** 오리지널은 plugin이 setup interview로
팀 playbook·escalation·risk calibration·house style을 학습한다.
이 sandbox에서는 **사용자가 playbook을 입력에 함께 붙여넣으면
반영, 없으면 한국 표준계약서·공정위 표준약관을 기본 기준으로
사용**한다(메커니즘 보존, 학습 데이터만 한국화). 흉내내지 않고
"playbook 미제공 시 표준약관 기준 적용"을 정직히 명시.

**이 하네스가 하지 않는 것:** 변호사 법률 자문 대체, 소송 전략,
외부 의뢰인 대상 법률서비스(변호사법 §109). 사내 1차 법무 검토
까지가 본분이며, 중대 사안은 "변호사 검토 권장"을 강제 표시한다.

---

## 1. Step 0 — 입력 수령 + 저장 경로 (오케스트레이터 본체)

계약서 텍스트(+선택 playbook)는 `$ARGUMENTS`로 받는다. **비어
있으면 "검토할 계약서 전문을 붙여넣어 주세요 (사내 playbook이
있으면 함께)"라고 한 번만 요청**하고, 채워져 있으면 질문 없이
끝까지.

```bash
now_kst=$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M KST')
today=$(TZ=Asia/Seoul date '+%Y-%m-%d')
run_id=$(TZ=Asia/Seoul date '+%H%M%S')
```

- `contract_type` — 입력에서 계약 유형 식별(용역/위탁/매매/
  하도급/대리점/공급/라이선스/비밀유지 등). 불명확 시 "유형
  불명확".
- `mode` — `A`(계약 검토, 기본) 또는 `B`(협상 메모. 발화에
  "협상 메모/양보 라인" 있으면 B).
- `slug` — `contract_type` + 핵심 대상 kebab-case
  (예: `service-outsourcing-2026`). 개인정보·기밀(실명·법인
  비공개정보·계좌)은 slug·로그·요약에 **쓰지 않는다**(원문에만
  두고 산출물엔 마스킹).

저장 경로(프로젝트 로컬):

```bash
base="./specs/claude-for-x-kr/korea-commercial-legal/<slug>/<today>"
mkdir -p "$base"
if [ -f "$base/00_commercial_review.md" ]; then
  out="$base/00_commercial_review_<run_id>.md"
else
  out="$base/00_commercial_review.md"
fi
```

---

## 2. Step 1 — 검토 (단일 워크플로우 — 오케스트레이터가 직접)

subagent 없이 오케스트레이터가 직접 검토한다(오리지널 plugin
단일 워크플로우 보존). WebSearch/WebFetch로 **한국 현행 법령·
표준약관·판례**를 대조한다(공개 자료만).

검토 절차:

1. **계약 유형·당사자·핵심 의무 파악** — 무슨 계약, 당사자
   권리·의무, 대가·기간·해지·분쟁해결.
2. **강행규정·약관규제법·특별법 점검** — 강행규정 위반 소지,
   약관규제법 제6~14조 불공정·무효 조항 소지, 하도급법·대규모
   유통업법 등 특별법 저촉 소지.
3. **한국 표준계약서·표준약관 대조** — 공정위 표준약관·분야별
   표준계약서 대비 누락·이탈·현저한 불리 조항. 대조 근거(법
   조문/표준약관 번호) 표기.
4. **협상 라인 정리 (Mode B 중심, A도 포함)** — 양보 가능 조항
   / 양보 시 리스크·대가 / 양보 불가(강행규정·중대 리스크) 라인.
5. **권고 정리** — 조항별 수정·보완 방향(대안 문구 예시 가능).
   중대 사안엔 "변호사 검토 권장" 강제 표시.

환각 방어(엄수): **입력 계약서에 없는 조항을 있다고 하지
않는다.** 법령 조문·판례·표준약관을 인용할 땐 **WebFetch로
실재 확인된 것만 단정 인용**, 확인 못 한 것은 "확인 필요"로
표기하고 결정 근거에서 배제(지어내지 않는다). 법령 해석은
"~소지/가능성"으로 기술하고 변호사 검토를 권고한다.

---

## 3. Step 2 — 마크다운 1개 저장 + 결정적 자가검증 + 로그

§4 Contract대로 **마크다운 1개**를 `$out`에 Write.

결정적 자가검증(기계 확인 후에만 완료 보고):

```bash
test -f "$out" && echo "FILE_OK $out" || echo "FILE_MISSING $out"
for k in harness contract_type mode slug run_at run_id risk_clause_count missing_clause_count; do
  grep -q "^$k:" "$out" && echo "key $k OK" || echo "key $k MISSING"
done
# 변호사법 §109 + 변호사 검토 디스클레이머 (필수 — 자문 대체 방지)
grep -q '변호사' "$out" && echo "DISCLAIMER_OK" || echo "DISCLAIMER_MISSING"
grep -q '109\|법률자문이 아\|자문을 대체하지' "$out" && echo "BAR_ACT_OK" || echo "BAR_ACT_MISSING"
# 인용 실재 검증 표기 (확인 필요/검증 라벨이 운용되는지)
grep -q '확인 필요\|검증\|소지\|가능성' "$out" && echo "CITATION_GUARD_OK" || echo "CITATION_GUARD_MISSING"
```

검증 통과(파일 + 키 + 디스클레이머 + 변호사법 + 인용가드)
**뒤에만** 완료 보고. 실패면 md 수정 후 재검증.

로그 1줄 append (개인정보·기밀 마스킹 — 계약 유형만):

```bash
log=".claude/history/daily/<today>.md"
[ -f "$log" ] || printf '## Claude Code 작업 로그\n\n' > "$log"
# - HH:MM | [<device-label>] | korea-commercial-legal | <contract_type> mode=<A|B> — 리스크 N건, 누락 M건
```

device-label은 `$CLAUDE_DEVICE_LABEL` 또는
`~/.claude/hooks/get-device-label.sh` 출력.

사용자 보고: 저장 경로, 리스크 조항 수, 누락 조항 수, 핵심
권고 1~2문장, 변호사 검토 권고 명시.

---

## 4. 최종 md Contract (구조 고정 — 표현 자유)

frontmatter에 아래 키 **전부**. Contract 외 키 금지.

```yaml
---
harness: korea-commercial-legal
contract_type: <식별한 계약 유형>
mode: <A | B>
slug: <slug>
run_at: <now_kst>
run_id: <run_id>
risk_clause_count: <리스크 조항 수>
missing_clause_count: <누락 조항 수>
---
```

본문 섹션(모두 포함, 요약 맨 앞):

1. **요약** *(맨 앞)* — 계약 유형, 핵심 리스크 한눈, 변호사
   검토 필요 여부, playbook 적용/미적용 명시.
2. **강행규정·약관규제 점검** — 조항별: 위치·문구 요지 / 위반
   소지 / 법 조문 근거(실재 확인분만, 미확인은 "확인 필요") /
   권고.
3. **표준계약서 대조** — 표준약관·표준계약서 대비 누락·이탈
   조항 + 보완 방향.
4. **협상 라인** — 양보 가능 / 양보 시 리스크·대가 / 양보 불가
   (강행규정·중대 리스크) 라인. (Mode B는 이 섹션 중심)
5. **권고·대안 문구** — 우선순위순 수정 권고. 대안 문구 예시.
6. **한계·면책** — 1차 사내 검토임, **변호사 검토 권장**(강제),
   본 출력은 법률자문이 아니며 변호사법 §109 준수 사내 보조도구
   임을 명시. "확인 필요" 표기 인용은 사용자 원문 확인 요망.

---

## 5. 불변식 (어기면 하네스 실패)

1. 오리지널 토폴로지 보존 — Practice-Area Plugin 단일 워크플로우.
   subagent·분업 위임을 끼우지 않는다(agent 파일 없음).
2. setup interview는 흉내내지 말고 "playbook 미제공 시 표준약관
   기준" 정직 명시. 학습 데이터만 한국화.
3. 입력에 없는 조항 생성 금지. 법령·판례·표준약관은 WebFetch
   실재 확인분만 단정 인용, 미확인은 "확인 필요"로 결정 배제.
4. 중대 사안 "변호사 검토 권장" + 변호사법 §109 디스클레이머
   강제. 외부 의뢰인 법률서비스·소송대리로 포지셔닝 금지.
5. 개인정보·기밀(실명·법인 비공개정보·계좌)은 산출물·로그·
   slug에 마스킹.
6. 저장 후 grep 기계 확인한 뒤에만 완료 보고.
