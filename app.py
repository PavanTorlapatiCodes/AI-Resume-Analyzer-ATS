import os
import json
import uuid
import shutil
from datetime import datetime
from flask import (Flask, render_template, request, redirect, url_for,
                   flash, jsonify, send_file, session)
from flask_login import (LoginManager, login_user, logout_user,
                          login_required, current_user)
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, Resume
from resume_parser import parse_resume
from ats_engine import analyze_resume
from chart_generator import generate_all_charts

# ── App setup ────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

os.makedirs(app.config['UPLOAD_FOLDER'],  exist_ok=True)
os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)
os.makedirs(os.path.join('static', 'charts'), exist_ok=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ── Auth routes ──────────────────────────────────────────────────────────────
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        error = None
        if not username or not email or not password:
            error = 'All fields are required.'
        elif password != confirm:
            error = 'Passwords do not match.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        elif User.query.filter_by(email=email).first():
            error = 'Email already registered.'
        elif User.query.filter_by(username=username).first():
            error = 'Username already taken.'

        if error:
            flash(error, 'danger')
            return render_template('register.html')

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Account created! Welcome.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user     = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ── Dashboard ────────────────────────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    resumes = Resume.query.filter_by(user_id=current_user.id)\
                          .order_by(Resume.uploaded_at.desc()).all()

    # Stats
    total       = len(resumes)
    avg_score   = round(sum(r.ats_score for r in resumes) / total, 1) if total else 0
    best_score  = max((r.ats_score for r in resumes), default=0)
    high_count  = sum(1 for r in resumes if r.ats_score >= 70)

    # Trend data for chart (last 7)
    trend_data  = []
    for r in reversed(resumes[-7:]):
        trend_data.append({'label': r.original_name[:10], 'score': r.ats_score})

    return render_template('dashboard.html',
                           resumes=resumes,
                           total=total,
                           avg_score=avg_score,
                           best_score=best_score,
                           high_count=high_count,
                           trend_data=json.dumps(trend_data))


# ── Upload & Analyze ─────────────────────────────────────────────────────────
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'resume' not in request.files:
            flash('No file selected.', 'warning')
            return redirect(request.url)

        file            = request.files['resume']
        job_title       = request.form.get('job_title', 'Not specified').strip()
        job_description = request.form.get('job_description', '').strip()

        if file.filename == '':
            flash('No file selected.', 'warning')
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash('Only PDF and DOCX files are allowed.', 'danger')
            return redirect(request.url)

        if not job_description:
            flash('Please paste the job description.', 'warning')
            return redirect(request.url)

        # Save file
        original_name = secure_filename(file.filename)
        unique_name   = f"{uuid.uuid4().hex}_{original_name}"
        filepath      = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
        file.save(filepath)

        # Parse & analyse
        try:
            parsed   = parse_resume(filepath)
            if 'error' in parsed:
                flash('Could not read file. Try a different PDF/DOCX.', 'danger')
                os.remove(filepath)
                return redirect(request.url)

            analysis = analyze_resume(parsed, job_description)
            charts   = generate_all_charts(analysis)

            # Persist to DB
            resume = Resume(
                user_id          = current_user.id,
                filename         = unique_name,
                original_name    = original_name,
                job_title        = job_title,
                job_description  = job_description,
                ats_score        = analysis['ats_score'],
                keyword_score    = analysis['keyword_score'],
                format_score     = analysis['format_score'],
                skills_score     = analysis['skills_score'],
                matched_keywords = json.dumps(analysis['matched_keywords']),
                missing_keywords = json.dumps(analysis['missing_keywords']),
                extracted_skills = json.dumps(analysis['extracted_skills']),
                recommendations  = json.dumps(analysis['recommendations']),
                word_count       = analysis['word_count'],
                sections_found   = json.dumps(analysis['sections_found']),
                analyzed_at      = datetime.utcnow(),
            )
            db.session.add(resume)
            db.session.commit()

            # Store charts in session for report page
            session['charts'] = charts
            session['resume_id'] = resume.id

            return redirect(url_for('report', resume_id=resume.id))

        except Exception as e:
            flash(f'Analysis failed: {str(e)}', 'danger')
            if os.path.exists(filepath):
                os.remove(filepath)
            return redirect(request.url)

    return render_template('upload.html')


# ── Report ───────────────────────────────────────────────────────────────────
@app.route('/report/<int:resume_id>')
@login_required
def report(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('dashboard'))

    matched  = json.loads(resume.matched_keywords  or '[]')
    missing  = json.loads(resume.missing_keywords  or '[]')
    skills   = json.loads(resume.extracted_skills  or '[]')
    recs     = json.loads(resume.recommendations   or '[]')
    sections = json.loads(resume.sections_found    or '[]')
    charts   = session.get('charts', {})

    grade_colors = {'A':'success','B':'info','C':'warning','D':'warning','F':'danger'}
    grade = _get_grade(resume.ats_score)

    return render_template('report.html',
                           resume=resume,
                           matched=matched,
                           missing=missing,
                           skills=skills,
                           recs=recs,
                           sections=sections,
                           charts=charts,
                           grade=grade,
                           grade_color=grade_colors.get(grade,'secondary'))


def _get_grade(score):
    if score >= 80: return 'A'
    if score >= 65: return 'B'
    if score >= 50: return 'C'
    if score >= 35: return 'D'
    return 'F'


# ── Delete resume ────────────────────────────────────────────────────────────
@app.route('/delete/<int:resume_id>', methods=['POST'])
@login_required
def delete_resume(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    if resume.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Remove file
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], resume.filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    db.session.delete(resume)
    db.session.commit()
    flash('Resume deleted.', 'success')
    return redirect(url_for('dashboard'))


# ── Profile ──────────────────────────────────────────────────────────────────
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        new_username = request.form.get('username', '').strip()
        current_pw   = request.form.get('current_password', '')
        new_pw       = request.form.get('new_password', '')

        if new_username and new_username != current_user.username:
            if User.query.filter_by(username=new_username).first():
                flash('Username already taken.', 'danger')
            else:
                current_user.username = new_username
                db.session.commit()
                flash('Username updated.', 'success')

        if current_pw and new_pw:
            if current_user.check_password(current_pw):
                if len(new_pw) >= 6:
                    current_user.set_password(new_pw)
                    db.session.commit()
                    flash('Password updated.', 'success')
                else:
                    flash('New password must be at least 6 characters.', 'danger')
            else:
                flash('Current password is incorrect.', 'danger')

    resumes = Resume.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', resumes=resumes)


# ── API endpoint for dashboard chart data ────────────────────────────────────
@app.route('/api/scores')
@login_required
def api_scores():
    resumes = Resume.query.filter_by(user_id=current_user.id)\
                          .order_by(Resume.uploaded_at).all()
    data = [{'name': r.original_name[:15], 'score': r.ats_score} for r in resumes]
    return jsonify(data)


# ── Bootstrap DB & run ───────────────────────────────────────────────────────
with app.app_context():
    db.create_all()
    # Create a demo admin if none exists
    if not User.query.filter_by(email='admin@demo.com').first():
        admin = User(username='admin', email='admin@demo.com', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
