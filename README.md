# 🤖 Terabot-AI

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://terabot-ai.streamlit.app/)

> A sleek, multi-persona AI chatbot workspace featuring secure out-of-band authentication, multi-tenant state separation, and dynamic conversation tracking.

**🔗 Live Link:** [https://terabot-ai.streamlit.app/](https://terabot-ai.streamlit.app/)  
**📅 Built:** Summer 2025

---

## 📝 What It Does

**Terabot-AI** is a personal AI chatbot web app where users can create an account, manage different conversation threads, and fully customize how the AI responds to them. 

Instead of just building a simple API wrapper, I wanted to push this project further. It handles the full user journey: signups gated by a custom email verification pipeline, strict data structures to keep different users' chat histories completely locked down, an interactive backend persona builder, and a secure multi-stage account purge.

---

## 🛠️ Tech Stack

* **Frontend & Framework:** `Streamlit` (Python)
* **Authentication:** `Firebase Authentication` (handled via backend workflows)
* **Database & Storage:** `Cloud Firestore` (managed via the `firebase-admin` Python SDK)
* **AI Core:** `OpenAI API` (using Chat Completions and Moderation endpoints)
* **Email Delivery:** `Gmail SMTP` (for formatting and sending dynamic HTML verification templates)
* **Hosting Platform:** `Streamlit Community Cloud`

---

## ✨ Key Features

* **Gated Verification Pipeline:** Keeps the app secure and stops spam signups by requiring users to input a time-sensitive, 6-digit verification pin sent straight to their inbox before they can use their account.
* **Smart Dynamic Workspaces:** Saves and organizes independent chat histories on the fly, making it easy to swap back and forth between completely different conversation topics.
* **Custom Persona Engine:** A dedicated workspace tab where users can build, store, and edit custom AI profiles (like a code helper, a writing critic, or a casual friend) using specific system instructions.
* **On-The-Fly Hot Swapping:** Users can switch the AI's persona right in the middle of a chat without breaking the conversation layout, wiping the history, or disrupting the active UI state.
* **Atomic Data Deletion:** A secure "Danger Zone" module that forces users to re-enter their password before completely wiping their footprint across Firestore (chats, configurations, access codes) and Firebase Auth.

---

## 🧠 What I Learned Building It

* **Battling Linear Execution Flows:** Streamlit re-runs your entire script from top to bottom every single time a user clicks a button or types text. Figuring out how to handle async-style logic—like maintaining separate chat tabs, keeping users logged in, and saving persona configurations across script re-runs—really forced me to master `st.session_state`.
* **Backend Security & SDKs:** Working with the `firebase-admin` SDK taught me how a backend actually acts as the gatekeeper. I had to learn how to securely handle service account keys, structure verification routines, and keep database queries secure.
* **Structured NoSQL Modeling:** Since everything is stored in Firestore, I had to map out a clean data schema to keep user metadata, custom system prompt templates, and deeply nested chat threads organized without any risk of data overlapping between accounts.

---

## 🔒 Technical Reflection & Code Hardening

### Credential Handling
* **Safe Secrets Management:** Every single API key and token (OpenAI keys, Firebase service certificates, Gmail SMTP passwords) is completely separated from the code. They are stored safely and injected at runtime using Streamlit’s native `st.secrets` vault.
* **Repository Safety:** The repo uses strict local environment rules and a solid `.gitignore` setup, making sure local testing files or `secrets.toml` payloads are never accidentally pushed to GitHub history.

### Access Rules & Permissions
* **Server-Side Data Isolation:** Because the app uses the server-side Firebase Admin SDK instead of client-side queries, security doesn't rely on loose database rules. The Python backend programmatically locks every single read/write path to a validated `session_user_id`. It is structurally impossible for User A to fetch or change User B's files.
* **Rate Limits and Cost Exposure:** The app includes a 6-message ceiling to limit anonymous guest traffic and protect my OpenAI credit limits from bots. Logged-in profiles have a message frequency framework to moderate usage, along with an active 1,000-character input cap per prompt.

### Input Validation & Safety Gaps
* **XSS Defenses:** The code applies `html.escape()` sanitization universally across user fields (like prompt boxes, username updates, and persona titles) before displaying them inside any markdown blocks that allow HTML formatting (`unsafe_allow_html=True`). This cuts off cross-site scripting risks.
* **Asymmetric Content Safety:** The persona creator runs custom background instructions through OpenAI's moderation endpoint before saving them to the database. However, regular live chat messages don't pass through this extra filter, meaning the main chat box relies entirely on the underlying model's built-in guardrails.
* **Error Handling Leaks:** A few catch blocks stream raw Python exceptions straight onto the UI (`st.error(f"... failed: {e}")`). While this made debugging a lot faster during development, it can leak technical backend traces to the front end and should be refactored to show clean, friendly error messages instead.

---

## 🚀 Next Steps

* [ ] **Unify Prompt Moderation:** Route real-time chat text through the moderation API block to align the core interface with the standard used in the persona-creation module.
* [ ] **Abstract Exception Interfaces:** Refactor user-facing error logs to display clean, generic messages while preserving technical stack details exclusively for backend tracing.
* [ ] **Regex Registration Boundaries:** Implement rigid character checks across username components to handle structural clean-up before variables arrive at database management functions.
