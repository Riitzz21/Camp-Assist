# 🏫 Camp-Assist
### Smart College Complaint & Maintenance Management System

**No Complaint Lost. No Task Unowned. No Resolution Unverified.**

Camp-Assist is a web-based college complaint and maintenance management platform designed to simplify the reporting, assignment, tracking, and resolution of campus maintenance issues.

The system provides a transparent and organized platform where students and faculty can report maintenance problems and track their progress until resolution.

---

## 📌 Project Overview

In many colleges, maintenance complaints are handled manually, making it difficult to track complaint status, assign maintenance staff, and monitor resolution.

Camp-Assist addresses these challenges by providing a centralized digital platform for complaint management.

The system supports role-based access for:

- Student
- Faculty
- Administrator
- Maintenance Staff

---

## ✨ Key Features

### 👨‍🎓 Student & Faculty
- User registration and login
- Submit maintenance complaints online
- View personal complaints
- Track complaint status
- Submit feedback and ratings after resolution

### 👨‍💼 Administrator
- Admin dashboard with complaint statistics
- View and manage all college complaints
- Assign complaints to maintenance staff
- Update complaint status
- Manage maintenance staff
- View student and faculty feedback
- Visual analytics and charts

### 🛠️ Maintenance Staff
- View assigned maintenance complaints
- Monitor assigned tasks
- Update complaint progress and status
- Add maintenance work remarks

### 📊 Dashboard & Analytics
- Total complaints
- Pending complaints
- Assigned complaints
- In-progress complaints
- Resolved complaints
- Rejected complaints
- User statistics
- Feedback overview and rating distribution

---

## 🧰 Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web application framework |
| MySQL | Database management |
| HTML | Web page structure |
| CSS | Styling and layout |
| JavaScript | Interactive functionality |
| Chart.js | Dashboard visualization |
| VS Code | Development environment |
| MySQL Workbench | Database administration |

---

## 🗂️ Project Structure

```text
Smart_College_Complaint_System/
│
├── database/
│   └── schema.sql
│
├── static/
│   ├── style.css
│   └── camp_assist.svg
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── admin_dashboard.html
│   ├── staff_dashboard.html
│   ├── all_complaints.html
│   ├── manage_staff.html
│   └── ...
│
├── .env
├── .gitignore
├── app.py
├── requirements.txt
└── README.md
```

*Note: The template list above shows the main files. Your actual project may contain additional templates and Python files.*

---

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Riittzz21/Camp-Assist.git
```

### 2. Navigate to the Project Folder

```bash
cd Camp-Assist
```

### 3. Create a Virtual Environment

```bash
python -m venv .venv
```

### 4. Activate the Virtual Environment

For Windows PowerShell:

```powershell
.venv\Scripts\Activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure the Database

- Open MySQL Workbench.
- Create or select the database `smart_college_complaints`.
- Execute the SQL commands from `database/schema.sql`.

### 7. Configure Environment Variables

Create a `.env` file in the project root and add your local configuration:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=smart_college_complaints
SECRET_KEY=your_flask_secret_key
```

Replace the example values with your own local credentials.

**Important:** Never upload your `.env` file or database passwords to GitHub.

### 8. Run the Application

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000
```

---

## 🗄️ Database Modules

The application uses MySQL to store and manage complaint-related information.

Main database tables include:

- `users`
- `categories`
- `complaints`
- `complaint_assignments`
- `complaint_status_history`
- `complaint_comments`
- `feedback`

These tables support user management, complaint tracking, staff assignment, status history, comments, and feedback.

---

## 🔄 Complaint Workflow

1. Student or faculty logs in.
2. User submits a maintenance complaint.
3. The complaint is stored in the MySQL database.
4. Administrator reviews the complaint.
5. Administrator assigns maintenance staff.
6. Staff performs the maintenance work and updates the status.
7. User tracks the complaint until resolution.
8. User submits feedback and rating after resolution.

---

## 🔐 Security

- Password hashing using Werkzeug
- Role-based access control
- Session-based authentication
- Environment variables for sensitive configuration
- `.gitignore` protection for `.env` and virtual environment

---

## 🚀 Future Enhancements

- AI-based complaint categorization
- Automatic complaint priority prediction
- Email notifications for complaint updates
- Mobile-friendly application
- QR code-based complaint submission
- Advanced maintenance analytics

---

## 🎓 Academic Project

**Project Name:** Camp-Assist  
**Project Title:** Smart College Complaint & Maintenance Management System  
**Course:** Master of Computer Applications (MCA) – AI/ML  
**Academic Year:** 2025–2027

---

## 👩‍💻 Developed By

**Rajeshwari Vyas**  
MCA – Artificial Intelligence & Machine Learning

---

## 📄 License

This project is developed for academic and educational purposes.
