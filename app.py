import streamlit as tf
import pandas as pd
import json
from pathlib import Path
import os
import sys

# Add current folder to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from rank import score_candidate, generate_reasoning

tf.set_page_config(
    page_title="Redrob Ranker - Sandbox Dashboard",
    page_icon="🎯",
    layout="wide"
)

# Custom Styling (Dark theme/Glassmorphism feel)
tf.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    h1, h2, h3 {
        color: #00f2fe;
        font-family: 'Outfit', sans-serif;
    }
    .stButton>button {
        background-color: #00f2fe;
        color: black;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #4facfe;
        color: white;
        box-shadow: 0 0 15px rgba(0, 242, 254, 0.4);
    }
    .candidate-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .badge {
        background-color: #00f2fe;
        color: black;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.8em;
        font-weight: bold;
        margin-right: 5px;
    }
    </style>
""", unsafe_allow_html=True)

tf.title("🎯 Redrob Ranker - Candidate Discovery Dashboard")
tf.subheader("Founding Team Senior AI Engineer Ranker Sandbox")

# Side bar details
tf.sidebar.header("Challenge Metadata")
tf.sidebar.markdown("""
**Role:** Senior AI Engineer — Founding Team
**Target Experience:** 5–9 Years
**Location:** Pune/Noida, India (Hybrid)
**Compute Limits:** 5 mins, 16GB RAM, CPU-Only, Offline
""")

# Load candidates from sample file or uploaded file
tf.sidebar.header("Rank Settings")
use_uploaded = tf.sidebar.checkbox("Upload custom candidates file")
candidates = []

if use_uploaded:
    uploaded_file = tf.sidebar.file_uploader("Upload candidates (.json or .jsonl)", type=["json", "jsonl"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".json"):
                candidates = json.load(uploaded_file)
            else:
                for line in uploaded_file:
                    if line.strip():
                        candidates.append(json.loads(line))
            tf.sidebar.success(f"Loaded {len(candidates)} candidates.")
        except Exception as e:
            tf.sidebar.error(f"Error loading file: {e}")
else:
    sample_path = Path(__file__).parent / "sample_candidates.json"
    if sample_path.exists():
        with open(sample_path, "r", encoding="utf-8") as f:
            candidates = json.load(f)
        tf.sidebar.info(f"Loaded 50 sample candidates from sample_candidates.json")
    else:
        tf.sidebar.error("sample_candidates.json not found. Please upload a candidates file.")

# Run ranking
if candidates:
    scored = []
    for cand in candidates:
        score, matched_skills, is_hp = score_candidate(cand)
        if not is_hp:
            scored.append({
                "candidate_id": cand.get("candidate_id"),
                "name": cand.get("profile", {}).get("anonymized_name", "Anonymized"),
                "title": cand.get("profile", {}).get("current_title", "N/A"),
                "experience": cand.get("profile", {}).get("years_of_experience", 0),
                "location": cand.get("profile", {}).get("location", "N/A"),
                "score": score,
                "matched_skills": matched_skills,
                "data": cand
            })
            
    # Sort
    scored.sort(key=lambda x: (-x["score"], x["candidate_id"]))
    
    # Render table
    df_data = []
    for idx, cand in enumerate(scored):
        rank = idx + 1
        reasoning = generate_reasoning(cand["data"], rank, cand["matched_skills"])
        df_data.append({
            "Rank": rank,
            "ID": cand["candidate_id"],
            "Name": cand["name"],
            "Title": cand["title"],
            "Experience (Yrs)": cand["experience"],
            "Location": cand["location"],
            "Score": cand["score"],
            "Reasoning": reasoning
        })
        
    df = pd.DataFrame(df_data)
    
    tf.markdown("### Top Ranked Candidates")
    tf.dataframe(df.set_index("Rank"), use_container_width=True)
    
    # Inspect individual candidate
    tf.markdown("### 🔍 Inspect Candidate Profiles")
    cand_ids = [c["candidate_id"] for c in scored]
    selected_id = tf.selectbox("Select Candidate ID to inspect:", cand_ids)
    
    if selected_id:
        selected_cand = next(c for c in scored if c["candidate_id"] == selected_id)
        data = selected_cand["data"]
        profile = data.get("profile", {})
        skills = data.get("skills", [])
        history = data.get("career_history", [])
        signals = data.get("redrob_signals", {})
        
        col1, col2 = tf.columns(2)
        with col1:
            tf.markdown(f"**Name:** {profile.get('anonymized_name')}")
            tf.markdown(f"**Current Title:** {profile.get('current_title')} at {profile.get('current_company')}")
            tf.markdown(f"**Headline:** *{profile.get('headline')}*")
            tf.markdown(f"**Location:** {profile.get('location')} ({profile.get('country')})")
            tf.markdown(f"**Years of Experience:** {profile.get('years_of_experience')}")
            tf.markdown(f"**Summary:** {profile.get('summary')}")
            
        with col2:
            tf.markdown(f"**Match Score:** `{selected_cand['score']}`")
            tf.markdown(f"**Notice Period:** `{signals.get('notice_period_days')}` days")
            tf.markdown(f"**Open to Work:** `{signals.get('open_to_work_flag')}`")
            tf.markdown(f"**Last Active:** `{signals.get('last_active_date')}`")
            tf.markdown(f"**Expected Salary:** {signals.get('expected_salary_range_inr_lpa', {}).get('min')} - {signals.get('expected_salary_range_inr_lpa', {}).get('max')} LPA")
            
        tf.markdown("#### Skills & Experience")
        skills_cols = tf.columns(4)
        for i, s in enumerate(skills):
            col_idx = i % 4
            skills_cols[col_idx].markdown(f"❇️ **{s.get('name')}** ({s.get('proficiency')}) - {s.get('duration_months', 0)} mo")
            
        tf.markdown("#### Career History")
        for h in history:
            tf.markdown(f"""
            <div class="candidate-card">
                <strong>{h.get('title')}</strong> at {h.get('company')} ({h.get('start_date')} to {h.get('end_date') or 'Present'}) - {h.get('duration_months')} months<br/>
                <em>Industry: {h.get('industry')} | Size: {h.get('company_size')}</em><br/>
                <p style='margin-top:8px;'>{h.get('description')}</p>
            </div>
            """, unsafe_allow_html=True)
else:
    tf.warning("No candidates available to rank. Please verify your workspace contains sample_candidates.json or upload a candidates file.")
