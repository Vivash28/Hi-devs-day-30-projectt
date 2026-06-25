from __future__ import annotations

import os
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
API_KEY = os.getenv("API_KEY", "change-me")

st.set_page_config(page_title="Learning Recommendation Service", layout="wide")

st.title("Learning Recommendation Service (Mini Frontend)")

with st.sidebar:
    st.header("Settings")
    user_id = st.number_input("User ID", min_value=1, value=1, step=1)
    limit = st.slider("Limit", min_value=1, max_value=20, value=10)
    api_base = st.text_input("API Base", value=API_BASE)
    api_key = st.text_input("API Key", value=API_KEY, type="password")
    st.caption("Tip: Start the FastAPI server, then use this UI to fetch recommendations and send feedback.")

headers = {"X-API-Key": api_key}

col1, col2 = st.columns([2, 1])

with col2:
    st.subheader("Service Status")
    try:
        r = requests.get(f"{api_base}/health", timeout=2)
        st.write(r.json())
    except Exception as e:
        st.error(f"API not reachable: {e}")

    if st.button("View Metrics"):
        try:
            r = requests.get(f"{api_base}/metrics", timeout=5)
            st.json(r.json())
        except Exception as e:
            st.error(str(e))

with col1:
    st.subheader("Recommendations")

    if st.button("Get Recommendations"):
        try:
            r = requests.get(
                f"{api_base}/recommend/{int(user_id)}",
                params={"limit": int(limit)},
                headers=headers,
                timeout=10,
            )
            if r.status_code != 200:
                st.error(f"Error {r.status_code}: {r.text}")
            else:
                payload = r.json()
                st.caption(f"cached={payload.get('cached')} cold_start={payload.get('cold_start')}")
                recs = payload.get("recommendations", [])
                st.session_state["recs"] = recs
        except Exception as e:
            st.error(str(e))

    recs = st.session_state.get("recs", [])
    if recs:
        for rec in recs:
            with st.container(border=True):
                st.markdown(f"### {rec['title']}")
                st.write(
                    {
                        "content_id": rec["content_id"],
                        "category": rec["category"],
                        "difficulty": rec["difficulty"],
                        "score": round(rec["score"], 4),
                        "explanation": rec["explanation"],
                    }
                )
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button(f"Like {rec['content_id']}"):
                        fb = {"user_id": int(user_id), "content_id": rec["content_id"], "type": "like", "rating": 5}
                        fr = requests.post(f"{api_base}/feedback", json=fb, headers=headers, timeout=10)
                        st.write(fr.json() if fr.ok else fr.text)
                with c2:
                    if st.button(f"Complete {rec['content_id']}"):
                        fb = {"user_id": int(user_id), "content_id": rec["content_id"], "type": "complete", "rating": 5}
                        fr = requests.post(f"{api_base}/feedback", json=fb, headers=headers, timeout=10)
                        st.write(fr.json() if fr.ok else fr.text)
                with c3:
                    if st.button(f"Dislike {rec['content_id']}"):
                        fb = {"user_id": int(user_id), "content_id": rec["content_id"], "type": "dislike", "rating": 1}
                        fr = requests.post(f"{api_base}/feedback", json=fb, headers=headers, timeout=10)
                        st.write(fr.json() if fr.ok else fr.text)