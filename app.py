
from flask import Flask, render_template, request
import sqlite3
import os
import sys
import importlib.util

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "exam.db")


# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_answer TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            exam_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL
        )
    """)

    count = conn.execute(
        "SELECT COUNT(*) FROM exams"
    ).fetchone()[0]

    if count == 0:
        cursor = conn.execute("""
            INSERT INTO exams (title, description)
            VALUES (?, ?)
        """, (
            "Cloud Computing Fundamentals",
            "Test your knowledge of cloud computing."
        ))

        exam_id = cursor.lastrowid

        questions = [
            (exam_id, "What does IaaS stand for?",
             "Internet as a Service",
             "Infrastructure as a Service",
             "Information as a Service",
             "Integration as a Service", "B"),

            (exam_id, "Which model provides software online?",
             "IaaS", "PaaS", "SaaS", "LAN", "C"),

            (exam_id, "Which Python framework are we using?",
             "Flask", "Django", "React", "Bootstrap", "A"),

            (exam_id, "Which database are we using locally?",
             "Excel", "SQLite", "PowerPoint", "HTML", "B"),

            (exam_id, "Which is an example of a cloud platform?",
             "Notepad", "Calculator", "AWS", "Paint", "C")
        ]

        conn.executemany("""
            INSERT INTO questions (
                exam_id, question, option_a, option_b,
                option_c, option_d, correct_answer
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, questions)

    conn.commit()
    conn.close()


# ---------------- HOME ----------------

@app.route("/")
def home():
    conn = get_db()
    exams = conn.execute(
        "SELECT * FROM exams"
    ).fetchall()
    conn.close()

    return render_template("index.html", exams=exams)


# ---------------- EXAM ----------------

@app.route("/exam/<int:exam_id>", methods=["GET", "POST"])
def exam(exam_id):
    conn = get_db()

    exam_data = conn.execute(
        "SELECT * FROM exams WHERE id = ?",
        (exam_id,)
    ).fetchone()

    questions = conn.execute(
        "SELECT * FROM questions WHERE exam_id = ?",
        (exam_id,)
    ).fetchall()

    conn.close()

    if exam_data is None:
        return "Exam not found", 404

    if request.method == "POST":
        student_name = request.form.get(
            "student_name", ""
        ).strip()

        if not student_name:
            return "Please enter your name.", 400

        score = 0

        for question in questions:
            selected = request.form.get(
                str(question["id"]), ""
            )

            if selected == question["correct_answer"]:
                score += 1

        conn = get_db()

        conn.execute("""
            INSERT INTO results (
                student_name, exam_id, score, total
            )
            VALUES (?, ?, ?, ?)
        """, (
            student_name,
            exam_id,
            score,
            len(questions)
        ))

        conn.commit()
        conn.close()

        return render_template(
            "result.html",
            student_name=student_name,
            score=score,
            total=len(questions)
        )

    return render_template(
        "exam.html",
        exam=exam_data,
        questions=questions
    )


# ---------------- RESULTS ----------------

@app.route("/results")
def results():
    conn = get_db()

    records = conn.execute("""
        SELECT results.*, exams.title
        FROM results
        JOIN exams ON results.exam_id = exams.id
        ORDER BY results.id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "results.html",
        results=records
    )


# ---------------- CLOUD MODELS ----------------

@app.route("/cloud-models")
def cloud_models():
    return render_template("cloud_models.html")


# ---------------- CLOUD MODEL TESTING ----------------

@app.route("/cloud-test/<model>")
def cloud_test(model):
    model = model.lower()

    if model not in ("iaas", "paas", "saas"):
        return "Cloud model not found", 404

    results = []

    def add_result(name, passed, details):
        results.append({
            "name": name,
            "status": "PASS" if passed else "FAIL",
            "details": details
        })

    # IaaS checks
    if model == "iaas":
        add_result(
            "Flask application",
            True,
            "The Flask application is serving this request."
        )

        try:
            conn = get_db()
            conn.execute("SELECT 1").fetchone()
            conn.close()

            add_result(
                "Database connectivity",
                True,
                "SQLite database connection succeeded."
            )
        except Exception as error:
            add_result(
                "Database connectivity",
                False,
                str(error)
            )

        add_result(
            "Infrastructure concepts",
            True,
            "Virtual machines, storage and networking "
            "are included as educational concepts."
        )

    # PaaS checks
    elif model == "paas":
        add_result(
            "Python runtime",
            sys.version_info >= (3, 10),
            "Python version: " + sys.version.split()[0]
        )

        add_result(
            "Flask installation",
            importlib.util.find_spec("flask") is not None,
            "Checks whether Flask is installed."
        )

        requirements_path = os.path.join(
            BASE_DIR, "requirements.txt"
        )

        add_result(
            "Requirements file",
            os.path.isfile(requirements_path),
            "Checks whether requirements.txt exists."
        )

        procfile_path = os.path.join(BASE_DIR, "Procfile")

        add_result(
            "Procfile configuration",
            os.path.isfile(procfile_path),
            "Checks whether a Procfile exists."
        )

    # SaaS checks
    elif model == "saas":
        for endpoint, label in [
            ("home", "Home page"),
            ("exam", "Examination page"),
            ("results", "Results page"),
            ("cloud_models", "Cloud Models page")
        ]:
            exists = endpoint in app.view_functions

            add_result(
                label,
                exists,
                "Application route is registered."
                if exists else "Application route is missing."
            )

        try:
            conn = get_db()

            conn.execute(
                "SELECT * FROM exams LIMIT 1"
            )
            conn.execute(
                "SELECT * FROM questions LIMIT 1"
            )
            conn.execute(
                "SELECT * FROM results LIMIT 1"
            )

            conn.close()

            add_result(
                "Database tables",
                True,
                "Exam, question and result tables are accessible."
            )
        except Exception as error:
            add_result(
                "Database tables",
                False,
                str(error)
            )

    passed_count = sum(
        1 for item in results
        if item["status"] == "PASS"
    )

    model_info = {
        "iaas": {
            "name": "IaaS",
            "full_name": "Infrastructure as a Service",
            "description": "Infrastructure and database checks."
        },
        "paas": {
            "name": "PaaS",
            "full_name": "Platform as a Service",
            "description": "Python runtime and deployment configuration checks."
        },
        "saas": {
            "name": "SaaS",
            "full_name": "Software as a Service",
            "description": "Application route and database checks."
        }
    }

    return render_template(
        "cloud_test.html",
        model=model_info[model],
        results=results,
        passed_count=passed_count,
        total_count=len(results)
    )


# ---------------- START APPLICATION ----------------

initialize_database()

if __name__ == "__main__":
    app.run(debug=True)