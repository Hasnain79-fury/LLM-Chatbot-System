/* ═══════════════════════════════════════════════════════════════════════════
   API Client — handles all backend communication
   ═══════════════════════════════════════════════════════════════════════════ */

const API_BASE = 'http://localhost:8000';

// ── Token helpers ────────────────────────────────────────────────────────────

export function getToken() {
  return localStorage.getItem('token');
}

export function setToken(token) {
  localStorage.setItem('token', token);
}

export function clearToken() {
  localStorage.removeItem('token');
}

export function isLoggedIn() {
  return !!getToken();
}

// ── Generic fetch wrapper ────────────────────────────────────────────────────

async function apiFetch(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };

  const token = getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore parse error
    }
    throw new Error(detail);
  }

  // 204 No Content
  if (res.status === 204) return null;
  return res.json();
}

// ── Auth ─────────────────────────────────────────────────────────────────────

export async function signup(email, username, password) {
  return apiFetch('/auth/signup', {
    method: 'POST',
    body: JSON.stringify({ email, username, password }),
  });
}

export async function login(email, password) {
  const data = await apiFetch('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  setToken(data.access_token);
  return data;
}

export async function getMe() {
  return apiFetch('/auth/me');
}

// ── Conversations ────────────────────────────────────────────────────────────

export async function getConversations() {
  return apiFetch('/conversations');
}

export async function getMessages(conversationId) {
  return apiFetch(`/conversations/${conversationId}/messages`);
}

export async function deleteConversation(conversationId) {
  return apiFetch(`/conversations/${conversationId}`, { method: 'DELETE' });
}

// ── Chat (non-streaming) ────────────────────────────────────────────────────

export async function sendMessage(message, conversationId = null) {
  const body = { message };
  if (conversationId) body.conversation_id = conversationId;

  return apiFetch('/chat', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

// ── Chat (streaming) ────────────────────────────────────────────────────────

export async function streamMessage(message, conversationId, onToken, onDone) {
  const body = { message };
  if (conversationId) body.conversation_id = conversationId;

  const token = getToken();
  const res = await fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const errBody = await res.json();
      detail = errBody.detail || detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });
    onToken(chunk);
  }

  if (onDone) onDone();
}
