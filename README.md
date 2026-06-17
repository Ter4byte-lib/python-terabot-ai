# Terabot-AI

A personal AI chatbot web app built to handle the real-world engineering challenges of a multi-user platform—like secure auth, data isolation, and persistent session states.

**🔗 Live Demo:** https://terabot-ai.streamlit.app/  
**📅 Built:** Summer 2025

---

## What It Does

Instead of just building another basic wrapper around an LLM API, I wanted to focus on what it takes to build a secure, production-style platform for multiple users. 

**Terabot-AI** lets users sign up, verify their emails, manage completely independent chat threads, and build their own custom AI personas. Under the hood, it handles the messy stuff: a custom out-of-band email verification system, isolated user data in Firestore, dynamic chat contexts, and a multi-stage account deletion process.

---

## Tech Stack

* **Frontend & Framework:** Streamlit (Python)
* **Authentication:** Firebase Authentication
* **Database & Storage:** Cloud Firestore
* **Backend SDK:** firebase-admin
* **AI Integration:** OpenAI API (Chat Completions & Moderation)
* **Email Delivery:** Gmail SMTP
* **Hosting:** Streamlit Community Cloud

---

## Features

### 🔐 Email Verification
<p align="center">
  <img src="assets/login.png" width="700"/>
</p>
To keep spam down and protect my API keys, new accounts have to enter a time-sensitive, 6-digit verification code sent to their email before they can log in.

### 💬 Multi-Thread Workspaces
<p align="center">
  <img src="assets/chat.png" width="700"/>
</p>
Users can run multiple independent chat threads at the same time. The app keeps the conversations completely separate so contexts never get mixed up.

### 🎭 Custom AI Personas
<p align="center">
  <img src="assets/persona.png" width="700"/>
</p>
Users can create and save reusable personas by writing custom system instructions (like a dedicated coding assistant or a harsh writing critic). 

### 🔄 On-the-Fly Persona Switching
You can swap personas right in the middle of a live chat thread without wiping the page, clearing the history, or breaking the current session state.

### 🗑️ The Danger Zone (Account Deletion)
To prevent accidental clicks, deleting an account requires the user to type out an explicit text confirmation before the app wipes their auth records and Firestore data for good.

---

## Security & Technical Choices

### Handling Credentials
* **Secrets Management:** Sensitive stuff like OpenAI keys, Firebase credentials, and SMTP passwords are completely kept out of the codebase. Everything is injected at runtime using Streamlit's `st.secrets` manager.
* **Git Practices:** A strict `.gitignore` setup ensures no local config files or API keys ever accidentally get pushed to GitHub.

### Access Control & Data Isolation
* **Server-Side Security:** I used the `firebase-admin` SDK strictly on the backend rather than exposing database controls to the client side. Every single database query is locked to the active `session_user_id` so users can only ever see their own data.
* **Rate Limiting & Abuse Prevention:** Unregistered guest accounts are cut off after 6 messages. To prevent users from spamming the API, authenticated users are limited to one active prompt at a time; hitting enter while the AI is still generating will trigger a simple "please wait" block.

### Input Validation
* **XSS Protection:** Because I use `unsafe_allow_html=True` to render Markdown cleanly, I pass user inputs (usernames, persona titles, and prompts) through `html.escape()` first to stop cross-site scripting.
* **Safety Filters:** Custom system instructions are automatically screened through OpenAI’s Moderation API before they get saved to the database. 

---

## What I Learned (The Hard Way)

### Taming Streamlit's Execution Model
Streamlit reruns the *entire* Python script from top to bottom every single time a user clicks a button or types a message. This drove me crazy at first. I had to learn how to heavily rely on `st.session_state` to make sure authentication states, chat logs, and active personas didn't instantly wipe themselves on a page refresh.

### Backend vs. Client Auth
Working with the `firebase-admin` SDK taught me how to use a backend administrative layer to securely handle tasks like generating verification codes and deleting user data without exposing administrative privileges to the frontend.

### NoSQL Data Modeling
Designing the Firestore structure was a great lesson in NoSQL design. I had to map out a nested structure (`users -> conversations -> messages`) that allowed for fast queries while ensuring complete data isolation between accounts.

---

## What's Next

- [ ] Run live chat messages through the OpenAI Moderation API for consistent content filtering.
- [ ] Swap out raw Python error messages (`st.error(f"... failed: {e}")`) with clean user-facing alerts and proper backend logging.
- [ ] Add strict regex validation for usernames to stop weird characters from breaking database entries.
- [ ] Implement actual per-user request quotas to protect API costs as usage grows.
- [ ] Write automated tests for the login, verification, and deletion lifecycles.
