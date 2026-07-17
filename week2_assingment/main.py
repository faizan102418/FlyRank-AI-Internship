from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: str
    done: bool

app = FastAPI()






tasks = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Complete Stage 2", "done": True},
    {"id": 3, "title": "Commit to Git", "done": False},
]

@app.post("/tasks", status_code=201)
def create_task(task_input: TaskCreate):
    """
    Create a new task with an auto-generated ID and default status set to incomplete.
    Raises a 400 error if the title is empty.
    """
    
    if not task_input.title or task_input.title.strip() == "":
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    if task_input.title in [task["title"] for task in tasks]:
        raise HTTPException(status_code=400, detail="Task with this title already exists")
    else:
        task_id = len(tasks) + 1
        new_task = {"id": task_id, "title": task_input.title, "done": False}
        tasks.append(new_task)
        return new_task



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
    Retrieve the entire list of tasks currently stored in memory.
    """
    return tasks


@app.get("/tasks/{id}")
def read_task(id:int):
    """
    Look up and retrieve a single task using its unique integer ID.
    Raises a 404 error if the task is not found.
    """
    for task in tasks:
        if task["id"] == id:
            return task
    return {"error": "Task not found"}



@app.put("/tasks/{id}")
def update_task(id: int, task_input: TaskUpdate):
    """
    Update the title and completed status of an existing task by its ID.
    Raises a 400 error if the title is empty, or a 404 if the ID is missing.
    """
    if not task_input.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    for task in tasks:
        if task["id"] == id:
            task["title"] = task_input.title
            task["done"] = task_input.done
            return task
    raise HTTPException(status_code=404, detail="Task not found")

@app.delete("/tasks/{id}", status_code=204)
def delete_task(id: int):
    """
    Permanently remove a task from the list by its ID.
    Raises a 404 error if the task is not found.
    """
    for task in tasks:
        if task["id"] == id:
            tasks.remove(task)
            return
    raise HTTPException(status_code=404, detail="Task not found")
