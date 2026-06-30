import re
import json
import numpy as np
from collections import Counter

# ── Weights for scoring sub-components ──────────────────────────────────────
WEIGHTS = {
    'keyword_match': 0.40,
    'skills_match':  0.25,
    'sections':      0.20,
    'format':        0.15,
}

REQUIRED_SECTIONS = ['education', 'experience', 'skills', 'contact', 'summary']
OPTIONAL_SECTIONS = ['projects', 'certifications', 'achievements']

FORMAT_CHECKS = {
    'has_email':       (r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',     5),
    'has_phone':       (r'(\+?\d[\d\s\-().]{7,}\d)',                                5),
    'has_linkedin':    (r'linkedin\.com',                                            5),
    'good_length':     None,   # handled separately
    'no_tables':       None,
    'no_photos':       None,
}


def tokenize_text(text):
    """Lower-case word tokens, stripping punctuation."""
    return re.findall(r'\b[a-zA-Z][a-zA-Z0-9+#.]*\b', text.lower())


def extract_keywords_from_jd(job_description):
    """Pull meaningful keywords from a job description (remove stopwords)."""
    STOPWORDS = {
        'the','a','an','and','or','but','in','on','at','to','for','of','with',
        'is','are','was','were','be','been','being','have','has','had','do',
        'does','did','will','would','could','should','may','might','shall',
        'we','you','they','it','this','that','these','those','our','your',
        'their','its','we\'re','you\'re','they\'re','i','me','my','myself',
        'as','by','from','up','about','into','through','during','including',
        'also','both','each','few','more','most','other','some','such','than',
        'too','very','just','because','if','while','although','however',
    }
    tokens = tokenize_text(job_description)
    return [t for t in tokens if t not in STOPWORDS and len(t) > 2]


def calculate_keyword_score(resume_text, job_description):
    """TF-based keyword match: what fraction of JD keywords appear in resume."""
    jd_keywords = extract_keywords_from_jd(job_description)
    if not jd_keywords:
        return 0.0, [], []

    resume_tokens = set(tokenize_text(resume_text))
    jd_counter   = Counter(jd_keywords)
    unique_jd_kw = list(jd_counter.keys())

    matched  = [kw for kw in unique_jd_kw if kw in resume_tokens]
    missing  = [kw for kw in unique_jd_kw if kw not in resume_tokens]

    # Weight by frequency in JD
    total_weight   = sum(jd_counter.values())
    matched_weight = sum(jd_counter[kw] for kw in matched)
    score = (matched_weight / total_weight) * 100 if total_weight else 0

    # Return top 20 of each
    return round(score, 2), matched[:20], missing[:20]


def calculate_skills_score(extracted_skills, job_description):
    """Score how many resume skills appear in the JD."""
    if not extracted_skills:
        return 0.0
    jd_lower = job_description.lower()
    matched  = [s for s in extracted_skills if s in jd_lower]
    score    = (len(matched) / max(len(extracted_skills), 1)) * 100
    return round(min(score, 100), 2)


def calculate_sections_score(sections_found):
    """Score based on presence of required + optional sections."""
    required_present = sum(1 for s in REQUIRED_SECTIONS if s in sections_found)
    optional_present = sum(1 for s in OPTIONAL_SECTIONS if s in sections_found)
    req_score = (required_present / len(REQUIRED_SECTIONS)) * 80
    opt_score = (optional_present / len(OPTIONAL_SECTIONS)) * 20
    return round(req_score + opt_score, 2)


def calculate_format_score(resume_text):
    """Simple format-quality checks."""
    score = 0
    text  = resume_text.lower()

    # Contact info
    if re.search(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', resume_text):
        score += 20
    if re.search(r'(\+?\d[\d\s\-().]{7,}\d)', resume_text):
        score += 15
    if 'linkedin' in text:
        score += 10

    # Length (ideal 400–900 words)
    word_count = len(re.findall(r'\b\w+\b', resume_text))
    if 400 <= word_count <= 900:
        score += 25
    elif 300 <= word_count < 400 or 900 < word_count <= 1200:
        score += 15
    else:
        score += 5

    # Action verbs
    action_verbs = ['developed','managed','led','created','implemented','designed',
                    'built','improved','increased','reduced','achieved','delivered',
                    'collaborated','optimized','automated','analyzed']
    found_verbs = sum(1 for v in action_verbs if v in text)
    score += min(found_verbs * 2, 20)

    # Quantifiable results
    if re.search(r'\d+\s*%', resume_text):
        score += 10

    return round(min(score, 100), 2)


def generate_recommendations(matched_kw, missing_kw, sections_found,
                              format_score, ats_score):
    recs = []

    if ats_score < 50:
        recs.append("🚨 Your ATS score is below 50. Significantly tailor this resume to the job description.")

    if missing_kw:
        top_missing = ', '.join(missing_kw[:8])
        recs.append(f"📌 Add these missing keywords from the JD: {top_missing}.")

    for sec in REQUIRED_SECTIONS:
        if sec not in sections_found:
            recs.append(f"📋 Add a '{sec.title()}' section — it is expected by ATS systems.")

    if 'projects' not in sections_found:
        recs.append("💡 Add a 'Projects' section with 2–3 relevant projects.")

    if 'certifications' not in sections_found:
        recs.append("🎓 Consider adding certifications relevant to the role.")

    if format_score < 60:
        recs.append("📐 Improve resume formatting: include email, phone, LinkedIn, and use action verbs.")

    if not re.search(r'\d+\s*%', ' '.join(missing_kw)):
        recs.append("📊 Quantify achievements with numbers/percentages (e.g., 'Improved performance by 30%').")

    recs.append("✅ Use a single-column ATS-friendly template (no tables, no graphics, no headers/footers).")

    return recs


def analyze_resume(resume_data, job_description):
    """
    Main entry point.
    resume_data  – dict returned by parse_resume()
    job_description – raw text of the JD
    Returns a complete analysis dict.
    """
    resume_text      = resume_data.get('text', '')
    sections_found   = resume_data.get('sections_found', [])
    extracted_skills = resume_data.get('extracted_skills', [])

    # Individual scores
    kw_score, matched_kw, missing_kw = calculate_keyword_score(resume_text, job_description)
    sk_score  = calculate_skills_score(extracted_skills, job_description)
    sec_score = calculate_sections_score(sections_found)
    fmt_score = calculate_format_score(resume_text)

    # Weighted ATS score
    ats_score = (
        kw_score  * WEIGHTS['keyword_match'] +
        sk_score  * WEIGHTS['skills_match']  +
        sec_score * WEIGHTS['sections']      +
        fmt_score * WEIGHTS['format']
    )
    ats_score = round(np.clip(ats_score, 0, 100), 1)

    # Grade
    if ats_score >= 80:
        grade = 'A'
    elif ats_score >= 65:
        grade = 'B'
    elif ats_score >= 50:
        grade = 'C'
    elif ats_score >= 35:
        grade = 'D'
    else:
        grade = 'F'

    recs = generate_recommendations(matched_kw, missing_kw, sections_found, fmt_score, ats_score)

    return {
        'ats_score':        ats_score,
        'grade':            grade,
        'keyword_score':    kw_score,
        'skills_score':     sk_score,
        'sections_score':   sec_score,
        'format_score':     fmt_score,
        'matched_keywords': matched_kw,
        'missing_keywords': missing_kw,
        'extracted_skills': extracted_skills,
        'sections_found':   sections_found,
        'word_count':       resume_data.get('word_count', 0),
        'recommendations':  recs,
        'contact': {
            'email':    resume_data.get('email'),
            'phone':    resume_data.get('phone'),
            'linkedin': resume_data.get('linkedin'),
            'github':   resume_data.get('github'),
        },
    }
