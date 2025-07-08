from flask import Flask, render_template_string, request, redirect
from datetime import datetime
import random
from collections import defaultdict
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
db = SQLAlchemy()
login_manager = LoginManager()

app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True)

# Task model
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

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>AutoDeployX - Task Manager</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet" />
</head>
<body>
    <div class="app-container" style="max-width:900px; margin:auto; padding:20px;">
        <div class="d-flex justify-content-between mb-3">
            <span>👤 Logged in as: {{ current_user.username }}</span>
            <a href="/logout" class="btn btn-sm btn-outline-secondary">Logout</a>
        </div>

        <h2 class="text-center mb-4">📅 AutoDeployX - GoalGrid</h2>

        {% if all_done %}
        <div class="alert alert-success text-center">🌟 All tasks for today are done!</div>
        {% endif %}

        <form method="POST" class="row g-2 mb-4">
            <div class="col-sm-5"><input name="task" class="form-control" placeholder="Task" required></div>
            <div class="col-sm-2">
                <select name="priority" class="form-select" required>
                    <option value="" disabled selected>Priority</option>
                    <option>High</option>
                    <option>Medium</option>
                    <option>Low</option>
                </select>
            </div>
            <div class="col-sm-3"><input type="date" name="due_date" class="form-control" required></div>
            <div class="col-sm-2"><button type="submit" class="btn btn-success w-100">Add</button></div>
        </form>

        <div class="calendar-box">
            {% for date, date_tasks in calendar.items() %}
                <div class="mb-3">
                    <strong>{{ date }}</strong>
                    <ul class="list-group">
                        {% for task in date_tasks %}
                        <li class="list-group-item d-flex justify-content-between">
                            <div>
                                <form method="POST" action="/toggle/{{ task.id }}" style="display:inline;">
                                    <input type="checkbox" onchange="this.form.submit()" {% if task.completed %}checked{% endif %} />
                                </form>
                                <span {% if task.completed %}style="text-decoration: line-through;"{% endif %}>{{ task.text }}</span>
                                <small class="text-muted">[{{ task.priority }} - {{ task.time }}]</small>
                            </div>
                            <a href="/delete/{{ task.id }}" class="btn btn-sm btn-danger">Delete</a>
                        </li>
                        {% endfor %}
                    </ul>
                </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
'''

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
        "Take a short walk", "Organize your files", "Water your plants",
        "Clear your inbox", "Read an article"], k=2)
    return suggestions

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        text = request.form.get("task")
        priority = request.form.get("priority")
        due_date = request.form.get("due_date")
        new_task = Task(text=text, priority=priority, due_date=due_date,
                        completed=False, time=datetime.now().strftime("%H:%M:%S"),
                        user_id=current_user.id)
        db.session.add(new_task)
        db.session.commit()
        return redirect("/")
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.completed, Task.time).all()
    calendar = defaultdict(list)
    for task in tasks:
        calendar[task.due_date].append(task)
    today_str = datetime.now().strftime('%Y-%m-%d')
    today_tasks = [t for t in tasks if t.due_date == today_str]
    all_done = all(t.completed for t in today_tasks) if today_tasks else False
    return render_template_string(HTML_TEMPLATE, calendar=calendar,
                                  today=today_str, all_done=all_done, current_user=current_user)

@app.route("/delete/<int:id>")
@login_required
def delete(id):
    task = Task.query.filter_by(id=id, user_id=current_user.id).first()
    if task:
        db.session.delete(task)
        db.session.commit()
    return redirect("/")

@app.route("/toggle/<int:id>", methods=["POST"])
@login_required
def toggle_complete(id):
    task = Task.query.filter_by(id=id, user_id=current_user.id).first()
    if task:
        task.completed = not task.completed
        db.session.commit()
    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect("/")
        return "Invalid credentials"
    return render_template_string('''<form method="POST" style="max-width:400px; margin:auto; padding:20px;">
        <h3>Login</h3>
        <input name="username" class="form-control mb-2" placeholder="Username" required>
        <input name="password" type="password" class="form-control mb-2" placeholder="Password" required>
        <button class="btn btn-success w-100">Login</button>
        <p><a href="/register">Register</a></p>
    </form>''')

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if User.query.filter_by(username=username).first():
            return "Username already exists"
        hashed_pw = generate_password_hash(password, method='sha256')
        user = User(username=username, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        return redirect("/login")
    return render_template_string('''<form method="POST" style="max-width:400px; margin:auto; padding:20px;">
        <h3>Register</h3>
        <input name="username" class="form-control mb-2" placeholder="Username" required>
        <input name="password" type="password" class="form-control mb-2" placeholder="Password" required>
        <button class="btn btn-primary w-100">Register</button>
        <p><a href="/login">Login</a></p>
    </form>''')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

@app.route("/status")
def status():
    return "OK", 200

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
