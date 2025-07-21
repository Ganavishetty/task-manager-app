from flask import Flask, render_template_string, request, redirect, flash
from datetime import datetime
import random
from collections import defaultdict
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import  check_password_hash

from werkzeug.security import generate_password_hash

app = Flask(__name__)

db = SQLAlchemy()
login_manager = LoginManager()

app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500), default='')  # 🆕 New field
    tasks = db.relationship('Task', backref='user', lazy=True)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    priority = db.Column(db.String(20))
    due_date = db.Column(db.String(50))
    completed = db.Column(db.Boolean, default=False)
    time = db.Column(db.String(20))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def suggest_tasks():
    now = datetime.now()
    weekday = now.strftime('%A')
    hour = now.hour
    suggestions = []
    if not current_user.is_authenticated:
        return suggestions
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    if weekday == 'Monday': suggestions.append("Plan weekly goals")
    if weekday == 'Friday': suggestions.append("Review weekly progress")
    if hour < 10: suggestions.append("Prioritize today's tasks")
    if any(t.priority == 'High' and not t.completed for t in tasks):
        suggestions.append("Focus on urgent tasks")
    suggestions += random.sample([
        "Review your top 3 priorities for the day",
        "Clear out 5 old emails from your inbox",
        "Drink a glass of water 💧",
        "Take a 5-minute deep breathing break 🧘",
        "Organize your files into folders",
        "Check your calendar for upcoming events",
        "Reflect on what went well yesterday",
        "Watch a short TED Talk",
        "Listen to your favorite upbeat song 🎵",
        "Check your tasks marked as 'High'",
    ], k=2)
    return suggestions

LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Login - AutoDeployX</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(to right, #e3f2fd, #e8f5e9);
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
        }
        .login-box {
            background: #fff;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 0 15px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
        }
        h2 {
            font-weight: 600;
            margin-bottom: 25px;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <h2 class="text-center">🔐 Welcome to AutoDeployX</h2>

        {% with messages = get_flashed_messages() %}
        {% if messages %}
        <div class="alert alert-danger">{{ messages[0] }}</div>
        {% endif %}
        {% endwith %}

        <form method="POST">
            <div class="mb-3">
                <input type="text" name="username"
                       class="form-control {% if username_invalid %}is-invalid{% endif %}"
                       placeholder="Username" required />
                {% if username_invalid %}
                <div class="invalid-feedback">Username not found</div>
                {% endif %}
            </div>

            <div class="input-group mb-3">
                <input type="password" name="password" id="passwordInput"
                       class="form-control {% if password_invalid %}is-invalid{% endif %}"
                       placeholder="Password" required />
                <span class="input-group-text" onclick="togglePassword('passwordInput', this)">👁️</span>
            </div>
            {% if password_invalid %}
            <div class="text-danger mb-2">Incorrect password</div>
            {% endif %}

            <div class="d-grid mb-3">
                <button type="submit" class="btn btn-primary">Login</button>
            </div>
        </form>
        <p class="text-center">New user? <a href="/signup">Sign up</a></p>
        <p class="mt-2">
            <a href="/forgot-password" class="text-decoration-none">Forgot your password?</a>
        </p>
    </div>

<script>
function togglePassword(fieldId, iconElement) {
    const input = document.getElementById(fieldId);
    if (input.type === "password") {
        input.type = "text";
        iconElement.textContent = "🙈";
    } else {
        input.type = "password";
        iconElement.textContent = "👁️";
    }
}
</script>

</body>
</html>
'''



SIGNUP_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Sign Up - AutoDeployX</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(to right, #fff3e0, #e1f5fe);
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
        }
        .signup-box {
            background: #fff;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 0 15px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
        }
        h2 {
            font-weight: 600;
            margin-bottom: 25px;
        }
    </style>
</head>
<body>
    <div class="signup-box">
        <h2 class="text-center">🚀 Join AutoDeployX</h2>
        <form method="POST">
            <div class="mb-3">
                <input type="text" name="username" class="form-control" placeholder="Username" required />
            </div>
            <div class="mb-3 position-relative">
    <input type="password" name="password" id="passwordInput" class="form-control" placeholder="Password" required />
    <span id="monkeyToggle" class="position-absolute top-50 end-0 translate-middle-y me-3" style="cursor:pointer; font-size: 20px;">🙈</span>
</div>

<script>
    const monkeyToggle = document.getElementById("monkeyToggle");
    const passwordInput = document.getElementById("passwordInput");

    monkeyToggle.addEventListener("click", function () {
        const isPassword = passwordInput.type === "password";
        passwordInput.type = isPassword ? "text" : "password";
        monkeyToggle.textContent = isPassword ? "🙉" : "🙈"; // Toggle monkey face
    });
</script>


            <div class="d-grid mb-3">
                <button type="submit" class="btn btn-success">Sign Up</button>
            </div>
        </form>
        <p class="text-center">Already have an account? <a href="/login">Log in</a></p>
    </div>
</body>
</html>
'''


PROFILE_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Profile - AutoDeployX</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container mt-5">
        <div class="card p-4 shadow" style="max-width: 500px; margin:auto;">
            <h4 class="mb-3 text-center">👤 Edit Your Profile</h4>
            {% with messages = get_flashed_messages(with_categories=true) %}
              {% if messages %}
                {% for category, message in messages %}
                  <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
              {% endif %}
            {% endwith %}
            <form method="POST">
                <div class="mb-3">
                    <label class="form-label">Username</label>
                    <input name="username" value="{{ user.username }}" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Description</label>
                    <textarea name="description" class="form-control" placeholder="Tell us about yourself..." rows="4">{{ user.description }}</textarea>
                </div>
                <div class="d-grid">
                    <button class="btn btn-primary">💾 Save Changes</button>
                </div>
            </form>
            <div class="text-center mt-3">
                <a href="/" class="text-decoration-none">⬅️ Back to Home</a>
            </div>
        </div>
    </div>
</body>
</html>
'''



HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AutoDeployX - Task Manager app atumated</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(to right, #e0f2f1, #f1f8e9);
            font-family: 'Segoe UI', sans-serif;
        }
        .task-card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 0 15px rgba(0,0,0,0.08);
        }
        .sticky-header {
            position: sticky;
            top: 0;
            z-index: 999;
            background-color: #ffffff;
            padding: 15px 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        .logout-btn {
            border-radius: 20px;
            font-weight: 500;
            padding: 6px 16px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
<div class="container py-4">

    <!-- Header -->
    
    <div class="sticky-header d-flex justify-content-between align-items-center">
    <div class="ms-3">
        <a href="/profile" class="text-decoration-none fw-bold">👤 {{ current_user.username }}</a>
        {% if current_user.description %}
            <div class="text-muted small">{{ current_user.description }}</div>
        {% else %}
            <div class="text-muted small fst-italic">No description added</div>
        {% endif %}
    </div>
    <a href="/logout" class="btn btn-danger btn-sm logout-btn me-3">🔓 Logout</a>
</div>

    


    <!-- App Title -->
    <div class="text-center my-4">
        <h2 class="fw-bold">📅 AutoDeployX - GoalGrid</h2>
        <p class="text-muted">Your smart AI-powered daily task planner</p>
    </div>

    <!-- Success Message -->
    {% if all_done %}
    <div class="alert alert-success text-center fw-bold">
        🎉 Great job! All your tasks for today are done!
    </div>
    {% endif %}

    <!-- Task Entry Form -->
    <div class="task-card mb-4">
        <form method="POST" class="row g-3 align-items-end">
            <div class="col-md-5">
                <label class="form-label">📝 Task</label>
                <input name="task" class="form-control" placeholder="Add a task..." required>
            </div>
            <div class="col-md-2">
                <label class="form-label">🔥 Priority</label>
                <select name="priority" class="form-select" required>
                    <option value="" disabled selected>Choose</option>
                    <option>High</option>
                    <option>Medium</option>
                    <option>Low</option>
                </select>
            </div>
            <div class="col-md-3">
                <label class="form-label">📆 Due Date</label>
                <input type="date" name="due_date" class="form-control" required>
            </div>
            <div class="col-md-2">
                <button type="submit" class="btn btn-success w-100">➕ Add Task</button>
            </div>
        </form>
    </div>

    <!-- AI Suggestions -->
    <div class="task-card mb-4">
        <h5 class="mb-3">💡 Suggested  AI Suggestions</h5>
        {% if suggestions %}
            {% for s in suggestions %}
            <button type="button" class="btn btn-outline-info btn-sm m-1"
                    onclick="document.querySelector('[name=task]').value='{{ s }}'">
                🤖 {{ s }}
            </button>
            {% endfor %}
        {% else %}
            <p class="text-muted">No suggestions right now</p>
        {% endif %}
    </div>

    <!-- Filter Dropdown -->
    <div class="mb-4 text-end">
        <label for="priorityFilter" class="me-2 fw-semibold">🔍 Filter by Priority:</label>
        <select id="priorityFilter" class="form-select d-inline-block w-auto">
            <option value="all">All</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
        </select>
    </div>

    <!-- Task List -->
    {% for date, date_tasks in calendar.items() %}
    <div class="task-card mb-4">
        <h5 class="mb-3">📆 {{ date }}</h5>
        <ul class="list-group">
            {% for task in date_tasks %}
            <li class="list-group-item d-flex justify-content-between align-items-center task-item" data-priority="{{ task.priority }}">
                <div>
                    <form method="POST" action="/toggle/{{ task.id }}" style="display:inline;">
                        <input type="checkbox" onchange="this.form.submit()" {% if task.completed %}checked{% endif %}>
                    </form>
                    <span {% if task.completed %}style="text-decoration:line-through;"{% endif %}>
                        {{ task.text }}
                    </span>
                    <small class="text-muted">[{{ task.priority }} - {{ task.time }}]</small>
                </div>
                <a href="/delete/{{ task.id }}" class="btn btn-sm btn-danger">🗑️ Delete</a>
            </li>
            {% endfor %}
        </ul>
    </div>
    {% endfor %}

</div>

<!-- Filter Script -->
<script>
    const filterDropdown = document.getElementById('priorityFilter');
    filterDropdown.addEventListener('change', function () {
        const selected = this.value;
        const items = document.querySelectorAll('.task-item');
        items.forEach(item => {
            const priority = item.getAttribute('data-priority');
            if (selected === 'all' || priority === selected) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });
    });
</script>

</body>
</html>
'''



@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        new_task = Task(
            text=request.form.get("task"),
            priority=request.form.get("priority"),
            due_date=request.form.get("due_date"),
            completed=False,
            time=datetime.now().strftime("%H:%M:%S"),
            user_id=current_user.id
        )
        db.session.add(new_task)
        db.session.commit()
        return redirect("/")

    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.completed, Task.time).all()
    calendar = defaultdict(list)
    for t in tasks:
        calendar[t.due_date].append(t)
    today_str = datetime.now().strftime('%Y-%m-%d')
    today_tasks = [t for t in tasks if t.due_date == today_str]
    all_done = all(t.completed for t in today_tasks) if today_tasks else False
    suggestions = suggest_tasks()
    return render_template_string(HTML_TEMPLATE, calendar=calendar, today=today_str, all_done=all_done, suggestions=suggestions)

@app.route("/toggle/<int:id>", methods=["POST"])
@login_required
def toggle_complete(id):
    task = Task.query.filter_by(id=id, user_id=current_user.id).first()
    if task:
        task.completed = not task.completed
        db.session.commit()
    return redirect("/")

@app.route("/delete/<int:id>")
@login_required
def delete(id):
    task = Task.query.filter_by(id=id, user_id=current_user.id).first()
    if task:
        db.session.delete(task)
        db.session.commit()
    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    username_invalid = False
    password_invalid = False

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if not user:
            username_invalid = True
        elif not check_password_hash(user.password, password):
            password_invalid = True
        else:
            login_user(user)
            return redirect("/")

        flash("Invalid username or password.")

    return render_template_string(LOGIN_HTML, username_invalid=username_invalid, password_invalid=password_invalid)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if User.query.filter_by(username=username).first():
            flash("Username exists")
            return redirect("/signup")
        db.session.add(User(username=username, password=generate_password_hash(password)))
        db.session.commit()
        return redirect("/login")
    return render_template_string(SIGNUP_HTML)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")



@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        new_username = request.form["username"]
        new_description = request.form["description"]

        # Prevent duplicate usernames
        if new_username != current_user.username and User.query.filter_by(username=new_username).first():
            flash("Username already taken!", "danger")
        else:
            current_user.username = new_username
            current_user.description = new_description
            db.session.commit()
            flash("Profile updated successfully!", "success")
            return redirect("/profile")

    return render_template_string(PROFILE_HTML, user=current_user)


@app.route("/status")
def status():
    return "OK", 200


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        new_password = request.form['password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect('/forgot-password')

        user = User.query.filter_by(username=username).first()
        if user:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            flash('Password reset successful! Please login.', 'success')
            return redirect('/login')
        else:
            flash('User not found.', 'danger')
            return redirect('/forgot-password')

    return render_template_string('''
    <!DOCTYPE html>
    <html><head><title>Reset Password</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
    <body class="d-flex align-items-center justify-content-center vh-100 bg-light">
        <div class="card p-4" style="max-width: 400px;">
            <h4 class="text-center mb-3">🔐 Reset Your Password</h4>
            <form method="POST">
                <input type="text" name="username" class="form-control mb-3" placeholder="Enter your username" required>
                <div class="input-group mb-3">
    <input type="password" name="password" class="form-control" placeholder="New password" id="newPassword" required>
    <span class="input-group-text" onclick="togglePassword('newPassword', this)">👁️</span>
</div>

<div class="input-group mb-3">
    <input type="password" name="confirm_password" class="form-control" placeholder="Confirm password" id="confirmPassword" required>
    <span class="input-group-text" onclick="togglePassword('confirmPassword', this)">👁️</span>
</div>

<script>
function togglePassword(fieldId, icon) {
    const input = document.getElementById(fieldId);
    if (input.type === "password") {
        input.type = "text";
        icon.textContent = "🙈";
    } else {
        input.type = "password";
        icon.textContent = "👁️";
    }
}
</script>

                <button type="submit" class="btn btn-primary w-100">Reset Password</button>
            </form>
            <a href="/login" class="d-block mt-3 text-center">Back to login</a>
        </div>
    </body></html>
    ''')


with app.app_context():
    # TEMPORARY FIX: Drop and recreate all tables
    #db.drop_all()
    db.create_all()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
