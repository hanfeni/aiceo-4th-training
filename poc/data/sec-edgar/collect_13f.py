#!/usr/bin/env python3
"""SEC EDGAR 13F 기관보유 데이터셋 다운로드 + 압축해제 (재현용).

SEC.gov 는 User-Agent 필수. 없으면 403/봇차단.
13F Form Data Sets 는 분기 단위 ZIP (TSV 묶음). 퍼블릭 도메인.

검증된 URL (2025 Q3 = 01sep2025~30nov2025 제출분):
  https://www.sec.gov/files/structureddata/data/form-13f-data-sets/01sep2025-30nov2025_form13f.zip

ZIP 내부 9파일: SUBMISSION/COVERPAGE/INFOTABLE/OTHERMANAGER/OTHERMANAGER2/
SUMMARYPAGE/SIGNATURE TSV + FORM13F_metadata.json + FORM13F_readme.htm
"""
import subprocess
import sys
import zipfile
from pathlib import Path

UA = "aiceo-4th-training-lecture noreply@example.com"
ZIP_URL = (
    "https://www.sec.gov/files/structureddata/data/form-13f-data-sets/"
    "01sep2025-30nov2025_form13f.zip"
)
HERE = Path(__file__).parent
ZIP_PATH = HERE / "form13f_2025q3.zip"
EXTRACT_DIR = HERE / "13f"


def download():
    if ZIP_PATH.exists() and ZIP_PATH.stat().st_size > 80_000_000:
        print(f"[skip] {ZIP_PATH.name} already present ({ZIP_PATH.stat().st_size:,} bytes)")
        return
    print(f"[dl] {ZIP_URL}")
    # SEC rate limit: 단발 요청 + UA 필수
    p = subprocess.run(
        ["curl", "-sS", "-L", "-A", UA, "-o", str(ZIP_PATH), ZIP_URL, "--max-time", "600"],
        capture_output=True,
    )
    if p.returncode != 0:
        print(p.stderr.decode("utf-8", "ignore"), file=sys.stderr)
        sys.exit(1)
    print(f"[ok] {ZIP_PATH.stat().st_size:,} bytes")


def extract():
    EXTRACT_DIR.mkdir(exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH) as z:
        names = z.namelist()
        for n in names:
            target = EXTRACT_DIR / n
            if target.exists() and target.stat().st_size > 0:
                continue
            z.extract(n, EXTRACT_DIR)
        print(f"[ok] extracted {len(names)} files -> {EXTRACT_DIR}/")
    for f in sorted(EXTRACT_DIR.iterdir()):
        print(f"  {f.name:28s} {f.stat().st_size:>12,} bytes")


if __name__ == "__main__":
    download()
    extract()
