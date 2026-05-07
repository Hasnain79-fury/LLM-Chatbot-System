/* ═══════════════════════════════════════════════════════════════════════════
   Auth Pages — Login & Signup
   ═══════════════════════════════════════════════════════════════════════════ */

import { signup, login } from './api.js';
import { navigate } from './router.js';

const app = () => document.getElementById('app');

// ── Login ────────────────────────────────────────────────────────────────────

export function renderLogin() {
  app().innerHTML = `
    <div class="auth-page">
      <div class="auth-card">
        <h1>Welcome Back</h1>
        <p class="subtitle">Sign in to continue chatting</p>

        <div id="auth-error"></div>

        <form id="login-form" autocomplete="on">
          <div class="form-group">
            <label for="login-email">Email</label>
            <input
              type="email" id="login-email" name="email"
              placeholder="you@example.com" required autocomplete="email"
            />
          </div>

          <div class="form-group">
            <label for="login-password">Password</label>
            <input
              type="password" id="login-password" name="password"
              placeholder="••••••••" required autocomplete="current-password"
            />
          </div>

          <button type="submit" class="btn-primary" id="login-btn">Sign In</button>
        </form>

        <p class="auth-footer">
          Don't have an account? <a href="#/signup">Sign up</a>
        </p>
      </div>
    </div>
  `;

  document.getElementById('login-form').addEventListener('submit', handleLogin);
}

async function handleLogin(e) {
  e.preventDefault();
  const errEl = document.getElementById('auth-error');
  const btn = document.getElementById('login-btn');
  errEl.innerHTML = '';

  const email = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value;

  if (!email || !password) {
    errEl.innerHTML = '<div class="auth-error">Please fill in all fields.</div>';
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Signing in…';

  try {
    await login(email, password);
    navigate('#/chat');
  } catch (err) {
    errEl.innerHTML = `<div class="auth-error">${escapeHtml(err.message)}</div>`;
    btn.disabled = false;
    btn.textContent = 'Sign In';
  }
}

// ── Signup ────────────────────────────────────────────────────────────────────

export function renderSignup() {
  app().innerHTML = `
    <div class="auth-page">
      <div class="auth-card">
        <h1>Create Account</h1>
        <p class="subtitle">Start chatting with AI in seconds</p>

        <div id="auth-error"></div>

        <form id="signup-form" autocomplete="on">
          <div class="form-group">
            <label for="signup-email">Email</label>
            <input
              type="email" id="signup-email" name="email"
              placeholder="you@example.com" required autocomplete="email"
            />
          </div>

          <div class="form-group">
            <label for="signup-username">Username</label>
            <input
              type="text" id="signup-username" name="username"
              placeholder="cooluser42" required autocomplete="username"
            />
          </div>

          <div class="form-group">
            <label for="signup-password">Password</label>
            <input
              type="password" id="signup-password" name="password"
              placeholder="••••••••" required autocomplete="new-password"
              minlength="6"
            />
          </div>

          <button type="submit" class="btn-primary" id="signup-btn">Create Account</button>
        </form>

        <p class="auth-footer">
          Already have an account? <a href="#/login">Sign in</a>
        </p>
      </div>
    </div>
  `;

  document.getElementById('signup-form').addEventListener('submit', handleSignup);
}

async function handleSignup(e) {
  e.preventDefault();
  const errEl = document.getElementById('auth-error');
  const btn = document.getElementById('signup-btn');
  errEl.innerHTML = '';

  const email = document.getElementById('signup-email').value.trim();
  const username = document.getElementById('signup-username').value.trim();
  const password = document.getElementById('signup-password').value;

  if (!email || !username || !password) {
    errEl.innerHTML = '<div class="auth-error">Please fill in all fields.</div>';
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Creating account…';

  try {
    await signup(email, username, password);
    // Auto-login after signup
    await login(email, password);
    navigate('#/chat');
  } catch (err) {
    errEl.innerHTML = `<div class="auth-error">${escapeHtml(err.message)}</div>`;
    btn.disabled = false;
    btn.textContent = 'Create Account';
  }
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
