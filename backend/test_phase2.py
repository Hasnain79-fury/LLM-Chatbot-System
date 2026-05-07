#!/usr/bin/env python3
"""
Phase 2 integration test — run this while the server is up.

Usage:
    python test_phase2.py

Requires the server to be running:
    uvicorn app.main:app --reload

And Ollama to be running:
    ollama serve
"""
import sys
import requests

BASE = "http://localhost:8000"
TEST_EMAIL = "phase2test@example.com"
TEST_PASSWORD = "testpassword123"
TEST_USERNAME = "phase2user"


def banner(title: str):
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print('─' * 50)


def ok(msg): print(f"  ✅ {msg}")
def fail(msg): print(f"  ❌ {msg}"); sys.exit(1)
def info(msg): print(f"  ℹ  {msg}")


# ── 1. Ollama health ──────────────────────────────────────────────────────────
banner("1. Ollama health check")
r = requests.get(f"{BASE}/health/llm")
data = r.json()
info(data["message"])
if not data["healthy"]:
    fail("Ollama is not healthy — start it with: ollama serve && ollama pull mistral")
ok("Ollama reachable and model loaded")


# ── 2. Signup ─────────────────────────────────────────────────────────────────
banner("2. Signup")
r = requests.post(f"{BASE}/auth/signup", json={
    "email": TEST_EMAIL, "username": TEST_USERNAME, "password": TEST_PASSWORD
})
if r.status_code == 400 and "already" in r.text:
    info("User already exists — skipping signup")
elif r.status_code == 201:
    ok(f"Signed up as {TEST_USERNAME}")
else:
    fail(f"Signup failed: {r.status_code} {r.text}")


# ── 3. Login ──────────────────────────────────────────────────────────────────
banner("3. Login")
r = requests.post(f"{BASE}/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
assert r.status_code == 200, fail(f"Login failed: {r.text}")
token = r.json()["access_token"]
ok("Logged in, JWT received")
headers = {"Authorization": f"Bearer {token}"}


# ── 4. First message (new conversation) ───────────────────────────────────────
banner("4. First message → new conversation")
r = requests.post(f"{BASE}/chat", json={"message": "Hello! What is 2 + 2?"}, headers=headers)
if r.status_code == 503:
    fail(f"Ollama unavailable: {r.json()['detail']}")
assert r.status_code == 200, fail(f"Chat failed: {r.status_code} {r.text}")
data = r.json()
conv_id = data["conversation_id"]
ai_reply = data["ai_message"]["content"]
ok(f"New conversation created: id={conv_id}")
info(f"AI reply: {ai_reply[:120]}{'…' if len(ai_reply) > 120 else ''}")


# ── 5. Follow-up message (same conversation = context test) ───────────────────
banner("5. Follow-up message (context test)")
r = requests.post(f"{BASE}/chat",
    json={"conversation_id": conv_id, "message": "What did I just ask you?"},
    headers=headers)
assert r.status_code == 200, fail(f"Follow-up failed: {r.text}")
data = r.json()
reply2 = data["ai_message"]["content"]
ok("Follow-up received")
info(f"AI reply: {reply2[:120]}{'…' if len(reply2) > 120 else ''}")


# ── 6. Conversation history ────────────────────────────────────────────────────
banner("6. Conversation history")
r = requests.get(f"{BASE}/conversations/{conv_id}/messages", headers=headers)
assert r.status_code == 200, fail(f"History failed: {r.text}")
msgs = r.json()
assert len(msgs) == 4, fail(f"Expected 4 messages, got {len(msgs)}")
roles = [m["role"] for m in msgs]
assert roles == ["user", "assistant", "user", "assistant"], fail(f"Unexpected roles: {roles}")
ok(f"History correct: {len(msgs)} messages, roles alternating user/assistant")


# ── 7. Streaming endpoint ─────────────────────────────────────────────────────
banner("7. Streaming endpoint")
r = requests.post(f"{BASE}/chat/stream",
    json={"message": "Count from 1 to 5."},
    headers=headers,
    stream=True)
assert r.status_code == 200, fail(f"Stream failed: {r.status_code} {r.text}")
tokens = []
for chunk in r.iter_content(chunk_size=None):
    tokens.append(chunk.decode())
full = "".join(tokens)
ok(f"Stream received {len(tokens)} chunks")
info(f"Full response: {full[:120]}{'…' if len(full) > 120 else ''}")


# ── 8. 404 on wrong conversation ──────────────────────────────────────────────
banner("8. Security: wrong conversation_id")
r = requests.post(f"{BASE}/chat", json={"conversation_id": 99999, "message": "hi"}, headers=headers)
assert r.status_code == 404, fail(f"Expected 404, got {r.status_code}")
ok("Correctly returned 404 for another user's conversation")


# ── Done ──────────────────────────────────────────────────────────────────────
banner("ALL PHASE 2 TESTS PASSED ✅")
print()
