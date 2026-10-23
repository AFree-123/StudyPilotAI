import os, re, sqlite3, secrets, json
from datetime import datetime, date, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "studypilot.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))
app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024
ALLOWED_EXTENSIONS = {"pdf"}

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS documents(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            extracted_text TEXT DEFAULT '',
            uploaded_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            due_date TEXT,
            subject TEXT DEFAULT '',
            done INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS quiz_results(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """)

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def current_user():
    if not session.get("user_id"):
        return None
    with db() as con:
        return con.execute("SELECT id,name,email FROM users WHERE id=?", (session["user_id"],)).fetchone()

def extract_pdf(path):
    try:
        import fitz
        doc = fitz.open(path)
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text[:100000]
    except Exception:
        return ""

def offline_answer(question, user_id=None):
    q = (question or "").strip()
    if not q:
        return "Type a question and I’ll help you plan your next study step."
    ql = q.lower()
    if any(x in ql for x in ["hello", "hi", "hey", "vanakkam"]):
        return "Hi! I’m StudyPilot AI, your study companion. You can ask for a study plan, PDF summary, quiz, or a simple explanation."
    if "plan" in ql or "study today" in ql or "schedule" in ql:
        if user_id:
            with db() as con:
                tasks = con.execute("SELECT title,due_date,done FROM tasks WHERE user_id=? AND done=0 ORDER BY COALESCE(due_date,'9999-12-31') LIMIT 5", (user_id,)).fetchall()
            if tasks:
                return "Here’s a simple plan based on your pending tasks:\n" + "\n".join(f"• {t['title']}" + (f" — {t['due_date']}" if t['due_date'] else "") for t in tasks) + "\n\nStart with the most urgent task, study for 25 minutes, then take a 5-minute break."
        return "Suggested 2-hour plan:\n1. 25 min — revise one important topic\n2. 5 min — break\n3. 25 min — solve practice questions\n4. 10 min — break\n5. 25 min — review mistakes\n6. 30 min — recall key points without notes."
    if "quiz" in ql or "question" in ql:
        return "Quick self-check:\n1. Explain the topic in your own words.\n2. Write two important definitions.\n3. Solve one example without looking at notes.\n\nThis demo uses rule-based prompts; it does not generate verified AI answers."
    if "pending" in ql or "task" in ql:
        if user_id:
            with db() as con:
                tasks = con.execute("SELECT title,due_date FROM tasks WHERE user_id=? AND done=0 ORDER BY due_date LIMIT 8", (user_id,)).fetchall()
            if tasks:
                return "Your pending tasks:\n" + "\n".join(f"• {t['title']}" + (f" — {t['due_date']}" if t['due_date'] else "") for t in tasks)
        return "No pending tasks yet. Add tasks from Study Plan to see them here."
    if "pdf" in ql or "summar" in ql or "notes" in ql or "topic" in ql:
        if user_id:
            with db() as con:
                docs = con.execute("SELECT original_name,extracted_text FROM documents WHERE user_id=? ORDER BY id DESC LIMIT 3", (user_id,)).fetchall()
            usable = [d for d in docs if d["extracted_text"].strip()]
            if usable:
                d = usable[0]
                sentences = re.split(r'(?<=[.!?])\s+', d["extracted_text"].replace("\n", " "))
                snippets = [s.strip() for s in sentences if len(s.strip()) > 35][:6]
                return f"Notes from {d['original_name']} (extractive preview):\n" + "\n".join(f"• {s[:280]}" for s in snippets or [d["extracted_text"][:1200]]) + "\n\nThis is an extractive demo summary, not a generative AI analysis."
        return "Upload a text-based PDF first. I can then show an extractive preview of the text found in it."
    return "I can help with a study plan, pending tasks, uploaded PDF text, or quiz practice. For this free demo, replies are rule-based/extractive and are not generated by a live LLM."

@app.context_processor
def inject_user():
    return {"logged_user": current_user()}

@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Enter your name, a valid email, and a password of at least 8 characters.", "error")
            return render_template("register.html")
        try:
            with db() as con:
                con.execute("INSERT INTO users(name,email,password_hash,created_at) VALUES(?,?,?,?)",
                            (name, email, generate_password_hash(password), datetime.now().isoformat(timespec="seconds")))
            flash("Account created. Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("That email is already registered. Please log in.", "error")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with db() as con:
            user = con.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("dashboard"))
        flash("Email or password is incorrect.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    uid = session["user_id"]
    with db() as con:
        docs = con.execute("SELECT COUNT(*) n FROM documents WHERE user_id=?", (uid,)).fetchone()["n"]
        tasks = con.execute("SELECT * FROM tasks WHERE user_id=? ORDER BY done, COALESCE(due_date,'9999-12-31'), id DESC LIMIT 6", (uid,)).fetchall()
        pending = con.execute("SELECT COUNT(*) n FROM tasks WHERE user_id=? AND done=0", (uid,)).fetchone()["n"]
    return render_template("dashboard.html", doc_count=docs, pending=pending, tasks=tasks)

@app.route("/chat")
@login_required
def chat():
    return render_template("chat.html")

@app.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    data = request.get_json(silent=True) or {}
    return jsonify({"reply": offline_answer(data.get("message", ""), session["user_id"]), "mode": "free-demo"})

@app.route("/alexa-demo")
def alexa_demo():
    return render_template("alexa_demo.html")

@app.route("/alexa-demo/chat", methods=["POST"])
def alexa_demo_chat():
    data = request.get_json(silent=True) or {}
    return jsonify({"reply": offline_answer(data.get("message", ""), session.get("user_id")), "mode": "simulated-demo"})

@app.route("/materials", methods=["GET", "POST"])
@login_required
def materials():
    uid = session["user_id"]
    if request.method == "POST":
        file = request.files.get("pdf")
        if not file or not file.filename:
            flash("Choose a PDF file first.", "error")
        elif not file.filename.lower().endswith(".pdf"):
            flash("Only PDF files are supported.", "error")
        else:
            original = secure_filename(file.filename)
            stored = f"{secrets.token_hex(8)}_{original}"
            path = os.path.join(UPLOAD_DIR, stored)
            file.save(path)
            extracted = extract_pdf(path)
            with db() as con:
                con.execute("INSERT INTO documents(user_id,filename,original_name,extracted_text,uploaded_at) VALUES(?,?,?,?,?)",
                            (uid, stored, original, extracted, datetime.now().isoformat(timespec="seconds")))
            flash("PDF uploaded. " + ("Text extracted." if extracted.strip() else "No selectable text found; scanned PDFs may need OCR."), "success")
            return redirect(url_for("materials"))
    with db() as con:
        docs = con.execute("SELECT * FROM documents WHERE user_id=? ORDER BY id DESC", (uid,)).fetchall()
    return render_template("materials.html", docs=docs)

@app.route("/materials/<int:doc_id>/delete", methods=["POST"])
@login_required
def delete_material(doc_id):
    with db() as con:
        row = con.execute("SELECT filename FROM documents WHERE id=? AND user_id=?", (doc_id, session["user_id"])).fetchone()
        if row:
            try: os.remove(os.path.join(UPLOAD_DIR, row["filename"]))
            except OSError: pass
            con.execute("DELETE FROM documents WHERE id=? AND user_id=?", (doc_id, session["user_id"]))
    flash("Document deleted.", "success")
    return redirect(url_for("materials"))

@app.route("/study-plan", methods=["GET", "POST"])
@login_required
def study_plan():
    uid = session["user_id"]
    if request.method == "POST":
        action = request.form.get("action", "add")
        if action == "toggle":
            task_id = request.form.get("task_id", type=int)
            with db() as con:
                con.execute("UPDATE tasks SET done=CASE done WHEN 0 THEN 1 ELSE 0 END WHERE id=? AND user_id=?", (task_id, uid))
        elif action == "add":
            title = request.form.get("title", "").strip()
            due_date = request.form.get("due_date", "").strip() or None
            subject = request.form.get("subject", "").strip()
            if title:
                with db() as con:
                    con.execute("INSERT INTO tasks(user_id,title,due_date,subject,created_at) VALUES(?,?,?,?,?)",
                                (uid, title[:160], due_date, subject[:80], datetime.now().isoformat(timespec="seconds")))
        return redirect(url_for("study_plan"))
    with db() as con:
        tasks = con.execute("SELECT * FROM tasks WHERE user_id=? ORDER BY done, COALESCE(due_date,'9999-12-31'), id DESC", (uid,)).fetchall()
    return render_template("study_plan.html", tasks=tasks)

@app.route("/quiz", methods=["GET", "POST"])
@login_required
def quiz():
    if request.method == "POST":
        subject = request.form.get("subject", "General").strip()[:80]
        questions = [
            ("Which habit helps long-term recall?", ["Cramming once", "Spaced revision", "Skipping breaks", "Only rereading"], 1),
            ("What should you do after a practice quiz?", ["Ignore mistakes", "Review wrong answers", "Delete notes", "Stop studying"], 1),
            ("A useful focused study block can start with:", ["A clear small goal", "Many open tabs", "No plan", "Multitasking"], 0),
            ("For a difficult topic, a good first step is:", ["Break it into smaller parts", "Memorize everything at once", "Avoid examples", "Skip it"], 0),
            ("Which is active recall?", ["Copying text repeatedly", "Trying to remember without notes", "Highlighting every line", "Watching without pausing"], 1)
        ]
        score = 0
        for i, item in enumerate(questions):
            if request.form.get(f"q{i}") == str(item[2]): score += 1
        with db() as con:
            con.execute("INSERT INTO quiz_results(user_id,subject,score,total,created_at) VALUES(?,?,?,?,?)",
                        (session["user_id"], subject, score, len(questions), datetime.now().isoformat(timespec="seconds")))
        return render_template("quiz_result.html", score=score, total=len(questions), subject=subject, questions=questions)
    with db() as con:
        history = con.execute("SELECT * FROM quiz_results WHERE user_id=? ORDER BY id DESC LIMIT 5", (session["user_id"],)).fetchall()
    return render_template("quiz.html", history=history)

@app.route("/notes")
@login_required
def notes():
    with db() as con:
        docs = con.execute("SELECT * FROM documents WHERE user_id=? ORDER BY id DESC", (session["user_id"],)).fetchall()
    return render_template("notes.html", docs=docs)

@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html")

@app.errorhandler(413)
def too_large(_):
    flash("File is too large. Maximum upload size is 15 MB.", "error")
    return redirect(url_for("materials"))

@app.errorhandler(404)
def not_found(_):
    return render_template("404.html"), 404

init_db()
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG", "0") == "1")
