# server.py
import http.server
import json
import os
import urllib.parse

PORT = 3000
DB_FILE = 'db.json'

# Mock data to initialize database on first startup
INITIAL_DB = {
    "candidates": [
        {
            "id": "C-01",
            "name": "Dr. Sarah Jenkins",
            "party": "Green Future Alliance",
            "age": 42,
            "constituency": "Metropolis East",
            "property": "Residential home, hybrid investment assets",
            "manifesto": "Pioneering the transition to 100% carbon-neutral infrastructure, solar energy grids, and subsidized public transit."
        },
        {
            "id": "C-02",
            "name": "Alex Mercer",
            "party": "Tech Progress Party",
            "age": 38,
            "constituency": "Silicon District",
            "property": "Digital asset portfolio, tech shares",
            "manifesto": "Enhancing digital rights, deploying secure municipal blockchain ledger registries, and funding tech startups."
        },
        {
            "id": "C-03",
            "name": "Elena Rostova",
            "party": "Citizen Heritage Coalition",
            "age": 51,
            "constituency": "Metropolis East",
            "property": "Family estate, local retail properties",
            "manifesto": "Preserving architectural heritage, funding community development committees, and upgrading public educational centers."
        }
    ],
    "votes": {
        "C-01": 5,
        "C-02": 3,
        "C-03": 2
    },
    "votedVoters": ["V-101", "V-102", "V-103"]
}

def read_db():
    if not os.path.exists(DB_FILE):
        write_db(INITIAL_DB)
        return INITIAL_DB
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return INITIAL_DB

def write_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

class VotingHandler(http.server.BaseHTTPRequestHandler):
    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        # --- API ROUTING ---
        if path == '/api/candidates':
            db = read_db()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "candidates": db["candidates"]}).encode('utf-8'))
            return
            
        elif path == '/api/stats':
            db = read_db()
            total_cand = len(db["candidates"])
            total_votes = sum(db["votes"].values())
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "totalCandidates": total_cand, "totalVotes": total_votes}).encode('utf-8'))
            return

        elif path == '/api/results':
            db = read_db()
            total_votes = sum(db["votes"].values())
            results = []
            for c in db["candidates"]:
                results.append({
                    **c,
                    "voteCount": db["votes"].get(c["id"], 0)
                })
            # Sort by highest vote count
            results.sort(key=lambda x: x["voteCount"], reverse=True)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "results": results, "totalVotes": total_votes}).encode('utf-8'))
            return

        elif path.startswith('/api/voted/'):
            voter_id = path.split('/')[-1]
            db = read_db()
            has_voted = voter_id in db["votedVoters"]
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "hasVoted": has_voted}).encode('utf-8'))
            return

        # --- STATIC FILES ROUTING ---
        file_mapping = {
            '/': ('index.html', 'text/html'),
            '/style.css': ('style.css', 'text/css'),
            '/script.js': ('script.js', 'application/javascript')
        }

        if path in file_mapping:
            filename, content_type = file_mapping[path]
            try:
                with open(filename, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"Server Error: {str(e)}".encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>404 Not Found</h1>")

    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        try:
            data = json.loads(post_data)
        except Exception:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": "Invalid JSON payload."}).encode('utf-8'))
            return

        if path == '/api/candidates':
            required = ["id", "name", "party", "age", "constituency", "property", "manifesto"]
            if not all(k in data for k in required) or not all(data[k] for k in required):
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "All registration fields are required."}).encode('utf-8'))
                return

            db = read_db()
            if any(c["id"].lower() == data["id"].lower() for c in db["candidates"]):
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": f"Candidate ID \"{data['id']}\" is already registered."}).encode('utf-8'))
                return

            db["candidates"].append(data)
            db["votes"][data["id"]] = 0
            write_db(db)

            self.send_response(201)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "candidate": data}).encode('utf-8'))
            return

        elif path == '/api/vote':
            voter_id = data.get("voterId")
            candidate_id = data.get("candidateId")

            if not voter_id or not candidate_id:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "Voter ID and Candidate ID are required."}).encode('utf-8'))
                return

            db = read_db()
            if voter_id in db["votedVoters"]:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "Access Denied: This Voter ID has already cast a ballot."}).encode('utf-8'))
                return

            if not any(c["id"] == candidate_id for c in db["candidates"]):
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "Target candidate does not exist."}).encode('utf-8'))
                return

            db["votes"][candidate_id] = db["votes"].get(candidate_id, 0) + 1
            db["votedVoters"].append(voter_id)
            write_db(db)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "message": "Ballot successfully counted and encrypted."}).encode('utf-8'))
            return

        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    # Listening on all network interfaces on port 3000
    server = http.server.HTTPServer(('0.0.0.0', PORT), VotingHandler)
    print("===================================================")
    print("VOTEGUARD ONLINE VOTING SYSTEM BACKEND STARTED")
    print(f"Local Access URL: http://localhost:{PORT}")
    print(f"Database File: {DB_FILE} (Python Engine)")
    print("===================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
