# College Online Voting System Setup Guide

A complete full-stack voting portal for college elections (President, Vice President, General Secretary). It runs on a Python FastAPI backend server connected to a MySQL database, serving a responsive glassmorphic frontend user interface.

---

## 📂 Project Directory Structure

```
Online Voting/
├── schema.sql           # Database schema & initial test datasets
├── requirements.txt     # Python backend dependencies
├── README.md            # Setup and configuration guide (This file)
├── backend/
│   ├── main.py          # FastAPI application routes
│   ├── database.py      # MySQL connection pool & auto-init
│   └── uploads/         # Directory where uploaded candidate photos are saved
└── frontend/
    ├── index.html       # Client interface layout
    ├── style.css        # Premium dark glassmorphism styling
    └── script.js        # Dynamic routing, API connections, & UI rendering
```

---

## 🛠️ Step-by-Step Setup Instructions

### Step 1: Start and Configure MySQL Server
1. Ensure your local **MySQL Server** is running (using tools like **XAMPP / WampServer** or a standard standalone MySQL installation).
2. The backend connects to MySQL on localhost using:
   * **Host**: `localhost`
   * **User**: `root`
   * **Password**: `""` (Empty password by default)
   * **Database**: `college_voting` (Automatically created if missing)
3. If your MySQL credentials are different (e.g. root password is set), open [backend/database.py](file:///c:/Users/dhars/OneDrive/Documents/Online%20Voting/backend/database.py#L9-L13) and change the variables:
   ```python
   DB_USER = "YOUR_USERNAME"
   DB_PASSWORD = "YOUR_PASSWORD"
   ```

> [!NOTE]
> You do **not** need to manually import `schema.sql` into MySQL. When the FastAPI application boots up, it automatically connects, verifies if the tables exist, and executes `schema.sql` to initialize the database and populate it with mock data if it's a new installation.

---

### Step 2: Install Python Dependencies
1. Open your terminal or Command Prompt.
2. Navigate to your project folder:
   ```powershell
   cd "c:\Users\dhars\OneDrive\Documents\Online Voting"
   ```
3. Install the dependencies listed in `requirements.txt` using `pip`:
   ```powershell
   pip install -r requirements.txt
   ```

---

### Step 3: Run the FastAPI Server
1. Start the server using Uvicorn:
   ```powershell
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```
2. You will see a console output stating:
   `🔒 VOTEGUARD ONLINE VOTING SYSTEM BACKEND STARTED`
   `🌍 Local Access URL: http://localhost:8000`

---

### Step 4: Open and Test the Voting System
Open your web browser and navigate to **https://online-voting-system-1-f2ra.onrender.com/**. The page will load your frontend and automatically sync with the API database.

*   **Voter login details (Student Voters)**:
    *   **Student ID**: `STU001` (up to `STU005`)
    *   **Password**: `password123`
*   **Candidate login details (Election Participants)**:
    *   **Candidate ID**: `PRES01` or `PRES02` (President), `VP01` or `VP02` (Vice President), `SEC01` or `SEC02` (General Secretary)
    *   **Password**: `pass123`

---

## 🔒 Verification Features in Action
1. **Single-Vote Constraint**: Log in as `STU001` under **Student Voters** and vote for a President. The system locks voting buttons for that category. Attempting to force-post a vote on the API level for the same position will return a database validation error.
2. **Profile Syncing**: Log in as `PRES01` under the **Candidate Console**, upload a new photo, modify your manifesto details, and click save. Log back in as a voter and click on `Jonathan Hughes` to see the updated photo and manifesto in real-time.
3. **Live Tallies**: The **Live Tallies** tab updates a visual graph using calculations from MySQL. The leading candidate in each category is crowned with a 👑 icon automatically.
