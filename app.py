import re
import os
import mysql.connector

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)

from dotenv import load_dotenv
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("Please configure FLASK_SECRET_KEY in .env")


# ---------------- DATABASE CONNECTION ----------------


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", "3306")),
        connection_timeout=5,
        use_pure=True
    )


# ---------------- HOME PAGE ----------------

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# ---------------- REGISTRATION ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    print("REGISTER ROUTE HIT:", request.method, flush=True)


    if request.method == "POST":
        print("STEP 1: POST received", flush=True)

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "").strip()
        department = request.form.get("department", "").strip()

        # Check required fields
        if not name or not email or not password or not role:
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("register"))

        # Validate role
        if role not in ("student", "faculty"):
            flash("Please select a valid role.", "error")
            return redirect(url_for("register"))

        # Strong password pattern
        password_pattern = (
            r"^(?=.*[a-z])"
            r"(?=.*[A-Z])"
            r"(?=.*\d)"
            r"(?=.*[@$!%*?&#])"
            r"[A-Za-z\d@$!%*?&#]{8,}$"
        )

        print("STEP 2: Checking password", flush=True)

        # Validate password
        if not re.fullmatch(password_pattern, password):
            flash(
                "Password must contain at least 8 characters, "
                "one uppercase letter, one lowercase letter, "
                "one number and one special character (@$!%*?&#).",
                "error"
            )
            return redirect(url_for("register"))

        print("STEP 3: Password accepted", flush=True)

        # Hash password before storing
        password_hash = generate_password_hash(password)

        connection = None
        cursor = None

        try:

            print("STEP 4: Connecting to database", flush=True)


            connection = get_db_connection()
            print("STEP 5: Database connected", flush=True)

            cursor = connection.cursor()
            print("STEP 6: Cursor created", flush=True)

            query = """
                INSERT INTO users
                (name, email, password_hash, role, department)
                VALUES (%s, %s, %s, %s, %s)
            """

            values = (
                name,
                email,
                password_hash,
                role,
                department or None
            )

            cursor.execute(query, values)
            print("STEP 7: Query executed", flush=True)

            connection.commit()

            print("STEP 8: Data committed", flush=True)

            flash(
                "Registration successful! Please log in.",
                "success"
            )

            return redirect(url_for("login"))

        except mysql.connector.IntegrityError:
            if connection and connection.is_connected():
                connection.rollback()

            flash(
                "This email address is already registered.",
                "error"
            )

        except mysql.connector.Error as error:
            if connection and connection.is_connected():
                connection.rollback()

            print("Registration Database Error:", error)

            flash(
                "Database error. Please try again.",
                "error"
            )

        except Exception as error:
            if connection and connection.is_connected():
                connection.rollback()

            print("Registration Error:", error)

            flash(
                "Something went wrong. Please try again.",
                "error"
            )

        finally:
            if cursor is not None:
                cursor.close()

            if connection is not None and connection.is_connected():
                connection.close()

        return redirect(url_for("register"))

    return render_template("register.html")


# ---------------- COMPLAINT SUBMISSION ----------------

@app.route("/complaints/new", methods=["GET", "POST"])
def new_complaint():

    # Check whether user is logged in
    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    # Allow only students and faculty
    if session.get("role") not in ("student", "faculty"):
        flash("You are not authorized to submit complaints.", "error")
        return redirect(url_for("dashboard"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        if request.method == "POST":

            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            location = request.form.get("location", "").strip()
            category_id = request.form.get("category_id", "")
            priority = request.form.get("priority", "medium")

            if not title or not description or not location or not category_id:
                flash("Please fill in all required fields.", "error")
                return redirect(url_for("new_complaint"))

            if priority not in ("low", "medium", "high"):
                flash("Invalid priority selected.", "error")
                return redirect(url_for("new_complaint"))

            # Verify category exists
            cursor.execute(
                "SELECT id FROM categories WHERE id = %s",
                (category_id,)
            )

            category = cursor.fetchone()

            if category is None:
                flash("Please select a valid category.", "error")
                return redirect(url_for("new_complaint"))

            # Insert complaint into database
            query = """
                INSERT INTO complaints
                (user_id, category_id, title, description, location, priority)
                VALUES (%s, %s, %s, %s, %s, %s)
            """

            values = (
                session["user_id"],
                category_id,
                title,
                description,
                location,
                priority
            )

            cursor.execute(query, values)
            connection.commit()

            flash("Your complaint has been submitted successfully!", "success")

            return redirect(url_for("dashboard"))

        # Fetch categories for dropdown
        cursor.execute(
            "SELECT id, name FROM categories ORDER BY name"
        )

        categories = cursor.fetchall()

        return render_template(
            "complaint_form.html",
            categories=categories
        )

    except mysql.connector.Error as error:
        if connection and connection.is_connected():
            connection.rollback()

        print("Complaint Database Error:", error, flush=True)

        flash("Database error. Please try again.", "error")
        return redirect(url_for("dashboard"))

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


# ---------------- MY COMPLAINTS ----------------


@app.route("/my-complaints")
def my_complaints():

    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    if session.get("role") not in ["student", "faculty"]:
        flash("Access denied.", "error")
        return redirect(url_for("dashboard"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                c.id,
                c.title,
                c.description,
                c.location,
                c.priority,
                c.status,
                c.created_at,
                cat.name AS category_name,

                (
                    SELECT GROUP_CONCAT(
                        DISTINCT staff.name
                        SEPARATOR ', '
                    )
                    FROM complaint_assignments ca
                    JOIN users staff ON ca.staff_id = staff.id
                    WHERE ca.complaint_id = c.id
                ) AS assigned_staff,

                (
                    SELECT GROUP_CONCAT(
                        cc.comment
                        ORDER BY cc.created_at DESC
                        SEPARATOR ' | '
                    )
                    FROM complaint_comments cc
                    WHERE cc.complaint_id = c.id
                ) AS work_remarks,

                (
                    SELECT GROUP_CONCAT(
                        CONCAT(
                            h.old_status, ' -> ', h.new_status,
                            ' (', COALESCE(h.remarks, 'No remarks'), ')'
                        )
                        ORDER BY h.id DESC
                        SEPARATOR ' | '
                    )
                    FROM complaint_status_history h
                    WHERE h.complaint_id = c.id
                ) AS status_history

            FROM complaints c

            LEFT JOIN categories cat
                ON c.category_id = cat.id

            WHERE c.user_id = %s

            ORDER BY c.created_at DESC
        """, (session["user_id"],))

        complaints = cursor.fetchall()

        return render_template(
            "my_complaints.html",
            complaints=complaints
        )

    except Exception as error:
        print("My Complaints Error:", error)
        flash("Unable to load your complaints.", "error")
        return redirect(url_for("dashboard"))

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

#-------------------------Submit feedback-------------------------

@app.route("/complaints/<int:complaint_id>/feedback", methods=["GET", "POST"])
def submit_feedback(complaint_id):

    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    if session.get("role") not in ["student", "faculty"]:
        flash("Access denied.", "error")
        return redirect(url_for("dashboard"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Verify complaint ownership and resolution
        cursor.execute("""
            SELECT id, title, status
            FROM complaints
            WHERE id = %s AND user_id = %s
        """, (complaint_id, session["user_id"]))

        complaint = cursor.fetchone()

        if not complaint:
            flash("Complaint not found.", "error")
            return redirect(url_for("my_complaints"))

        if complaint["status"] != "resolved":
            flash("Feedback can only be submitted for resolved complaints.", "error")
            return redirect(url_for("my_complaints"))

        # Check whether feedback already exists
        cursor.execute("""
            SELECT id
            FROM feedback
            WHERE complaint_id = %s
        """, (complaint_id,))

        existing_feedback = cursor.fetchone()

        if existing_feedback:
            flash("Feedback has already been submitted for this complaint.", "error")
            return redirect(url_for("my_complaints"))

        if request.method == "POST":

            rating = request.form.get("rating", type=int)
            comments = request.form.get("comments", "").strip()

            if rating is None or rating < 1 or rating > 5:
                flash("Please select a rating between 1 and 5.", "error")
                return render_template(
                    "feedback.html",
                    complaint=complaint
                )

            cursor.execute("""
                INSERT INTO feedback
                (complaint_id, user_id, rating, comments)
                VALUES (%s, %s, %s, %s)
            """, (
                complaint_id,
                session["user_id"],
                rating,
                comments or None
            ))

            connection.commit()

            flash("Thank you! Your feedback was submitted successfully.", "success")
            return redirect(url_for("my_complaints"))

        return render_template(
            "feedback.html",
            complaint=complaint
        )

    except mysql.connector.IntegrityError:
        if connection:
            connection.rollback()

        flash("Feedback has already been submitted.", "error")
        return redirect(url_for("my_complaints"))

    except Exception as error:
        if connection:
            connection.rollback()

        print("Feedback Error:", error)
        flash("Unable to submit feedback.", "error")
        return redirect(url_for("my_complaints"))

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

#-----------------------Admin feedback-------------------------

@app.route("/admin/feedback")
def admin_feedback():

    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        flash("Access denied. Admin only.", "error")
        return redirect(url_for("dashboard"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                f.id,
                f.complaint_id,
                f.rating,
                f.comments,
                f.created_at,
                u.name AS user_name,
                u.email AS user_email,
                c.title AS complaint_title

            FROM feedback f

            JOIN users u
                ON f.user_id = u.id

            JOIN complaints c
                ON f.complaint_id = c.id

            ORDER BY f.created_at DESC
        """)

        feedback_list = cursor.fetchall()

        return render_template(
            "admin_feedback.html",
            feedback_list=feedback_list
        )

    except Exception as error:
        print("Admin Feedback Error:", error)
        flash("Unable to load feedback.", "error")
        return redirect(url_for("admin_dashboard"))

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


# ---------------- ADMIN DASHBOARD ----------------



@app.route("/admin/dashboard")
def admin_dashboard():

    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        flash("Access denied. Admin only.", "error")
        return redirect(url_for("dashboard"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # 1. Complaint statistics
        cursor.execute("""
            SELECT
                COUNT(*) AS total_complaints,

                SUM(CASE WHEN status = 'pending'
                    THEN 1 ELSE 0 END) AS pending_complaints,

                SUM(CASE WHEN status = 'assigned'
                    THEN 1 ELSE 0 END) AS assigned_complaints,

                SUM(CASE WHEN status = 'in_progress'
                    THEN 1 ELSE 0 END) AS in_progress_complaints,

                SUM(CASE WHEN status = 'resolved'
                    THEN 1 ELSE 0 END) AS resolved_complaints,

                SUM(CASE WHEN status = 'rejected'
                    THEN 1 ELSE 0 END) AS rejected_complaints

            FROM complaints
        """)

        complaint_stats = cursor.fetchone()

        # 2. User statistics
        cursor.execute("""
            SELECT
                SUM(CASE WHEN role = 'student'
                    THEN 1 ELSE 0 END) AS total_students,

                SUM(CASE WHEN role = 'faculty'
                    THEN 1 ELSE 0 END) AS total_faculty,

                SUM(CASE WHEN role = 'staff'
                    THEN 1 ELSE 0 END) AS total_staff

            FROM users
        """)

        user_stats = cursor.fetchone()

        # 3. Feedback statistics
        cursor.execute("""
            SELECT
                COUNT(*) AS total_feedback,
                COALESCE(ROUND(AVG(rating), 2), 0)
                    AS average_rating
            FROM feedback
        """)

        feedback_stats = cursor.fetchone()

        # 4. Feedback rating distribution
        cursor.execute("""
            SELECT rating, COUNT(*) AS total
            FROM feedback
            GROUP BY rating
        """)

        rating_rows = cursor.fetchall()

        rating_map = {
            int(row["rating"]): row["total"]
            for row in rating_rows
            if row["rating"] is not None
        }

        rating_counts = [
            rating_map.get(i, 0)
            for i in range(1, 6)
        ]

        # 5. Display admin dashboard
        return render_template(
            "admin_dashboard.html",
            name=session.get("name"),
            complaint_stats=complaint_stats,
            user_stats=user_stats,
            feedback_stats=feedback_stats,
            rating_counts=rating_counts
        )

    except Exception as error:
        print("Admin Dashboard Error:", error)

        flash(
            "Unable to load dashboard statistics.",
            "error"
        )

        return redirect(url_for("login"))

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()



# -----------------------Login-----------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter email and password.", "error")
            return redirect(url_for("login"))

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT id, name, email, password_hash, role
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            user = cursor.fetchone()

            if user and check_password_hash(
                user["password_hash"], password
            ):

                # Store user information in session
                session["user_id"] = user["id"]
                session["name"] = user["name"]
                session["role"] = user["role"]

                flash(
                    "Welcome, " + user["name"] + "!",
                    "success"
                )

                # Redirect according to user role
                if user["role"] == "admin":
                    return redirect(url_for("admin_dashboard"))

                elif user["role"] == "staff":
                    return redirect(url_for("staff_dashboard"))

                else:
                    return redirect(url_for("dashboard"))

            else:
                flash("Invalid email or password.", "error")
                return redirect(url_for("login"))

        except Exception as error:
            print("Login Error:", error)
            flash("Something went wrong. Please try again.", "error")
            return redirect(url_for("login"))

        finally:
            if cursor is not None:
                cursor.close()

            if connection is not None and connection.is_connected():
                connection.close()

    return render_template("login.html")




# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        name=session["name"],
        role=session["role"]
    )


# ---------------- ALL COLLEGE COMPLAINTS ----------------

@app.route("/admin/complaints")
def all_complaints():

    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        flash("Access denied. Admin only.", "error")
        return redirect(url_for("dashboard"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Fetch all complaints
        cursor.execute("""
            SELECT
            c.id,
            c.title,
            c.description,
            c.location,
            c.priority,
            c.status,
            c.created_at,

            u.name AS student_name,
            u.email AS student_email,
            cat.name AS category_name,

        (
            SELECT GROUP_CONCAT(
                DISTINCT staff.name
                SEPARATOR ', '
            )
            FROM complaint_assignments ca
            JOIN users staff ON ca.staff_id = staff.id
            WHERE ca.complaint_id = c.id
        ) AS assigned_staff,

        (
            SELECT GROUP_CONCAT(
                cc.comment
                ORDER BY cc.created_at DESC
                SEPARATOR ' | '
            )
            FROM complaint_comments cc
            WHERE cc.complaint_id = c.id
        ) AS work_remarks,

        (
            SELECT GROUP_CONCAT(
                CONCAT(
                    h.old_status, ' -> ', h.new_status,
                    ' (', COALESCE(h.remarks, 'No remarks'), ')'
                )
                ORDER BY h.id DESC
                SEPARATOR ' | '
            )
            FROM complaint_status_history h
            WHERE h.complaint_id = c.id
        ) AS status_history

        FROM complaints c

        LEFT JOIN users u ON c.user_id = u.id
        LEFT JOIN categories cat ON c.category_id = cat.id

        ORDER BY c.created_at DESC
        """)

        complaints = cursor.fetchall()

        # Fetch all maintenance staff
        cursor.execute("""
            SELECT id, name
            FROM users
            WHERE role = 'staff'
            ORDER BY name
        """)

        staff_members = cursor.fetchall()

        return render_template(
            "all_complaints.html",
            complaints=complaints,
            staff_members=staff_members
        )

    except Exception as error:
        print("All Complaints Error:", error)
        flash("Unable to load complaints.", "error")
        return redirect(url_for("admin_dashboard"))

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()




# ---------------- ADMIN: UPDATE COMPLAINT STATUS ----------------

@app.route(
    "/admin/complaints/<int:complaint_id>/status",
    methods=["POST"]
)
def update_complaint_status(complaint_id):

    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        flash("Access denied. Admin only.", "error")
        return redirect(url_for("dashboard"))

    allowed_statuses = [
        "pending",
        "assigned",
        "in_progress",
        "resolved",
        "rejected"
    ]

    new_status = request.form.get("status", "").strip()
    remarks = request.form.get("remarks", "").strip()

    if new_status not in allowed_statuses:
        flash("Invalid complaint status.", "error")
        return redirect(url_for("all_complaints"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        connection.start_transaction()

        cursor = connection.cursor(dictionary=True)

        # Get the current status
        cursor.execute(
            "SELECT status FROM complaints WHERE id = %s FOR UPDATE",
            (complaint_id,)
        )

        complaint = cursor.fetchone()

        if complaint is None:
            flash("Complaint not found.", "error")
            return redirect(url_for("all_complaints"))

        old_status = complaint["status"]

        if old_status == new_status:
            connection.rollback()
            flash("Complaint already has this status.", "info")
            return redirect(url_for("all_complaints"))

        # Update complaint status
        cursor.execute(
            """
            UPDATE complaints
            SET status = %s
            WHERE id = %s
            """,
            (new_status, complaint_id)
        )

        # Record status history
        cursor.execute(
            """
            INSERT INTO complaint_status_history
            (complaint_id, changed_by, old_status, new_status, remarks)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                complaint_id,
                session["user_id"],
                old_status,
                new_status,
                remarks or None
            )
        )

        connection.commit()

        flash("Complaint status updated successfully!", "success")

    except Exception as error:
        if connection and connection.is_connected():
            connection.rollback()

        print("Status Update Error:", error)
        flash("Unable to update complaint status.", "error")

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

    return redirect(url_for("all_complaints"))


@app.route(
    "/admin/complaints/<int:complaint_id>/assign",
    methods=["POST"]
)
def assign_complaint(complaint_id):

    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        flash("Access denied. Admin only.", "error")
        return redirect(url_for("dashboard"))

    staff_id = request.form.get("staff_id", type=int)
    notes = request.form.get("notes", "").strip()

    if not staff_id:
        flash("Please select a staff member.", "error")
        return redirect(url_for("all_complaints"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        connection.start_transaction()
        cursor = connection.cursor(dictionary=True)

        # Check whether complaint exists
        cursor.execute(
            "SELECT id, status FROM complaints WHERE id = %s FOR UPDATE",
            (complaint_id,)
        )
        complaint = cursor.fetchone()

        if complaint is None:
            connection.rollback()
            flash("Complaint not found.", "error")
            return redirect(url_for("all_complaints"))

        # Check whether selected user is maintenance staff
        cursor.execute(
            "SELECT id FROM users WHERE id = %s AND role = 'staff'",
            (staff_id,)
        )
        staff = cursor.fetchone()

        if staff is None:
            connection.rollback()
            flash("Invalid maintenance staff member.", "error")
            return redirect(url_for("all_complaints"))

        # Create assignment
        cursor.execute(
            """
            INSERT INTO complaint_assignments
            (complaint_id, staff_id, assigned_by, notes)
            VALUES (%s, %s, %s, %s)
            """,
            (
                complaint_id,
                staff_id,
                session["user_id"],
                notes or None
            )
        )

        old_status = complaint["status"]

        # Update complaint status
        cursor.execute(
            """
            UPDATE complaints
            SET status = 'assigned'
            WHERE id = %s
            """,
            (complaint_id,)
        )

        # Record status history if status changed
        if old_status != "assigned":
            cursor.execute(
                """
                INSERT INTO complaint_status_history
                (complaint_id, changed_by, old_status, new_status, remarks)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    complaint_id,
                    session["user_id"],
                    old_status,
                    "assigned",
                    notes or "Complaint assigned to maintenance staff"
                )
            )

        connection.commit()
        flash("Complaint assigned successfully!", "success")

    except Exception as error:
        if connection and connection.is_connected():
            connection.rollback()

        print("Assignment Error:", error)
        flash("Unable to assign complaint.", "error")

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

    return redirect(url_for("all_complaints"))

# ---------------- MANAGE STAFF ----------------

@app.route("/admin/staff")
def manage_staff():

    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        flash("Access denied. Admin only.", "error")
        return redirect(url_for("dashboard"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, name, email, department
            FROM users
            WHERE role = 'staff'
            ORDER BY name
        """)

        staff_members = cursor.fetchall()

        return render_template(
            "manage_staff.html",
            staff_members=staff_members
        )

    except Exception as error:
        print("Manage Staff Error:", error)
        flash("Unable to load staff members.", "error")
        return redirect(url_for("admin_dashboard"))

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


@app.route("/admin/staff/add", methods=["GET", "POST"])
def add_staff():
    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        flash("Access denied. Admin only.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        department = request.form.get("department", "").strip()

        if not name or not email or not password:
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("add_staff"))

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
            return redirect(url_for("add_staff"))

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO users
                (name, email, password_hash, role, department)
                VALUES (%s, %s, %s, 'staff', %s)
                """,
                (
                    name,
                    email,
                    generate_password_hash(password),
                    department or None
                )
            )

            connection.commit()
            flash("Staff member added successfully!", "success")
            return redirect(url_for("manage_staff"))

        except mysql.connector.IntegrityError:
            if connection:
                connection.rollback()
            flash("This email address is already registered.", "error")

        except Exception as error:
            if connection:
                connection.rollback()
            print("Add Staff Error:", error)
            flash("Unable to add staff member.", "error")

        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None and connection.is_connected():
                connection.close()

    return render_template("add_staff.html")



# ---------------- STAFF DASHBOARD ----------------

@app.route("/staff/dashboard")
def staff_dashboard():

    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    if session.get("role") != "staff":
        flash("Access denied. Staff only.", "error")
        return redirect(url_for("dashboard"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                c.id,
                c.title,
                c.description,
                c.location,
                c.priority,
                c.status,
                c.created_at,
                cat.name AS category_name,
                ca.notes AS assignment_notes
            FROM complaint_assignments ca
            JOIN complaints c
                ON ca.complaint_id = c.id
            LEFT JOIN categories cat
                ON c.category_id = cat.id
            WHERE ca.staff_id = %s
            ORDER BY ca.assigned_at DESC
        """, (session["user_id"],))

        complaints = cursor.fetchall()

        return render_template(
            "staff_dashboard.html",
            complaints=complaints,
            name=session["name"]
        )

    except Exception as error:
        print("Staff Dashboard Error:", error)
        flash("Unable to load assigned complaints.", "error")
        return redirect(url_for("login"))

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


@app.route("/staff/complaints/<int:complaint_id>/update", methods=["POST"])
def staff_update_complaint(complaint_id):

    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    if session.get("role") != "staff":
        flash("Access denied. Staff only.", "error")
        return redirect(url_for("dashboard"))

    new_status = request.form.get("status", "").strip()
    work_remark = request.form.get("comment", "").strip()

    if new_status not in ["in_progress", "resolved"]:
        flash("Invalid complaint status.", "error")
        return redirect(url_for("staff_dashboard"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        connection.start_transaction()
        cursor = connection.cursor(dictionary=True)

        # Check whether this complaint is assigned to this staff member
        cursor.execute("""
            SELECT c.id, c.status
            FROM complaints c
            JOIN complaint_assignments ca
                ON c.id = ca.complaint_id
            WHERE c.id = %s AND ca.staff_id = %s
            FOR UPDATE
        """, (complaint_id, session["user_id"]))

        complaint = cursor.fetchone()

        if not complaint:
            connection.rollback()
            flash("This complaint is not assigned to you.", "error")
            return redirect(url_for("staff_dashboard"))

        old_status = complaint["status"]

        # Update complaint status
        if old_status != new_status:
            cursor.execute("""
                UPDATE complaints
                SET status = %s
                WHERE id = %s
            """, (new_status, complaint_id))

            cursor.execute("""
                INSERT INTO complaint_status_history
                (complaint_id, changed_by, old_status, new_status, remarks)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                complaint_id,
                session["user_id"],
                old_status,
                new_status,
                work_remark or None
            ))

        # Save maintenance work remark
        if work_remark:
            cursor.execute("""
                INSERT INTO complaint_comments
                (complaint_id, user_id, comment)
                VALUES (%s, %s, %s)
            """, (
                complaint_id,
                session["user_id"],
                work_remark
            ))

        connection.commit()
        flash("Complaint updated successfully!", "success")

    except Exception as error:
        if connection:
            connection.rollback()
        print("Staff Update Error:", error)
        flash("Unable to update complaint.", "error")

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

    return redirect(url_for("staff_dashboard"))


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()
    flash("You have been logged out successfully.", "success")

    return redirect(url_for("login"))


# ---------------- ABOUT PAGE ----------------

@app.route("/about")
def about():
    return render_template("about.html")

# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        use_reloader=False
    )
