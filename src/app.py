"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import os
import secrets
import time
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path

from .auth import TeacherCredentialConfigError, verify_teacher_credentials

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

TEACHER_SESSION_COOKIE = "teacher_session"
TEACHER_SESSION_DURATION = 8 * 60 * 60
TEACHER_COOKIE_SECURE = os.getenv("TEACHER_COOKIE_SECURE", "false").lower() == "true"
active_teacher_sessions: dict[str, tuple[str, float]] = {}


class TeacherLogin(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=1024)


def get_authenticated_teacher(request: Request) -> str | None:
    session_id = request.cookies.get(TEACHER_SESSION_COOKIE)
    if session_id is None:
        return None

    session = active_teacher_sessions.get(session_id)
    if session is None:
        return None

    username, expires_at = session
    if expires_at <= time.time():
        active_teacher_sessions.pop(session_id, None)
        return None

    return username


def require_teacher(request: Request) -> str:
    username = get_authenticated_teacher(request)
    if username is None:
        raise HTTPException(status_code=401, detail="Teacher login required")
    return username


# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.post("/auth/login")
def login(credentials: TeacherLogin, response: Response):
    try:
        is_valid = verify_teacher_credentials(credentials.username, credentials.password)
    except TeacherCredentialConfigError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    session_id = secrets.token_urlsafe(32)
    active_teacher_sessions[session_id] = (
        credentials.username,
        time.time() + TEACHER_SESSION_DURATION,
    )
    response.set_cookie(
        key=TEACHER_SESSION_COOKIE,
        value=session_id,
        max_age=TEACHER_SESSION_DURATION,
        httponly=True,
        secure=TEACHER_COOKIE_SECURE,
        samesite="strict",
        path="/",
    )
    return {"message": "Logged in"}


@app.post("/auth/logout")
def logout(request: Request, response: Response):
    session_id = request.cookies.get(TEACHER_SESSION_COOKIE)
    if session_id is not None:
        active_teacher_sessions.pop(session_id, None)

    response.delete_cookie(
        key=TEACHER_SESSION_COOKIE,
        httponly=True,
        secure=TEACHER_COOKIE_SECURE,
        samesite="strict",
        path="/",
    )
    return {"message": "Logged out"}


@app.get("/auth/status")
def auth_status(request: Request):
    return {"authenticated": get_authenticated_teacher(request) is not None}


@app.get("/activities")
def get_activities():
    return activities


@app.post(
    "/activities/{activity_name}/signup",
    dependencies=[Depends(require_teacher)],
)
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete(
    "/activities/{activity_name}/unregister",
    dependencies=[Depends(require_teacher)],
)
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
