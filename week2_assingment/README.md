# Task Management API (yRank AI Internship - Week 2)

A robust, lightweight Task Management RESTful API built with **FastAPI** and run via **Uvicorn**. This project implements full CRUD (Create, Read, Update, Delete) functionality with robust, custom input validation to handle tricky edge cases.

---

## Features

- **Full CRUD Support:** Smoothly manage task resources (`GET`, `POST`, `PUT`, `DELETE`).
- **Input Validation:** Custom validation to catch empty inputs, blank spaces, and invalid requests (returns `400 Bad Request`).
- **Auto-Documented:** Fully self-documenting interface using FastAPI's integrated Swagger UI.
- **In-Memory Storage:** Faster operational performance with structured local lists.

---

## Technology Stack

- **Framework:** FastAPI
- **ASGI Server:** Uvicorn
- **Language:** Python 3.x
- **Environment:** virtualenv

---

## Installation & Setup

Follow these quick steps to get the API running locally on your machine.

### 1. Clone the Repository
```bash
git clone [https://github.com/faizan102418/FlyRank-AI-Internship.git](https://github.com/faizan102418/FlyRank-AI-Internship.git)
cd FlyRank-AI-Internship/week2_assingment

2. Set Up Virtual EnvironmentBash# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
3. Install DependenciesBashpip install fastapi uvicorn
4. Run the ServerBashuvicorn main:app --reload
The server will boot up at http://localhost:8000.API Documentation & EndpointsInteractive DocumentationOnce the server is running, you can access the interactive Swagger UI directly at:👉 http://localhost:8000/docsEndpoint SummaryMethodEndpointDescriptionExpected PayloadResponse StatusGET/API MetadataNone200 OKGET/healthServer Health StatusNone200 OKGET/tasksGet all tasksNone200 OKGET/tasks/{id}Get task by IDNone200 OK / 404 Not FoundPOST/tasksCreate new task{"title": "string"}201 Created / 400 Bad RequestPUT/tasks/{id}Update existing task{"title": "string", "done": bool}200 OK / 400 Bad / 404 MissingDELETE/tasks/{id}Delete task by IDNone204 No Content / 404 Not FoundTesting Input ValidationThis API strictly validates inputs. Passing empty strings or strings consisting only of blank spaces ("   ") is blocked.Run tests with curl:Attempting to update a task with blank spaces:Bashcurl -i -X PUT http://localhost:8000/tasks/1 -H "Content-Type: application/json" -d "{\"title\": \"   \", \"done\": true}"
Response:JSONHTTP/1.1 400 Bad Request
Content-Type: application/json

{"detail":"Title cannot be empty"}


![Swagger UI web page showing FastAPI documentation header with badges 0.1.0 and OAS 3.1. Main panel lists API endpoints in collapsible colored boxes: GET /tasks Read Tasks, POST /tasks Create Task, GET / Read Root, GET /health Read Health, GET /tasks/{id} Read Task, PUT /tasks/{id} Update Task. Browser address bar shows localhost:8000/docs. The page has a white background and a neutral professional tone.](swagger_docs.png)