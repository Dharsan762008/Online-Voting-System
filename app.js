/* app.js */

// Global State
let currentPortal = 'voter'; // 'voter' or 'admin'
let isPasswordVisible = false;

// DOM Elements
const tabVoter = document.getElementById('tabVoter');
const tabAdmin = document.getElementById('tabAdmin');
const userInput = document.getElementById('userInput');
const userLabel = document.getElementById('userLabel');
const passwordInput = document.getElementById('passwordInput');
const passwordLabel = document.getElementById('passwordLabel');
const submitBtn = document.getElementById('submitBtn');
const submitBtnText = document.getElementById('submitBtnText');
const idIcon = document.getElementById('idIcon');
const footerText = document.getElementById('footerText');
const footerLink = document.getElementById('footerLink');
const successScreen = document.getElementById('successScreen');
const successMsg = document.getElementById('successMsg');
const toast = document.getElementById('toast');
const toastMessage = document.getElementById('toastMessage');
const toastIcon = document.getElementById('toastIcon');
const eyeIcon = document.getElementById('eyeIcon');

/**
 * Switch between Voter and Admin login modes
 * @param {string} portal 
 */
function switchPortal(portal) {
  if (currentPortal === portal) return;
  currentPortal = portal;

  // Update tabs visual state
  if (portal === 'voter') {
    tabVoter.classList.add('active');
    tabAdmin.classList.remove('active');
    
    // Update labels and inputs for Voter
    userLabel.textContent = 'Voter ID / National ID';
    userInput.placeholder = 'Voter ID';
    passwordLabel.textContent = 'Secure Verification PIN';
    passwordInput.placeholder = 'Secure Pin';
    submitBtnText.textContent = 'Authenticate & Login';
    footerText.textContent = 'Not registered to vote yet?';
    footerLink.textContent = 'Register Online';
    
    // Set Icon to User
    idIcon.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>
        <circle cx="12" cy="7" r="4"/>
      </svg>
    `;
  } else {
    tabAdmin.classList.add('active');
    tabVoter.classList.remove('active');
    
    // Update labels and inputs for Admin
    userLabel.textContent = 'Admin Username / Email';
    userInput.placeholder = 'Admin Username';
    passwordLabel.textContent = 'Administrator Password';
    passwordInput.placeholder = 'Password';
    submitBtnText.textContent = 'Access Control Console';
    footerText.textContent = 'Authorized Officers only.';
    footerLink.textContent = 'Request access';
    
    // Set Icon to Shield-Alert
    idIcon.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        <path d="M12 8v4"/>
        <path d="M12 16h.01"/>
      </svg>
    `;
  }

  // Clear inputs and reset floating label status
  userInput.value = '';
  passwordInput.value = '';
  userInput.blur();
  passwordInput.blur();
}

/**
 * Toggle Password Visibility (Eye Icon click)
 */
function togglePasswordVisibility() {
  isPasswordVisible = !isPasswordVisible;
  if (isPasswordVisible) {
    passwordInput.type = 'text';
    // Eye off icon
    eyeIcon.innerHTML = `
      <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/>
      <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/>
      <path d="M6.61 6.61A13.52 13.52 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/>
      <line x1="2" x2="22" y1="2" y2="22"/>
    `;
  } else {
    passwordInput.type = 'password';
    // Eye icon
    eyeIcon.innerHTML = `
      <path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0z"/>
      <circle cx="12" cy="12" r="3"/>
    `;
  }
}

/**
 * Custom Toast Notifications
 * @param {string} msg 
 * @param {string} type 
 */
function showToast(msg, type = 'error') {
  toastMessage.textContent = msg;
  toast.className = `notification-toast show toast-${type}`;
  
  if (type === 'error') {
    toastIcon.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ff3366" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" x2="12" y1="8" y2="12"/>
        <line x1="12" x2="12.01" y1="16" y2="16"/>
      </svg>
    `;
  } else {
    toastIcon.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2ec4b6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="20 6 9 17 4 12"/>
      </svg>
    `;
  }

  // Hide after 4 seconds
  setTimeout(() => {
    toast.classList.remove('show');
  }, 4000);
}

/**
 * Handle Mock Register Link Click
 */
function triggerRegisterFlow(e) {
  e.preventDefault();
  if (currentPortal === 'voter') {
    showToast("Redirecting to Citizen National Registry Database...", "success");
  } else {
    showToast("Opening Official Access Request Ticket Form...", "success");
  }
}

/**
 * Handle Mock Forgot Password Link Click
 */
function triggerForgotFlow(e) {
  e.preventDefault();
  if (currentPortal === 'voter') {
    showToast("Reset instructions sent to registered E-Mail and SMS.", "success");
  } else {
    showToast("Please contact the Chief Election Commissioner's IT desk.", "error");
  }
}

/**
 * Validation and Form Submit Handlers
 */
function handleLoginSubmit(event) {
  event.preventDefault();
  
  const idValue = userInput.value.trim();
  const passwordValue = passwordInput.value;

  // 1. Validation Rules
  if (!idValue) {
    showToast(currentPortal === 'voter' ? "Voter ID cannot be empty." : "Admin Username/Email cannot be empty.");
    return;
  }

  if (!passwordValue) {
    showToast(currentPortal === 'voter' ? "Verification PIN cannot be empty." : "Password cannot be empty.");
    return;
  }

  // Voter ID mock format validation (e.g., standard Alpha-Numeric length)
  if (currentPortal === 'voter' && idValue.length < 5) {
    showToast("Invalid Voter ID format. ID must be at least 5 alphanumeric characters.");
    return;
  }

  // PIN validation (e.g., minimum 4 digits)
  if (currentPortal === 'voter' && passwordValue.length < 4) {
    showToast("Security PIN must be at least 4 digits.");
    return;
  }

  // Admin validation (e.g. email or username validation)
  if (currentPortal === 'admin' && idValue.length < 4) {
    showToast("Invalid Username or Registry Email.");
    return;
  }

  // 2. Perform Authentic Validation & Start Cryptographic Simulation
  submitBtn.classList.add('loading');
  submitBtn.disabled = true;
  userInput.disabled = true;
  passwordInput.disabled = true;

  // Simulate remote security handshake
  setTimeout(() => {
    submitBtn.classList.remove('loading');
    
    // Demo success criteria
    // For demo purposes, we will accept any valid input formatting
    const successTitle = currentPortal === 'voter' ? 'Authorization Successful' : 'Console Decrypted';
    const successMessage = currentPortal === 'voter' 
      ? 'Verifying cryptographic digital ballot ticket... Your identity has been authenticated. Redirecting to ballot room.'
      : 'Access granted. Opening cryptographic ledger dashboard...';

    // Update overlay text
    document.querySelector('.success-title').textContent = successTitle;
    successMsg.textContent = successMessage;
    
    // Show success overlay
    successScreen.classList.add('active');
    
    showToast("Decrypted credentials verified successfully!", "success");
  }, 2000);
}

/**
 * Reset form back to initial state
 */
function resetForm() {
  successScreen.classList.remove('active');
  submitBtn.disabled = false;
  userInput.disabled = false;
  passwordInput.disabled = false;
  userInput.value = '';
  passwordInput.value = '';
  userInput.blur();
  passwordInput.blur();
}
