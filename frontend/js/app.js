/* ═══════════════════════════════════════════════════════════════════════════
   App Entry Point — initializes router, guards routes
   ═══════════════════════════════════════════════════════════════════════════ */

import { isLoggedIn } from './api.js';
import { registerRoute, navigate, startRouter, currentRoute } from './router.js';
import { renderLogin, renderSignup } from './auth.js';
import { renderChat } from './chat.js';

// ── Route definitions ────────────────────────────────────────────────────────

registerRoute('#/login', () => {
  if (isLoggedIn()) return navigate('#/chat');
  renderLogin();
});

registerRoute('#/signup', () => {
  if (isLoggedIn()) return navigate('#/chat');
  renderSignup();
});

registerRoute('#/chat', () => {
  if (!isLoggedIn()) return navigate('#/login');
  renderChat();
});

// ── Boot ─────────────────────────────────────────────────────────────────────

// If no hash set and user is logged in, go straight to chat
if (!window.location.hash) {
  window.location.hash = isLoggedIn() ? '#/chat' : '#/login';
}

startRouter();
