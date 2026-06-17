Terabot-AI
Live Link: https://terabot-ai.streamlit.app/

Built: Summer 2025

What It Does
Terabot-AI is a personal AI chatbot web application that allows users to create accounts, manage distinct conversation threads, and customize how the AI responds to them.

The project goes beyond a simple chat interface by implementing a custom out-of-band email verification system for signups, custom data structures to keep users' data separate, a dynamic persona-creation dashboard, and a multi-stage profile deletion workflow.

Tech Stack
Frontend & Framework: Streamlit (Python)

Authentication: Firebase Authentication (coupled with custom HTML verification code delivery)

Database: Cloud Firestore (managed via the backend firebase-admin SDK)

AI Engine: OpenAI API (Chat Completions and Moderation endpoints)

Email Layer: Gmail SMTP (used for formatting and sending dynamic HTML verification templates)

Hosting: Streamlit Community Cloud

Key Features
Gated Verification Pipeline: Protects server compute and prevents dummy accounts by requiring users to enter a time-sensitive 6-digit verification code sent to their email before their account is fully activated.

Smart Dynamic Workspaces: Automatically saves, updates, and structures independent chat histories so users can seamlessly switch between different conversational contexts.

Custom Persona Engine: Includes a dedicated settings area where users can build, store, and edit custom AI profiles (such as text-critics, creative prompts, or technical guides) with distinct background instructions.

On-The-Fly Hot Swapping: Allows users to alternate between active system personas mid-conversation without breaking or losing their existing chat history or UI states.

Atomic Data Deletion: Features a secure "Danger Zone" module that forces account re-authentication before executing a clean wipe of the user's data across Firestore (chat files, metadata logs, codes) and Firebase Auth.

What I Learned Building It
Handling Linear Execution States: Streamlit works by running script code from top to bottom on every user interaction. Learning how to cleanly manage complex async actions—like tracking parallel chat tabs, holding user login states, and capturing custom-persona data across script reruns—required mastering st.session_state.

Backend Security Orchestration: Implementing the firebase-admin Python SDK forced me to learn how a backend programmatically acts as an authority layer, handling authentication keys, formatting verification routines, and isolating database calls safely.

Structured NoSQL Modeling: Mapping multi-user database layouts required building a strict data schema in Firestore to organize user profiles, custom prompt configurations, and granular chat structures efficiently without data overlap.

Technical Reflection & Code Hardening
Credential Handling
Safe Secrets Management: All application credentials (OpenAI secret tokens, Firebase service account keys, Gmail SMTP credentials) are completely separated from the code. Everything is stored and injected at runtime via Streamlit’s native st.secrets manager.

Repository Safety: The codebase uses strict local environment variable boundaries and a configured .gitignore setup, ensuring that local testing credentials or secrets.toml payloads are never accidentally pushed to GitHub.

Access Rules & Permissions
Server-Side Data Isolation: Since the app communicates using a server-side Firebase Admin pattern rather than client-side SDK calls, user security does not rely on open Firestore rules. Instead, the Python backend programmatically wraps database transactions specifically around a validated session_user_id, ensuring it is structurally impossible for User A to fetch or mutate User B's documents.

Rate Limits and Exposure: The application includes a 6-message safety block to cap unauthenticated guest activity and shield compute resources from basic automated script calls. For authenticated accounts, a message frequency framework helps moderate usage, alongside an active 1,000-character input boundary per request.

Input Validation & Safety Gaps
XSS Defenses: The app applies html.escape() sanitization across user fields (such as text prompts, custom assistant titles, and profile metadata) before displaying them inside any markdown blocks allowing raw HTML code execution (unsafe_allow_html=True). This mitigates common cross-site scripting risks.

Asymmetric Content Safety: The persona creation dashboard integrates OpenAI's moderation endpoints to check prompt instructions before adding them to the database. However, regular, live chat prompts do not loop through this extra endpoint layer, meaning the chat window relies strictly on the underlying model's default safety guardrails.

Error Handling Information Leakage: Some catch blocks output raw Python exceptions straight onto the dashboard screen (st.error(f"... failed: {e}")). While this is convenient for quick local testing and validation, it represents a minor security exposure that should be refactored to show friendly, generic alerts while logging detailed errors server-side.

Next Steps
Unify Prompt Moderation: Route real-time chat text through the moderation API block to align the core interface with the standard used in the persona-creation module.

Abstract Exception Interfaces: Refactor user-facing error logs to display clean, generic messages while preserving technical stack details exclusively for backend tracing.

Regex Registration Boundaries: Implement rigid character checks across username components to handle structural clean-up before variables arrive at database management functions.
