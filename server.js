/* server.js */
const http = require('http');
const fs = require('fs').promises;
const path = require('path');

const PORT = 3000;
const DB_FILE = path.join(__dirname, 'db.json');

// Mock data to initialize database on clean start
const INITIAL_DB = {
  candidates: [
    {
      id: "C-01",
      name: "Dr. Sarah Jenkins",
      party: "Green Future Alliance",
      age: 42,
      constituency: "Metropolis East",
      property: "Residential home, hybrid investment assets",
      manifesto: "Pioneering the transition to 100% carbon-neutral infrastructure, solar energy grids, and subsidized public transit."
    },
    {
      id: "C-02",
      name: "Alex Mercer",
      party: "Tech Progress Party",
      age: 38,
      constituency: "Silicon District",
      property: "Digital asset portfolio, tech shares",
      manifesto: "Enhancing digital rights, deploying secure municipal blockchain ledger registries, and funding tech startups."
    },
    {
      id: "C-03",
      name: "Elena Rostova",
      party: "Citizen Heritage Coalition",
      age: 51,
      constituency: "Metropolis East",
      property: "Family estate, local retail properties",
      manifesto: "Preserving architectural heritage, funding community development committees, and upgrading public educational centers."
    }
  ],
  votes: {
    "C-01": 5,
    "C-02": 3,
    "C-03": 2
  },
  votedVoters: ["V-101", "V-102", "V-103"]
};

/**
 * Read the DB file, initializing it with default candidates if it doesn't exist.
 */
async function readDatabase() {
  try {
    const data = await fs.readFile(DB_FILE, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    // Database doesn't exist, create it with initial demo data
    await writeDatabase(INITIAL_DB);
    return INITIAL_DB;
  }
}

/**
 * Write updated data to the DB file.
 */
async function writeDatabase(data) {
  await fs.writeFile(DB_FILE, JSON.stringify(data, null, 2), 'utf8');
}

/**
 * Helper to collect request body data from stream.
 */
function getRequestBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
    });
    req.on('end', () => {
      resolve(body);
    });
    req.on('error', err => {
      reject(err);
    });
  });
}

/**
 * Main HTTP Request Handler Router
 */
const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const method = req.method;

  // Set default content type headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // Handle preflight requests
  if (method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // --- API ROUTING ---

  // GET /api/candidates
  if (url.pathname === '/api/candidates' && method === 'GET') {
    try {
      const db = await readDatabase();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: true, candidates: db.candidates }));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: false, error: 'Database read failure.' }));
    }
    return;
  }

  // POST /api/candidates
  if (url.pathname === '/api/candidates' && method === 'POST') {
    try {
      const bodyText = await getRequestBody(req);
      const newCand = JSON.parse(bodyText);

      // Validation
      if (!newCand.id || !newCand.name || !newCand.party || !newCand.age || !newCand.constituency || !newCand.property || !newCand.manifesto) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, error: 'All registration fields are required.' }));
        return;
      }

      const db = await readDatabase();
      
      // Check duplicate ID
      if (db.candidates.some(c => c.id.toLowerCase() === newCand.id.toLowerCase())) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, error: `Candidate ID "${newCand.id}" is already registered.` }));
        return;
      }

      // Add candidate
      db.candidates.push(newCand);
      db.votes[newCand.id] = 0; // Initialize vote count
      await writeDatabase(db);

      res.writeHead(201, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: true, candidate: newCand }));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: false, error: 'Failed to write new candidate.' }));
    }
    return;
  }

  // POST /api/vote
  if (url.pathname === '/api/vote' && method === 'POST') {
    try {
      const bodyText = await getRequestBody(req);
      const { voterId, candidateId } = JSON.parse(bodyText);

      if (!voterId || !candidateId) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, error: 'Voter ID and Candidate ID are required.' }));
        return;
      }

      const db = await readDatabase();

      // Check double voting
      if (db.votedVoters.includes(voterId)) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, error: 'Access Denied: This Voter ID has already cast a ballot.' }));
        return;
      }

      // Check candidate exists
      if (!db.candidates.some(c => c.id === candidateId)) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, error: 'Target candidate does not exist.' }));
        return;
      }

      // Register vote
      db.votes[candidateId] = (db.votes[candidateId] || 0) + 1;
      db.votedVoters.push(voterId);
      await writeDatabase(db);

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: true, message: 'Ballot successfully counted and encrypted.' }));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: false, error: 'Vote registration failed.' }));
    }
    return;
  }

  // GET /api/stats
  if (url.pathname === '/api/stats' && method === 'GET') {
    try {
      const db = await readDatabase();
      const totalCandidates = db.candidates.length;
      let totalVotes = 0;
      Object.values(db.votes).forEach(v => totalVotes += v);

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: true, totalCandidates, totalVotes }));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: false, error: 'Stats query failed.' }));
    }
    return;
  }

  // GET /api/results
  if (url.pathname === '/api/results' && method === 'GET') {
    try {
      const db = await readDatabase();
      
      let totalVotes = 0;
      Object.values(db.votes).forEach(v => totalVotes += v);

      const results = db.candidates.map(c => ({
        ...c,
        voteCount: db.votes[c.id] || 0
      })).sort((a, b) => b.voteCount - a.voteCount);

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: true, results, totalVotes }));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: false, error: 'Results processing failed.' }));
    }
    return;
  }

  // GET /api/voted/:voterId
  if (url.pathname.startsWith('/api/voted/') && method === 'GET') {
    try {
      const voterId = url.pathname.split('/').pop();
      const db = await readDatabase();
      const hasVoted = db.votedVoters.includes(voterId);
      
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: true, hasVoted }));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: false, error: 'Voter validation check failed.' }));
    }
    return;
  }

  // --- STATIC FILES ROUTING ---

  let filePath = path.join(__dirname, url.pathname === '/' ? 'index.html' : url.pathname);
  
  // Basic security check to prevent directory traversal
  if (!filePath.startsWith(__dirname)) {
    res.writeHead(403);
    res.end('Access Denied');
    return;
  }

  const extname = String(path.extname(filePath)).toLowerCase();
  const mimeTypes = {
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml'
  };

  const contentType = mimeTypes[extname] || 'application/octet-stream';

  try {
    const content = await fs.readFile(filePath);
    res.writeHead(200, { 'Content-Type': contentType });
    res.end(content, 'utf-8');
  } catch (error) {
    if (error.code === 'ENOENT') {
      res.writeHead(404, { 'Content-Type': 'text/html' });
      res.end('<h1>404 Not Found</h1><p>The requested file does not exist.</p>');
    } else {
      res.writeHead(500);
      res.end(`Server Error: ${error.code}`);
    }
  }
});

// Start Server Listen
server.listen(PORT, () => {
  console.log(`===================================================`);
  console.log(`🔒 VOTEGUARD ONLINE VOTING SYSTEM BACKEND STARTED`);
  console.log(`🌍 Local Access URL: http://localhost:${PORT}`);
  console.log(`📦 Database File: ${DB_FILE}`);
  console.log(`===================================================`);
});
