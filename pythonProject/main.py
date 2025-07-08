from flask import Flask, render_template_string, request, redirect
from datetime import datetime
import random
from collections import defaultdict
import os

app = Flask(__name__)
tasks = []
task_id_counter = 1

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>

 <meta charset="UTF-8" />
    <title>AutoDeployX - Task Manager</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet" />
    <style>
        body {
            background: linear-gradient(135deg, #e8f5e9, #c8e6c9);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .app-container {
            max-width: 900px;
            margin: 40px auto;
            padding: 2rem;
            background-color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }
        .task-completed {
            text-decoration: line-through;
            color: #999;
        }
        .priority-high { color: #d32f2f; font-weight: bold; }
        .priority-medium { color: #f57c00; font-weight: bold; }
        .priority-low { color: #388e3c; font-weight: bold; }
        .calendar-box {
            margin-top: 30px;
        }
        .day-label {
            background: #e0f2f1;
            padding: 6px;
            font-weight: bold;
            border-radius: 5px;
        }
        .suggestion-button {
            margin: 2px;
        }
    </style>
</head>
<body>
    <div class="app-container">
        <h2 class="text-center mb-4">📅 AutoDeployX - GoalGrid</h2>

        {% if all_done %}
        <div class="alert alert-success text-center" role="alert">
            🌟 <strong>Fantastic!</strong> You've completed all your tasks for today. Keep shining! 🌈
        </div>
        {% endif %}

        <form method="POST" class="row g-2 mb-4">
            <div class="col-sm-5">
                <input type="text" name="task" class="form-control" placeholder="Add a task..." required />
            </div>
            <div class="col-sm-2">
                <select name="priority" class="form-select" required>
                    <option value="" disabled selected>Priority</option>
                    <option>High</option>
                    <option>Medium</option>
                    <option>Low</option>
                </select>
            </div>
            <div class="col-sm-3">
                <input type="date" name="due_date" class="form-control" required />
            </div>
            <div class="col-sm-2 d-grid">
                <button type="submit" class="btn btn-success">Add</button>
            </div>
        </form>

        {% if suggestions %}
        <div class="mb-3">
            <h6>💡 AI Suggestions:</h6>
            <div>
                {% for s in suggestions %}
                <form method="POST" style="display:inline;">
                    <input type="hidden" name="task" value="{{ s }}">
                    <input type="hidden" name="priority" value="Medium">
                    <input type="hidden" name="due_date" value="{{ today }}">
                    <button class="btn btn-sm btn-outline-success suggestion-button">{{ s }}</button>
                </form>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        <div class="calendar-box">
            {% for date, date_tasks in calendar.items() %}
                <div class="mb-3">
                    <div class="day-label">{{ date }}</div>
                    <ul class="list-group">
                        {% for task in date_tasks %}
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            <div>
                                <form method="POST" action="/toggle/{{ task.id }}" style="display:inline;">
                                    <input type="checkbox" name="completed" onchange="this.form.submit()" {% if task.completed %}checked{% endif %} />
                                </form>
                                <span class="{% if task.completed %}task-completed{% endif %}">
                                    {{ task.text }} 
                                    <small class="text-muted">({{ task.time }})</small>
                                </span>
                                <span class="
                                    {% if task.priority == 'High' %}priority-high{% elif task.priority == 'Medium' %}priority-medium{% else %}priority-low{% endif %}
                                ">
                                    [{{ task.priority }}]
                                </span>
                            </div>
                            <a href="/delete/{{ task.id }}" class="btn btn-sm btn-outline-danger">Delete</a>
                        </li>
                        {% endfor %}
                    </ul>
                </div>
            {% else %}
                <p class="text-muted">No tasks yet.</p>
            {% endfor %}
        </div>
    </div>
</body>
</html>
'''


def sort_tasks(task):
    priority_order = {'High': 1, 'Medium': 2, 'Low': 3}
    return (task['completed'], priority_order.get(task['priority'], 4), task['time'])


def suggest_tasks():
    now = datetime.now()
    weekday = now.strftime('%A')
    hour = now.hour
    suggestions = []

    if weekday == 'Monday':
        suggestions.append("Plan weekly goals")
    if weekday == 'Friday':
        suggestions.append("Review weekly progress")
    if hour < 10:
        suggestions.append("Prioritize today's tasks")
    if any(t['priority'] == 'High' and not t['completed'] for t in tasks):
        suggestions.append("Focus on urgent tasks")

    suggestions += random.sample([
        "Take a short walk",
        "Organize your files",
        "Water your plants",
        "Clear your inbox",
        "Read an article"
    ], k=2)

    return suggestions


@app.route("/", methods=["GET", "POST"])
def index():
    global task_id_counter
    if request.method == "POST":
        text = request.form.get("task")
        priority = request.form.get("priority")
        due_date = request.form.get("due_date")
        if text and priority and due_date:
            task = {
                "id": task_id_counter,
                "text": text,
                "priority": priority,
                "due_date": due_date,
                "completed": False,
                "time": datetime.now().strftime("%H:%M:%S")
            }
            tasks.append(task)
            task_id_counter += 1
        return redirect("/")

    calendar = defaultdict(list)
    for task in sorted(tasks, key=sort_tasks):
        calendar[task['due_date']].append(task)

    today_str = datetime.now().strftime('%Y-%m-%d')
    today_tasks = [t for t in tasks if t['due_date'] == today_str]
    all_done = all(t['completed'] for t in today_tasks) if today_tasks else False

    return render_template_string(HTML_TEMPLATE,
                                  tasks=tasks,
                                  calendar=calendar,
                                  suggestions=suggest_tasks(),
                                  today=today_str,
                                  all_done=all_done)


@app.route("/delete/<int:id>")
def delete(id):
    global tasks
    tasks = [t for t in tasks if t["id"] != id]
    return redirect("/")


@app.route("/toggle/<int:id>", methods=["POST"])
def toggle_complete(id):
    for task in tasks:
        if task["id"] == id:
            task["completed"] = not task["completed"]
            break
    return redirect("/")


@app.route("/status")
def status():
    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # use PORT from environment
    app.run(host="0.0.0.0", port=port, debug=True)  # bind to external IP