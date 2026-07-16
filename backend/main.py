# backend/main.py
import os
import shutil
import sys
import csv
import io

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

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

UPLOADS_DIR = os.path.join(BACKEND_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")


# Initialize database tables on server launch
@app.on_event("startup")
def startup_event():
    # Ensure uploads directory exists
    os.makedirs(UPLOADS_DIR, exist_ok=True)

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


class AdminCandidateRequest(BaseModel):
    candidateId: str
    password: str
    name: str
    degree: str
    qualification: str
    achievements: str
    manifesto: str
    position: str


class DeleteCandidateRequest(BaseModel):
    candidateId: str
    
    
class CSVUploadResponse(BaseModel):
    success: bool
    message: str

# --- API Endpoints ---

@app.get("/api/health")
def health_check():
    """Simple API check connection endpoint"""
    return {"status": "ok", "message": "Voting system API server is running."}
@app.get("/api/admin/election-status")
def get_election_status():
    row = database.fetch_one(
        "SELECT election_status FROM election_settings WHERE id = 1"
    )

    return {
        "success": True,
        "status": row["election_status"]
    }


@app.post("/api/admin/start-election")
def start_election():

    database.execute_query(
        "UPDATE election_settings SET election_status='STARTED' WHERE id = 1"
    )

    return {
        "success": True,
        "message": "Election Started"
    }


@app.post("/api/admin/stop-election")
def stop_election():

    database.execute_query(
        "UPDATE election_settings SET election_status='STOPPED' WHERE id = 1"
    )

    return {
        "success": True,
        "message": "Election Stopped"
    }

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

@app.get("/api/admin/winners")
def get_winners():

    results = database.fetch_all("""
        SELECT
            c.position,
            c.name,
            c.degree,
            COUNT(v.candidate_id) AS vote_count
        FROM candidates c
        LEFT JOIN votes v
            ON c.candidate_id = v.candidate_id
        GROUP BY
            c.candidate_id,
            c.position,
            c.name,
            c.degree
        ORDER BY
            c.position,
            vote_count DESC
    """)

    winners = []
    seen_positions = set()

    for row in results:
        if row["position"] not in seen_positions:
            winners.append(row)
            seen_positions.add(row["position"])

    return {
        "success": True,
        "winners": winners
    }

@app.post("/api/auth/voter/login")
def voter_login(req: VoterLoginRequest):
    """
    Authenticate a student voter.
    """
    voter = database.fetch_one(
        "SELECT voter_id, name, department FROM voters WHERE voter_id = %s AND password = %s",
        (req.voterId, req.password),
    )
    if not voter:
        raise HTTPException(status_code=401, detail="Invalid Voter ID or password.")

    voted_positions_rows = database.fetch_all(
        "SELECT position FROM votes WHERE voter_id = %s",
        (req.voterId,),
    )
    voted_positions = [row["position"] for row in voted_positions_rows]

    return {
        "success": True,
        "voter": {
            "id": voter["voter_id"],
            "name": voter["name"],
            "department": voter["department"],
            "votedPositions": voted_positions,
        },
    }


@app.post("/api/auth/candidate/login")
def candidate_login(req: CandidateLoginRequest):
    """
    Authenticate an election participant/candidate.
    """
    candidate = database.fetch_one(
        "SELECT candidate_id, name, position FROM candidates WHERE candidate_id = %s AND password = %s",
        (req.candidateId, req.password),
    )
    if not candidate:
        raise HTTPException(status_code=401, detail="Invalid Candidate ID or password.")

    return {
        "success": True,
        "candidate": {
            "id": candidate["candidate_id"],
            "name": candidate["name"],
            "position": candidate["position"],
        },
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
        (candidate_id,),
    )
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    return {"success": True, "candidate": candidate}


@app.post("/api/vote")
def cast_vote(req: VoteRequest):
    """
    Records a vote after ensuring the voter hasn't already voted for this position.
    """
    voter = database.fetch_one("SELECT voter_id FROM voters WHERE voter_id = %s", (req.voterId,))
    if not voter:
        raise HTTPException(status_code=404, detail="Voter registration record not found.")
    status = database.fetch_one("SELECT election_status FROM election_settings WHERE id = 1")
    if not status or status.get("election_status") != "STARTED":
        raise HTTPException(status_code=400, detail="Election is not active.")

    existing_vote = database.fetch_one(
        "SELECT candidate_id FROM votes WHERE voter_id = %s AND position = %s",
        (req.voterId, req.position),
    )
    if existing_vote:
        raise HTTPException(
            status_code=400,
            detail=f"You have already cast your vote for the {req.position} position.",
        )

    candidate = database.fetch_one(
        "SELECT candidate_id FROM candidates WHERE candidate_id = %s AND position = %s",
        (req.candidateId, req.position),
    )
    if not candidate:
        raise HTTPException(status_code=404, detail="Selected candidate does not exist for this position.")

    try:
        database.execute_query(
            "INSERT INTO votes (voter_id, position, candidate_id) VALUES (%s, %s, %s)",
            (req.voterId, req.position, req.candidateId),
        )
        return {"success": True, "message": f"Your vote for {req.position} was registered successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database transaction error: {str(e)}")


@app.put("/api/candidate/profile")
def update_candidate_profile(req: CandidateProfileUpdateRequest):
    """
    Allow candidate to modify their own profile achievements, degree, qualification, and manifesto.
    """
    candidate = database.fetch_one(
        "SELECT candidate_id FROM candidates WHERE candidate_id = %s AND password = %s",
        (req.candidateId, req.password),
    )
    if not candidate:
        raise HTTPException(status_code=401, detail="Authentication failed. Incorrect password.")

    try:
        database.execute_query(
            """UPDATE candidates
               SET name = %s, degree = %s, qualification = %s, achievements = %s, manifesto = %s
               WHERE candidate_id = %s""",
            (req.name, req.degree, req.qualification, req.achievements, req.manifesto, req.candidateId),
        )
        return {"success": True, "message": "Candidate profile updated successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profile update failed: {str(e)}")


@app.post("/api/admin/add-candidate")
def admin_add_candidate(req: AdminCandidateRequest):
    existing = database.fetch_one(
        "SELECT candidate_id FROM candidates WHERE candidate_id = %s",
        (req.candidateId,),
    )   

    if existing:
        raise HTTPException(status_code=400, detail="Candidate ID already exists.")

    try:
        database.execute_query(
            """
            INSERT INTO candidates
            (
                candidate_id,
                password,
                name,
                degree,
                qualification,
                achievements,
                manifesto,
                image_url,
                position
            )
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, '', %s)
            """,
            (
                req.candidateId,
                req.password,
                req.name,
                req.degree,
                req.qualification,
                req.achievements,
                req.manifesto,
                req.position,
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add candidate: {str(e)}")

    return {
        "success": True,
        "message": "Candidate added successfully.",
    }
    
from pydantic import BaseModel

class UpdateCandidate(BaseModel):
    candidateId: str
    name: str
    degree: str
    qualification: str
    manifesto: str
    position: str

@app.put("/api/admin/update-candidate")
def update_candidate(data: UpdateCandidate):

    rows = database.execute_query(
        """
        UPDATE candidates
        SET
            name=%s,
            degree=%s,
            qualification=%s,
            manifesto=%s,
            position=%s
        WHERE candidate_id=%s
        """,
        (
            data.name,
            data.degree,
            data.qualification,
            data.manifesto,
            data.position,
            data.candidateId
        )
    )

    if rows == 0:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found."
        )

    return {
        "success": True,
        "message": "Candidate updated successfully."
    }
    
@app.delete("/api/admin/delete-candidate")
def delete_candidate(req: DeleteCandidateRequest):
    candidate = database.fetch_one(
        "SELECT candidate_id, image_url FROM candidates WHERE candidate_id = %s",
        (req.candidateId,),
    )

    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    try:
        database.execute_query("DELETE FROM candidates WHERE candidate_id = %s", (req.candidateId,))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete candidate: {str(e)}")

    if candidate.get("image_url"):
        try:
            image_path = os.path.join(UPLOADS_DIR, os.path.basename(candidate["image_url"]))
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception:
            pass

    return {
        "success": True,
        "message": "Candidate deleted successfully.",
    }

@app.post("/api/admin/upload-students")
def upload_students(file: UploadFile = File(...)):

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")

    try:
        content = file.file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))

        count = 0

        for row in reader:

            existing = database.fetch_one(
                "SELECT voter_id FROM voters WHERE voter_id = %s",
                (row["voter_id"],)
            )

            if existing:
                continue

            database.execute_query(
                """
                INSERT INTO voters
                (voter_id, password, name, department)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    row["voter_id"],
                    row["password"],
                    row["name"],
                    row["department"]
                )
            )

            count += 1

        return {
            "success": True,
            "message": f"{count} students uploaded successfully."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))  
 
@app.post("/api/candidate/upload-image")
def upload_candidate_image(
    candidateId: str = Form(...),
    password: str = Form(...),
    image: UploadFile = File(...),
):
    candidate = database.fetch_one(
        "SELECT candidate_id FROM candidates WHERE candidate_id = %s AND password = %s",
        (candidateId, password),
    )
    if not candidate:
        raise HTTPException(status_code=401, detail="Authentication failed. Incorrect password.")

    if not image.filename:
        raise HTTPException(status_code=400, detail="No file selected.")

    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    ext = os.path.splitext(image.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Unsupported image format.")

    os.makedirs(UPLOADS_DIR, exist_ok=True)

    filename = f"{candidateId}{ext}"
    save_path = os.path.join(UPLOADS_DIR, filename)

    try:
        with open(save_path, "wb") as f:
            shutil.copyfileobj(image.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")

    image_url = f"/uploads/{filename}"
    try:
        database.execute_query(
            "UPDATE candidates SET image_url = %s WHERE candidate_id = %s",
            (image_url, candidateId),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update candidate image: {str(e)}")

    return {
        "success": True,
        "message": "Image uploaded successfully.",
        "imageUrl": image_url,
    }