from flask import Flask, render_template, request, redirect, session
import mysql.connector
import os
import PyPDF2
import docx2txt


#PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
app.secret_key = "secretkey"

# Upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Static folder
os.makedirs("static", exist_ok=True)

# MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="resume_analyzer"
)

cursor = db.cursor(buffered=True)

# ---------------- SKILLS ----------------
skills_list = [
    "python", "java", "c++", "html", "css", "javascript",
    "react", "node", "flask", "django", "mysql", "mongodb",
    "machine learning", "data science", "ai", "git"
]

required_skills = [
    "python", "mongodb", "mysql", "html", "css", "javascript","react", "node", "flask", "django", "machine learning", "data science", "ai", "git"
]

# ---------------- FUNCTIONS ----------------
def extract_skills(text):
    text = text.lower()
    return [skill for skill in skills_list if skill in text]

def calculate_ats_score(found_skills):
    score = 0
    for skill in required_skills:
        if skill in found_skills:
            score += 1
    return int((score / len(required_skills)) * 100)

def generate_feedback(found_skills):
    missing = [skill for skill in required_skills if skill not in found_skills]

    if not missing:
        return "Great Resume! All required skills present ✅"

    return "You should improve these skills: " + ", ".join(missing)

def smart_ai_feedback(found_skills, ats_score):
    feedback = []

    if len(found_skills) >= 5:
        feedback.append("✅ Good number of technical skills present")
    else:
        feedback.append("⚠️ Add more technical skills")

    if ats_score >= 70:
        feedback.append("✅ Your resume is ATS friendly")
    elif ats_score >= 40:
        feedback.append("⚠️ Resume is average")
    else:
        feedback.append("❌ Low ATS score")

    missing = [skill for skill in required_skills if skill not in found_skills]
    if missing:
        feedback.append("📌 Recommended skills: " + ", ".join(missing))

    feedback.append("💡 Add projects and achievements")
    feedback.append("💡 Improve formatting and keywords")

    return "<br>".join(feedback)



# 🔥 JOB RECOMMENDATION
def recommend_jobs(skills):
    jobs = []

    # 🔥 FRONTEND
    if "html" in skills or "css" in skills or "javascript" in skills:
        jobs.append("Frontend Developer")

    # 🔥 BACKEND
    if "python" in skills or "java" in skills or "node" in skills:
        jobs.append("Backend Developer")

    # 🔥 FULL STACK
    if ("html" in skills and "css" in skills and "javascript" in skills) and ("python" in skills or "node" in skills):
        jobs.append("Full Stack Developer")

    # 🔥 DATABASE
    if "power bi " in skills or "mongodb" in skills:
        jobs.append("Power Bi Developer")

    # 🔥 AI / ML
    if "machine learning" in skills or "ai" in skills:
        jobs.append("AI / ML Engineer")

    # 🔥 FRAMEWORK BASED
    if "react" in skills:
        jobs.append("React Developer")

    if "flask" in skills:
        jobs.append("Python Flask Developer")

    if "django" in skills:
        jobs.append("Django Developer")

    # 🔥 DEFAULT
    if not jobs:
        jobs.append("Software Developer")

    return list(set(jobs))  # remove duplicates


# 🔥 PDF GENERATION
def create_pdf(skills, ats_score, feedback, ai_feedback, jobs):
    file_path = "static/report.pdf"

    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    content = []

    content.append(Paragraph("Resume Analysis Report", styles['Title']))
    content.append(Spacer(1, 15))

    content.append(Paragraph("Skills:", styles['Heading3']))
    content.append(Paragraph(skills, styles['Normal']))
    content.append(Spacer(1, 10))

    content.append(Paragraph("ATS Score:", styles['Heading3']))
    content.append(Paragraph(f"{ats_score}%", styles['Normal'])) 
    content.append(Spacer(1, 10))

    content.append(Paragraph("Basic Feedback:", styles['Heading3']))
    content.append(Paragraph(feedback, styles['Normal']))
    content.append(Spacer(1, 10))

    clean_feedback = ai_feedback.replace("<br>", "<br/>")

    content.append(Paragraph("AI Feedback:", styles['Heading3']))
    content.append(Paragraph(clean_feedback, styles['Normal']))
    content.append(Spacer(1, 10))

    content.append(Paragraph("Recommended Jobs:", styles['Heading3']))
    content.append(Paragraph(jobs, styles['Normal']))

    doc.build(content)
    return file_path

# ---------------- ROUTES ----------------

@app.route('/')
def home():
    return redirect('/login')

# SIGNUP
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, 'user')",
            (username, password)
        )
        db.commit()

        return redirect('/login')

    return render_template('signup.html')

# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()

        if user:
            session['user'] = username
            session['role'] = user[3]
            return redirect('/dashboard')

        return "Invalid Credentials ❌"

    return render_template('login.html')

# ADMIN LOGIN
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s AND role='admin'",
            (username, password)
        )
        user = cursor.fetchone()

        if user:
            session['user'] = username
            session['role'] = 'admin'
            return redirect('/admin')

        return "Invalid Admin Credentials ❌"

    return render_template('login.html')



# DASHBOARD
@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        return render_template('dashboard.html', user=session['user'], role=session['role'])
    return redirect('/login')

@app.route('/admin')
def admin():
    if 'user' in session and session.get('role') == 'admin':

        # USERS
        cursor.execute("SELECT id, username, role FROM users")
        users = cursor.fetchall()

        # USER ANALYTICS
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
        total_admins = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE role='user'")
        total_normal_users = cursor.fetchone()[0]

        # 🔥 RESUME ANALYTICS
        cursor.execute("SELECT COUNT(*) FROM resumes")
        total_resumes = cursor.fetchone()[0]

        cursor.execute("SELECT AVG(ats_score) FROM resumes")
        avg_score = cursor.fetchone()[0] or 0

        # 🔥 RECENT RESUMES
        cursor.execute("SELECT username, skills, ats_score, created_at FROM resumes ORDER BY id DESC LIMIT 5")
        recent_resumes = cursor.fetchall()

        #  FINAL RETURN (IMPORTANT ALIGNMENT)
        return render_template(
            'admin.html',
            users=users,
            total_users=total_users,
            total_admins=total_admins,
            total_normal_users=total_normal_users,
            total_resumes=total_resumes,
            avg_score=int(avg_score),
            recent_resumes=recent_resumes
        )

    return "Access Denied ❌"

# DELETE USER
@app.route('/delete-user/<int:user_id>')
def delete_user(user_id):
    if 'user' in session and session.get('role') == 'admin':

        cursor.execute("SELECT username FROM users WHERE id=%s", (user_id,))
        user = cursor.fetchone()

        if user and user[0] == session['user']:
            return "You cannot delete yourself ❌"

        cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
        db.commit()

        return redirect('/admin')

    return "Access Denied ❌"

# CHANGE ROLE
@app.route('/make-user/<int:user_id>')
def make_user(user_id):
    if session.get('role') == 'admin':
        cursor.execute("UPDATE users SET role='user' WHERE id=%s", (user_id,))
        db.commit()
        return redirect('/admin')

@app.route('/make-admin/<int:user_id>')
def make_admin(user_id):
    if session.get('role') == 'admin':
        cursor.execute("UPDATE users SET role='admin' WHERE id=%s", (user_id,))
        db.commit()
        return redirect('/admin')

# UPLOAD PAGE
@app.route('/upload')
def upload_page():
    if 'user' not in session:
        return redirect('/login')

    if session.get('role') != 'user':
        return redirect('/dashboard')

    return render_template('upload.html')

# HANDLE UPLOAD
@app.route('/upload', methods=['POST'])
def upload():
    if 'user' not in session or session.get('role') != 'user':
        return redirect('/login')

    file = request.files['resume']

    if file.filename == '':
        return "No file selected ❌"

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    # FILE TYPE CHECK
    if file.filename.endswith('.pdf'):
        text = extract_pdf(filepath)
    elif file.filename.endswith('.docx'):
        text = extract_docx(filepath)
    else:
        return "Unsupported file ❌"

    # 🔥 PROCESSING (IMPORTANT: INDENTED)
    skills = extract_skills(text)
    ats_score = calculate_ats_score(skills)
    feedback = generate_feedback(skills)
    ai_feedback = smart_ai_feedback(skills, ats_score)
    jobs = recommend_jobs(skills)

    # 🔥 SAVE TO DATABASE
    cursor.execute(
        "INSERT INTO resumes (username, skills, ats_score) VALUES (%s, %s, %s)",
        (session['user'], ', '.join(skills), ats_score)
    )
    db.commit()

    # 🔥 PDF GENERATE
    pdf_path = create_pdf(
        ', '.join(skills),
        ats_score,
        feedback,
        ai_feedback,
        ', '.join(jobs)
    )

    # 🔥 RETURN RESULT
    return render_template(
        'result.html',
        skills=', '.join(skills),
        ats_score=ats_score,
        feedback=feedback,
        ai_feedback=ai_feedback,
        jobs=', '.join(jobs),
        pdf_path=pdf_path
    )

@app.route('/history')
def history():
    if 'user' not in session:
        return redirect('/login')

    cursor.execute(
        "SELECT skills, ats_score, created_at FROM resumes WHERE username=%s",
        (session['user'],)
    )
    data = cursor.fetchall()

    return render_template("history.html", data=data)

# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# TEXT
def extract_pdf(path):
    text = ""
    with open(path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

def extract_docx(path):
    return docx2txt.process(path)
@app.route('/analytics')
def analytics():
    if 'user' not in session or session.get('role') != 'admin':
        return "Access Denied ❌"

    # TOTAL RESUMES
    cursor.execute("SELECT COUNT(*) FROM resumes")
    total_resumes = cursor.fetchone()[0]

    # AVG SCORE
    cursor.execute("SELECT AVG(ats_score) FROM resumes")
    avg_score = cursor.fetchone()[0] or 0

    # PIE CHART DATA
    cursor.execute("SELECT COUNT(*) FROM resumes WHERE ats_score < 40")
    low = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM resumes WHERE ats_score BETWEEN 40 AND 70")
    medium = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM resumes WHERE ats_score > 70")
    high = cursor.fetchone()[0]

    # BAR GRAPH DATA
    cursor.execute("SELECT username, ats_score FROM resumes ORDER BY id DESC LIMIT 5")
    bar_data = cursor.fetchall()

    # TABLE DATA
    cursor.execute("SELECT username, skills, ats_score, created_at FROM resumes ORDER BY id DESC")
    all_resumes = cursor.fetchall()

    return render_template(
        "analytics.html",
        total_resumes=total_resumes,
        avg_score=int(avg_score),
        all_resumes=all_resumes,
        low=low,
        medium=medium,
        high=high,
        bar_data=bar_data
    )# RUN
if __name__ == '__main__':
    app.run(debug=True)