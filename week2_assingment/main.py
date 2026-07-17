from fastapi import FastAPI

app = FastAPI()

tasks = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Complete Stage 2", "done": True},
    {"id": 3, "title": "Commit to Git", "done": False},
]

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