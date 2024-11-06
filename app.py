from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
import sqlite3
from datetime import datetime
from functools import wraps


app = Flask(__name__)
app.secret_key = 'your_secret_key'
bcrypt = Bcrypt(app)

def get_db_connection():
    conn = sqlite3.connect("job_applications.db")  # Ensure this matches the actual path
    conn.row_factory = sqlite3.Row
    return conn

# Signup Route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                         (username, email, hashed_password))
            conn.commit()
        except sqlite3.IntegrityError:
            flash("Username or email already exists")
            return redirect(url_for("signup"))
        conn.close()
        flash("Signup successful, please log in.")
        return redirect(url_for("login"))

    return render_template("signup.html")

# Login Route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        
        if user and bcrypt.check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Login successful!")
            return redirect(url_for("index"))
        else:
            flash("Incorrect email or password.")
    return render_template("login.html")

# Logout Route
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for("login"))

# Check if user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
@login_required
def index():
    user_id = session["user_id"]
    conn = get_db_connection()
    applications = conn.execute("SELECT * FROM applications WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()
    return render_template("index.html", applications=applications)

@app.route("/add", methods=["GET", "POST"])
@login_required
def add_application():
    if request.method == "POST":
        title = request.form["title"]
        company = request.form["company"]
        stage = request.form["stage"]
        salary = int(request.form["salary"])
        date_applied = request.form["date_applied"]
        deadline = request.form.get("deadline", None)
        role_type = request.form.get("role_type", None)
        priority = 1 if "priority" in request.form else 0
        user_id = session["user_id"]

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO applications (title, company, stage, salary, date_applied, deadline, role_type, priority, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, company, stage, salary, date_applied, deadline, role_type, priority, user_id))
        conn.commit()
        conn.close()

        return redirect(url_for("index"))

    return render_template("add_application.html")


# Selection Sort: Sort by Salary
def selection_sort(applications):
    n = len(applications)
    for i in range(n):
        min_index = i
        for j in range(i + 1, n):
            if applications[j]["salary"] < applications[min_index]["salary"]:
                min_index = j
        # Swap
        applications[i], applications[min_index] = applications[min_index], applications[i]
    return applications

# Shell Sort: Sort by Date Applied
def shell_sort(applications):
    n = len(applications)
    gap = n // 2
    while gap > 0:
        for i in range(gap, n):
            temp = applications[i]
            j = i
            # Sort by date_applied
            while j >= gap and applications[j - gap]["date_applied"] > temp["date_applied"]:
                applications[j] = applications[j - gap]
                j -= gap
            applications[j] = temp
        gap //= 2
    return applications

# Bucket Sort: Sort by Stage
def bucket_sort(applications):
    # Define buckets based on stages
    buckets = {
        "Applied": [],
        "Interview": [],
        "Offer": [],
        "Rejected": []
    }

    # Place applications in the corresponding bucket
    for app in applications:
        stage = app["stage"]
        if stage in buckets:
            buckets[stage].append(app)
        else:
            buckets["Applied"].append(app)  # Default to "Applied" if stage is unknown

    # Concatenate buckets
    sorted_applications = []
    for stage in ["Applied", "Interview", "Offer", "Rejected"]:
        sorted_applications.extend(buckets[stage])

    return sorted_applications


# Route to delete an application by ID
@app.route("/delete/<int:id>", methods=["POST"])
def delete_application(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM applications WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

# Route to view applications by filter
@app.route("/view/<filter_type>")
def view_applications(filter_type):
    conn = get_db_connection()
    applications = conn.execute("SELECT * FROM applications").fetchall()
    applications = [dict(app) for app in applications]  # Convert Row objects to dictionaries
    conn.close()

    # Apply sorting based on filter_type
    if filter_type == "salary":
        applications = selection_sort(applications)
    elif filter_type == "date":
        applications = shell_sort(applications)
    elif filter_type == "stage":
        applications = bucket_sort(applications)

    return render_template("view_applications.html", applications=applications, filter_type=filter_type)

# Route to update the stage of an application
@app.route("/update_stage/<int:id>", methods=["POST"])
def update_stage(id):
    new_stage = request.form["stage"]
    conn = get_db_connection()
    conn.execute("UPDATE applications SET stage = ? WHERE id = ?", (new_stage, id))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


# Route to search applications by role type
@app.route("/search", methods=["GET", "POST"])
def search():
    applications = None
    if request.method == "POST":
        role_type = request.form["role_type"]
        conn = get_db_connection()
        applications = conn.execute("SELECT * FROM applications WHERE role_type = ?", (role_type,)).fetchall()
        conn.close()
    return render_template("view_applications.html", applications=applications, filter_type="search")



if __name__ == "__main__":
    app.run(debug=True)