from __future__ import annotations

import os
from collections import defaultdict

import pandas as pd
import matplotlib.pyplot as plt

from sqlalchemy import select
from sqlalchemy.orm import Session

from data.database import make_engine, make_session_factory
from data.models import Interaction, User, Base
from engine.orchestrator import RecommendationOrchestrator
from engine.evaluator import precision_at_k, recall_at_k, ndcg_at_k

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./learning_reco.db")


def main():
    engine = make_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    SessionFactory = make_session_factory(engine)

    orch = RecommendationOrchestrator(cache_ttl_seconds=0)

    with SessionFactory() as db:
        users = list(db.scalars(select(User).order_by(User.id)))

        # Define "relevant" items as those the user liked/completed historically
        relevant_by_user = defaultdict(set)
        rows = list(db.scalars(select(Interaction)))
        for r in rows:
            if r.type in ("like", "complete"):
                relevant_by_user[r.user_id].add(r.content_id)

        results = []
        for u in users:
            rec = orch.get_recommendations(db=db, user_id=u.id, limit=10)
            rec_ids = [x["content_id"] for x in rec["recommendations"]]
            relevant = relevant_by_user[u.id]

            p5 = precision_at_k(rec_ids, relevant, k=5)
            r5 = recall_at_k(rec_ids, relevant, k=5)
            n5 = ndcg_at_k(rec_ids, relevant, k=5)

            results.append({"user_id": u.id, "precision@5": p5, "recall@5": r5, "ndcg@5": n5})

    df = pd.DataFrame(results)
    summary = df[["precision@5", "recall@5", "ndcg@5"]].mean().to_dict()
    print("Evaluation summary:", summary)

    # Chart
    ax = df[["precision@5", "recall@5", "ndcg@5"]].plot(kind="bar", figsize=(10, 4), title="Offline Metrics per User")
    ax.set_xlabel("user index")
    ax.set_ylabel("score")
    plt.tight_layout()
    plt.savefig("evaluation_metrics.png")

    # Report markdown
    report_lines = []
    report_lines.append("# Evaluation Report\n")
    report_lines.append(f"- Database: `{DATABASE_URL}`\n")
    report_lines.append("## Mean Metrics\n")
    report_lines.append("| Metric | Value |\n|---|---:|\n")
    for k, v in summary.items():
        report_lines.append(f"| {k} | {v:.4f} |\n")
    report_lines.append("\n## Per-user Metrics (first 10)\n")
    report_lines.append(df.head(10).to_markdown(index=False))
    report_lines.append("\n\n## Chart\n")
    report_lines.append("![metrics](evaluation_metrics.png)\n")

    with open("evaluation_report.md", "w", encoding="utf-8") as f:
        f.write("".join(report_lines))

    print("Wrote evaluation_report.md and evaluation_metrics.png")


if __name__ == "__main__":
    main()