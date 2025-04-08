from flask import Flask, render_template_string, redirect, url_for, session, request, send_file
from datetime import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'super_secure_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'html', 'txt'}

# Mock databases with explicit IDs
users = {
    'admin': {'id': 0, 'password': 'admin123', 'type': 'admin', 'email': 'admin@example.com'},
    'company1': {'id': 1, 'password': 'comp123', 'type': 'company', 'email': 'comp1@example.com'},
    'student1': {'id': 2, 'password': 'stud123', 'type': 'student', 'email': 'stud1@example.com'}
}
jobs = []  # Will use explicit 'id' field
applications = []  # Will use index as ID
profiles = {}
next_user_id = 3  # Track next available user ID
next_job_id = 0  # Track next available job ID

# Base template
BASE_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Portal - {{ title }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .sidebar { background: #f8f9fa; min-height: 100vh; padding: 20px; }
        .sidebar a { display: block; padding: 10px; color: #333; text-decoration: none; }
        .sidebar a:hover { background: #e9ecef; }
        .content { padding: 20px; }
        .active { background: #e9ecef; font-weight: bold; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('home') }}">Job Portal</a>
            <div class="collapse navbar-collapse">
                <ul class="navbar-nav ms-auto">
                    {% if 'user' not in session %}
                        <li class="nav-item">
                            <a class="nav-link" href="{{ url_for('student_register') }}">Student Sign Up</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="{{ url_for('company_register') }}">Company Sign Up</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="{{ url_for('student_login') }}">Student Login</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="{{ url_for('company_login') }}">Company Login</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="{{ url_for('admin_login') }}">Admin Login</a>
                        </li>
                    {% else %}
                        <li class="nav-item">
                            <a class="nav-link" href="{{ url_for('logout') }}">Logout</a>
                        </li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </nav>
    {{ content }}
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# Templates
MAIN_TEMPLATE = """
{% set title = 'Welcome' %}
{% set content %}
<div class="container mt-5">
    <h1>Welcome to Job Portal</h1>
    <p>Please sign up or log in to continue.</p>
</div>
{% endset %}
""" + BASE_CONTENT

LOGIN_TEMPLATE = """
{% set title = title %}
{% set content %}
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h3>{{ title }}</h3>
                </div>
                <div class="card-body">
                    {% if message %}
                        <div class="alert alert-{{ message_type }}">{{ message }}</div>
                    {% endif %}
                    <form method="post">
                        <div class="mb-3">
                            <label class="form-label">Username</label>
                            <input type="text" name="username" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Password</label>
                            <input type="password" name="password" class="form-control" required>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">Login</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endset %}
""" + BASE_CONTENT

STUDENT_REGISTER_TEMPLATE = """
{% set title = 'Student Sign Up' %}
{% set content %}
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h3>Student Sign Up</h3>
                </div>
                <div class="card-body">
                    {% if message %}
                        <div class="alert alert-{{ message_type }}">{{ message }}</div>
                    {% endif %}
                    <form method="post">
                        <div class="mb-3">
                            <label class="form-label">Username</label>
                            <input type="text" name="username" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Password</label>
                            <input type="password" name="password" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Email</label>
                            <input type="email" name="email" class="form-control" required>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">Sign Up</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endset %}
""" + BASE_CONTENT

COMPANY_REGISTER_TEMPLATE = """
{% set title = 'Company Sign Up' %}
{% set content %}
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h3>Company Sign Up</h3>
                </div>
                <div class="card-body">
                    {% if message %}
                        <div class="alert alert-{{ message_type }}">{{ message }}</div>
                    {% endif %}
                    <form method="post">
                        <div class="mb-3">
                            <label class="form-label">Username</label>
                            <input type="text" name="username" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Password</label>
                            <input type="password" name="password" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Email</label>
                            <input type="email" name="email" class="form-control" required>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">Sign Up</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endset %}
""" + BASE_CONTENT

STUDENT_DASHBOARD = """
{% set title = 'Student Dashboard' %}
{% set content %}
<div class="container-fluid">
    <div class="row">
        <div class="col-md-3 sidebar">
            <h4>Menu</h4>
            <a href="{{ url_for('student_jobs') }}" class="{% if active == 'jobs' %}active{% endif %}">Available Jobs</a>
            <a href="{{ url_for('student_applications') }}" class="{% if active == 'applications' %}active{% endif %}">My Applications</a>
        </div>
        <div class="col-md-9 content">
            <h2>Welcome, {{ username }}</h2>
            {% if message %}
                <div class="alert alert-{{ message_type }}">{{ message }}</div>
            {% endif %}
            {% if section == 'jobs' %}
                <div class="card mt-4">
                    <div class="card-header">Available Jobs</div>
                    <div class="card-body">
                        {% if jobs %}
                            {% for job in jobs %}
                                <div class="card mb-3">
                                    <div class="card-body">
                                        <h5>{{ job['title'] }} (ID: {{ job['id'] }})</h5>
                                        <p>{{ job['company'] }}</p>
                                        <p>{{ job['description'] }}</p>
                                        <a href="{{ url_for('apply_form', job_id=job['id']) }}" class="btn btn-primary">Apply</a>
                                    </div>
                                </div>
                            {% endfor %}
                        {% else %}
                            <p>No jobs available at the moment. Check back later!</p>
                        {% endif %}
                    </div>
                </div>
            {% elif section == 'applications' %}
                <div class="card mt-4">
                    <div class="card-header">My Applications</div>
                    <div class="card-body">
                        {% if my_applications %}
                            {% for app in my_applications %}
                                <div class="card mb-3">
                                    <div class="card-body">
                                        <p>Applied to: {{ app['job']['title'] }} at {{ app['job']['company'] }}</p>
                                        <p>Status: {{ app['status'] }}</p>
                                        <p>Applied on: {{ app['date'] }}</p>
                                    </div>
                                </div>
                            {% endfor %}
                        {% else %}
                            <p>No applications yet.</p>
                        {% endif %}
                    </div>
                </div>
            {% endif %}
        </div>
    </div>
</div>
{% endset %}
""" + BASE_CONTENT

COMPANY_DASHBOARD = """
{% set title = 'Company Dashboard' %}
{% set content %}
<div class="container-fluid">
    <div class="row">
        <div class="col-md-3 sidebar">
            <h4>Menu</h4>
            <a href="{{ url_for('company_post_job') }}" class="{% if active == 'post' %}active{% endif %}">Post Job</a>
            <a href="{{ url_for('company_applications') }}" class="{% if active == 'applications' %}active{% endif %}">Applications</a>
        </div>
        <div class="col-md-9 content">
            <h2>Welcome, {{ username }}</h2>
            {% if message %}
                <div class="alert alert-{{ message_type }}">{{ message }}</div>
            {% endif %}
            {% if section == 'post' %}
                <div class="card mt-4">
                    <div class="card-header">Post New Job</div>
                    <div class="card-body">
                        <form method="post" action="{{ url_for('company_post_job') }}">
                            <div class="mb-3">
                                <label class="form-label">Job Title</label>
                                <input type="text" name="title" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Description</label>
                                <textarea name="description" class="form-control" required></textarea>
                            </div>
                            <button type="submit" class="btn btn-primary">Post Job</button>
                        </form>
                    </div>
                </div>
            {% elif section == 'applications' %}
                <div class="card mt-4">
                    <div class="card-header">Applications</div>
                    <div class="card-body">
                        {% for app in applications if app['job']['company'] == username %}
                            <div class="card mb-3">
                                <div class="card-body">
                                    <p>{{ app['student'] }} applied for {{ app['job']['title'] }}</p>
                                    <p>Status: {{ app['status'] }}</p>
                                    <p>Cover Letter: {{ app['cover_letter'] }}</p>
                                    <p>Highest Qualification: {{ app['qualification'] }}</p>
                                    <p>Years of Experience: {{ app['experience'] }}</p>
                                    <p>Current CTC: {{ app['current_ctc'] }} LPA</p>
                                    <p>Expected CTC: {{ app['expected_ctc'] }} LPA</p>
                                    <p>Notice Period: {{ app['notice_period'] }} days</p>
                                    <p><a href="{{ url_for('download_resume', app_id=loop.index) }}" class="btn btn-primary btn-sm">Download Resume</a></p>
                                </div>
                            </div>
                        {% endfor %}
                    </div>
                </div>
            {% endif %}
        </div>
    </div>
</div>
{% endset %}
""" + BASE_CONTENT

ADMIN_DASHBOARD = """
{% set title = 'Admin Dashboard' %}
{% set content %}
<div class="container-fluid">
    <div class="row">
        <div class="col-md-3 sidebar">
            <h4>Menu</h4>
            <a href="{{ url_for('admin_users') }}" class="{% if active == 'users' %}active{% endif %}">Manage Users</a>
            <a href="{{ url_for('admin_jobs') }}" class="{% if active == 'jobs' %}active{% endif %}">Manage Jobs</a>
            <a href="{{ url_for('admin_applications') }}" class="{% if active == 'applications' %}active{% endif %}">Manage Applications</a>
        </div>
        <div class="col-md-9 content">
            <h2>Welcome, Admin</h2>
            {% if message %}
                <div class="alert alert-{{ message_type }}">{{ message }}</div>
            {% endif %}
            {% if section == 'users' %}
                <div class="card mt-4">
                    <div class="card-header">Manage Users</div>
                    <div class="card-body">
                        <form method="post" action="{{ url_for('admin_add_user') }}" class="mb-4">
                            <h5>Add New User</h5>
                            <div class="mb-3">
                                <label class="form-label">Username</label>
                                <input type="text" name="username" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Password</label>
                                <input type="password" name="password" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Email</label>
                                <input type="email" name="email" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Type</label>
                                <select name="type" class="form-control">
                                    <option value="student">Student</option>
                                    <option value="company">Company</option>
                                    <option value="admin">Admin</option>
                                </select>
                            </div>
                            <button type="submit" class="btn btn-success">Add User</button>
                        </form>
                        {% for username, info in users.items() %}
                            <div class="card mb-3">
                                <div class="card-body">
                                    <form method="post" action="{{ url_for('admin_update_user', user_id=info['id']) }}">
                                        <p>Username: <input type="text" name="username" value="{{ username }}" class="form-control d-inline w-25" readonly></p>
                                        <p>Password: <input type="password" name="password" value="{{ info['password'] }}" class="form-control d-inline w-25"></p>
                                        <p>Email: <input type="email" name="email" value="{{ info['email'] }}" class="form-control d-inline w-50"></p>
                                        <p>Type: <input type="text" name="type" value="{{ info['type'] }}" class="form-control d-inline w-25"></p>
                                        <button type="submit" class="btn btn-primary btn-sm">Update</button>
                                        <a href="{{ url_for('admin_delete_user', user_id=info['id']) }}" class="btn btn-danger btn-sm">Delete</a>
                                    </form>
                                </div>
                            </div>
                        {% endfor %}
                    </div>
                </div>
            {% elif section == 'jobs' %}
                <div class="card mt-4">
                    <div class="card-header">Manage Jobs</div>
                    <div class="card-body">
                        <form method="post" action="{{ url_for('admin_add_job') }}" class="mb-4">
                            <h5>Add New Job</h5>
                            <div class="mb-3">
                                <label class="form-label">Job Title</label>
                                <input type="text" name="title" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Description</label>
                                <textarea name="description" class="form-control" required></textarea>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Company</label>
                                <input type="text" name="company" class="form-control" required>
                            </div>
                            <button type="submit" class="btn btn-success">Add Job</button>
                        </form>
                        {% for job in jobs %}
                            <div class="card mb-3">
                                <div class="card-body">
                                    <form method="post" action="{{ url_for('admin_update_job', job_id=job['id']) }}">
                                        <p>ID: {{ job['id'] }}</p>
                                        <p>Title: <input type="text" name="title" value="{{ job['title'] }}" class="form-control d-inline w-50"></p>
                                        <p>Company: <input type="text" name="company" value="{{ job['company'] }}" class="form-control d-inline w-50"></p>
                                        <p>Description: <textarea name="description" class="form-control">{{ job['description'] }}</textarea></p>
                                        <button type="submit" class="btn btn-primary btn-sm">Update</button>
                                        <a href="{{ url_for('admin_delete_job', job_id=job['id']) }}" class="btn btn-danger btn-sm">Delete</a>
                                    </form>
                                </div>
                            </div>
                        {% endfor %}
                    </div>
                </div>
            {% elif section == 'applications' %}
                <div class="card mt-4">
                    <div class="card-header">Manage Applications</div>
                    <div class="card-body">
                        {% for app in applications %}
                            <div class="card mb-3">
                                <div class="card-body">
                                    <p>ID: {{ loop.index }}</p>
                                    <p>{{ app['student'] }} applied for {{ app['job']['title'] }} at {{ app['job']['company'] }}</p>
                                    <p>Status: {{ app['status'] }}</p>
                                    <p>Applied on: {{ app['date'] }}</p>
                                    <p>Highest Qualification: {{ app['qualification'] }}</p>
                                    <p>Years of Experience: {{ app['experience'] }}</p>
                                    <p>Current CTC: {{ app['current_ctc'] }} LPA</p>
                                    <p>Expected CTC: {{ app['expected_ctc'] }} LPA</p>
                                    <p>Notice Period: {{ app['notice_period'] }} days</p>
                                    <p><a href="{{ url_for('download_resume', app_id=loop.index) }}" class="btn btn-primary btn-sm">Download Resume</a></p>
                                    <form method="post" action="{{ url_for('admin_update_application', app_id=loop.index) }}" class="d-inline">
                                        <select name="status" class="form-control d-inline w-25">
                                            <option value="pending" {% if app['status'] == 'pending' %}selected{% endif %}>Pending</option>
                                            <option value="accepted" {% if app['status'] == 'accepted' %}selected{% endif %}>Accepted</option>
                                            <option value="rejected" {% if app['status'] == 'rejected' %}selected{% endif %}>Rejected</option>
                                        </select>
                                        <button type="submit" class="btn btn-primary btn-sm">Update</button>
                                    </form>
                                    <a href="{{ url_for('admin_delete_application', app_id=loop.index) }}" class="btn btn-danger btn-sm">Delete</a>
                                </div>
                            </div>
                        {% endfor %}
                    </div>
                </div>
            {% endif %}
        </div>
    </div>
</div>
{% endset %}
""" + BASE_CONTENT

APPLICATION_FORM = """
{% set title = 'Job Application' %}
{% set content %}
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h3>Apply for {{ job['title'] }} at {{ job['company'] }} (ID: {{ job['id'] }})</h3>
                </div>
                <div class="card-body">
                    {% if message %}
                        <div class="alert alert-{{ message_type }}">{{ message }}</div>
                    {% endif %}
                    <form method="post" enctype="multipart/form-data" action="{{ url_for('apply_form', job_id=job_id) }}">
                        <div class="mb-3">
                            <label class="form-label">Cover Letter</label>
                            <textarea name="cover_letter" class="form-control" required></textarea>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Highest Qualification</label>
                            <input type="text" name="qualification" class="form-control" required placeholder="e.g., B.Tech, MBA">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Years of Experience</label>
                            <input type="number" name="experience" class="form-control" required min="0" placeholder="e.g., 2">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Current CTC (in LPA)</label>
                            <input type="number" name="current_ctc" class="form-control" required step="0.1" placeholder="e.g., 5.5">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Expected CTC (in LPA)</label>
                            <input type="number" name="expected_ctc" class="form-control" required step="0.1" placeholder="e.g., 7.0">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Notice Period (in days)</label>
                            <input type="number" name="notice_period" class="form-control" required min="0" placeholder="e.g., 30">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Resume (PDF, DOCX, HTML, TXT)</label>
                            <input type="file" name="resume" class="form-control" accept=".pdf,.docx,.html,.txt" required>
                        </div>
                        <input type="hidden" name="job_id" value="{{ job_id }}">
                        <button type="submit" class="btn btn-primary">Submit Application</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endset %}
""" + BASE_CONTENT

# Helper functions
def is_logged_in():
    return 'user' in session

def get_user_type():
    return session.get('user_type') if 'user' in session else None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_job_by_id(job_id):
    for job in jobs:
        if job['id'] == job_id:
            return job
    return None

# Routes
@app.route('/')
def home():
    if is_logged_in():
        user_type = get_user_type()
        if user_type == 'admin':
            return redirect(url_for('admin_users'))
        elif user_type == 'company':
            return redirect(url_for('company_post_job'))
        elif user_type == 'student':
            return redirect(url_for('student_jobs'))
    return render_template_string(MAIN_TEMPLATE)

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password and users[username]['type'] == 'student':
            session['user'] = username
            session['user_type'] = 'student'
            return redirect(url_for('student_jobs'))
        return render_template_string(LOGIN_TEMPLATE, title="Student Login", message="Invalid credentials", message_type="danger")
    return render_template_string(LOGIN_TEMPLATE, title="Student Login")

@app.route('/company/login', methods=['GET', 'POST'])
def company_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password and users[username]['type'] == 'company':
            session['user'] = username
            session['user_type'] = 'company'
            return redirect(url_for('company_post_job'))
        return render_template_string(LOGIN_TEMPLATE, title="Company Login", message="Invalid credentials", message_type="danger")
    return render_template_string(LOGIN_TEMPLATE, title="Company Login")

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password and users[username]['type'] == 'admin':
            session['user'] = username
            session['user_type'] = 'admin'
            return redirect(url_for('admin_users'))
        return render_template_string(LOGIN_TEMPLATE, title="Admin Login", message="Invalid credentials", message_type="danger")
    return render_template_string(LOGIN_TEMPLATE, title="Admin Login")

@app.route('/student/register', methods=['GET', 'POST'])
def student_register():
    global next_user_id
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        if username in users:
            return render_template_string(STUDENT_REGISTER_TEMPLATE, message="Username already exists", message_type="danger")
        users[username] = {'id': next_user_id, 'password': password, 'type': 'student', 'email': email}
        profiles[username] = {}
        next_user_id += 1
        session['user'] = username
        session['user_type'] = 'student'
        return redirect(url_for('student_jobs'))
    return render_template_string(STUDENT_REGISTER_TEMPLATE)

@app.route('/company/register', methods=['GET', 'POST'])
def company_register():
    global next_user_id
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        if username in users:
            return render_template_string(COMPANY_REGISTER_TEMPLATE, message="Username already exists", message_type="danger")
        users[username] = {'id': next_user_id, 'password': password, 'type': 'company', 'email': email}
        profiles[username] = {}
        next_user_id += 1
        session['user'] = username
        session['user_type'] = 'company'
        return redirect(url_for('company_post_job'))
    return render_template_string(COMPANY_REGISTER_TEMPLATE)

@app.route('/student/jobs')
def student_jobs():
    if not is_logged_in() or get_user_type() != 'student':
        return redirect(url_for('student_login'))
    username = session['user']
    return render_template_string(STUDENT_DASHBOARD,
                                username=username,
                                section='jobs',
                                active='jobs',
                                jobs=jobs,
                                my_applications=[app for app in applications if app['student'] == username])

@app.route('/student/applications')
def student_applications():
    if not is_logged_in() or get_user_type() != 'student':
        return redirect(url_for('student_login'))
    username = session['user']
    return render_template_string(STUDENT_DASHBOARD,
                                username=username,
                                section='applications',
                                active='applications',
                                jobs=jobs,
                                my_applications=[app for app in applications if app['student'] == username])

@app.route('/company/post', methods=['GET', 'POST'])
def company_post_job():
    global next_job_id
    if not is_logged_in() or get_user_type() != 'company':
        return redirect(url_for('company_login'))
    username = session['user']
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        jobs.append({'id': next_job_id, 'title': title, 'description': description, 'company': username})
        next_job_id += 1
        return render_template_string(COMPANY_DASHBOARD,
                                    username=username,
                                    section='post',
                                    active='post',
                                    jobs=jobs,
                                    applications=applications,
                                    message="Job posted successfully",
                                    message_type="success")
    return render_template_string(COMPANY_DASHBOARD,
                                username=username,
                                section='post',
                                active='post',
                                jobs=jobs,
                                applications=applications)

@app.route('/company/applications')
def company_applications():
    if not is_logged_in() or get_user_type() != 'company':
        return redirect(url_for('company_login'))
    username = session['user']
    return render_template_string(COMPANY_DASHBOARD,
                                username=username,
                                section='applications',
                                active='applications',
                                jobs=jobs,
                                applications=applications)

@app.route('/admin/users')
def admin_users():
    if not is_logged_in() or get_user_type() != 'admin':
        return redirect(url_for('admin_login'))
    return render_template_string(ADMIN_DASHBOARD,
                                section='users',
                                active='users',
                                users=users,
                                jobs=jobs,
                                applications=applications)

@app.route('/admin/add_user', methods=['POST'])
def admin_add_user():
    global next_user_id
    if not is_logged_in() or get_user_type() != 'admin':
        return redirect(url_for('admin_login'))
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    user_type = request.form['type']
    if username in users:
        return render_template_string(ADMIN_DASHBOARD,
                                    section='users',
                                    active='users',
                                    users=users,
                                    jobs=jobs,
                                    applications=applications,
                                    message="Username already exists",
                                    message_type="danger")
    users[username] = {'id': next_user_id, 'password': password, 'type': user_type, 'email': email}
    profiles[username] = {}
    next_user_id += 1
    return redirect(url_for('admin_users'))

@app.route('/admin/update_user/<int:user_id>', methods=['POST'])
def admin_update_user(user_id):
    if not is_logged_in() or get_user_type() != 'admin':
        return redirect(url_for('admin_login'))
    for username, info in list(users.items()):
        if info['id'] == user_id:
            new_password = request.form['password']
            new_email = request.form['email']
            new_type = request.form['type']
            users[username] = {'id': user_id, 'password': new_password, 'type': new_type, 'email': new_email}
            break
    return redirect(url_for('admin_users'))

@app.route('/admin/delete_user/<int:user_id>')
def admin_delete_user(user_id):
    if not is_logged_in() or get_user_type() != 'admin':
        return redirect(url_for('admin_login'))
    for username, info in list(users.items()):
        if info['id'] == user_id:
            del users[username]
            profiles.pop(username, None)
            break
    return redirect(url_for('admin_users'))

@app.route('/admin/jobs')
def admin_jobs():
    if not is_logged_in() or get_user_type() != 'admin':
        return redirect(url_for('admin_login'))
    return render_template_string(ADMIN_DASHBOARD,
                                section='jobs',
                                active='jobs',
                                users=users,
                                jobs=jobs,
                                applications=applications)

@app.route('/admin/add_job', methods=['POST'])
def admin_add_job():
    global next_job_id
    if not is_logged_in() or get_user_type() != 'admin':
        return redirect(url_for('admin_login'))
    title = request.form['title']
    description = request.form['description']
    company = request.form['company']
    jobs.append({'id': next_job_id, 'title': title, 'description': description, 'company': company})
    next_job_id += 1
    return redirect(url_for('admin_jobs'))

@app.route('/admin/update_job/<int:job_id>', methods=['POST'])
def admin_update_job(job_id):
    if not is_logged_in() or get_user_type() != 'admin':
        return redirect(url_for('admin_login'))
    for job in jobs:
        if job['id'] == job_id:
            job['title'] = request.form['title']
            job['description'] = request.form['description']
            job['company'] = request.form['company']
            break
    return redirect(url_for('admin_jobs'))

@app.route('/admin/delete_job/<int:job_id>')
def admin_delete_job(job_id):
    if not is_logged_in() or get_user_type() != 'admin':
        return redirect(url_for('admin_login'))
    global jobs
    jobs = [job for job in jobs if job['id'] != job_id]
    return redirect(url_for('admin_jobs'))

@app.route('/admin/applications')
def admin_applications():
    if not is_logged_in() or get_user_type() != 'admin':
        return redirect(url_for('admin_login'))
    return render_template_string(ADMIN_DASHBOARD,
                                section='applications',
                                active='applications',
                                users=users,
                                jobs=jobs,
                                applications=applications)

@app.route('/admin/update_application/<int:app_id>', methods=['POST'])
def admin_update_application(app_id):
    if not is_logged_in() or get_user_type() != 'admin':
        return redirect(url_for('admin_login'))
    if app_id < len(applications):
        applications[app_id]['status'] = request.form['status']
    return redirect(url_for('admin_applications'))

@app.route('/admin/delete_application/<int:app_id>')
def admin_delete_application(app_id):
    if not is_logged_in() or get_user_type() != 'admin':
        return redirect(url_for('admin_login'))
    if app_id < len(applications):
        del applications[app_id]
    return redirect(url_for('admin_applications'))

@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
def apply_form(job_id):
    if not is_logged_in() or get_user_type() != 'student':
        return redirect(url_for('student_login'))
    
    if not jobs:
        username = session['user']
        return render_template_string(STUDENT_DASHBOARD,
                                    username=username,
                                    section='jobs',
                                    active='jobs',
                                    jobs=jobs,
                                    my_applications=[app for app in applications if app['student'] == username],
                                    message="No jobs available to apply for",
                                    message_type="warning")
    
    job = get_job_by_id(job_id)
    if not job:
        username = session['user']
        return render_template_string(STUDENT_DASHBOARD,
                                    username=username,
                                    section='jobs',
                                    active='jobs',
                                    jobs=jobs,
                                    my_applications=[app for app in applications if app['student'] == username],
                                    message=f"Invalid job ID: {job_id}. Please select a valid job.",
                                    message_type="danger")

    if request.method == 'POST':
        required_fields = ['cover_letter', 'qualification', 'experience', 'current_ctc', 'expected_ctc', 'notice_period']
        for field in required_fields:
            if field not in request.form or not request.form[field]:
                return render_template_string(APPLICATION_FORM,
                                            job=job,
                                            job_id=job_id,
                                            message=f"Please fill out {field.replace('_', ' ')}",
                                            message_type="danger")

        if 'resume' not in request.files:
            return render_template_string(APPLICATION_FORM,
                                        job=job,
                                        job_id=job_id,
                                        message="Resume file is required",
                                        message_type="danger")

        file = request.files['resume']
        if file.filename == '':
            return render_template_string(APPLICATION_FORM,
                                        job=job,
                                        job_id=job_id,
                                        message="No resume file selected",
                                        message_type="danger")

        if not allowed_file(file.filename):
            return render_template_string(APPLICATION_FORM,
                                        job=job,
                                        job_id=job_id,
                                        message="Invalid file format (use PDF, DOCX, HTML, or TXT)",
                                        message_type="danger")

        filename = secure_filename(f"{session['user']}_{job_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file.filename.rsplit('.', 1)[1].lower()}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        applications.append({
            'student': session['user'],
            'job': job,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'cover_letter': request.form['cover_letter'],
            'qualification': request.form['qualification'],
            'experience': request.form['experience'],
            'current_ctc': request.form['current_ctc'],
            'expected_ctc': request.form['expected_ctc'],
            'notice_period': request.form['notice_period'],
            'resume_path': filename,
            'status': 'pending'
        })

        username = session['user']
        return render_template_string(STUDENT_DASHBOARD,
                                    username=username,
                                    section='applications',
                                    active='applications',
                                    jobs=jobs,
                                    my_applications=[app for app in applications if app['student'] == username],
                                    message="Application submitted successfully",
                                    message_type="success")

    return render_template_string(APPLICATION_FORM, job=job, job_id=job_id)

@app.route('/download_resume/<int:app_id>')
def download_resume(app_id):
    if not is_logged_in() or get_user_type() not in ['company', 'admin']:
        return redirect(url_for('home'))
    if app_id >= len(applications):
        return redirect(url_for('company_applications'))
    resume_path = os.path.join(app.config['UPLOAD_FOLDER'], applications[app_id]['resume_path'])
    return send_file(resume_path, as_attachment=True)

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('user_type', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
