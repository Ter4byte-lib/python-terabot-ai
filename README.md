# 🤖 Terabot-AI

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://terabot-ai.streamlit.app/)

> An advanced, multi-persona AI chatbot workspace featuring secure out-of-band authentication, multi-tenant state separation, and dynamic conversation tracking.

**🔗 Live Link:** [https://terabot-ai.streamlit.app/](https://terabot-ai.streamlit.app/)  
**📅 Built:** Summer 2025

---

## 📝 What It Does

Terabot-AI is a personal AI chatbot web application, built with Streamlit, Firebase, and the OpenAI API. It allows users to create authenticated accounts, manage distinct conversation threads, and fully customize how the AI assistant responds to them.

The project goes beyond a simple chat wrapper by implementing a custom out-of-band email verification system for signups, complex NoSQL data architectures to keep user profiles completely separated, an interactive persona-creation suite, and an atomic multi-stage profile deletion workflow.

---

## 🛠️ Tech Stack

* **Frontend & Framework:** `Streamlit` (Python)
* **Authentication:** `Firebase Authentication` (integrated via server-side workflows)
* **Database & Storage:** `Cloud Firestore` (managed via the backend `firebase-admin` SDK)
* **AI Core:** `OpenAI API` (Chat Completions and Moderation endpoints)
* **Email Layer:** `Gmail SMTP` (used for formatting and dispatching dynamic HTML verification templates)
* **Hosting Platform:** `Streamlit Community Cloud`

---

## ✨ Key Features

* **Gated Verification Pipeline:** Protects server compute allocations and blocks dummy registrations by requiring users to enter a time-sensitive, 6-digit verification pin sent directly to their email before their profile is activated.
* **Smart Dynamic Workspaces:** Seamlessly saves, index-maps, and isolates separate chat histories so users can branch off and alternate between entirely different conversational contexts.
* **Custom Persona Engine:** Includes a dedicated configurations tab where users can design, store, and edit custom AI profiles (such as code advisors, creative writing critics, or technical mentors) running specialized background instruction sets.
* **On-The-Fly Hot Swapping:** Allows users to alternate backend system personas mid-conversation without breaking, flushing, or disrupting their active UI session state or chat history.
* **Atomic Data Deletion:** Features a secure "Danger Zone" block that requires credential re-authentication before triggering a comprehensive backend wipe of the user's data across Firestore (chats, configurations, access codes) and Firebase Auth.

---

## 🧠 What I Learned Building It

* **Handling Linear Execution States:** Streamlit works by running script code from top to bottom on every user interaction. Learning how to cleanly manage asynchronous state mechanics—like tracking independent chat tabs, keeping session authentication states active, and carrying persona variables across script reruns—required mastering `st.session_state`.
* **Backend Security Orchestration:** Implementing the `firebase-admin` Python SDK taught me how a backend acts as an explicit authority layer, safely handling administrative API authentication keys, generating secure verification codes, and isolating database calls.
* **Structured NoSQL Modeling:** Mapping a multi-user environment required building a scalable data schema in Firestore to organize user documents, nested persona parameters, and granular message objects without risk of data overlap.

---

## 🔒 Technical Reflection & Code Hardening

### Credential Handling
* **Safe Secrets Management:** All application credentials (OpenAI tokens, Firebase service accounts, Gmail SMTP passwords) are completely decoupled from the repository code. Values are stored and securely injected at runtime via Streamlit’s native `st.secrets` cloud vault.
* **Repository Safety:** The project enforces strict environmental boundaries alongside an active `.gitignore` setup, ensuring that local testing credentials or `secrets.toml` payloads are never accidentally staged or committed to GitHub history.

### Access Rules & Permissions
* **Server-Side Data Isolation:** Because the application connects using a server-side Firebase Admin pattern rather than open client-side SDK entries, security does not rely on permissive Firestore rules. Instead, the Python backend programmatically filters all read/write paths strictly around a validated `session_user_id`, rendering it structurally impossible for an account to query or change another user's documents.
* **Rate Limits and Exposure:** The application executes a 6-message safety block to cap anonymous guest actions and shield runtime compute pools from bot scraping. For verified profiles, a custom request frequency boundary works to moderate server usage, alongside an active 1,000-character input limitation per submission.

### Input Validation & Safety Gaps
* **XSS Defenses:** The app applies `html.escape()` sanitization universally across user fields (such as text boxes, custom persona titles, and usernames) before displaying them inside markdown blocks that allow raw HTML formatting (`unsafe_allow_html=True`). This mitigates common cross-site scripting risks.
* **Asymmetric Content Safety:** The persona creation panel integrates OpenAI's moderation endpoints to check prompt instructions before adding them to the database. However, regular, live chat prompts do not loop through this extra endpoint layer, meaning the chat window relies strictly on the underlying model's default safety guardrails.
* **Error Handling Information Leakage:** Some catch blocks output raw Python exceptions straight onto the dashboard screen (`st.error(f"... failed: {e}")`). While this is convenient for quick local testing and validation, it represents a minor security exposure that should be refactored to show friendly, generic alerts while logging detailed errors server-side.

---

## 🚀 Next Steps

* [ ] **Unify Prompt Moderation:** Route real-time chat text through the moderation API block to align the core interface with the standard used in the persona-creation module.
* [ ] **Abstract Exception Interfaces:** Refactor user-facing error logs to display clean, generic messages while preserving technical stack details exclusively for backend tracing.
* [ ] **Regex Registration Boundaries:** Implement rigid character checks across username components to handle structural clean-up before variables arrive at database management functions.
