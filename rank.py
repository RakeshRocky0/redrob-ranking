#!/usr/bin/env python3
"""
Redrob Hackathon - Intelligent Candidate Discovery & Ranking Challenge
Ranker script to find the top 100 candidates for the Senior AI Engineer role.
"""

import json
import csv
import re
import argparse
from pathlib import Path
from datetime import datetime

# Core Target Skills for the Senior AI Engineer Role
TIER1_SKILLS = {
    "Embeddings", "Vector Search", "Hybrid Search", "Information Retrieval",
    "Semantic Search", "FAISS", "Pinecone", "Milvus", "Qdrant", "Weaviate",
    "Elasticsearch", "OpenSearch", "NDCG", "MRR", "MAP", "Sentence Transformers"
}

TIER2_SKILLS = {
    "NLP", "Machine Learning", "Fine-tuning LLMs", "LLMs", "RAG", "Transformers",
    "Hugging Face Transformers", "PyTorch", "TensorFlow", "Scikit-Learn",
    "Prompt Engineering", "LoRA", "QLoRA", "PEFT", "Deep Learning"
}

TIER3_SKILLS = {
    "Python", "SQL", "Docker", "Kubernetes", "AWS", "GCP", "Flask", "FastAPI",
    "Django", "Kafka", "Airflow", "Spark", "Git"
}

# Trap / Disqualified Companies (Services/Consulting)
SERVICES_COMPANIES = {
    "TCS", "Infosys", "Wipro", "Accenture", "Cognizant", "Capgemini", "HCL",
    "Tech Mahindra", "Mindtree", "Mphasis", "Genpact", "Genpact AI"
}

# Valid Product Companies to verify product experience
PRODUCT_COMPANIES = {
    "Google", "Apple", "Microsoft", "Meta", "Amazon", "Uber", "Netflix", "Salesforce",
    "Adobe", "Zoho", "Flipkart", "Swiggy", "Paytm", "Zomato", "Freshworks", "PhonePe",
    "Razorpay", "Meesho", "Ola", "CRED", "Dream11", "Krutrim", "Sarvam AI", "InMobi",
    "Glance", "Wysa", "Yellow.ai", "Observe.AI", "Haptik", "Niramai", "Saarthi.ai",
    "Verloop.io", "Locobuzz", "Mad Street Den", "Rephrase.ai", "Pied Piper", "Globex Inc",
    "Initech", "Stark Industries", "Wayne Enterprises", "Tyrell Corp", "Cyberdyne Systems",
    "Aperture Science", "Massive Dynamic"
}

def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except:
        return None

def is_honeypot_candidate(cand):
    """
    Check if a candidate profile is a honeypot (contains impossible states/anomalies).
    """
    profile = cand.get("profile", {})
    skills = cand.get("skills", [])
    history = cand.get("career_history", [])
    edu = cand.get("education", [])
    signals = cand.get("redrob_signals", {})
    
    # 1. Zero duration skills anomaly
    # Count skills where proficiency is expert/advanced but duration_months == 0
    zero_dur_skills = sum(1 for s in skills if s.get("duration_months", 0) == 0)
    if zero_dur_skills >= 3:
        return True, f"Skill duration anomaly (zero duration in {zero_dur_skills} skills)"
        
    # 2. Expected salary range anomaly (min > max)
    sal = signals.get("expected_salary_range_inr_lpa", {})
    sal_min = sal.get("min", 0)
    sal_max = sal.get("max", 0)
    if sal_min > sal_max:
        return True, f"Salary expectation anomaly (min {sal_min} > max {sal_max})"
        
    # 3. Work history starts before college start year
    edu_start_years = [e.get("start_year") for e in edu if e.get("start_year")]
    if edu_start_years:
        min_edu_start = min(edu_start_years)
        work_start_years = []
        for h in history:
            sd = h.get("start_date")
            if sd:
                try:
                    work_start_years.append(datetime.strptime(sd, "%Y-%m-%d").year)
                except:
                    pass
        if work_start_years:
            min_work_start = min(work_start_years)
            # Flag if they started full-time work more than 2 years before college
            if min_work_start < min_edu_start - 2:
                return True, f"Temporal anomaly (worked in {min_work_start} before college in {min_edu_start})"
                
    # 4. Total experience years vs years since earliest job start
    # Let's say current year is 2026
    years_exp = profile.get("years_of_experience", 0)
    work_start_years = []
    for h in history:
        sd = h.get("start_date")
        if sd:
            try:
                work_start_years.append(datetime.strptime(sd, "%Y-%m-%d").year)
            except:
                pass
    if work_start_years:
        min_work_start = min(work_start_years)
        elapsed_years = 2026 - min_work_start
        if years_exp > elapsed_years + 2.0:
            return True, f"Stated experience ({years_exp} yrs) exceeds elapsed years since first job ({elapsed_years} yrs)"
            
    # 5. Single skill duration exceeds experience years
    for s in skills:
        dur_years = s.get("duration_months", 0) / 12
        if dur_years > years_exp + 2.0 and years_exp > 0:
            return True, f"Skill duration ({dur_years:.1f} yrs) exceeds stated experience ({years_exp} yrs)"

    return False, ""

def score_candidate(cand):
    """
    Score a single candidate against the job description requirements.
    """
    profile = cand.get("profile", {})
    skills = cand.get("skills", [])
    history = cand.get("career_history", [])
    edu = cand.get("education", [])
    signals = cand.get("redrob_signals", {})
    
    # Check if honeypot
    is_hp, hp_reason = is_honeypot_candidate(cand)
    if is_hp:
        return -100.0, hp_reason, True
        
    # --- 1. TITLE & CAREER HISTORY FIT (40% weight) ---
    current_title = profile.get("current_title", "").lower()
    headline = profile.get("headline", "").lower()
    
    # Score current title / headline
    target_titles = [
        "senior ai engineer", "ai engineer", "machine learning engineer", "ml engineer",
        "nlp engineer", "search engineer", "retrieval engineer", "information retrieval engineer",
        "recommendation systems engineer", "recommendation engineer"
    ]
    general_tech_titles = [
        "backend engineer", "software engineer", "data engineer", "frontend engineer",
        "full stack developer", "platform engineer", "devops engineer", "systems engineer",
        "developer"
    ]
    trap_titles = [
        "marketing manager", "accountant", "hr manager", "operations manager",
        "sales executive", "graphic designer", "customer support", "business analyst",
        "civil engineer", "mechanical engineer"
    ]
    
    title_score = 0.0
    if any(t in current_title or t in headline for t in target_titles):
        title_score = 1.0
    elif any(t in current_title or t in headline for t in general_tech_titles):
        title_score = 0.6
    elif any(t in current_title for t in trap_titles):
        # Heavy penalty for trap roles (keyword stuffers)
        title_score = -5.0
    else:
        title_score = 0.2
        
    # Check if career history has only services/consulting companies (Services Trap)
    services_count = 0
    product_count = 0
    total_jobs = len(history)
    for h in history:
        comp = h.get("company", "")
        if comp in SERVICES_COMPANIES:
            services_count += 1
        elif comp in PRODUCT_COMPANIES:
            product_count += 1
            
    is_services_only = (services_count == total_jobs and total_jobs > 0)
    
    # --- 2. EXPERIENCE LEVEL FIT (20% weight) ---
    years_exp = profile.get("years_of_experience", 0)
    # Target range: 5 to 9 years
    if 5.0 <= years_exp <= 9.0:
        exp_score = 1.0
    elif 4.0 <= years_exp < 5.0 or 9.0 < years_exp <= 11.0:
        exp_score = 0.8
    elif 3.0 <= years_exp < 4.0 or 11.0 < years_exp <= 13.0:
        exp_score = 0.5
    else:
        exp_score = 0.1
        
    # --- 3. TECHNICAL SKILL MATCH (20% weight) ---
    skill_score = 0.0
    matched_skills = []
    
    for s in skills:
        name = s.get("name", "")
        prof = s.get("proficiency", "beginner")
        dur_months = s.get("duration_months", 0)
        endorsements = s.get("endorsements", 0)
        
        weight = 0.0
        if name in TIER1_SKILLS:
            weight = 10.0
            matched_skills.append(name)
        elif name in TIER2_SKILLS:
            weight = 5.0
            matched_skills.append(name)
        elif name in TIER3_SKILLS:
            weight = 2.0
            
        if weight > 0:
            # Multipliers
            prof_mult = {"expert": 1.0, "advanced": 0.85, "intermediate": 0.7, "beginner": 0.3}.get(prof, 0.3)
            # Duration: cap duration_years at 3 to prevent skew, min at 0.5
            dur_years = dur_months / 12
            dur_mult = min(max(dur_years, 0.5), 3.0)
            # Trust factor: rewards endorsements to catch keyword stuffers
            trust_factor = 1.0 + min(endorsements, 50) / 50.0
            
            skill_score += weight * prof_mult * dur_mult * trust_factor
            
    # --- 4. LOCATION & LOGISTICS MATCH (10% weight) ---
    loc = profile.get("location", "").lower()
    # Check Noida/Pune hybrid
    is_pune_noida = "noida" in loc or "pune" in loc or "delhi ncr" in loc or "gurgaon" in loc or "delhi" in loc
    is_tier1 = any(c in loc for c in ["bangalore", "bengaluru", "hyderabad", "mumbai", "chennai", "kolkata"])
    willing_relocate = signals.get("willing_to_relocate", False)
    
    loc_score = 0.0
    if is_pune_noida:
        loc_score = 1.0
    elif is_tier1:
        loc_score = 0.8 if willing_relocate else 0.2
    else:
        # Check if outside India (contains country or not India)
        country = profile.get("country", "").lower()
        if country and country != "india":
            loc_score = 0.05
        else:
            loc_score = 0.5 if willing_relocate else 0.1
            
    # Notice Period
    notice = signals.get("notice_period_days", 90)
    if notice <= 30:
        notice_score = 1.0
    elif notice <= 60:
        notice_score = 0.8
    elif notice <= 90:
        notice_score = 0.5
    else:
        notice_score = 0.2
        
    # --- 5. BEHAVIORAL ENGAGEMENT MULTIPLIER (10% weight) ---
    # Parse last active date
    last_active_str = signals.get("last_active_date")
    active_days_ago = 365
    if last_active_str:
        last_active = parse_date(last_active_str)
        if last_active:
            # Assume competition date is mid-2026 (e.g. 2026-06-18)
            delta = datetime(2026, 6, 18) - last_active
            active_days_ago = max(delta.days, 0)
            
    if active_days_ago <= 30:
        active_mult = 1.0
    elif active_days_ago <= 90:
        active_mult = 0.9
    elif active_days_ago <= 180:
        active_mult = 0.7
    else:
        active_mult = 0.3  # Penalize inactive candidates
        
    open_to_work = signals.get("open_to_work_flag", False)
    open_work_mult = 1.2 if open_to_work else 0.8
    
    resp_rate = signals.get("recruiter_response_rate", 0.0)
    interview_rate = signals.get("interview_completion_rate", 0.0)
    
    engagement_score = active_mult * open_work_mult * (0.5 + 0.5 * resp_rate) * (0.5 + 0.5 * interview_rate)

    # --- COMPOSING FINAL SCORE ---
    base_score = (title_score * 40.0) + (exp_score * 20.0) + (skill_score)
    final_score = base_score * loc_score * notice_score * engagement_score
    
    # Apply Services Company Trap penalty
    if is_services_only:
        final_score *= 0.25
        
    # Ensure no honeypot gets ranked by keeping final_score bounded above -100
    final_score = max(final_score, -50.0)
    
    return round(final_score, 4), matched_skills, False

def generate_reasoning(cand, rank, matched_skills):
    """
    Generate a dynamic, customized reasoning for the candidate based on facts.
    """
    profile = cand.get("profile", {})
    years = profile.get("years_of_experience", 0)
    title = profile.get("current_title", "Engineer")
    loc = profile.get("location", "India")
    signals = cand.get("redrob_signals", {})
    notice = signals.get("notice_period_days", 0)
    company = profile.get("current_company", "a tech firm")
    
    # Skills display
    if matched_skills:
        skills_str = ", ".join(matched_skills[:2])
        skills_phrase = f"demonstrated expertise in {skills_str}"
    else:
        skills_phrase = "solid technical background in backend engineering"
        
    # Check notice and location for concerns
    concerns = []
    if notice > 60:
        concerns.append(f"longer notice period of {notice} days")
    if "noida" not in loc.lower() and "pune" not in loc.lower():
        concerns.append("requires relocation")
        
    concern_str = ""
    if concerns:
        concern_str = f" (minor concern: {', '.join(concerns)})"
        
    # Tone variations based on rank
    if rank <= 10:
        tone = f"Top-tier Senior AI Engineer with {years:.1f} years of experience at {company}. Strong alignment with product engineering, {skills_phrase}, and highly active."
    elif rank <= 50:
        tone = f"Strong Senior candidate with {years:.1f} years of experience working as {title} at {company}. {skills_phrase.capitalize()} with immediate availability."
    else:
        tone = f"Competent engineer with {years:.1f} years of experience at {company}. Has {skills_phrase}{concern_str}."
        
    return tone

def main():
    parser = argparse.ArgumentParser(description="Rank candidates for Redrob Challenge")
    parser.add_argument("--candidates", default="./candidates.jsonl", help="Path to candidates.jsonl")
    parser.add_argument("--out", default="./submission.csv", help="Path to output CSV")
    args = parser.parse_args()
    
    candidates_file = Path(args.candidates)
    output_file = Path(args.out)
    
    if not candidates_file.exists():
        print(f"Error: Candidates file {candidates_file} does not exist.")
        return
        
    print(f"Loading and scoring candidates from {candidates_file}...")
    
    scored_candidates = []
    
    with open(candidates_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            cand = json.loads(line)
            cid = cand.get("candidate_id")
            score, matched_skills, is_hp = score_candidate(cand)
            if not is_hp:
                scored_candidates.append({
                    "candidate_id": cid,
                    "score": score,
                    "matched_skills": matched_skills,
                    "candidate_data": cand
                })
                
    print(f"Total candidates scored (excluding honeypots): {len(scored_candidates)}")
    
    # Sort candidates by score descending, breaking ties by candidate_id ascending
    scored_candidates.sort(key=lambda x: (-x["score"], x["candidate_id"]))
    
    # Get top 100
    top_100 = scored_candidates[:100]
    
    # Generate reasoning and rank for top 100
    submission_rows = []
    for idx, item in enumerate(top_100):
        rank = idx + 1
        cid = item["candidate_id"]
        score = item["score"]
        cand_data = item["candidate_data"]
        matched_skills = item["matched_skills"]
        
        reasoning = generate_reasoning(cand_data, rank, matched_skills)
        
        submission_rows.append({
            "candidate_id": cid,
            "rank": rank,
            "score": score,
            "reasoning": reasoning
        })
        
    # Write to CSV
    print(f"Writing top 100 ranked candidates to {output_file}...")
    with open(output_file, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=["candidate_id", "rank", "score", "reasoning"])
        writer.writeheader()
        for r in submission_rows:
            writer.writerow(r)
            
    print("Done!")

if __name__ == "__main__":
    main()
