# backend/main.py
import os
import shutil
import sys
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

# Make backend-local imports work when the app is started from the project root.
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import database

app = FastAPI(title="College Online Voting API")

# Enable CORS for frontend connectivity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database tables on server launch
@app.on_event("startup")
def startup_event():
    # Ensure uploads directory exists
    uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Check/create tables
    success = database.init_db()
    if not success:
        print("Warning: Database initialization failed. Please verify MySQL service is running.")

# --- Pydantic Models for API Requests ---

class VoterLoginRequest(BaseModel):
    voterId: str
    password: str

class CandidateLoginRequest(BaseModel):
    candidateId: str
    password: str

class VoteRequest(BaseModel):
    voterId: str
    candidateId: str
    position: str

class CandidateProfileUpdateRequest(BaseModel):
    candidateId: str
    password: str
    name: str
    degree: str
    qualification: str
    achievements: str
    manifesto: str

# --- API Endpoints ---

@app.get("/api/health")
def health_check():
    """Simple API check connection endpoint"""
    return {"status": "ok", "message": "Voting system API server is running."}

@app.get("/api/results")
def get_results():
    """Return vote tallies for the Live Tallies tab."""
    rows = database.fetch_all(
        """
        SELECT
            c.candidate_id,
            c.name,
            c.degree,
            c.position,
            COUNT(v.candidate_id) AS voteCount
        FROM candidates c
        LEFT JOIN votes v ON c.candidate_id = v.candidate_id
        GROUP BY c.candidate_id, c.name, c.degree, c.position
        ORDER BY c.position, voteCount DESC
        """
    )
    total_votes = sum(int(row.get("voteCount", 0) or 0) for row in rows)
    return {"success": True, "results": rows, "totalVotes": total_votes}

@app.post("/api/auth/voter/login")
def voter_login(req: VoterLoginRequest):
    """
    Authenticate a student voter.
    """
    voter = database.fetch_one(
        "SELECT voter_id, name, department FROM voters WHERE voter_id = %s AND password = %s",
        (req.voterId, req.password)
    )
    if not voter:
        raise HTTPException(status_code=401, detail="Invalid Voter ID or password.")
    
    # Fetch positions this voter has already voted for
    voted_positions_rows = database.fetch_all(
        "SELECT position FROM votes WHERE voter_id = %s",
        (req.voterId,)
    )
    voted_positions = [row['position'] for row in voted_positions_rows]

    return {
        "success": True,
        "voter": {
            "id": voter["voter_id"],
            "name": voter["name"],
            "department": voter["department"],
            "votedPositions": voted_positions
        }
    }

@app.post("/api/auth/candidate/login")
def candidate_login(req: CandidateLoginRequest):
    """
    Authenticate an election participant/candidate.
    """
    candidate = database.fetch_one(
        "SELECT candidate_id, name, position FROM candidates WHERE candidate_id = %s AND password = %s",
        (req.candidateId, req.password)
    )
    if not candidate:
        raise HTTPException(status_code=401, detail="Invalid Candidate ID or password.")
    return {
        "success": True,
        "candidate": {
            "id": candidate["candidate_id"],
            "name": candidate["name"],
            "position": candidate["position"]
        }
    }

@app.get("/api/candidates")
def get_candidates():
    """
    Fetch all registered candidates and group them.
    """
    candidates = database.fetch_all(
        "SELECT candidate_id, name, degree, qualification, achievements, manifesto, image_url, position FROM candidates"
    )
    return {"success": True, "candidates": candidates}

@app.get("/api/candidate/profile/{candidate_id}")
def get_candidate_profile(candidate_id: str):
    """
    Fetch detailed profile of a single candidate.
    """
    candidate = database.fetch_one(
        "SELECT candidate_id, name, degree, qualification, achievements, manifesto, image_url, position FROM candidates WHERE candidate_id = %s",
        (candidate_id,)
    )
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    return {"success": True, "candidate": candidate}

@app.post("/api/vote")
def cast_vote(req: VoteRequest):
    """
    Records a vote after ensuring the voter hasn't already voted for this position.
    """
    # 1. Verify Voter Exists
    voter = database.fetch_one("SELECT voter_id FROM voters WHERE voter_id = %s", (req.voterId,))
    if not voter:
        raise HTTPException(status_code=404, detail="Voter registration record not found.")

    # 2. Check if already voted for this specific position
    existing_vote = database.fetch_one(
        "SELECT candidate_id FROM votes WHERE voter_id = %s AND position = %s",
        (req.voterId, req.position)
    )
    if existing_vote:
        raise HTTPException(status_code=400, detail=f"You have already cast your vote for the {req.position} position.")

    # 3. Verify Candidate exists and belongs to that position
    candidate = database.fetch_one(
        "SELECT candidate_id FROM candidates WHERE candidate_id = %s AND position = %s",
        (req.candidateId, req.position)
    )
    if not candidate:
        raise HTTPException(status_code=404, detail="Selected candidate does not exist for this position.")

    # 4. Insert vote transaction
    try:
        database.execute_query(
            "INSERT INTO votes (voter_id, position, candidate_id) VALUES (%s, %s, %s)",
            (req.voterId, req.position, req.candidateId)
        )
        return {"success": True, "message": f"Your vote for {req.position} was registered successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database transaction error: {str(e)}")

@app.put("/api/candidate/profile")
def update_candidate_profile(req: CandidateProfileUpdateRequest):
    """
    Allow candidate to modify their own profile achievements, degree, qualification, and manifesto.
    """
    # 1. Authenticate candidate credentials
    candidate = database.fetch_one(
        "SELECT candidate_id FROM candidates WHERE candidate_id = %s AND password = %s",
        (req.candidateId, req.password)
    )
    if not candidate:
        raise HTTPException(status_code=401, detail="Authentication failed. Incorrect password.")

    # 2. Perform Profile Update
    try:
        database.execute_query(
            """UPDATE candidates 
               SET name = %s, degree = %s, qualification = %s, achievements = %s, manifesto = %s 
               WHERE candidate_id = %s""",
            (req.name, req.degree, req.qualification, req.achievements, req.manifesto, req.candidateId)
        )
        return {"success": True, "message": "Candidate profile updated successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profile update failed: {str(e)}")

@app.post("/api/candidate/upload-image")
def upload_candidate_image(
    candidateId: str = Form(...),
    password: str = Form(...),
    image: UploadFile = File(...)
):
    """
    Handles candidate uploading their campaign profile picture.
    """
    # 1. Verify candidate details
    candidate = database.fetch_one(
        "SELECT candidate_id FROM candidates WHERE candidate_id = %s AND password = %s",
        (candidateId, password)
    )
    if not candidate:
        raise HTTPException(status_code=401, detail="Authentication failed. Incorrect ID or password.")

    # Validate file format
    file_ext = os.path.splitext(image.filename)[1].lower()
    if file_ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        raise HTTPException(status_code=400, detail="Only JPG, PNG, and WebP images are allowed.")

    # Create safe unique filename
    safe_filename = f"cand_{candidateId}{file_ext}"
    uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
    save_path = os.path.join(uploads_dir, safe_filename)

    # Save to uploads folder
    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file to disk: {str(e)}")

    # Update database image path
    web_image_url = f"/uploads/{safe_filename}"
    database.execute_query(
        "UPDATE candidates SET image_url = %s WHERE candidate_id = %s",
        (web_image_url, candidateId)
    )

    return {"success": True, "imageUrl": web_image_url, "message": "Profile image uploaded successfully!"}

# --- STATIC MOUNTS ROUTING ---

# Mount uploaded candidate photos route
app.mount("/uploads", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "uploads")), name="uploads")

# Mount client side frontend SPA
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:
    print(f"Warning: Frontend folder not found at path: {frontend_dir}. Make sure you create the frontend folder.")
