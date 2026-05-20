#!/usr/bin/env python3
"""
논문 인용 온톨로지 데이터셋 생성 — SEC EDGAR subset 과 동일 CSV 형식.

배경(aiceo-4th-agent 온톨로지 실습): movies 와 동일하게 "데이터 소스만
교체" 구조. 노드/관계 골격 재사용, 데이터만 학술 도메인으로.

컬럼 매핑(SEC EDGAR 형식 그대로):
  managers   = 저자    : accession_number(저자 id), cik, manager_name(저자명),
                         city/state(소속 기관), ...
  holdings   = 집필 엣지: accession_number(저자), cusip(논문 id),
                         name_of_issuer(논문 제목), value_usd_thousands(기여도),
                         shares, shares_type(SH), put_call
  top_issuers= 논문 crowding: cusip, name_of_issuer, n_filer_managers(공저자 수),
                         total_value_usd_thousands(피인용 등 영향력)

합성 설계: 연구자 풀 + 논문 풀. 공저(2홉)·공저 네트워크(3홉)·다작 저자
질의가 풍부하도록 한 논문에 여러 저자 배정. 결정론적 시드.
"""

import csv
import hashlib
import random

random.seed(7)

# 합성 연구자 40명 (분야별 — 공저 네트워크 데모)
AUTHORS = [
    "Geoffrey Hinton", "Yann LeCun", "Yoshua Bengio", "Andrew Ng",
    "Fei-Fei Li", "Ian Goodfellow", "Demis Hassabis", "Ilya Sutskever",
    "Christopher Manning", "Jurgen Schmidhuber", "Daphne Koller", "Michael Jordan",
    "Sebastian Thrun", "Pieter Abbeel", "Chelsea Finn", "Sergey Levine",
    "Kaiming He", "Ross Girshick", "Jitendra Malik", "Andrej Karpathy",
    "Quoc Le", "Jeff Dean", "Oriol Vinyals", "Alex Graves",
    "Richard Sutton", "David Silver", "Volodymyr Mnih", "Tomas Mikolov",
    "Ashish Vaswani", "Noam Shazeer", "Jacob Devlin", "Ming-Wei Chang",
    "Dario Amodei", "Tom Brown", "Sam Altman", "Wojciech Zaremba",
    "Jared Kaplan", "Jan Leike", "Paul Christiano", "Chris Olah",
]

# 합성 논문 60편
PAPERS = [
    "Deep Residual Learning", "Attention Is All You Need", "BERT Pretraining",
    "GANs", "ImageNet Classification", "AlphaGo", "Playing Atari with RL",
    "Word2Vec", "Sequence to Sequence Learning", "Dropout Regularization",
    "Batch Normalization", "Adam Optimizer", "GPT Language Models",
    "Scaling Laws for Neural LMs", "InstructGPT", "Constitutional AI",
    "Diffusion Models", "Vision Transformers", "CLIP", "Contrastive Learning",
    "Graph Neural Networks", "Variational Autoencoders", "Neural Turing Machines",
    "Memory Networks", "Pointer Networks", "Neural Machine Translation",
    "Transformer-XL", "XLNet", "RoBERTa", "T5 Text-to-Text",
    "ELECTRA", "DistilBERT", "ALBERT", "ELMo Contextual Embeddings",
    "FastText", "GloVe Embeddings", "Capsule Networks", "Wide ResNet",
    "DenseNet", "EfficientNet", "MobileNets", "SqueezeNet",
    "U-Net Segmentation", "Mask R-CNN", "Faster R-CNN", "YOLO Detection",
    "SSD Detection", "Feature Pyramid Networks", "Style Transfer",
    "CycleGAN", "Progressive GANs", "StyleGAN", "BigGAN",
    "WaveNet Audio", "Tacotron Speech", "Deep Q-Networks", "Policy Gradients",
    "Proximal Policy Optimization", "Soft Actor-Critic", "Model-Agnostic Meta-Learning",
]

INSTITUTIONS = [("TORONTO", "A6"), ("STANFORD", "CA"), ("MONTREAL", "A6"),
                ("MOUNTAIN VIEW", "CA"), ("LONDON", "X0"), ("BERKELEY", "CA")]


def fake_cusip(seed: str) -> str:
    h = hashlib.md5(seed.encode()).hexdigest()
    digits = "".join(c for c in h if c.isdigit())
    return (digits + "000000000")[:9]


def fake_accession(seed: str, idx: int) -> str:
    h = hashlib.md5(seed.encode()).hexdigest()
    digits = "".join(c for c in h if c.isdigit()) + "0000000000000000"
    return f"{digits[:10]}-25-{idx:06d}"


author_acc = {a: fake_accession(a, i) for i, a in enumerate(AUTHORS)}
author_cik = {a: fake_accession(a, i).split("-")[0] for i, a in enumerate(AUTHORS)}
paper_cusip = {p: fake_cusip(p) for p in PAPERS}

# 집필 관계: 논문당 2~6명 공저. 기여도(value)는 저자 순위 가중.
holdings_rows = []
paper_author_count = {p: 0 for p in PAPERS}
for p in PAPERS:
    n = random.randint(2, 6)
    authors = random.sample(AUTHORS, n)
    paper_author_count[p] = n
    for rank, a in enumerate(authors):
        contribution = (n - rank) * random.randint(500, 1800)
        holdings_rows.append({
            "accession_number": author_acc[a],
            "cusip": paper_cusip[p],
            "name_of_issuer": p,
            "value_usd_thousands": contribution,
            "shares": random.randint(1, 3),
            "shares_type": "SH",
            "put_call": "",
        })

managers_rows = []
for i, a in enumerate(AUTHORS):
    city, st = INSTITUTIONS[i % len(INSTITUTIONS)]
    managers_rows.append({
        "accession_number": author_acc[a],
        "cik": author_cik[a],
        "manager_name": a,
        "city": city,
        "state_or_country": st,
        "zipcode": f"{20000 + i:05d}",
        "filing_date": "01-JAN-2025",
        "submission_type": "PAPER",
        "period_of_report": "31-DEC-2024",
    })

# top_issuers(논문 crowding) — 공저자 수 + 피인용 흉내(기여도 합계 ×배수)
issuer_value = {}
for r in holdings_rows:
    issuer_value[r["cusip"]] = issuer_value.get(r["cusip"], 0) + r["value_usd_thousands"]
top_issuers_rows = []
for p in PAPERS:
    cu = paper_cusip[p]
    # 피인용 흉내: 기여도 합 × 랜덤 인용 배수(영향력 변별)
    citations = issuer_value.get(cu, 0) * random.randint(3, 40)
    top_issuers_rows.append({
        "cusip": cu,
        "name_of_issuer": p,
        "n_filer_managers": paper_author_count[p],
        "total_value_usd_thousands": citations,
    })


def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"  {path}: {len(rows)}행")


print("논문 인용 온톨로지 데이터셋 생성:")
write_csv(
    "managers_subset.csv",
    ["accession_number", "cik", "manager_name", "city", "state_or_country",
     "zipcode", "filing_date", "submission_type", "period_of_report"],
    managers_rows,
)
write_csv(
    "holdings_subset.csv",
    ["accession_number", "cusip", "name_of_issuer", "value_usd_thousands",
     "shares", "shares_type", "put_call"],
    holdings_rows,
)
write_csv(
    "top_issuers_subset.csv",
    ["cusip", "name_of_issuer", "n_filer_managers", "total_value_usd_thousands"],
    top_issuers_rows,
)
print(f"저자 {len(AUTHORS)}명 · 논문 {len(PAPERS)}편 · 집필 {len(holdings_rows)}건")
