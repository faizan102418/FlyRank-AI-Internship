from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


import sqlite3

DB_PATH = "tasks.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets you access columns by name
    return conn

def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0
        )
    """)
    count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    if count == 0:
        conn.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            [("Buy milk", 0), ("Complete Stage 2", 1), ("Commit to Git", 0)]
        )
        conn.commit()
    conn.close()

init_db()







class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: str
    done: bool

app = FastAPI()



@app.get("/")
def read_root():
    """
    Retrieve API metadata, including the service name, version, and available endpoints.
    """
    return { 
  "name": "Task API", 
  "version": "1.0", 
  "endpoints": ["/tasks"] 
}
    
@app.get("/health")
def read_health():
    """
    Check the running status of the API server to ensure it is alive and healthy.
    """
    return   { 
        "status": "ok" 
}
    
@app.get("/tasks")
def read_tasks():
    """
    Retrieve the entire list of tasks from the database.
    """
    conn = get_conn()
    rows = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/tasks/{id}")
def read_task(id: int):
    """
    Look up and retrieve a single task using its unique integer ID.
    Raises a 404 error if the task is not found.
    """
    conn = get_conn()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return dict(row)


@app.post("/tasks", status_code=201)
def create_task(task_input: TaskCreate):
    """
    Create a new task with an auto-generated ID and default status set to incomplete.
    Raises a 400 error if the title is empty or already exists.
    """
    if not task_input.title or task_input.title.strip() == "":
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    conn = get_conn()
    existing = conn.execute(
        "SELECT 1 FROM tasks WHERE title = ?", (task_input.title,)
    ).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="Task with this title already exists")

    cur = conn.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        (task_input.title, 0)
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()

    return {"id": new_id, "title": task_input.title, "done": False}





@app.put("/tasks/{id}")
def update_task(id: int, task_input: TaskUpdate):
    """
    Update the title and completed status of an existing task by its ID.
    Raises a 400 error if the title is empty, or a 404 if the ID is missing.
    """
    if not task_input.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    conn = get_conn()
    cur = conn.execute(
        "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
        (task_input.title, int(task_input.done), id)
    )
    conn.commit()

    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")

    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (id,)).fetchone()
    conn.close()
    return dict(row)


@app.delete("/tasks/{id}", status_code=204)
def delete_task(id: int):
    """
    Permanently remove a task from the database by its ID.
    Raises a 404 error if the task is not found.
    """
    conn = get_conn()
    cur = conn.execute("DELETE FROM tasks WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Task not found")