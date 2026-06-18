# Redrob Candidate Discovery & Ranking Engine

This repository contains the ranking engine and interactive sandbox app built for the **Redrob Intelligent Candidate Discovery & Ranking Challenge**. 

Our solution ranks a pool of 100,000 candidate profiles to find the top 100 best-fit candidates for the **Senior AI Engineer — Founding Team** role. It operates completely offline, uses CPU-only processing, and executes in **under 15 seconds** with **0% honeypots in the top 100**.

---

## 🚀 Getting Started

### 1. Setup Environment
Ensure you have Python 3.8+ installed. Install the dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run the Ranking Pipeline (Replication)
To run the ranker on the candidate pool and produce the final compliant CSV:
```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

### 3. Launch the Interactive Sandbox Dashboard
To interactively view the ranking list, search candidates, and inspect individual profile score breakdowns:
```bash
streamlit run app.py
```

---

## 🎯 Architecture & Ranking Methodology

The scoring engine uses a multi-layered rule-based heuristic model. This architecture was chosen over heavy LLM embedding matching to meet the strict compute constraints ($\le 5$ minutes, CPU-only, offline) while maintaining full control over trap avoidance.

```
       [ 100,000 Candidates Pool ]
                   │
                   ▼
       ┌────────────────────────┐
       │   Honeypot Filter      │ ──► Discard Temporal & Schema Anomalies
       └────────────────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │   Title Relevance (40%)│ ──► Boost target AI roles; penalize traps
       └────────────────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │   Experience Curve (20%)│ ──► Optimal 5-9 years; scale down edges
       └────────────────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │   Technical Skills (20%)│ ──► Endorsement & duration trust-weighting
       └────────────────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │   Logistics & Loc (10%)│ ──► Noida/Pune hybrid, relocation & notice
       └────────────────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │   Engagement Mult (10%)│ ──► Login active days & response rates
       └────────────────────────┘
                   │
                   ▼
         [ Top 100 Selected ] ──► Programmatic Dynamic Reasoning Gen
```

### 1. Honeypot & Anomaly Filtering (Hard Constraints)
We identify and discard candidate profiles with impossible states (relevance tier 0):
*   **Zero-Duration Skills**: Discard candidates who have expert/advanced skills with $0$ months duration.
*   **Temporal Collisions**: Discard candidates whose career history starts before their education start year.
*   **Imbalance Experience**: Discard candidates whose stated experience exceeds the years since their first job.
*   **Expected Salary Conflict**: Discard candidates where min salary expectation exceeds max salary expectation.

### 2. Title Relevance & Traps (40% Weight)
*   **Boost**: Candidates with titles matching AI, ML, NLP, Search, Retrieval, or Recommendation Engineer.
*   **Neutral-Tech**: Backend, Software, Data, DevOps, or Frontend Engineers are scored moderately.
*   **Trap Penalties**: Candidates holding non-technical titles (Marketing Manager, HR Manager, Accountant, Operations Manager) are heavily penalized to neutralize keyword stuffers.
*   **Services Trap**: Candidates whose entire career history belongs to IT consulting firms (TCS, Wipro, Infosys, Accenture, Cognizant, etc.) are down-weighted by a factor of 4 unless they have product company experience.

### 3. Experience Fit (20% Weight)
*   Candidates with **5 to 9 years** of experience receive a 1.0 multiplier.
*   Candidates slightly outside (4 years or 10-12 years) receive 0.8.
*   Extreme junior ($<3$ years) or executive/tech-lead only ($>15$ years) roles are down-weighted.

### 4. Technical Skill Match (20% Weight)
*   **Core Retrieval Skills (Weight 10)**: Embeddings, Vector Search, FAISS, Pinecone, Milvus, Qdrant, NDCG, MRR, MAP.
*   **General ML Skills (Weight 5)**: NLP, RAG, PyTorch, LLMs, Fine-tuning LLMs, Transformers.
*   *Trust Weighting*: Skill score is multiplied by the duration (capped at 3 years) and an endorsement trust factor (`1.0 + endorsements / 50.0`) to avoid rating candidates who simply list keywords with zero validation.

### 5. Location & Logistics (10% Weight)
*   Noida/Pune-based candidates are prioritized. Relocation from Tier-1 cities (Bangalore, Hyderabad, Mumbai, Chennai) is accepted if `willing_to_relocate` is true. Notice period is scaled (preferring $\le 30$ days, penalizing $>90$ days).

### 6. Engagement & Availability Multiplier (10% Weight)
*   Scores are scaled by candidate active dates (penalizing if inactive for $>180$ days), recruiter response rates, and interview completion rates.

---

## 📊 Presentation (Slide Deck Outline)

Use this slide-by-slide guide to build your submission PPT deck/PDF.

### Slide 1: Title Slide
*   **Title:** Intelligent Candidate Discovery & Ranking Engine
*   **Subtitle:** Building a Scalable, Trap-Resistant Filter for Senior AI Engineers
*   **Details:** Your Team Name & Contact Details.

### Slide 2: Problem & Requirements
*   **The Target Role:** Senior AI Engineer (Founding Team, Pune/Noida hybrid, 5-9 years experience, hands-on production code, retrieval/search systems).
*   **Constraints:** Run on 100K candidates under 5 minutes on CPU only, offline.
*   **The Traps:** Keyword stuffers (marketing/accountant titles with AI skills), Services/consulting company traps, and ~80 honeypot profiles with impossible dates.

### Slide 3: Our Solution Architecture
*   **Core Approach:** A layered, rule-based heuristic pipeline.
*   **Why Rule-Based over LLM/Embeddings?** Running LLM embeddings or local sentence-transformers over 100K candidates takes hours and violates the 5-minute CPU constraint. Our parser takes **15 seconds** and yields full control over trap detection.
*   **Pipeline Stages:** Data Load $\rightarrow$ Honeypot Hard Filter $\rightarrow$ Title & Experience Scoring $\rightarrow$ Skill & Trust Weighting $\rightarrow$ Logistics & Location Scoring $\rightarrow$ Engagement Modifiers $\rightarrow$ Dynamic Reasoning Gen.

### Slide 4: Trap & Honeypot Defenses
*   **Zero-Duration Skills**: Filters candidates listing expert skills with $0$ months duration.
*   **Temporal Check**: Checks if career start date predates college start date.
*   **Title/Career Check**: Heavy negative weights applied to non-technical roles. Disqualifies consulting-firm-only career history.
*   **Result:** **0% Honeypot rate** in the final Top 100 recommendation.

### Slide 5: Interactive Sandbox Dashboard
*   Include a screenshot of the Streamlit App (`app.py`).
*   **Features:** Allows uploading custom subsets, inspects detailed candidate score breakdowns, lists career history, and tracks notice/logistics parameters.

---

## 📄 Repository Structure
*   `rank.py`: Core ranking script.
*   `app.py`: Streamlit Sandbox Dashboard.
*   `requirements.txt`: Project dependencies.
*   `submission_metadata.yaml`: Team details and AI declarations.
*   `validate_submission.py`: Hackathon format validator.
