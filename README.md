# Terabot README Revisit
**Link:** https://terabot-ai.streamlit.app/
**Original built:** during 2025 summer holiday
---
## What It Does
Terabot is a personal AI chatbot, similar in spirit to ChatGPT, built with Streamlit on 
the frontend, Firebase for auth and data, and the OpenAI API powering the actual 
conversation. Users sign up with email verification, log in, and chat with the 
assistant. Authenticated users get access to a settings area where they can create and 
save custom "personas" (named instruction sets that change how the assistant behaves), 
manage account info, and fully delete their account.
---
## Tech Stack
- **Frontend/app framework:** Streamlit
- **Auth:** Firebase Authentication — email/password signup with email verification 
  (6-digit code sent to the user's inbox), login, and a forgot-password/reset flow
- **Database:** Firestore — storing per-user data (saved personas, account settings)
- **AI:** OpenAI API
- **Hosting:** Streamlit Community Cloud (based on the .streamlit.app domain)
---
## Features
- Email/password sign-up gated behind email verification before the account is usable
- Login, forgot password, and reset password flows
- Core chat interface with the AI assistant
- "Customize Your AI Assistant" settings — create, save, and switch between multiple 
  custom personas, each with its own instructions
- Account settings page (view account info, change password)
- "Danger Zone" — full account deletion, which requires re-entering your password to confirm
---
## What I Learned Building It
TODO — this one's genuinely yours to answer, I can see what the app does but not what 
building it actually felt like. A couple of things worth reflecting on, given what's 
visible: you clearly worked through Firebase's email verification flow and per-user 
Firestore data modeling (the saved-persona feature implies structured per-user 
documents) — was that the part that took the longest, or was it something else 
entirely? What would you genuinely do differently if you started it today?
---
## Revisiting It with a Security Lens
These are not praise questions. They're hard reflection prompts. Answer honestly.

### Credential Handling
- **Where do API keys/secrets live in this code?** Not visible from the recordings 
  since they only show the running app, not the source. Check your actual repo: search 
  for any hardcoded `sk-` prefixed strings or Firebase config objects, and check whether 
  a `.env` or `secrets.toml` file was ever committed (even once, even if later removed — 
  check git history, not just the current state).
- **If someone cloned this repo, could they accidentally commit secrets?** Confirm 
  there's a `.gitignore` entry for your secrets file specifically, not just a general one.
- **If this deployed to production, how would you inject credentials securely?** Since 
  it's already on Streamlit Community Cloud, the standard answer is Streamlit's built-in 
  Secrets manager (`st.secrets`) rather than anything committed to the repo — confirm 
  that's actually what you're using.

### Access Rules & Permissions
- **Who can access this app right now?** From the recordings, there's no visible guest 
  or anonymous mode — chat appears gated behind verified login, which is the right 
  default. Confirm there's no way to reach the chat endpoint without authenticating.
- **Should there be rate limiting?** No rate limiting is visible in the UI, and since 
  every chat message is an OpenAI API call you're paying for, an authenticated user (or 
  a compromised account) sending requests in a tight loop is a real cost-exposure risk 
  worth checking for.
- **If users can save state, can user A see user B's data?** The persona-saving feature 
  means per-user Firestore documents exist. This is the one to check most carefully: 
  open your Firestore Rules tab and confirm reads/writes are scoped to `request.auth.uid 
  == resource.data.uid` (or equivalent) rather than left on permissive default rules.

### Input Validation
- **What user inputs does this app accept?** Free-text chat messages, and free-text 
  persona/instruction fields.
- **What happens if someone sends malicious input?** Since personas let a user define 
  instruction-like text that presumably gets fed toward the model's behavior, this is 
  worth testing specifically for prompt injection — could a crafted persona get the 
  assistant to ignore other constraints you've set elsewhere in the app?
- **Are you sanitizing or validating inputs before passing them to the AI/API?** Not 
  observable from the UI. Check whether there's any length cap or sanitization on chat 
  messages and persona text before they reach the OpenAI call.
---
## Next Steps
- Confirm no API keys or Firebase config are hardcoded or sitting anywhere in git 
  history; move to Streamlit secrets if not already there
- Review and tighten Firestore security rules so users can only read/write their own documents
- Add basic rate limiting per user to control OpenAI API cost exposure
- Add input length limits/sanitization on chat messages and persona instructions
- Decide and document what account deletion actually wipes — does it clear Firestore 
  documents tied to that user, or just the Firebase Auth record?
