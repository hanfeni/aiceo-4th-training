# 의료/제약 도메인 샘플 데이터 (AI CEO 4기 실습용)

서울대 AI CEO 4기 강의(2026-05-22) RAG/임베딩 실습용으로 **실제 수집**한
공공 의료/제약 데이터입니다. 추측·시뮬레이션 없이 전부 실 curl/HTTP 수집.

## 파일 구성

| 파일 | 종류 | 설명 |
|------|------|------|
| `drug_master_sample.csv` | 구조화 | 심평원 약가마스터 의약품표준코드 샘플 (헤더+20,000행, 22컬럼, UTF-8) |
| `drug_detail.jsonl` | 검색 문서 | 의약품안전나라(nedrug) 허가상세 본문. 1줄=1문서 |
| `_collect_meta.json` | 메타 | 수집 출처·통계·라이선스·JOIN 키 명세 |

## 1. drug_master_sample.csv (구조화 데이터)

- **출처**: 공공데이터포털 — 건강보험심사평가원_약가마스터_의약품표준코드
  - 데이터셋: https://www.data.go.kr/data/15067462/fileData.do
  - 직링크(무인증): `fileDownload.do?atchFileId=FILE_000000003550228&fileDetailSn=1&insertDataPrcus=N`
- **원본**: 52MB CSV / EUC-KR / 305,522 데이터행 / 22컬럼
- **샘플링**: EUC-KR→UTF-8 iconv 변환 후 1/15 systematic sampling으로 20,000행 추출
- **라이선스**: 공공누리 제1유형 (출처표시) — 출처: 건강보험심사평가원
- **컬럼(22)**: 한글상품명, 업체명, 약품규격, 제품총수량, 제형구분, 포장형태,
  **품목기준코드**, 품목허가일자, 전문일반구분, 대표코드, **표준코드**,
  제품코드(개정후), 일반명코드(성분명코드), 비고, 취소일자, 양도양수적용(공고)일자,
  양도양수종료일자, 일련번호생략여부, 일련번호생략사유, **국제표준코드(ATC코드)**,
  특수관리약품구분, 의약품판독장비구분

## 2. drug_detail.jsonl (검색 문서)

- **출처**: 식약처 의약품안전나라 nedrug.mfds.go.kr (무인증)
  - 검색: `POST /searchDrug` (etcOtcCode=02=전문의약품 필터)
  - 본문: `GET /pbp/cmn/html/drb/<itemSeq>/{EE,UD,NB}`
    - EE=효능효과, UD=용법용량, NB=사용상의 주의사항
- **필터**: 전문의약품 위주, 본문 char_count >= 2000 (짧은 일반약/취하품목 제외)
- **레코드 스키마**:
  ```json
  {
    "doc_id": "nedrug-<itemSeq>",
    "item_seq": "<itemSeq>",
    "title": "<제품명>",
    "body": "<효능효과+용법용량+사용상의주의사항 텍스트>",
    "url": "https://nedrug.mfds.go.kr/pbp/CCBBB01/getItemDetail?itemSeq=<NNN>",
    "collected_at": "<KST ISO8601>",
    "char_count": <본문 글자수>,
    "item_base_code": "<품목기준코드 — 약가마스터 JOIN 키>",
    "std_code": "<표준코드>",
    "ingredient": "<성분명>",
    "entp_name": "<업체명>",
    "etc_otc": "<전문/일반>"
  }
  ```
- **라이선스**: 식약처 공공저작물 (저작권법 §24의2, 출처표시 — 식품의약품안전처)

## JOIN 키

`drug_detail.jsonl.item_base_code` ↔ `drug_master_sample.csv.품목기준코드`

두 데이터셋을 품목기준코드로 조인하면 비정형 허가상세 문서에
약가마스터의 구조화 속성(ATC코드, 전문일반구분, 허가일자 등)을 결합할 수 있습니다.

## 재현 방법

```bash
# 1. 약가마스터
curl -L -o raw.csv "https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000003550228&fileDetailSn=1&insertDataPrcus=N"
iconv -f EUC-KR -t UTF-8 raw.csv > utf8.csv
# atchFileId 만료 시: data.go.kr/data/15067462/fileData.do HTML의
#   schema.org contentUrl에서 최신 FILE_xxx 재추출

# 2. nedrug 허가상세
python3 collect_nedrug.py 70   # 70페이지 itemSeq → 본문 수집 → 2000자 필터
```
