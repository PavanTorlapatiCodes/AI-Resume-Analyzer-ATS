# AI Resume Analyzer & ATS Score Checker

A full-stack web application that analyzes resumes against job descriptions and provides an ATS (Applicant Tracking System) compatibility score with actionable feedback.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-3-blue?logo=sqlite)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple?logo=bootstrap)

---

## Features

- **ATS Score (0–100)** — weighted scoring across keywords, skills, sections, and format
- **Keyword Matching** — identifies matched and missing keywords from the JD
- **Skill Gap Analysis** — detects technical skills present/absent
- **Section Coverage** — checks for Education, Experience, Skills, Projects, etc.
- **Format Quality** — validates contact info, word count, action verbs, quantifiers
- **Visual Charts** — gauge, bar, and donut charts using Matplotlib
- **Resume History** — track score improvements over time with trend chart
- **User Authentication** — register, login, profile management
- **PDF & DOCX Support** — automatic file type detection
- **Print / Export PDF** — browser-native print to PDF

---

## Tech Stack

| Layer      | Technology                              |
|------------|-----------------------------------------|
| Backend    | Python 3.10+, Flask 3.0                 |
| Database   | SQLite + Flask-SQLAlchemy               |
| Auth       | Flask-Login + Werkzeug password hashing |
| Parsing    | PyPDF2, python-docx, NLTK               |
| Analysis   | NumPy, Pandas, scikit-learn             |
| Charts     | Matplotlib, Seaborn                     |
| Frontend   | Bootstrap 5.3, Chart.js, Vanilla JS     |
| Deployment | Render (gunicorn)                       |

---

## Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/AI-Resume-Analyzer-ATS.git
cd AI-Resume-Analyzer-ATS

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py
```

Open http://localhost:5000 in your browser.

**Demo login:** `admin@demo.com` / `admin123`

---

## Project Structure

```
AI-Resume-Analyzer-ATS/
├── app.py              # Flask application & routes
├── config.py           # Configuration
├── models.py           # SQLAlchemy models (User, Resume)
├── resume_parser.py    # PDF/DOCX text extraction
├── ats_engine.py       # Scoring engine (keywords, skills, sections, format)
├── chart_generator.py  # Matplotlib chart generation
├── requirements.txt
├── Procfile            # Render deployment
├── templates/
│   ├── index.html      # Landing page
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html  # Resume history + stats
│   ├── upload.html     # File upload + JD input
│   ├── report.html     # Full ATS report
│   └── profile.html
└── static/
    ├── css/style.css
    ├── js/script.js
    └── charts/         # Generated chart images
```

---

## Deployment on Render

1. Push to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Add environment variable: `SECRET_KEY` = any random string
6. Deploy

---

## Key Interview Talking Points

- Implemented a **weighted multi-factor scoring algorithm** using NumPy for ATS compatibility
- Used **PyPDF2 and python-docx** for cross-format text extraction with error handling
- Designed **normalized SQLAlchemy models** with foreign keys and relationship loading
- Built **token-frequency keyword matching** with TF-weighted scoring
- Generated **dynamic Matplotlib charts** saved to static files and served per-request
- Secured routes with **Flask-Login session management** and Werkzeug password hashing
- Deployed on **Render with gunicorn** using environment variable configuration

---

## License

MIT License — free to use, modify, and distribute.
