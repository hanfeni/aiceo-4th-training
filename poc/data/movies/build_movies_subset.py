#!/usr/bin/env python3
"""
영화 온톨로지 데이터셋 생성 — SEC EDGAR subset 과 동일 CSV 형식.

배경(aiceo-4th-agent 온톨로지 실습):
  GraphRAG vs RAG vs Text-to-SQL 비교 데모에서 "데이터 소스만 교체"
  하는 구조다. 노드/관계 골격(주체-[관계]->대상 + crowding + Position)은
  SEC EDGAR 와 동일하게 재사용하고, 데이터만 영화 도메인으로 바꾼다.

컬럼 매핑(SEC EDGAR 형식 그대로 — load.ts 가 같은 인덱스로 읽음):
  managers   = 배우    : accession_number(배우 고유 id), cik, manager_name(배우명),
                         city, state_or_country, zipcode, filing_date,
                         submission_type, period_of_report
  holdings   = 출연 엣지: accession_number(배우), cusip(영화 id),
                         name_of_issuer(영화 제목), value_usd_thousands(배역 비중),
                         shares, shares_type(SH), put_call
  top_issuers= 영화 crowding: cusip, name_of_issuer, n_filer_managers(출연 배우 수),
                         total_value_usd_thousands

합성 설계: 유명 배우 풀 + 영화 풀을 두고, 각 영화에 여러 배우를 배정해
공동출연(2홉)·연결고리(3홉)·다작 배우 질의가 풍부하도록 한다(GraphRAG
우월성 시연 목적). 결정론적 시드로 재현 가능.
"""

import csv
import hashlib
import random

random.seed(42)

# 유명 배우 40명 (멀티홉 데모 — 실명 기반 합성 출연 관계)
ACTORS = [
    "Tom Hanks", "Leonardo DiCaprio", "Meryl Streep", "Denzel Washington",
    "Cate Blanchett", "Brad Pitt", "Scarlett Johansson", "Morgan Freeman",
    "Tom Cruise", "Natalie Portman", "Robert De Niro", "Julia Roberts",
    "Christian Bale", "Anne Hathaway", "Matt Damon", "Charlize Theron",
    "Joaquin Phoenix", "Emma Stone", "Ryan Gosling", "Jennifer Lawrence",
    "Samuel L Jackson", "Viola Davis", "Hugh Jackman", "Amy Adams",
    "Michael Fassbender", "Jessica Chastain", "Christoph Waltz", "Saoirse Ronan",
    "Mark Ruffalo", "Margot Robbie", "Gary Oldman", "Frances McDormand",
    "Idris Elba", "Florence Pugh", "Oscar Isaac", "Tilda Swinton",
    "Adam Driver", "Lupita Nyongo", "Timothee Chalamet", "Zendaya",
]

# 영화 60편 (합성 — 다양한 앙상블 규모)
MOVIES = [
    "Inception", "The Departed", "Pulp Fiction", "Forrest Gump",
    "The Revenant", "Black Swan", "Gladiator", "Interstellar",
    "The Dark Knight", "Once Upon a Time in Hollywood", "Joker", "La La Land",
    "The Wolf of Wall Street", "Mad Max Fury Road", "Dunkirk", "Oppenheimer",
    "Barbie", "Dune", "Dune Part Two", "No Country for Old Men",
    "The Grand Budapest Hotel", "Birdman", "Whiplash", "Arrival",
    "The Shape of Water", "Parasite Remake", "Knives Out", "Marriage Story",
    "Little Women", "Jojo Rabbit", "Ford v Ferrari", "1917",
    "Tenet", "The Irishman", "Bohemian Rhapsody", "A Star Is Born",
    "Green Book", "Roma Nights", "Vice", "The Favourite",
    "Three Billboards", "Phantom Thread", "Lady Bird", "Call Me By Your Name",
    "Manchester by the Sea", "Moonlight", "Hidden Figures", "Hacksaw Ridge",
    "Spotlight", "The Big Short", "The Martian", "Bridge of Spies",
    "Sicario", "Nightcrawler", "Gone Girl", "12 Years a Slave",
    "American Hustle", "Her", "Gravity", "Captain Phillips",
]


def fake_cusip(seed: str) -> str:
    """영화 제목 → 9자리 의사 CUSIP(SEC 형식 흉내, 결정론적)."""
    h = hashlib.md5(seed.encode()).hexdigest()
    digits = "".join(c for c in h if c.isdigit())
    return (digits + "000000000")[:9]


def fake_accession(seed: str, idx: int) -> str:
    """배우 → accession_number 형식(NNNNNNNNNN-NN-NNNNNN) 흉내."""
    h = hashlib.md5(seed.encode()).hexdigest()
    digits = "".join(c for c in h if c.isdigit()) + "0000000000000000"
    return f"{digits[:10]}-25-{idx:06d}"


# 배우별 accession/cik 부여
actor_acc = {a: fake_accession(a, i) for i, a in enumerate(ACTORS)}
actor_cik = {a: fake_accession(a, i).split("-")[0] for i, a in enumerate(ACTORS)}
movie_cusip = {m: fake_cusip(m) for m in MOVIES}

# 출연 관계 생성: 각 영화에 4~9명 배우 배정(앙상블). 일부 배우는 다작
# (멀티홉 허브). value_usd_thousands = 배역 비중(주연 큰 값).
holdings_rows = []
movie_actor_count = {m: 0 for m in MOVIES}
for m in MOVIES:
    n = random.randint(4, 9)
    cast = random.sample(ACTORS, n)
    movie_actor_count[m] = n
    for rank, a in enumerate(cast):
        # 주연(앞 순위) 비중 큼 — 흥행/배역 가중치 흉내
        billing = (n - rank) * random.randint(800, 2200)
        holdings_rows.append({
            "accession_number": actor_acc[a],
            "cusip": movie_cusip[m],
            "name_of_issuer": m,
            "value_usd_thousands": billing,
            "shares": random.randint(1, 5),  # 배역 수 흉내
            "shares_type": "SH",
            "put_call": "",
        })

# managers(배우) — 도시는 합성(LA/NY 등)
CITIES = [("LOS ANGELES", "CA"), ("NEW YORK", "NY"), ("LONDON", "X0"),
          ("SYDNEY", "C3"), ("DUBLIN", "L2")]
managers_rows = []
for i, a in enumerate(ACTORS):
    city, st = CITIES[i % len(CITIES)]
    managers_rows.append({
        "accession_number": actor_acc[a],
        "cik": actor_cik[a],
        "manager_name": a,
        "city": city,
        "state_or_country": st,
        "zipcode": f"{10000 + i:05d}",
        "filing_date": "01-JAN-2025",
        "submission_type": "FILM",
        "period_of_report": "31-DEC-2024",
    })

# top_issuers(영화 crowding) — 출연 배우 수 + 비중 합계
issuer_value = {}
for r in holdings_rows:
    issuer_value[r["cusip"]] = issuer_value.get(r["cusip"], 0) + r["value_usd_thousands"]
top_issuers_rows = []
for m in MOVIES:
    cu = movie_cusip[m]
    top_issuers_rows.append({
        "cusip": cu,
        "name_of_issuer": m,
        "n_filer_managers": movie_actor_count[m],
        "total_value_usd_thousands": issuer_value.get(cu, 0),
    })


def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"  {path}: {len(rows)}행")


print("영화 온톨로지 데이터셋 생성:")
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
print(f"배우 {len(ACTORS)}명 · 영화 {len(MOVIES)}편 · 출연 {len(holdings_rows)}건")
