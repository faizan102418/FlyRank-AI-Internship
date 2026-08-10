from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()


DATABASE_URL = os.environ["DATABASE_URL"]

def get_conn():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT FALSE
        )
    """)
    cur.execute("SELECT COUNT(*) FROM tasks")
    count = cur.fetchone()["count"]
    if count == 0:
        cur.executemany(
            "INSERT INTO tasks (title, done) VALUES (%s, %s)",
            [("Buy milk", False), ("Complete Stage 2", True), ("Commit to Git", False)]
        )
    conn.commit()
    cur.close()
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
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


@app.get("/tasks/{id}")
def read_task(id: int):
    """
    Look up and retrieve a single task using its unique integer ID.
    Raises a 404 error if the task is not found.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = %s", (id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return row

@app.post("/tasks", status_code=201)
def create_task(task_input: TaskCreate):
    """
    Create a new task with an auto-generated ID and default status set to incomplete.
    Raises a 400 error if the title is empty or already exists.
    """
    if not task_input.title or task_input.title.strip() == "":
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM tasks WHERE title = %s", (task_input.title,))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Task with this title already exists")

    cur.execute(
        "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING *",
        (task_input.title, False)
    )
    new_task = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return new_task


@app.put("/tasks/{id}")
def update_task(id: int, task_input: TaskUpdate):
    """
    Update the title and completed status of an existing task by its ID.
    Raises a 400 error if the title is empty, or a 404 if the ID is missing.
    """
    if not task_input.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING *",
        (task_input.title, task_input.done, id)
    )
    updated = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if updated is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated


@app.delete("/tasks/{id}", status_code=204)
def delete_task(id: int):
    """
    Permanently remove a task from the database by its ID.
    Raises a 404 error if the task is not found.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = %s RETURNING id", (id,))
    deleted = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if deleted is None:
        raise HTTPException(status_code=404, detail="Task not found")