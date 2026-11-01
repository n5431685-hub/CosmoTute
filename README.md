# 🪐 CosmoTute — Adaptive Learning Engine

**India-focused adaptive assessment for Class 6–10 students, powered by Bayesian Knowledge Tracing (BKT)**

Built for hackathon demo. Class 8 Math seed data included (8 skills, 28 questions, 5 demo students).

---

## Quick Start (2 terminals)

### Terminal 1 — Backend
```bash
cd backend
pip install fastapi uvicorn sqlmodel pyBKT numpy pandas pydantic httpx pytest
python seed/seed_db.py        # seed the database once
uvicorn app.main:app --reload --port 8000
```


### Terminal 2 — Frontend
```bash
cd frontend
npm install
npm run dev
```


---

## Run Tests
```bash
# From project root
python -m pytest tests/ -v
```
Expected: **57 passed** ✅

---

## Architecture

```
CosmoTute/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── bkt.py              ← BKT HMM forward-pass engine
│   │   │   ├── question_selector.py← Adaptive difficulty selector
│   │   │   └── error_tagger.py     ← Conceptual/Careless/Language-confusion tagger
│   │   ├── models/
│   │   │   ├── db.py               ← SQLModel tables (SQLite)
│   │   │   └── schemas.py          ← Pydantic API schemas
│   │   ├── routers/
│   │   │   ├── answers.py          ← POST /api/answer
│   │   │   ├── questions.py        ← GET /api/next-question/{student}/{skill}
│   │   │   ├── students.py         ← GET /api/students + mastery
│   │   │   ├── skills.py           ← GET /api/skills
│   │   │   └── dashboard.py        ← GET /api/dashboard/*
│   │   ├── services/
│   │   │   ├── bkt_service.py      ← BKT orchestration + DB
│   │   │   └── dashboard_service.py← Heatmap + flag aggregation
│   │   └── main.py                 ← FastAPI app
│   └── seed/
│       ├── skills.json             ← 8 Class-8 skills with BKT params
│       ├── questions.json          ← 28 questions (difficulty 1/2/3)
│       ├── students.json           ← 5 Indian student profiles
│       └── seed_db.py              ← Database seeder
├── tests/
│   ├── test_bkt_math.py            ← 32 unit tests: BKT formulas
│   └── test_bkt_simulation.py      ← 25 simulation tests
└── frontend/
    └── src/
        ├── api/client.ts           ← Typed API client
        ├── pages/
        │   ├── StudentApp.tsx      ← Learn/Solve/Test mode UI
        │   └── TeacherDashboard.tsx← Heatmap + flags + error charts
        └── App.tsx                 ← Landing + role selector
```

---

## BKT Model

Each skill has 4 hidden Markov parameters:

| Param | Meaning |
|---|---|
| P(L₀) | Initial mastery probability |
| P(T) | Learning rate (unmastered → mastered) |
| P(S) | Slip (mastered student answers wrong) |
| P(G) | Guess (unmastered student answers correctly) |

**Update rule per answer:**
1. Bayesian posterior: P(L | obs) using Bayes' theorem
2. Learning step: P(L_next) = P(L | obs) + (1 - P(L | obs)) × P(T)

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/answer` | Submit answer → BKT update |
| GET | `/api/next-question/{sid}/{skill_id}` | Adaptive question selection |
| GET | `/api/students` | List students |
| GET | `/api/students/{id}/mastery` | Per-skill mastery for student |
| GET | `/api/skills` | List skills |
| GET | `/api/dashboard/heatmap` | Skill × student mastery grid |
| GET | `/api/dashboard/flags` | At-risk students |
| GET | `/api/dashboard/errors/{id}` | Error breakdown per student |

---

## Error Types

| Type | Trigger |
|---|---|
| **Conceptual** | Wrong on easy Q, low mastery → fundamental gap |
| **Careless** | Wrong on hard Q, high mastery → silly mistake |
| **Language Confusion** | Answer matches India-specific L1 interference pattern (lakh/million, SI formula direction, etc.) |

---

## Demo Students

| Name | Profile | School |
|---|---|---|
| Aarav Sharma | Strong student | DPS Noida |
| Priya Nair | Average | KV Bangalore |
| Rohan Mehta | Struggling | St Xavier's Mumbai |
| Sneha Reddy | Strong algebra, weak geometry | Narayana Hyderabad |
| Kiran Patel | New student | Amreli Ahmedabad |
