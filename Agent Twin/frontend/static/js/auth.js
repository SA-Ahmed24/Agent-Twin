// Authentication JavaScript

// Use relative URL to avoid CORS issues
// Store in window to avoid redeclaration errors when multiple scripts load
if (typeof window.API_BASE === 'undefined') {
    window.API_BASE = '/api';
}
// Don't create a local const - just use window.API_BASE throughout

// Login form handler
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const errorDiv = document.getElementById('errorMessage');
        
        try {
            const response = await fetch(`${window.API_BASE}/auth/login/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({ username, password })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                // Check if onboarding is needed
                if (!data.onboarding_completed) {
                    window.location.href = '/onboarding/';
                } else {
                    window.location.href = '/';
                }
            } else {
                errorDiv.textContent = data.error || 'Login failed';
                errorDiv.classList.add('show');
            }
        } catch (error) {
            console.error('Login error:', error);
            errorDiv.textContent = `Error: ${error.message}. Make sure the server is running at ${window.location.origin}`;
            errorDiv.classList.add('show');
        }
    });
}

// Signup form handler
const signupForm = document.getElementById('signupForm');
if (signupForm) {
    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        const errorDiv = document.getElementById('errorMessage');
        
        // Validate passwords match
        if (password !== confirmPassword) {
            errorDiv.textContent = 'Passwords do not match';
            errorDiv.classList.add('show');
            return;
        }
        
        try {
            const response = await fetch(`${window.API_BASE}/auth/signup/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({ username, email, password })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                // Redirect to onboarding
                window.location.href = '/onboarding/';
            } else {
                errorDiv.textContent = data.error || 'Signup failed';
                errorDiv.classList.add('show');
            }
        } catch (error) {
            console.error('Signup error:', error);
            errorDiv.textContent = `Error: ${error.message}. Make sure the server is running at ${window.location.origin}`;
            errorDiv.classList.add('show');
        }
    });
}

// Check if user is authenticated on page load
async function checkAuth() {
    try {
        const response = await fetch(`${window.API_BASE}/auth/user/`, {
            credentials: 'include'
        });
        
        // If request fails, assume not authenticated
        if (!response.ok) {
            throw new Error('Not authenticated');
        }
        
        const data = await response.json();
        
        if (data.authenticated) {
            // User is logged in
            if (window.location.pathname === '/login/' || window.location.pathname === '/signup/') {
                // Redirect to main page if already logged in
                window.location.href = '/';
            }
        } else {
            // User is not logged in
            if (window.location.pathname !== '/login/' && window.location.pathname !== '/signup/' && window.location.pathname !== '/onboarding/') {
                // Redirect to login if not on auth pages
                window.location.href = '/login/';
            }
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        // If on a protected page and auth fails, redirect to login
        if (window.location.pathname !== '/login/' && window.location.pathname !== '/signup/' && window.location.pathname !== '/onboarding/') {
            window.location.href = '/login/';
        }
    }
}

// Run auth check on pages that need it (but not on chat page - it handles its own auth)
if (window.location.pathname !== '/login/' && window.location.pathname !== '/signup/' && window.location.pathname !== '/') {
    checkAuth();
}

