from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class TaskCreate(BaseModel):
    title: str

app = FastAPI()






tasks = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Complete Stage 2", "done": True},
    {"id": 3, "title": "Commit to Git", "done": False},
]

@app.post("/tasks", status_code=201)
def create_task(task_input: TaskCreate):
    # Your logic goes here...
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
    return { 
  "name": "Task API", 
  "version": "1.0", 
  "endpoints": ["/tasks"] 
}
    
@app.get("/health")
def read_health():
    return   { 
        "status": "ok" 
}
    
@app.get("/tasks")
def read_tasks():
    return tasks


@app.get("/tasks/{id}")
def read_task(id:int):
    for task in tasks:
        if task["id"] == id:
            return task
    return {"error": "Task not found"}