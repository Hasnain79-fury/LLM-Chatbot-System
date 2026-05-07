/* ═══════════════════════════════════════════════════════════════════════════
   Chat Page — sidebar, messages, streaming input
   ═══════════════════════════════════════════════════════════════════════════ */

import {
  getMe,
  getConversations,
  getMessages,
  deleteConversation,
  streamMessage,
  clearToken,
} from './api.js';
import { navigate } from './router.js';

const appEl = () => document.getElementById('app');

let currentUser = null;
let conversations = [];
let activeConvId = null;
let isStreaming = false;

// ── Render shell ─────────────────────────────────────────────────────────────

export async function renderChat() {
  // Fetch user info
  try {
    currentUser = await getMe();
  } catch {
    clearToken();
    navigate('#/login');
    return;
  }

  const initials = currentUser.username.slice(0, 2).toUpperCase();

  appEl().innerHTML = `
    <div class="chat-layout">
      <!-- Sidebar overlay (mobile) -->
      <div class="sidebar-overlay" id="sidebar-overlay"></div>

      <!-- Sidebar -->
      <aside class="sidebar" id="sidebar">
        <div class="sidebar-header">
          <button class="btn-new-chat" id="btn-new-chat">
            <span class="icon">＋</span> New Chat
          </button>
        </div>

        <div class="sidebar-conversations" id="conv-list">
          <!-- Populated dynamically -->
        </div>

        <div class="sidebar-footer">
          <div class="user-avatar">${initials}</div>
          <div class="user-info">
            <div class="user-name">${escapeHtml(currentUser.username)}</div>
            <div class="user-email">${escapeHtml(currentUser.email)}</div>
          </div>
          <button class="btn-logout" id="btn-logout" title="Sign out">⏻</button>
        </div>
      </aside>

      <!-- Main -->
      <main class="chat-main">
        <header class="chat-header">
          <button class="btn-sidebar-toggle" id="btn-sidebar-toggle">☰</button>
          <div class="chat-title" id="chat-title">New Chat</div>
        </header>

        <div class="messages-container" id="messages-container">
          <div class="messages-list" id="messages-list">
            <!-- Messages or empty state -->
          </div>
        </div>

        <div class="input-bar">
          <div class="input-bar-inner">
            <textarea
              id="chat-input"
              placeholder="Type a message…"
              rows="1"
            ></textarea>
            <button class="btn-send" id="btn-send" title="Send">▶</button>
          </div>
          <div class="input-hint">Press Enter to send · Shift+Enter for new line</div>
        </div>
      </main>
    </div>
  `;

  bindEvents();
  await loadConversations();
  showEmptyState();
}

// ── Event bindings ───────────────────────────────────────────────────────────

function bindEvents() {
  // New chat
  document.getElementById('btn-new-chat').addEventListener('click', () => {
    activeConvId = null;
    document.getElementById('chat-title').textContent = 'New Chat';
    showEmptyState();
    clearActiveConv();
    closeSidebar();
  });

  // Logout
  document.getElementById('btn-logout').addEventListener('click', () => {
    clearToken();
    navigate('#/login');
  });

  // Send
  document.getElementById('btn-send').addEventListener('click', handleSend);

  // Textarea auto-resize + Enter shortcut
  const textarea = document.getElementById('chat-input');
  textarea.addEventListener('input', autoResize);
  textarea.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  });

  // Mobile sidebar toggle
  document.getElementById('btn-sidebar-toggle').addEventListener('click', toggleSidebar);
  document.getElementById('sidebar-overlay').addEventListener('click', closeSidebar);
}

function autoResize() {
  const el = document.getElementById('chat-input');
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 160) + 'px';
}

// ── Sidebar mobile ───────────────────────────────────────────────────────────

function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
  document.getElementById('sidebar-overlay').classList.toggle('open');
}

function closeSidebar() {
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('sidebar-overlay').classList.remove('open');
}

// ── Conversations ────────────────────────────────────────────────────────────

async function loadConversations() {
  try {
    conversations = await getConversations();
  } catch {
    conversations = [];
  }
  renderConversationList();
}

function renderConversationList() {
  const container = document.getElementById('conv-list');
  if (!conversations.length) {
    container.innerHTML = '';
    return;
  }

  container.innerHTML = conversations
    .map(
      (c) => `
      <div class="conv-item ${c.id === activeConvId ? 'active' : ''}" data-id="${c.id}">
        <span class="conv-icon">💬</span>
        <span class="conv-title">${escapeHtml(c.title)}</span>
        <button class="conv-delete" data-delete-id="${c.id}" title="Delete">🗑</button>
      </div>
    `
    )
    .join('');

  // Click to open
  container.querySelectorAll('.conv-item').forEach((el) => {
    el.addEventListener('click', (e) => {
      if (e.target.closest('.conv-delete')) return;
      const id = Number(el.dataset.id);
      openConversation(id);
      closeSidebar();
    });
  });

  // Delete buttons
  container.querySelectorAll('.conv-delete').forEach((btn) => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const id = Number(btn.dataset.deleteId);
      if (!confirm('Delete this conversation?')) return;
      try {
        await deleteConversation(id);
        if (activeConvId === id) {
          activeConvId = null;
          showEmptyState();
          document.getElementById('chat-title').textContent = 'New Chat';
        }
        await loadConversations();
      } catch (err) {
        alert('Failed to delete: ' + err.message);
      }
    });
  });
}

function clearActiveConv() {
  document.querySelectorAll('.conv-item').forEach((el) => el.classList.remove('active'));
}

async function openConversation(id) {
  activeConvId = id;
  const conv = conversations.find((c) => c.id === id);
  if (conv) {
    document.getElementById('chat-title').textContent = conv.title;
  }

  renderConversationList();

  // Load messages
  try {
    const messages = await getMessages(id);
    renderMessages(messages);
  } catch {
    showEmptyState();
  }
}

// ── Messages rendering ───────────────────────────────────────────────────────

function showEmptyState() {
  document.getElementById('messages-list').innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">✦</div>
      <h2>Start a conversation</h2>
      <p>Send a message below to begin chatting with the AI assistant.</p>
    </div>
  `;
}

function renderMessages(messages) {
  const container = document.getElementById('messages-list');
  if (!messages.length) {
    showEmptyState();
    return;
  }

  container.innerHTML = messages.map((m) => messageHTML(m.role, m.content)).join('');
  scrollToBottom();
}

function messageHTML(role, content) {
  const isUser = role === 'user';
  const avatarText = isUser ? (currentUser?.username?.slice(0, 2).toUpperCase() || 'U') : 'AI';
  const label = isUser ? 'You' : 'Assistant';

  return `
    <div class="message ${role}">
      <div class="message-avatar">${avatarText}</div>
      <div class="message-content">
        <div class="message-role">${label}</div>
        <div class="message-text">${escapeHtml(content)}</div>
      </div>
    </div>
  `;
}

function appendMessage(role, content) {
  // Remove empty state if present
  const emptyState = document.querySelector('.empty-state');
  if (emptyState) emptyState.remove();

  const container = document.getElementById('messages-list');
  container.insertAdjacentHTML('beforeend', messageHTML(role, content));
  scrollToBottom();
}

function appendStreamingMessage() {
  const emptyState = document.querySelector('.empty-state');
  if (emptyState) emptyState.remove();

  const avatarText = 'AI';
  const html = `
    <div class="message assistant" id="streaming-msg">
      <div class="message-avatar">${avatarText}</div>
      <div class="message-content">
        <div class="message-role">Assistant</div>
        <div class="message-text" id="streaming-text">
          <div class="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>
  `;

  document.getElementById('messages-list').insertAdjacentHTML('beforeend', html);
  scrollToBottom();
}

function appendTokenToStream(token) {
  const el = document.getElementById('streaming-text');
  if (!el) return;

  // Remove typing indicator on first token
  const indicator = el.querySelector('.typing-indicator');
  if (indicator) {
    indicator.remove();
  }

  el.textContent += token;
  scrollToBottom();
}

function finalizeStream() {
  const el = document.getElementById('streaming-msg');
  if (el) el.removeAttribute('id');

  const textEl = document.querySelector('#streaming-text');
  if (textEl) textEl.removeAttribute('id');
}

function scrollToBottom() {
  const container = document.getElementById('messages-container');
  if (container) {
    container.scrollTop = container.scrollHeight;
  }
}

// ── Send message ─────────────────────────────────────────────────────────────

async function handleSend() {
  if (isStreaming) return;

  const textarea = document.getElementById('chat-input');
  const message = textarea.value.trim();
  if (!message) return;

  const sendBtn = document.getElementById('btn-send');
  textarea.value = '';
  textarea.style.height = 'auto';
  sendBtn.disabled = true;
  isStreaming = true;

  // Show user message immediately
  appendMessage('user', message);

  // Show streaming placeholder
  appendStreamingMessage();

  try {
    await streamMessage(
      message,
      activeConvId,
      // onToken
      (token) => {
        appendTokenToStream(token);
      },
      // onDone
      () => {
        finalizeStream();
      }
    );

    // After streaming, reload conversations to get the updated list & title
    await loadConversations();

    // If this was a new chat, figure out the conversation ID from the updated list
    if (!activeConvId && conversations.length) {
      // The newest conversation is first (sorted by created_at desc)
      activeConvId = conversations[0].id;
      document.getElementById('chat-title').textContent = conversations[0].title;
      renderConversationList();
    }
  } catch (err) {
    // Remove streaming placeholder and show error
    const streamEl = document.getElementById('streaming-msg');
    if (streamEl) streamEl.remove();

    appendMessage('assistant', `⚠️ Error: ${err.message}`);
  } finally {
    isStreaming = false;
    sendBtn.disabled = false;
    textarea.focus();
  }
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
