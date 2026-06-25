# Learning Recommendation Service

A complete, end-to-end recommendation system for learning content with a SQLite data layer, a modular recommendation engine, and a FastAPI backend. Includes offline evaluation (Precision@5, Recall@5, NDCG@5), unit tests, a simple caching layer, and a Streamlit mini-frontend to explore results in the browser.

## Features
- SQLite + SQLAlchemy models (users, content, skills, interactions, mappings)
- Recommendation orchestration with cold-start support, caching, and explanations
- FastAPI REST API: `/recommend`, `/feedback`, `/health`, `/metrics`
- Seed script with sample dataset (10 users, 20 content items)
- Evaluation report generator + chart
- Concurrent load test script
- Streamlit mini-frontend

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
copy .env.example .env
```

### Seed the database
```bash
python scripts/seed_data.py
```

### Run the API
```bash
set API_KEY=change-me
set DATABASE_URL=sqlite:///./learning_reco.db
uvicorn api.app:app --reload
```

Open:
- Swagger UI: http://127.0.0.1:8000/docs

### Run the mini-frontend (Streamlit)
In a second terminal:
```bash
set API_BASE=http://127.0.0.1:8000
set API_KEY=change-me
streamlit run frontend/app.py
```

Open:
- Frontend UI: http://127.0.0.1:8501

## Evaluation
```bash
python scripts/evaluate.py
```
Outputs:
- `evaluation_report.md`
- `evaluation_metrics.png`

## Load test (10 concurrent users)
Start the API first, then:
```bash
set API_BASE=http://127.0.0.1:8000
set API_KEY=change-me
python scripts/load_test.py
```

## API Authentication
Pass an API key header:
- `X-API-Key: change-me`