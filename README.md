# 🤖 Terabot-AI

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://terabot-ai.streamlit.app/)

> An advanced, multi-persona AI chatbot workspace featuring secure out-of-band authentication, multi-tenant data isolation, and persistent conversation management.

**🔗 Live Demo:** [https://terabot-ai.streamlit.app/](https://terabot-ai.streamlit.app/) | **📅 Built:** Summer 2025

---

## 📝 What It Does
**Terabot-AI** is a personal AI chatbot web application built with Streamlit, Firebase, and the OpenAI API. It allows users to create authenticated accounts, manage independent conversation threads, and customize how the AI responds through reusable personas.

Rather than a simple interface over an LLM, the project focuses on the engineering challenges of building a production-style multi-user platform, implementing custom email verification, user-isolated Firestore data structures, dynamic persona management, and a secure multi-stage account deletion process.

---

## 🛠️ Tech Stack
* **Frontend:** `Streamlit` (Python)
* **Auth:** `Firebase Authentication`
* **Database:** `Cloud Firestore` (via `firebase-admin` SDK)
* **AI:** `OpenAI API` (Chat & Moderation)
* **Email:** `Gmail SMTP`
* **Hosting:** `Streamlit Community Cloud`

---

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| **🔐 Email Verification** | Time-sensitive 6-digit codes prevent spam and secure user registration. |
| **💬 Dynamic Workspaces** | Independent chat threads ensure conversation contexts never bleed together. |
| **🎭 Persona Engine** | Create and save reusable AI profiles with custom system instructions. |
| **🔄 Live Hot-Swapping** | Swap personas mid-chat without resetting history or the UI state. |
| **🗑️ Danger Zone** | Secure, authenticated account teardown for full data privacy. |

*(Images: [Verification Workflow](assets/login.png) | [Chat Interface](assets/chat.png) | [Persona Dashboard](assets/persona.png))*

---

## 🧠 What I Learned

* **Mastering the Streamlit Loop:** Since the entire script reruns on every interaction, I learned to effectively use `st.session_state` to track auth, chat history, and persona configs without losing context.
* **Server-Side Security:** By utilizing the `firebase-admin` SDK, I moved the gatekeeping logic to the backend, ensuring Firestore data isolation is enforced by the server rather than just client-side rules.
* **NoSQL Architecture:** Building this required designing a scalable Firestore schema that handles nested user profiles, persona configs, and granular chat histories with zero cross-user visibility.
* **Credential Hygiene:** The project cemented best practices in secret management, ensuring sensitive tokens stay out of the repo and are injected only at runtime.

---

## 🔒 Security & Code Hardening

### Credential Handling
* **Secrets Management:** All API keys and service certificates are injected at runtime via `st.secrets`, never hardcoded.
* **Git Hygiene:** Strict `.gitignore` rules prevent local config files from ever touching the repo.

### Access Control
* **Data Isolation:** All operations are scoped to a server-validated `session_user_id`, preventing any potential data bleeding between users.
* **Usage Caps:** Anonymous guests are capped at 6 messages; authenticated users are governed by a "one-request-at-a-time" semaphore to moderate API usage.

### Input Validation
* **Sanitization:** I use `html.escape()` on all user-submitted fields before rendering them to the UI, effectively neutralizing XSS risks.
* **Moderation:** Persona instructions pass through OpenAI's Moderation API; standard chat messages rely on the model's native safety guardrails.
* **Error Handling:** I am currently refactoring dev-stage exception messages (which currently show raw Python tracebacks) into clean, user-friendly alerts.

---

## 🚀 Future Improvements

- [ ] **Unified Moderation:** Extend OpenAI Moderation to cover live chat messages, not just persona definitions.
- [ ] **Clean Errors:** Replace raw exception tracebacks with standardized, user-facing error messages.
- [ ] **Stricter Validation:** Implement Regex-based filtering for usernames and registration input.
- [ ] **Scalable Throttling:** Introduce per-user request quotas to protect API resources as usage grows.
