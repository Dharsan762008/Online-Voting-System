/* script.js */

// State variables
let activeVoterId = null;
const API_BASE = ''; // Empty string means local relative path on the same server

// Show micro notifications (toasts)
function showToast(message, type = 'success') {
  let toast = document.getElementById('app-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'app-toast';
    document.body.appendChild(toast);
  }
  
  toast.className = `toast-msg show ${type}-toast`;
  
  // Custom SVG icon matching message type
  const iconMarkup = type === 'success' 
    ? `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`
    : `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>`;

  toast.innerHTML = `${iconMarkup} <span>${message}</span>`;
  
  setTimeout(() => {
    toast.classList.remove('show');
  }, 3500);
}

/**
 * Handle switching between different tab sections
 * @param {string} sectionId 
 */
function showSection(sectionId) {
  // Hide all sections
  const sections = document.querySelectorAll('.section');
  sections.forEach(sec => {
    sec.classList.remove('active');
  });

  // Show clicked section
  const targetSection = document.getElementById(sectionId);
  if (targetSection) {
    targetSection.classList.add('active');
  }

  // Update navigation button active state
  const menuButtons = document.querySelectorAll('.menu button');
  menuButtons.forEach(btn => {
    btn.classList.remove('active');
    if (btn.getAttribute('onclick').includes(sectionId)) {
      btn.classList.add('active');
    }
  });

  // Auto-refresh stats when visiting admin panel or results
  if (sectionId === 'admin') {
    refreshAdmin();
  } else if (sectionId === 'results') {
    showResults();
  }
}

/**
 * Register a new Candidate (Sends to Node.js Backend API)
 */
async function registerCandidate() {
  const id = document.getElementById('candidateId').value.trim();
  const name = document.getElementById('candidateName').value.trim();
  const party = document.getElementById('party').value.trim();
  const ageVal = document.getElementById('age').value;
  const constituency = document.getElementById('constituency').value.trim();
  const property = document.getElementById('property').value.trim();
  const manifesto = document.getElementById('manifesto').value.trim();

  // Field Validations
  if (!id || !name || !party || !ageVal || !constituency || !property || !manifesto) {
    showToast("Please fill in all candidate registration fields.", "error");
    return;
  }

  const age = parseInt(ageVal);
  if (age < 18 || age > 100) {
    showToast("Candidate must be of legal eligible age (18 - 100).", "error");
    return;
  }

  const candidateData = { id, name, party, age, constituency, property, manifesto };

  try {
    const response = await fetch(`${API_BASE}/api/candidates`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(candidateData)
    });

    const result = await response.json();

    if (response.ok && result.success) {
      showToast(`Candidate "${name}" registered successfully on Server!`, "success");
      
      // Clear inputs
      document.getElementById('candidateId').value = '';
      document.getElementById('candidateName').value = '';
      document.getElementById('party').value = '';
      document.getElementById('age').value = '';
      document.getElementById('constituency').value = '';
      document.getElementById('property').value = '';
      document.getElementById('manifesto').value = '';
    } else {
      showToast(result.error || "Candidate registration failed.", "error");
    }
  } catch (error) {
    console.error("API Error:", error);
    showToast("Server connection error during registration.", "error");
  }
}

/**
 * Load Candidates for Voter casting (Fetches status & database from Backend API)
 */
async function loadCandidates() {
  const voterIdInput = document.getElementById('voterId');
  const voterId = voterIdInput.value.trim();

  if (!voterId) {
    showToast("Voter ID verification is required to load candidates.", "error");
    return;
  }

  activeVoterId = voterId;
  const listContainer = document.getElementById('candidateList');
  listContainer.innerHTML = `<div style="text-align: center; margin-top: 1.5rem; color: var(--text-secondary);">Verifying voter access credentials...</div>`;

  try {
    // 1. Check double voting status from backend check
    const statusRes = await fetch(`${API_BASE}/api/voted/${activeVoterId}`);
    const statusData = await statusRes.json();
    const hasVoted = statusData.hasVoted;

    // 2. Load all candidates
    const candRes = await fetch(`${API_BASE}/api/candidates`);
    const candData = await candRes.json();
    const candidates = candData.candidates || [];

    listContainer.innerHTML = '';

    if (candidates.length === 0) {
      listContainer.innerHTML = `<p style="color: var(--text-secondary); text-align: center; margin-top: 1.5rem;">No candidates registered in this constituency yet.</p>`;
      return;
    }

    if (hasVoted) {
      showToast("Access Denied: This Voter ID has already cast their ballot.", "error");
    } else {
      showToast(`Authentication secure. Welcome Voter ${activeVoterId}`, "success");
    }

    // Generate cards
    const grid = document.createElement('div');
    grid.className = 'candidate-cards-grid';

    candidates.forEach(candidate => {
      const card = document.createElement('div');
      card.className = 'candidate-card';

      card.innerHTML = `
        <span class="card-party-badge">${candidate.party}</span>
        <h3 class="card-title">${candidate.name}</h3>
        <p class="card-subtitle">ID: ${candidate.id}</p>
        
        <p class="card-info-item"><strong>Age:</strong> ${candidate.age} yrs</p>
        <p class="card-info-item"><strong>Constituency:</strong> ${candidate.constituency}</p>
        
        <p class="card-info-item" style="margin-top: 10px;"><strong>Property Declarations:</strong></p>
        <div class="card-text-block">${candidate.property}</div>

        <p class="card-info-item" style="margin-top: 10px;"><strong>Manifesto details:</strong></p>
        <div class="card-text-block" style="font-style: italic;">"${candidate.manifesto}"</div>
        
        <button class="card-vote-btn" 
                style="margin-top: 1.5rem;"
                ${hasVoted ? 'disabled' : ''} 
                onclick="castVote('${candidate.id}', '${candidate.name}')">
          ${hasVoted ? 'Ballot Cast' : 'Vote for Candidate'}
        </button>
      `;
      grid.appendChild(card);
    });

    listContainer.appendChild(grid);

  } catch (error) {
    console.error("API Error:", error);
    listContainer.innerHTML = `<p style="color: var(--error); text-align: center; margin-top: 1.5rem;">Failed to connect to backend voting terminal.</p>`;
    showToast("Failed to fetch voter authorization data.", "error");
  }
}

/**
 * Cast a Vote for a candidate (Submits securely to Node.js Backend API)
 */
async function castVote(candidateId, candidateName) {
  if (!activeVoterId) {
    showToast("Voter verification required before voting.", "error");
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/api/vote`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        voterId: activeVoterId,
        candidateId: candidateId
      })
    });

    const result = await response.json();

    if (response.ok && result.success) {
      showToast(`Thank you! Your vote for "${candidateName}" has been encrypted & cast.`, "success");
      // Re-load candidates layout to lock vote selections
      loadCandidates();
    } else {
      showToast(result.error || "Ballot casting failed.", "error");
    }
  } catch (error) {
    console.error("API Error:", error);
    showToast("Network encryption handshake error.", "error");
  }
}

/**
 * Refresh stats in Admin Dashboard (Fetches active statistics from Backend API)
 */
async function refreshAdmin() {
  try {
    const res = await fetch(`${API_BASE}/api/stats`);
    const data = await res.json();

    if (res.ok && data.success) {
      document.getElementById('totalCandidates').textContent = data.totalCandidates;
      document.getElementById('totalVotes').textContent = data.totalVotes;
      showToast("Server metrics synchronized successfully.", "success");
    } else {
      showToast("Failed to retrieve system metrics.", "error");
    }
  } catch (error) {
    console.error("API Error:", error);
    showToast("Failed to query system dashboard metrics.", "error");
  }
}

/**
 * Calculate & display election results with animated progress bars (Fetches from API)
 */
async function showResults() {
  const resultList = document.getElementById('resultList');
  resultList.innerHTML = `<div style="text-align: center; color: var(--text-secondary);">Retrieving secure election tallies...</div>`;

  try {
    const res = await fetch(`${API_BASE}/api/results`);
    const data = await res.json();

    if (!res.ok || !data.success) {
      resultList.innerHTML = `<p style="color: var(--error); text-align: center;">Failed to retrieve active result ledger.</p>`;
      return;
    }

    const sortedResults = data.results || [];
    const totalVotesCount = data.totalVotes || 0;

    resultList.innerHTML = '';

    if (sortedResults.length === 0) {
      resultList.innerHTML = `<p style="color: var(--text-secondary); text-align: center;">No results available: No candidates are registered.</p>`;
      return;
    }

    // Determine leading candidate banner
    if (totalVotesCount > 0) {
      const winner = sortedResults[0];
      const isTie = sortedResults.length > 1 && sortedResults[0].voteCount === sortedResults[1].voteCount;

      let winnerHtml = '';
      if (isTie) {
        winnerHtml = `
          <div class="winner-banner">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
            <span>Current Standing: Election Tie! Leading candidates have equal votes.</span>
          </div>
        `;
      } else {
        winnerHtml = `
          <div class="winner-banner">
            <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/>
              <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/>
              <path d="M4 22h16"/>
              <path d="M10 14.66V17c0 .55-.45 1-1 1H4v2h16v-2h-5c-.55 0-1-.45-1-1v-2.34"/>
              <path d="M12 2a6 6 0 0 1 6 6v5a6 6 0 0 1-6 6 6 6 0 0 1-6-6V8a6 6 0 0 1 6-6Z"/>
            </svg>
            <span>Current Leading Candidate: <strong>${winner.name} (${winner.party})</strong> with ${winner.voteCount} votes!</span>
          </div>
        `;
      }

      const wrapper = document.createElement('div');
      wrapper.innerHTML = winnerHtml;
      resultList.appendChild(wrapper.firstElementChild);
    }

    // Generate progress rows
    const resultsContainer = document.createElement('div');
    resultsContainer.className = 'results-wrapper';

    sortedResults.forEach(cand => {
      const pct = totalVotesCount > 0 ? ((cand.voteCount / totalVotesCount) * 100).toFixed(1) : 0;
      
      const row = document.createElement('div');
      row.className = 'result-card';
      row.innerHTML = `
        <div class="result-header">
          <div class="result-name-party">
            ${cand.name} <span class="result-party">(${cand.party})</span>
          </div>
          <div class="result-votes-count">
            ${cand.voteCount} vote${cand.voteCount === 1 ? '' : 's'} (${pct}%)
          </div>
        </div>
        <div class="result-progress-container">
          <div class="result-progress-bar" data-width="${pct}%"></div>
        </div>
      `;
      resultsContainer.appendChild(row);
    });

    resultList.appendChild(resultsContainer);

    // Trigger animations for the progress bars
    setTimeout(() => {
      const progressBars = document.querySelectorAll('.result-progress-bar');
      progressBars.forEach(bar => {
        bar.style.width = bar.getAttribute('data-width');
      });
    }, 100);

    showToast("Results tally computed.", "success");

  } catch (error) {
    console.error("API Error:", error);
    resultList.innerHTML = `<p style="color: var(--error); text-align: center;">Failed to connect to results tally terminal.</p>`;
    showToast("Failed to fetch current results tally.", "error");
  }
}

// Initial Load
document.addEventListener('DOMContentLoaded', () => {
  // Set default view active
  showSection('candidate');
});
