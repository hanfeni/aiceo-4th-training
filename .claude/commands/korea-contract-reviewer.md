---
description: 붙여넣은 한국어 계약서 텍스트의 조항을 한국 계약법·표준약관 관점에서 검토해, 리스크 조항·누락 조항·독소 조항을 정리한 검토 마크다운 1개를 산출한다 (Anthropic Small Business "Contract Reviewer"의 한국형 — 패턴 불변, 데이터·문화 레이어만 치환. 전자서명 연동은 미연결 명시)
argument-hint: <검토할 계약서 텍스트 붙여넣기 (또는 비우면 입력 요청)>
allowed-tools: Bash, Read, Write, Grep, Glob, WebSearch, WebFetch
---

# /korea-contract-reviewer — 한국형 계약서 검토 하네스

## 0. 정체성 (오리지널 패턴 충실 — 무엇이 불변인가)

이 하네스는 Anthropic Small Business 라인업의 **Contract Reviewer**
(토폴로지 = **Skill**, Cowork 단일 워크플로우, subagent 없음)를
**기능·토폴로지·출력 포맷 불변**으로 한국에 이식한 것이다.

**오리지널에서 변하지 않는 것 (절대 변형 금지):**

- **기능**: 계약서 조항을 검토해 리스크·문제 조항을 식별·정리.
  Legal Commercial 플러그인의 SMB 경량판(전문 법률 자문이 아니라
  사업자가 1차로 훑는 검토).
- **토폴로지**: **Skill 단일 워크플로우.** subagent를 두지 않는다.
  Financial 하네스의 분업 위임 패턴을 여기 끼우면 패턴 과잉이다 —
  agent 파일을 만들지 않는다(command+SKILL 2파일).
- **입력**: 붙여넣은 계약서 텍스트(오리지널도 텍스트 검토가 본질).
- **출력**: 검토 리포트(요약 → 리스크 조항 → 누락 조항 → 권고).

**변형되는 것 — 데이터·문화 레이어 단 2개:**

| 레이어 | US 오리지널 | → 한국 |
|---|---|---|
| 데이터·법 | 美 계약법, 美 표준 조항 | 한국 민법(계약), 약관규제법, 표준약관(공정위), 분야별 표준계약서(고용·임대차·용역·하도급 등) |
| 문화·연동 | DocuSign(서명·상태추적·파일관리) | 모두싸인 등 한국 전자서명 — **이 sandbox에 미연결**. 검토 기능은 텍스트만으로 완결, 서명 연동은 "향후 연동 지점"으로만 명시 |

**전자서명 미연결 처리:** 오리지널의 DocuSign 부분(서명 발송·상태
추적)은 이 sandbox에 커넥터가 없다. 임의로 흉내내지 않는다. 리포트
말미에 "전자서명 연동(모두싸인 등)은 미연결 — 검토 후 수동 진행"
이라고 **정직히 명시**한다. 검토 자체는 텍스트만으로 완결되므로
오리지널 핵심 기능은 손상 없다.

**이 하네스가 하지 않는 것:** 변호사 법률 자문 대체, 소송 전략,
계약 체결 결정 대행. 1차 리스크 식별까지가 본분이며, 중대 사안은
"전문가(변호사·노무사) 검토 권장"을 강제 표시한다.

---

## 1. Step 0 — 입력 수령 + 저장 경로 (오케스트레이터 본체)

계약서 텍스트는 `$ARGUMENTS`로 받는다. **비어 있으면 "검토할
계약서 전문을 붙여넣어 주세요"라고 한 번만 요청**하고, 채워져
있으면 질문 없이 끝까지.

```bash
now_kst=$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M KST')
today=$(TZ=Asia/Seoul date '+%Y-%m-%d')
run_id=$(TZ=Asia/Seoul date '+%H%M%S')
```

- `contract_type` — 입력 텍스트에서 계약 유형을 식별(근로/임대차/
  용역/하도급/비밀유지/매매 등). 불명확하면 "유형 불명확"으로 기재.
- `slug` — `contract_type` + 핵심 당사자/대상 kebab-case
  (예: `employment-parttime-2026`). 개인정보(실명·주민번호·연락처)는
  slug·로그·요약에 **쓰지 않는다**(원문에만 두고 산출물엔 마스킹).

저장 경로(프로젝트 로컬):

```bash
base="./specs/claude-for-x-kr/korea-contract-reviewer/<slug>/<today>"
mkdir -p "$base"
if [ -f "$base/00_contract_review.md" ]; then
  out="$base/00_contract_review_<run_id>.md"
else
  out="$base/00_contract_review.md"
fi
```

---

## 2. Step 1 — 조항 검토 (단일 워크플로우 — 오케스트레이터가 직접)

subagent 없이 오케스트레이터가 직접 검토한다(오리지널 Skill 단일
워크플로우 보존). 필요 시 WebSearch/WebFetch로 **한국 표준약관·
표준계약서·관련 법 조문**을 대조한다(공개 자료만).

검토 절차:

1. **계약 유형·당사자·핵심 의무 파악** — 무슨 계약인지, 당사자
   권리·의무, 기간·대가·해지 조건.
2. **리스크 조항 식별** — 일방 불리, 과도한 위약·손해배상, 모호한
   책임 범위, 부당한 면책, 자동연장·해지제한, 관할·준거법 편향 등.
3. **한국 법·표준 대조** — 약관규제법상 무효 가능 조항, 강행규정
   위반 소지(예: 근로계약의 근로기준법 위반), 해당 분야 표준계약서
   대비 누락·이탈 조항. 대조 근거(법 조문/표준약관 출처) 표기.
4. **누락 조항 식별** — 그 유형 계약에 통상 있어야 하나 빠진 조항.
5. **권고 정리** — 조항별 수정·보완 방향(대안 문구 예시 가능).
   중대 사안엔 "전문가 검토 권장" 강제 표시.

환각 방어(엄수): **입력 계약서에 없는 조항을 있다고 하지 않는다.**
법 조문·표준약관을 인용할 땐 실재하는 것만(불확실하면 "확인 필요"
로 표기, 지어내지 않는다). 법령 해석이 단정적이지 않도록 "~소지/
가능성"으로 기술하고 전문가 검토를 권고한다.

---

## 3. Step 2 — 마크다운 1개 저장 + 결정적 자가검증 + 로그

§4 Contract대로 **마크다운 1개**를 `$out`에 Write.

결정적 자가검증(기계 확인 후에만 완료 보고):

```bash
test -f "$out" && echo "FILE_OK $out" || echo "FILE_MISSING $out"
for k in harness contract_type slug run_at run_id risk_clause_count missing_clause_count; do
  grep -q "^$k:" "$out" && echo "key $k OK" || echo "key $k MISSING"
done
# 전문가 검토 권고 디스클레이머가 실제로 들어갔는지 (필수 — 자문 대체 방지)
grep -q '전문가\|변호사\|노무사' "$out" && echo "DISCLAIMER_OK" || echo "DISCLAIMER_MISSING"
# 전자서명 미연결 명시가 들어갔는지 (오리지널 정직 이식 검증)
grep -q '미연결' "$out" && echo "ESIGN_NOTE_OK" || echo "ESIGN_NOTE_MISSING"
```

검증 통과(파일 + 키 + 디스클레이머 + 미연결 명시) **뒤에만** 완료
보고. 실패면 md 수정 후 재검증.

로그 1줄 append (개인정보 마스킹 — 계약 유형만):

```bash
log=".claude/history/daily/<today>.md"
[ -f "$log" ] || printf '## Claude Code 작업 로그\n\n' > "$log"
# - HH:MM | [<device-label>] | korea-contract-reviewer | <contract_type> — 리스크 N건, 누락 M건
```

device-label은 `$CLAUDE_DEVICE_LABEL` 또는
`~/.claude/hooks/get-device-label.sh` 출력.

사용자 보고: 저장 경로, 리스크 조항 수, 누락 조항 수, 핵심 권고
1~2문장, 전문가 검토 권고 명시.

---

## 4. 최종 md Contract (구조 고정 — 표현 자유)

frontmatter에 아래 키 **전부**. Contract 외 키 금지.

```yaml
---
harness: korea-contract-reviewer
contract_type: <식별한 계약 유형>
slug: <slug>
run_at: <now_kst>
run_id: <run_id>
risk_clause_count: <리스크 조항 수>
missing_clause_count: <누락 조항 수>
---
```

본문 섹션(모두 포함, 요약 맨 앞):

1. **요약** *(맨 앞)* — 계약 유형, 핵심 리스크 한눈, 전문가 검토
   필요 여부.
2. **리스크 조항** — 조항별: 위치·문구 요지 / 왜 리스크 / 한국
   법·표준 대조 근거 / 권고 방향.
3. **누락 조항** — 통상 있어야 하나 빠진 조항 + 보완 방향.
4. **권고·대안 문구** — 우선순위순 수정 권고. 대안 문구 예시.
5. **한계·면책** — 1차 검토임, 변호사·노무사 등 **전문가 검토
   권장**(강제), 전자서명 연동(모두싸인 등) **미연결 — 검토 후
   수동 진행** 명시.

---

## 5. 불변식 (어기면 하네스 실패)

1. 오리지널 토폴로지 보존 — Skill 단일 워크플로우. subagent·분업
   위임을 끼우지 않는다(agent 파일 없음).
2. 텍스트 검토 기능 보존. 전자서명 연동은 흉내내지 말고 "미연결"
   정직 명시.
3. 입력에 없는 조항 생성 금지. 법령·표준약관은 실재하는 것만,
   불확실은 "확인 필요"로.
4. 중대 사안 "전문가 검토 권장" 디스클레이머 강제. 법률 자문
   대체 금지.
5. 개인정보(실명·주민번호·연락처)는 산출물·로그·slug에 마스킹.
6. 저장 후 grep 기계 확인한 뒤에만 완료 보고.
