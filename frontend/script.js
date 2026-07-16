/* frontend/script.js */

// Application State
let activeVoter = null;
let activeCandidate = null; // Stores { id, name, position, password }
let candidatesList = [];
let selectedPositionTab = "President"; // Default category
let selectedPhotoFile = null;

const API_BASE = "https://online-voting-system-fqi3.onrender.com";

// Initialize connections on page load
document.addEventListener("DOMContentLoaded", () => {
  checkServerHealth();
  loadCandidatesData();
  
  // Set up connection checker interval (every 10 seconds)
  setInterval(checkServerHealth, 10000);
});

/**
 * Checks if FastAPI server is responsive
 */
async function checkServerHealth() {
  const dot = document.querySelector(".status-dot");
  const text = document.getElementById("statusText");
  
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    if (res.ok) {
      dot.className = "status-dot online";
      text.textContent = "System Secure & Online";
    } else {
      throw new Error();
    }
  } catch (err) {
    dot.className = "status-dot offline";
    text.textContent = "Server Offline (Sync Issue)";
  }
}

/**
 * Show clean toast notification banner
 */
function showToast(message, type = "success") {
  const toast = document.getElementById("appToast");
  const icon = document.getElementById("toastIcon");
  const msgText = document.getElementById("toastMessage");
  
  msgText.textContent = message;
  toast.className = `toast-card show ${type}-toast`;
  
  if (type === "success") {
    icon.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="20 6 9 17 4 12"/>
      </svg>
    `;
  } else {
    icon.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" x2="12" y1="8" y2="12"/>
        <line x1="12" x2="12.01" y1="16" y2="16"/>
      </svg>
    `;
  }

  // Clear timeout
  if (window.toastTimeout) {
    clearTimeout(window.toastTimeout);
  }
  
  window.toastTimeout = setTimeout(() => {
    toast.classList.remove("show");
  }, 4000);
}

/**
 * Handle Switching Main Navigation tabs (SPA)
 */
function switchMainTab(tabName) {
  // Hide all sections
  const sections = document.querySelectorAll(".tab-section");
  sections.forEach(s => s.classList.remove("active"));
  
  // Update menu buttons
  const navButtons = document.querySelectorAll(".main-menu button");
  navButtons.forEach(btn => {
    btn.classList.remove("active");
    if (btn.getAttribute("onclick").includes(tabName)) {
      btn.classList.add("active");
    }
  });

  // Show target section
  if (tabName === "voter") {
    document.getElementById("voterPortal").classList.add("active");
    renderCandidates();
  } else if (tabName === "candidate") {
    document.getElementById("candidatePortal").classList.add("active");
  } else if (tabName === "results") {
    document.getElementById("resultsPortal").classList.add("active");
    loadResultsData();
  }
}

// ===================================================
// VOTER DASHBOARD FLOW
// ===================================================

/**
 * Student Voter Login Handler
 */
async function handleVoterLogin() {
  const voterId = document.getElementById("voterIdInput").value.trim();
  const password = document.getElementById("voterPassInput").value;

  if (!voterId || !password) {
    showToast("Please fill in Student ID and Password.", "error");
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/api/auth/voter/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ voterId, password })
    });

    const data = await response.json();

    if (response.ok && data.success) {
      activeVoter = data.voter;
      
      // Update DOM
      document.getElementById("sessionVoterName").textContent = activeVoter.name;
      document.getElementById("sessionVoterDetails").textContent = `${activeVoter.id} • Department of ${activeVoter.department}`;
      
      document.getElementById("voterLoginCard").style.display = "none";
      document.getElementById("voterDashboard").style.display = "block";
      
      showToast(`Authentication secure. Welcome, ${activeVoter.name}`, "success");
      
      // Load and draw candidates
      await loadCandidatesData();
      renderCandidates();
    } else {
      showToast(data.detail || "Authentication credentials failed.", "error");
    }
  } catch (error) {
    console.error(error);
    showToast("Failed to establish secure session connection.", "error");
  }
}

/**
 * Student Voter Logout Handler
 */
function handleVoterLogout() {
  activeVoter = null;
  document.getElementById("voterIdInput").value = "";
  document.getElementById("voterPassInput").value = "";
  document.getElementById("voterLoginCard").style.display = "block";
  document.getElementById("voterDashboard").style.display = "none";
  showToast("Voter session closed.", "success");
}

/**
 * Position tab switcher (Voter Dashboard)
 */
function switchPositionTab(positionName) {
  selectedPositionTab = positionName;
  
  const tabs = document.querySelectorAll(".pos-tab");
  tabs.forEach(t => {
    t.classList.remove("active");
    if (t.textContent.trim() === positionName) {
      t.classList.add("active");
    }
  });

  renderCandidates();
}

/**
 * Load global candidate details from server
 */
async function loadCandidatesData() {
  try {
    const res = await fetch(`${API_BASE}/api/candidates`);
    const data = await res.json();
    if (res.ok && data.success) {
      candidatesList = data.candidates;
    }
  } catch (err) {
    console.error("Error loading candidates list:", err);
  }
}

/**
 * Renders Candidate Cards based on current category and voting history
 */
function renderCandidates() {
  const grid = document.getElementById("voterCandidatesGrid");
  const badge = document.getElementById("ballotCastBadge");
  grid.innerHTML = "";
  
  if (!activeVoter) return;

  // Check if voter has already cast ballot for current position category
  const hasVoted = activeVoter.votedPositions.includes(selectedPositionTab);
  
  if (hasVoted) {
    badge.style.display = "flex";
  } else {
    badge.style.display = "none";
  }

  // Filter candidates matching current selected position
  const filtered = candidatesList.filter(c => c.position === selectedPositionTab);
  
  if (filtered.length === 0) {
    grid.innerHTML = `<p style="color: var(--text-secondary); text-align: center; grid-column: 1/-1; margin-top: 1rem;">No registered candidates for ${selectedPositionTab}.</p>`;
    return;
  }

  filtered.forEach(cand => {
    const card = document.createElement("div");
    card.className = "candidate-card";
    
    // Choose appropriate image url or default SVG avatar
    const imgHtml = cand.image_url 
      ? `<img src="${cand.image_url}" alt="${cand.name}">`
      : `<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`;

    card.innerHTML = `
      <div class="card-avatar-box">${imgHtml}</div>
      <h3 class="card-name">${cand.name}</h3>
      <p class="card-degree">${cand.degree}</p>
      
      <p class="card-info"><strong>Qualification:</strong> ${cand.qualification}</p>

      <!-- Accordion Block for Achievements -->
      <div class="collapsible-box" id="achBox_${cand.candidate_id}">
        <div class="collapsible-header" onclick="toggleAccordion('achBox_${cand.candidate_id}')">Achievements & Activities</div>
        <div class="collapsible-content">${cand.achievements}</div>
      </div>

      <!-- Accordion Block for Manifesto -->
      <div class="collapsible-box" id="manBox_${cand.candidate_id}">
        <div class="collapsible-header" onclick="toggleAccordion('manBox_${cand.candidate_id}')">Manifesto & Agenda</div>
        <div class="collapsible-content">${cand.manifesto}</div>
      </div>

      <div class="card-vote-btn-wrapper">
        <button class="btn-primary" ${hasVoted ? "disabled" : ""} onclick="castBallot('${cand.candidate_id}', '${cand.name}')">
          ${hasVoted ? "Ballot Locked" : "Cast Vote"}
        </button>
      </div>
    `;
    
    grid.appendChild(card);
  });
}

/**
 * Expand/Collapse Accordion Blocks
 */
function toggleAccordion(boxId) {
  const box = document.getElementById(boxId);
  box.classList.toggle("open");
}

/**
 * Cast a Vote for a candidate
 */
async function castBallot(candidateId, candidateName) {
  if (!activeVoter) {
    showToast("Voter session expired. Please re-login.", "error");
    return;
  }

  if (activeVoter.votedPositions.includes(selectedPositionTab)) {
    showToast("Vote already cast for this position.", "error");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/vote`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        voterId: activeVoter.id,
        candidateId: candidateId,
        position: selectedPositionTab
      })
    });

    const data = await res.json();

    if (res.ok && data.success) {
      showToast(`Ballot Cast: You voted for ${candidateName}!`, "success");
      
      // Update voter state
      activeVoter.votedPositions.push(selectedPositionTab);
      
      // Sync candidates and re-render
      await loadCandidatesData();
      renderCandidates();
    } else {
      showToast(data.detail || "Could not cast vote.", "error");
    }
  } catch (error) {
    console.error(error);
    showToast("Database communication error casting vote.", "error");
  }
}

// ===================================================
// CANDIDATE CONSOLE PROFILE FLOW
// ===================================================

/**
 * Candidate Login Handler
 */
async function handleCandidateLogin() {
  const candidateId = document.getElementById("candidateIdInput").value.trim();
  const password = document.getElementById("candidatePassInput").value;

  if (!candidateId || !password) {
    showToast("Please fill in Candidate ID and Password.", "error");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/auth/candidate/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ candidateId, password })
    });

    const data = await res.json();

    if (res.ok && data.success) {
      activeCandidate = {
        ...data.candidate,
        password: password // Save password in memory to validate profile changes
      };

      document.getElementById("candidateLoginCard").style.display = "none";
      document.getElementById("candidateEditor").style.display = "block";
      
      showToast("Candidate credentials verified. Console Decrypted.", "success");
      
      // Load candidate profile fields
      await loadCandidateProfileDetails();
    } else {
      showToast(data.detail || "Authentication credentials failed.", "error");
    }
  } catch (error) {
    console.error(error);
    showToast("Failed to verify candidate console credentials.", "error");
  }
}

/**
 * Loads current candidate profile into text fields and previews
 */
async function loadCandidateProfileDetails() {
  if (!activeCandidate) return;

  try {
    const res = await fetch(`${API_BASE}/api/candidate/profile/${activeCandidate.id}`);
    const data = await res.json();

    if (res.ok && data.success) {
      const c = data.candidate;
      
      // Populate text inputs
      document.getElementById("candEditName").value = c.name;
      document.getElementById("candEditPosition").value = c.position;
      document.getElementById("candEditDegree").value = c.degree;
      document.getElementById("candEditQual").value = c.qualification;
      document.getElementById("candEditAchievements").value = c.achievements;
      document.getElementById("candEditManifesto").value = c.manifesto;
      
      // Load photo preview
      const preview = document.getElementById("profileImagePreview");
      const placeholder = document.getElementById("photoAvatarPlaceholder");
      
      if (c.image_url) {
        preview.src = c.image_url;
        preview.style.display = "block";
        placeholder.style.display = "none";
      } else {
        preview.style.display = "none";
        placeholder.style.display = "flex";
      }
    }
  } catch (error) {
    console.error("Error loading candidate profile:", error);
    showToast("Failed to retrieve candidate profile details.", "error");
  }
}

/**
 * Preview local image selection in browser before upload
 */
function previewSelectedImage(event) {
  const file = event.target.files[0];
  if (!file) return;

  selectedPhotoFile = file;

  const preview = document.getElementById("profileImagePreview");
  const placeholder = document.getElementById("photoAvatarPlaceholder");
  
  const reader = new FileReader();
  reader.onload = function(e) {
    preview.src = e.target.result;
    preview.style.display = "block";
    placeholder.style.display = "none";
  };
  reader.readAsDataURL(file);
}

/**
 * Handle Photo Uploading to API Server
 */
async function handleCandidateImageUpload() {
  if (!activeCandidate) return;
  if (!selectedPhotoFile) {
    showToast("Please select a photo file first.", "error");
    return;
  }

  // package as Form-Data
  const formData = new FormData();
  formData.append("candidateId", activeCandidate.id);
  formData.append("password", activeCandidate.password);
  formData.append("image", selectedPhotoFile);

  try {
    const res = await fetch(`${API_BASE}/api/candidate/upload-image`, {
      method: "POST",
      body: formData
    });

    const data = await res.json();

    if (res.ok && data.success) {
      showToast("Profile photo uploaded and synced successfully!", "success");
      selectedPhotoFile = null; // Clear input buffer
      
      // Update global candidates state list
      await loadCandidatesData();
    } else {
      showToast(data.detail || "Image upload failed.", "error");
    }
  } catch (error) {
    console.error(error);
    showToast("Network upload buffer failure.", "error");
  }
}

/**
 * Update candidate text profile details (Manifesto, achievements, etc.)
 */
async function handleCandidateProfileUpdate() {
  if (!activeCandidate) return;

  const name = document.getElementById("candEditName").value.trim();
  const degree = document.getElementById("candEditDegree").value.trim();
  const qualification = document.getElementById("candEditQual").value.trim();
  const achievements = document.getElementById("candEditAchievements").value.trim();
  const manifesto = document.getElementById("candEditManifesto").value.trim();

  if (!name || !degree || !qualification || !achievements || !manifesto) {
    showToast("Please fill in all details.", "error");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/candidate/profile`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        candidateId: activeCandidate.id,
        password: activeCandidate.password,
        name,
        degree,
        qualification,
        achievements,
        manifesto
      })
    });

    const data = await res.json();

    if (res.ok && data.success) {
      showToast("Candidate profile details updated successfully!", "success");
      // Update global candidates list
      await loadCandidatesData();
    } else {
      showToast(data.detail || "Profile update failed.", "error");
    }
  } catch (error) {
    console.error(error);
    showToast("Database communication error updating profile.", "error");
  }
}

/**
 * Candidate Logout Handler
 */
function handleCandidateLogout() {
  activeCandidate = null;
  selectedPhotoFile = null;
  document.getElementById("candidateIdInput").value = "";
  document.getElementById("candidatePassInput").value = "";
  document.getElementById("candidateImageFile").value = "";
  
  document.getElementById("candidateLoginCard").style.display = "block";
  document.getElementById("candidateEditor").style.display = "none";
  showToast("Candidate console locked.", "success");
}

// ===================================================
// RESULTS PORTAL TALLY VIEW
// ===================================================

/**
 * Fetches voting aggregates and draws progress graphs per position
 */
async function loadResultsData() {
  const container = document.getElementById("resultsTalliesContainer");
  container.innerHTML = `<div style="text-align: center; color: var(--text-secondary); margin-top: 2rem;">Fetching database results tally ledger...</div>`;

  try {
    const res = await fetch(`${API_BASE}/api/results`);
    const data = await res.json();

    if (!res.ok || !data.success) {
      container.innerHTML = `<p style="color: var(--error); text-align: center; margin-top: 2rem;">Failed to retrieve results ledger from database.</p>`;
      return;
    }

    const resultsList = data.results || [];
    const totalVotesAll = data.totalVotes || 0;

    container.innerHTML = "";

    if (resultsList.length === 0) {
      container.innerHTML = `<p style="color: var(--text-secondary); text-align: center; margin-top: 2rem;">No candidates are currently registered.</p>`;
      return;
    }

    // Group results by position
    const grouped = {};
    resultsList.forEach(cand => {
      if (!grouped[cand.position]) {
        grouped[cand.position] = [];
      }
      grouped[cand.position].push(cand);
    });

    // Draw position-wise metrics
    for (const [position, candidates] of Object.entries(grouped)) {
      const posCard = document.createElement("div");
      posCard.className = "results-position-block";
      
      // Calculate total votes cast for this position category
      const posTotalVotes = candidates.reduce((sum, c) => sum + c.voteCount, 0);
      
      posCard.innerHTML = `
        <h3 class="results-position-title">${position} Category (Total Cast: ${posTotalVotes})</h3>
        <div class="results-rows-wrapper" id="rows_${position.replace(/\s+/g, '')}"></div>
      `;
      container.appendChild(posCard);

      const rowsWrapper = posCard.querySelector(".results-rows-wrapper");
      
      // Find leading candidate's high vote (to highlight with a crown)
      const maxVotes = Math.max(...candidates.map(c => c.voteCount));

      candidates.forEach(cand => {
        // Calculate percentage relative to this position category total
        const pct = posTotalVotes > 0 ? ((cand.voteCount / posTotalVotes) * 100).toFixed(1) : 0;
        
        const row = document.createElement("div");
        // Highlight leading candidates if they have votes
        const isLeading = posTotalVotes > 0 && cand.voteCount === maxVotes;
        row.className = `result-row-card ${isLeading ? "leading" : ""}`;
        
        row.innerHTML = `
          <div class="result-row-header">
            <div class="result-row-name">
              ${cand.name} <span class="result-row-party">(${cand.degree})</span>
            </div>
            <div class="result-row-votes">${cand.voteCount} vote${cand.voteCount === 1 ? "" : "s"} (${pct}%)</div>
          </div>
          <div class="result-bar-outer">
            <div class="result-bar-inner" data-pct="${pct}"></div>
          </div>
        `;
        rowsWrapper.appendChild(row);
      });
    }

    // Trigger visual transitions on progress bars
    setTimeout(() => {
      const bars = document.querySelectorAll(".result-bar-inner");
      bars.forEach(bar => {
        const pct = bar.getAttribute("data-pct");
        bar.style.width = `${pct}%`;
      });
    }, 100);

    showToast("Live election tallies synchronized.", "success");

  } catch (error) {
    console.error(error);
    container.innerHTML = `<p style="color: var(--error); text-align: center; margin-top: 2rem;">Failed to connect to backend results database.</p>`;
    showToast("Failed to fetch database results ledger.", "error");
  }
}
// ================================
// ADMIN ELECTION CONTROL
// ================================

async function startElection() {
  try {
    const res = await fetch(`${API_BASE}/api/admin/start-election`, {
      method: "POST"
    });

    const data = await res.json();

    if (res.ok && data.success) {
      showToast(data.message, "success");
    } else {
      showToast(data.detail || "Failed to start election", "error");
    }

  } catch (error) {
    console.error(error);
    showToast("Server connection failed", "error");
  }
}


async function stopElection() {
  try {
    const res = await fetch(`${API_BASE}/api/admin/stop-election`, {
      method: "POST"
    });

    const data = await res.json();

    if (res.ok && data.success) {
      showToast(data.message, "success");
    } else {
      showToast(data.detail || "Failed to stop election", "error");
    }

  } catch (error) {
    console.error(error);
    showToast("Server connection failed", "error");
  }
}