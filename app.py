"""A small Task Manager web app built with Flask.

Tasks are kept in memory (a Python list), so there is no database to set up.
That also means tasks reset whenever the app restarts - fine for a CI/CD demo.
"""

from flask import Flask, jsonify, redirect, render_template_string, request, url_for

app = Flask(__name__)

# In-memory storage: a list of dictionaries.
tasks = []
next_id = 1

PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Task Manager</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f4f6f8; margin: 0; }
    .box { max-width: 560px; margin: 40px auto; background: #fff; padding: 24px;
           border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,.1); }
    h1 { margin-top: 0; color: #24292f; }
    form.add { display: flex; gap: 8px; margin-bottom: 20px; }
    form.add input { flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 4px; }
    button { padding: 8px 14px; border: 0; border-radius: 4px; background: #2da44e;
             color: #fff; cursor: pointer; }
    button.del { background: #cf222e; }
    ul { list-style: none; padding: 0; }
    li { display: flex; justify-content: space-between; align-items: center;
         padding: 10px 0; border-bottom: 1px solid #eee; }
    li.done span { text-decoration: line-through; color: #888; }
    .actions { display: flex; gap: 6px; }
    .empty { color: #888; }
    footer { margin-top: 16px; font-size: 12px; color: #888; }
  </style>
</head>
<body>
  <div class="box">
    <h1>Task Manager</h1>
    <form class="add" method="post" action="{{ url_for('add_task') }}">
      <input type="text" name="title" placeholder="What needs to be done?" required maxlength="100">
      <button type="submit">Add</button>
    </form>
    {% if tasks %}
    <ul>
      {% for t in tasks %}
      <li class="{{ 'done' if t.done else '' }}">
        <span>{{ t.title }}</span>
        <div class="actions">
          <form method="post" action="{{ url_for('toggle_task', task_id=t.id) }}">
            <button type="submit">{{ 'Undo' if t.done else 'Done' }}</button>
          </form>
          <form method="post" action="{{ url_for('delete_task', task_id=t.id) }}">
            <button class="del" type="submit">Delete</button>
          </form>
        </div>
      </li>
      {% endfor %}
    </ul>
    {% else %}
    <p class="empty">No tasks yet. Add your first one above.</p>
    {% endif %}
    <footer>Health check: <a href="{{ url_for('health') }}">/health</a></footer>
  </div>
</body>
</html>
"""


@app.route("/")
def home():
    """Home page: shows the task list and the add form."""
    return render_template_string(PAGE, tasks=tasks)


@app.route("/add", methods=["POST"])
def add_task():
    """Add a new task from the form."""
    global next_id
    title = request.form.get("title", "").strip()
    if title:
        tasks.append({"id": next_id, "title": title[:100], "done": False})
        next_id += 1
    return redirect(url_for("home"))


@app.route("/toggle/<int:task_id>", methods=["POST"])
def toggle_task(task_id):
    """Mark a task done or not done."""
    for task in tasks:
        if task["id"] == task_id:
            task["done"] = not task["done"]
            break
    return redirect(url_for("home"))


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    """Remove a task."""
    tasks[:] = [t for t in tasks if t["id"] != task_id]
    return redirect(url_for("home"))


@app.route("/health")
def health():
    """Health endpoint used by CI, load balancers and deployment checks."""
    return jsonify(status="ok"), 200


if __name__ == "__main__":
    # Development server only. In production we use Gunicorn (see README).
    app.run(host="127.0.0.1", port=5000)
