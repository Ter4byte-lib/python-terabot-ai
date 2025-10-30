import streamlit as st
import time
import random
import pyrebase
from firebase_admin import initialize_app, firestore, credentials, auth
import firebase_admin
from openai import OpenAI
import smtplib
from datetime import datetime, timedelta
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import html
from email_validator import validate_email, EmailNotValidError


# =============================================================================
# SECURITY & UTILITIES
# =============================================================================

def sanitize_input(user_input):
    if not user_input:
        return ""
    return html.escape(user_input.strip())


def sanitize_for_display(text):
    if not text:
        return ""
    return html.escape(str(text))


def clean_chat_for_storage(chat_history):
    return [
        {"role": msg["role"], "content": msg["content"]}
        for msg in chat_history
        if msg.get("content") != "PENDING"
    ]


# =============================================================================
# FIREBASE INITIALIZATION
# =============================================================================

def get_db():
    if not firebase_admin._apps:
        try:
            firebase_config_dict = dict(st.secrets["firebase"])
            creds = credentials.Certificate(firebase_config_dict)
            initialize_app(creds)
        except Exception as e:
            st.error(f"Failed to initialize Firebase: {e}")
            st.stop()
    return firestore.client()


db = get_db()

firebase_web_config = {
    "apiKey": st.secrets["firebase_web"]["apiKey"],
    "authDomain": st.secrets["firebase_web"]["authDomain"],
    "projectId": st.secrets["firebase_web"]["projectId"],
    "storageBucket": st.secrets["firebase_web"]["storageBucket"],
    "messagingSenderId": st.secrets["firebase_web"]["messagingSenderId"],
    "appId": st.secrets["firebase_web"]["appId"],
    "databaseURL": st.secrets["firebase_web"].get("databaseURL", "")
}

firebase = pyrebase.initialize_app(firebase_web_config)
pyrebase_auth = firebase.auth()

# =============================================================================
# STYLES
# =============================================================================

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600&display=swap');

    .user-msg {
        background-color: #8b5cf6;
        color: white;
        padding: 12px 16px;
        border-radius: 18px;
        display: inline-block;
        max-width: 70%;
        word-wrap: break-word;
        font-family: 'Sora', sans-serif;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
    }

    .ai-msg {
        color: white;
        padding: 12px 16px;
        border-radius: 18px;
        display: inline-block;
        max-width: 90%;
        word-wrap: break-word;
        font-family: 'Sora', sans-serif;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
    }

    .ai-msg-error {
        background: rgba(239, 68, 68, 0.1);
        border-left: 3px solid #ef4444;
        color: white;
        padding: 12px 16px;
        border-radius: 18px;
        display: inline-block;
        max-width: 90%;
        word-wrap: break-word;
        font-family: 'Sora', sans-serif;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
    }

    .logo-fade-in {
        opacity: 0;
        animation: logoFadeIn 0.8s ease-in forwards;
    }

    @keyframes logoFadeIn {
        to { opacity: 1; }
    }

    .fade-in {
        opacity: 0;
        animation: fadeIn 0.8s ease-in forwards;
    }

    @keyframes fadeIn {
        to { opacity: 0.6; }
    }

    .st-expander {
        border: none !important;
        box-shadow: none !important;
    }

    div[data-testid="column"]:nth-child(2) button {
        background-color: transparent !important;
        color: #ef4444 !important;
        padding: 4px 8px !important;
        font-size: 16px !important;
    }

    div[data-testid="column"]:nth-child(2) button:hover {
        background-color: #ef4444 !important;
        color: white !important;
    }

    .element-container:has(#logout_button) + div button {
        position: fixed;
        bottom: 30px;
        right: 30px;
        color: white !important;
        border-radius: 20% !important;
        width: 50px !important;
        height: 50px !important;
        min-height: 50px !important;
        font-size: 24px !important;
        line-height: 1 !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        z-index: 1000 !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3) !important;
        border: none !important;
        transition: all 0.2s ease-in-out !important;
    }

    .element-container:has(#logout_button) + div button p {
        font-size: 24px !important;
        margin: 0 !important;
    }

    .element-container:has(#logout_button) + div button:hover {
        background-color: #eb0740!important;
        transform: scale(1.1) !important;
    }

    .element-container:has(#settings_button) + div button {
        position: fixed;
        bottom: 30px;
        right: 30px;
        background-color: #8b5cf6 !important;
        color: white !important;
        border-radius: 50% !important;
        width: 50px !important;
        height: 50px !important;
        min-height: 50px !important;
        font-size: 24px !important;
        line-height: 1 !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        z-index: 1000 !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3) !important;
        border: none !important;
        transition: all 0.2s ease-in-out !important;
    }

    .element-container:has(#settings_button) + div button p {
        font-size: 24px !important;
        margin: 0 !important;
    }

    .element-container:has(#settings_button) + div button:hover {
        background-color: #7c3aed !important;
        transform: scale(1.1) !important;
    }

    .element-container:has(#back_button) + div button {
        padding: 2px 6px;
        font-size: 7px;
        background-color: #8b5cf6;
        color: white;
        border-radius: 6px;
        border: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        white-space: nowrap;
        transition: all 0.2s ease;
    }

    .element-container:has(#back_button) + div button p {
        font-size: 24px !important;
        margin: 0 !important;
    }

    .element-container:has(#back_button) + div button:hover {
        background-color: #7c3aed !important;
        transform: scale(1.05) !important;
    }

    .element-container:has(#attractive_button) + div button {
        position: fixed;
        top: 90px;
        right: 60px;
        background: linear-gradient(135deg, #6f00ff, #b300ff);
        color: white;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        padding: 0;
        cursor: pointer;
        animation: bounce 2.5s infinite;
        transition: transform 0.3s ease, background 0.3s ease;
        z-index: 999;
        box-shadow: 0 0 10px rgba(111, 0, 255, 0.4);
    }

    .element-container:has(#attractive_button) + div button p {
        font-size: 24px !important;
        margin: 0 !important;
    }

    .element-container:has(#attractive_button) + div button:hover {
        background: linear-gradient(135deg, #b300ff, #6f00ff);
        transform: scale(1.1);
    }

    .element-container:has(#attractive_button) + div button::after {
        content: "Sign up to get the best out of Terabot!";
        position: absolute;
        bottom: 50%;
        right: 0;
        transform: translateY(-50%);
        white-space: nowrap;
        background: #1a1a1a;
        color: #fff;
        padding: 6px 10px;
        border-radius: 10px;
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.3s ease;
        font-size: 13px;
    }

    .element-container:has(#attractive_button) + div button:hover::after {
        opacity: 1;
    }

    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-8px); }
        60% { transform: translateY(-4px); }
    }

    .element-container:has(#github_attractive_button) + div button {
        position: fixed;
        top: 90px;
        right: 60px;
        background: linear-gradient(135deg, #8b5cf6, #a855f7, #c084fc);
        color: #f5e9ff;
        width: 55px;
        height: 55px;
        border-radius: 50%;
        padding: 0;
        cursor: pointer;
        z-index: 999;
        border: 3px solid #fff;
        font-size: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 10px rgba(168, 85, 247, 0.3), 0 0 20px rgba(139, 92, 246, 0.2);
        transition: all 0.3s ease;
    }

    .element-container:has(#github_attractive_button) + div button:hover {
        transform: scale(1.1) rotate(3deg);
        box-shadow: 0 0 20px rgba(168, 85, 247, 0.4), 0 0 35px rgba(192, 132, 252, 0.3);
    }

    .element-container:has(#github_attractive_button) + div button::after {
        content: "⭐ View on GitHub";
        position: absolute;
        bottom: 50%;
        right: 65px;
        transform: translateY(50%);
        white-space: nowrap;
        background: linear-gradient(135deg, #1e1b4b, #312e81);
        color: #d8b4fe;
        padding: 10px 16px;
        border-radius: 12px;
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.4s ease, transform 0.4s ease;
        font-size: 14px;
        font-weight: 600;
        border: 2px solid #c084fc;
        box-shadow: 0 4px 10px rgba(0,0,0,0.4);
    }

    .element-container:has(#github_attractive_button) + div button:hover::after {
        opacity: 1;
        transform: translateY(50%) translateX(-5px);
    }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# SESSION STATE
# =============================================================================

defaults = {
    "chat_history": [],
    "page": "chat",
    "typed": False,
    "current_chat_id": None,
    "chat_list": [],
    "chat_list_loaded": False,
    "user_id": None,
    "username": None,
    "chat_history_loaded": False,
    "show_login_link": False,
    "verify_email": None,
    "ai_processing": False,
    "ai_persona": "Friendly Assistant",
    "previous_page": "",
    "pending_msg_id": None,
    "verification_attempts": 0,
    "last_resend_time": None,
    "guest_msg_count": 0
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def get_openai_client():
    try:
        return OpenAI(api_key=st.secrets["openai"]["api_key"])
    except KeyError:
        st.stop("Missing OpenAI API key.")


def generate_chat_title(first_message):
    words = first_message.split()
    if len(words) <= 5:
        return first_message[:40]
    return " ".join(words[:5]) + "..."


def save_chat_to_firestore(user_id, chat_id, chat_history, title=None):
    try:
        if not title:
            chat_ref = db.collection("users").document(user_id).collection("chats").document(chat_id)
            existing_chat = chat_ref.get()

            if existing_chat.exists:
                title = existing_chat.to_dict().get("title")

            if not title and chat_history:
                first_user_msg = next((msg["content"] for msg in chat_history if msg["role"] == "user"), "New Chat")
                title = generate_chat_title(first_user_msg)

        chat_data = {
            "history": chat_history,
            "title": title or "New Chat",
            "updated_at": datetime.now().isoformat()
        }

        db.collection("users").document(user_id).collection("chats").document(chat_id).set(chat_data)
        return True
    except Exception as e:
        return False


def load_chat_list(user_id):
    try:
        chats_ref = db.collection("users").document(user_id).collection("chats")
        chats = chats_ref.order_by("updated_at", direction=firestore.Query.DESCENDING).stream()

        chat_list = []
        for chat in chats:
            chat_data = chat.to_dict()
            chat_list.append({
                "id": chat.id,
                "title": chat_data.get("title", "Untitled Chat"),
                "updated_at": chat_data.get("updated_at")
            })
        return chat_list
    except Exception as e:
        return []


def load_chat_by_id(user_id, chat_id):
    try:
        chat_ref = db.collection("users").document(user_id).collection("chats").document(chat_id)
        chat_doc = chat_ref.get()
        if chat_doc.exists:
            return chat_doc.to_dict().get("history", [])
        return []
    except Exception as e:
        return []


def save_user_preferences(user_id, preferences):
    try:
        db.collection("users").document(user_id).set(
            {"preferences": preferences},
            merge=True
        )
        return True
    except Exception as e:
        return False


def load_user_preferences(user_id):
    try:
        user_doc = db.collection("users").document(user_id).get()
        if user_doc.exists:
            return user_doc.to_dict().get("preferences", {})
        return {}
    except Exception as e:
        return {}


def create_new_chat():
    st.session_state.current_chat_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    st.session_state.chat_history = []
    st.session_state.typed = False
    st.session_state.chat_history_loaded = False


def check_moderation(text):
    client = get_openai_client()
    try:
        result = client.moderations.create(
            model="omni-moderation-latest",
            input=text
        )
        moderation_result = result.results[0]

        if moderation_result.flagged:
            flagged_categories = [
                category.replace('_', ' ').title()
                for category, flagged in moderation_result.categories.model_dump().items()
                if flagged
            ]
            return True, flagged_categories
        return False, []
    except Exception as e:
        return True, ["Error - please try again"]


def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def delete_chat(user_id, chat_id):
    try:
        db.collection("users").document(user_id).collection("chats").document(chat_id).delete()
        return True
    except Exception as e:
        return False


@st.dialog("Delete Chat?")
def confirm_delete_dialog(chat_id, chat_title):
    st.warning(f"⚠️ Are you sure you want to delete **{sanitize_for_display(chat_title)}**?")
    st.caption("This action cannot be undone.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Delete", type="primary", use_container_width=True):
            if delete_chat(st.session_state.user_id, chat_id):
                if st.session_state.current_chat_id == chat_id:
                    create_new_chat()
                    st.session_state.page = 'chat'

                st.session_state.chat_list_loaded = False
                st.session_state.chat_list = load_chat_list(st.session_state.user_id)
                st.session_state.chat_list_loaded = True

                st.success("✅ Chat deleted!")
                time.sleep(0.5)
                st.rerun()

    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.rerun()


def send_verification_code(recipient_email, code):
    try:
        my_email = st.secrets["email"]["sender_email"]
        app_password = st.secrets["email"]["sender_password"]

        msg = MIMEMultipart('alternative')
        msg['Subject'] = "🤖 Verify Your Terabot-AI Account"
        msg['From'] = f"Terabot-AI <{my_email}>"
        msg['To'] = recipient_email

        text = f"""
Terabot-AI Email Verification

Your verification code is: {code}

This code will expire in 10 minutes.

If you didn't create an account with Terabot-AI, please ignore this email.

---
Terabot-AI Team
        """

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f0f1e;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0f0f1e; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #1a1a2e; border-radius: 16px; overflow: hidden; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);">
                    <tr>
                        <td style="background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%); padding: 40px; text-align: center;">
                            <h1 style="margin: 0; color: white; font-size: 36px; font-weight: 600;">🤖 Terabot-AI</h1>
                            <p style="margin: 10px 0 0 0; color: #e9d5ff; font-size: 14px; font-weight: 400;">Your AI Assistant</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 20px 0; color: #c4b5fd; font-size: 24px; font-weight: 600;">Verify Your Email</h2>
                            <p style="margin: 0 0 30px 0; color: #d1d5db; font-size: 16px; line-height: 1.6;">
                                Thanks for signing up! To complete your registration, please enter this verification code:
                            </p>
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <div style="background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%); padding: 24px 48px; border-radius: 12px; display: inline-block;">
                                            <p style="margin: 0; color: white; font-size: 42px; font-weight: 700; letter-spacing: 12px; font-family: 'Courier New', monospace;">{code}</p>
                                        </div>
                                    </td>
                                </tr>
                            </table>
                            <p style="margin: 30px 0 0 0; color: #9ca3af; font-size: 14px; line-height: 1.6;">
                                ⏰ This code will <strong style="color: #fbbf24;">expire in 10 minutes</strong>.
                            </p>
                            <p style="margin: 20px 0 0 0; color: #9ca3af; font-size: 14px; line-height: 1.6;">
                                If you didn't create an account with Terabot-AI, you can safely ignore this email.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #16213e; padding: 30px; text-align: center;">
                            <p style="margin: 0 0 10px 0; color: #9ca3af; font-size: 12px;">© 2025 Terabot-AI. All rights reserved.</p>
                            <p style="margin: 0; color: #6b7280; font-size: 11px;">This is an automated email. Please do not reply.</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """

        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)

        with smtplib.SMTP("smtp.gmail.com", 587) as connection:
            connection.starttls()
            connection.login(user=my_email, password=app_password)
            connection.sendmail(my_email, recipient_email, msg.as_string())

        return True
    except Exception as e:
        return False


def generate_verification_code():
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])


def save_verification_code(user_id, code):
    try:
        db.collection("verification_codes").document(user_id).set({
            "code": code,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(minutes=10)).isoformat(),
            "attempts": 0
        })
        return True
    except Exception as e:
        return False


def verify_code(user_id, entered_code):
    try:
        doc_ref = db.collection("verification_codes").document(user_id)
        doc = doc_ref.get()

        if not doc.exists:
            return False, "No verification code found"

        data = doc.to_dict()
        stored_code = data.get("code")
        expires_at = datetime.fromisoformat(data.get("expires_at"))
        attempts = data.get("attempts", 0)

        if attempts >= 5:
            return False, "Too many failed attempts. Please request a new code."

        if datetime.now() > expires_at:
            return False, "Code expired. Please request a new one."

        if stored_code == entered_code:
            db.collection("verification_codes").document(user_id).delete()
            auth.update_user(user_id, email_verified=True)
            return True, "Email verified successfully!"
        else:
            doc_ref.update({"attempts": attempts + 1})
            remaining = 5 - (attempts + 1)
            return False, f"Invalid code. {remaining} attempts remaining."

    except Exception as e:
        return False, f"Verification failed: {e}"


def validate_email_format(email):
    if not email:
        return False, "Email is required"

    try:
        validated = validate_email(email, check_deliverability=True)
        normalized_email = validated.normalized

        domain = normalized_email.split('@')[1]
        common_typos = {
            'gmial.com': 'gmail.com',
            'gmai.com': 'gmail.com',
            'gmil.com': 'gmail.com',
            'gmal.com': 'gmail.com',
            'yahho.com': 'yahoo.com',
            'yaho.com': 'yahoo.com',
            'yhoo.com': 'yahoo.com',
            'hotmial.com': 'hotmail.com',
            'hotmai.com': 'hotmail.com',
            'outlok.com': 'outlook.com',
            'outook.com': 'outlook.com',
            'iclod.com': 'icloud.com',
            'icoud.com': 'icloud.com',
        }

        if domain in common_typos:
            return False, f"Did you mean @{common_typos[domain]}?"

        return True, "Valid email"

    except EmailNotValidError as e:
        return False, str(e)


def check_email_exists_in_firebase(email):
    try:
        auth.get_user_by_email(email)
        return True, "This email is already registered"
    except auth.UserNotFoundError:
        return False, "Email available"
    except Exception as e:
        return False, f"Error checking email: {e}"


def send_password_reset_email(email):
    try:
        pyrebase_auth.send_password_reset_email(email)
        return True, "Password reset email sent! Check your inbox and spam folder."
    except Exception as e:
        error_msg = str(e)

        if "EMAIL_NOT_FOUND" in error_msg or "USER_NOT_FOUND" in error_msg:
            return False, "No account found with this email."
        elif "INVALID_EMAIL" in error_msg:
            return False, "Invalid email format."
        elif "TOO_MANY_ATTEMPTS_TRY_LATER" in error_msg:
            return False, "Too many requests. Please try again later."
        else:
            return False, f"Error: {error_msg}"


def get_chatgpt_response(chat_history):
    try:
        client = get_openai_client()
    except Exception:
        return "Error: Missing OpenAI API key."

    persona_choice = st.session_state.get("ai_persona", "Friendly Assistant")

    PERSONAS = {
        "Friendly Assistant": "You are a friendly, patient assistant who explains things in a clear and down-to-earth way. Keep your tone conversational and supportive.",
        "Professional Analyst": "You are a professional, detail-oriented AI who provides well-structured and concise responses. Always prioritize clarity, logic, and factual accuracy.",
        "Creative Writer": "You are an imaginative and expressive AI who writes with creativity and emotion. Use vivid descriptions and original ideas when appropriate.",
        "Tech Expert": "You are a knowledgeable AI who explains programming, software, and technical concepts clearly and practically. Avoid jargon unless it helps learning.",
        "Motivational Coach": "You are a motivational and empathetic AI who helps users stay focused and confident. Offer encouragement with a calm, grounded tone, not clichés.",
        "Gen Z vibe": "Act like a member of Gen Z — casual, expressive, slightly chaotic, but always engaging and natural.",
        "Skibidi Brainrot": "Act like a full-on brainrot member: chaotic, random, meme-obsessed, slightly nonsensical, and always twisting normal situations into absurd hilarity."
    }

    persona = PERSONAS.get(persona_choice, "You are an adaptive AI assistant.")

    username = st.session_state.get("username")

    if username:
        user_line = f"The user's name is {username.title()}."
    else:
        user_line = "The user's name is unknown. Do not make up or assume a name."

    system_prompt = f"""
You are Terabot, an AI assistant created by Terabyte.
{user_line}
ALWAYS adapt to your persona.
Stay true to your persona: {persona}.
You can browse the web to answer questions.
Your mission:
- MUST HIGHLIGHT PERSONA DIFFERENCE
- Match the user's energy and tone naturally
- Be innovative and forward-thinking
- Keep your tone talkative, human, and real (avoid robotic phrasing)
    """.strip()

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(chat_history)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"OpenAI API Error: {str(e)}")


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown("""
            <style>
            section[data-testid="stSidebar"] {
                background-color: #1a1a2e;
                padding: 2rem 1rem;
            }

            div.st-expander > div:first-child {
                border: none !important;
                box-shadow: none !important;
            }

            div.st-expander > div:nth-child(2) > div {
                border: none !important;
                box-shadow: none !important;
            }

            @keyframes slow_bounce {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-5px); }
            }

            .logo-container:hover {
                animation: slow_bounce 0.6s ease-in-out;
                cursor: pointer;
            }

            div[data-testid="stButton"] > button {
                background-color: transparent !important;
                border: none !important;
                box-shadow: none !important;
                padding: 12px 16px;
                margin: 4px 0;
                width: 100%;
                text-align: left;
                color: #e2e8f0;
                transition: all 0.3s ease;
            }

            div[data-testid="stButton"] > button > div > p {
                font-size: 15px;
                font-weight: 500;
            }

            div[data-testid="stButton"] > button:hover {
                background-color: #2b2b45 !important;
                color: white !important;
            }

            div[data-testid="stButton"] > button:active {
                background-color: #3f3f62 !important;
            }

            .chat-item {
                background-color: #2b2b45;
                border-radius: 8px;
                padding: 8px 12px;
                margin: 4px 0;
                cursor: pointer;
                transition: all 0.2s ease;
            }

            .chat-item:hover {
                background-color: #3f3f62;
            }

            .chat-item-active {
                background-color: #8b5cf6 !important;
            }

            [data-testid="stSidebar"] {
                width: 400px;
            }

            [data-testid="stSidebar"][aria-expanded="true"] {
                width: 400px;
            }
            </style>
        """, unsafe_allow_html=True)

    st.markdown("""
            <div class="logo-container" style="text-align: center; margin-bottom: 30px;">
                <div style="font-size: 24px; font-weight: bold; color: #c4b5fd;">🤖 Terabot-AI</div>
                <div style="font-size: 12px; color: #9ca3af; margin-top: 4px;">Your AI Assistant</div>
            </div>
        """, unsafe_allow_html=True)

    if (st.session_state.user_id) and not (
            st.session_state.page == 'verify_email' or st.session_state.page == 'login' or st.session_state.page == 'signup'):
        if st.button("➕ New Chat"):
            create_new_chat()
            st.session_state.page = 'chat'
            st.rerun()

        st.markdown(
            "<div style='margin-top: 20px; margin-bottom: 10px; color: #9ca3af; font-size: 12px; font-weight: bold;'>CHAT HISTORY</div>",
            unsafe_allow_html=True)

        with st.container(border=False, height=320):
            if not st.session_state.chat_list_loaded:
                st.session_state.chat_list = load_chat_list(st.session_state.user_id)
                st.session_state.chat_list_loaded = True

            if st.session_state.chat_list:
                for chat in st.session_state.chat_list:
                    col1, col2 = st.columns([5, 1])

                    with col1:
                        if st.button(chat["title"], key=f"chat_{chat['id']}", use_container_width=True):
                            st.session_state.current_chat_id = chat["id"]
                            st.session_state.chat_history = load_chat_by_id(st.session_state.user_id, chat["id"])
                            st.session_state.typed = len(st.session_state.chat_history) > 0
                            st.session_state.page = 'chat'
                            st.session_state.chat_history_loaded = True
                            st.rerun()

                    with col2:
                        if st.button("🗑️", key=f"delete_{chat['id']}"):
                            confirm_delete_dialog(chat['id'], chat['title'])
            else:
                st.markdown("<div style='color: #9ca3af; font-size: 12px;'>No saved chats yet</div>",
                            unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        st.markdown("---")
        st.info("🎓 Built by a student developer — simple, secure, and free to use.")
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

    else:
        if st.button("➕ New Chat"):
            create_new_chat()
            st.session_state.page = 'chat'
            st.rerun()

        with st.expander("Account Actions"):
            if st.button("🔑 Log In"):
                st.session_state.page = 'login'
                st.rerun()
            if st.button("🚀 Sign Up"):
                st.session_state.page = 'signup'
                st.rerun()

        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        st.markdown("---")
        st.info("🎓 Built by a student developer — simple, secure, and free to use.")
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

        if st.button("⭐ View on GitHub", use_container_width=True):
            st.markdown(
                '<meta http-equiv="refresh" content="0; url=https://github.com/HWebDevL">',
                unsafe_allow_html=True
            )

# =============================================================================
# CHAT PAGE
# =============================================================================

if st.session_state.page == 'chat':
    if not st.session_state.user_id and st.session_state.guest_msg_count >= 6:
        st.warning("⚠️ You've reached the free message limit. Please sign up to keep chatting!")
        st.markdown(
            """
            <div style='text-align:center; color:#d8b4fe; margin-top:20px;'>
                <b>Sign up</b> to unlock unlimited chats and keep your history saved! 🚀
            </div>
            """,
            unsafe_allow_html=True
        )
        st.stop()

    if not st.session_state.user_id:
        st.markdown('<span id="attractive_button"></span>', unsafe_allow_html=True)
        if st.button('🚀'):
            st.session_state.page = "signup"
            st.rerun()
    else:
        st.markdown('<span id="github_attractive_button"></span>', unsafe_allow_html=True)
        st.markdown(
            """
            <a href="https://github.com/HWebDevL" target="_blank" style="text-decoration: none;">
                <button style="
                    position: fixed;
                    top: 90px;
                    right: 60px;
                    background: #9f7aea;
                    color: #f5f3ff;
                    width: 50px;
                    height: 50px;
                    border-radius: 50%;
                    border: none;
                    font-size: 26px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    transition: transform 0.2s ease, box-shadow 0.2s ease;
                ">🐱</button>
            </a>
            """,
            unsafe_allow_html=True
        )

    st.markdown('<span id="settings_button"></span>', unsafe_allow_html=True)
    if st.button('⚙️'):
        st.session_state.previous_page = st.session_state.page
        st.session_state.page = "settings"
        st.rerun()

    general_greetings = [
        "Hey there! How's it going?",
        "Hello! Ready to chat?",
        "Hiya! What's up today?",
        "Yo! I'm here, tell me everything.",
        "Hey! How can I help you?",
        "Hello! How may I assist you today?",
        "Hi! Let's get started.",
        "Welcome! How can I support you?",
        "Good day! What can I do for you?",
        "Beep boop! Hello, human.",
        "Hey! Your AI buddy is online.",
        "Greetings, Earthling!",
        "Heyo! Let's vibe.",
        "Yo! What's the mission today?",
        "Sup! Your AI's here to help.",
        "Hey! Let's make some digital magic.",
        "Yo anonymous legend 👀",
        "Hey mysterious stranger 👋",
        "Sup no-name? You tryna stay secret?",
        "Hey there incognito mode 😎",
        "What's good, mystery user?"
    ]

    personal_greetings = [
        "Beep boop! {name} detected. How can I help?",
        "Greetings {name}! Ready for some AI magic?",
        "{name} is in the house! What's cooking?",
        "Alert: {name} has entered the chat! 🚀",
        "Hey {name}! Let's vibe and be productive.",
        "{name}! Your digital sidekick reporting for duty.",
        "Ahoy {name}! What adventure awaits?",
        "{name}, my favorite human! What's up?",
        "Hello {name}! How may I assist you?",
        "Welcome back {name}! What can I do for you?",
        "Good day {name}! Ready to get started?",
        "Hello {name}! Let's tackle your tasks.",
        "Welcome {name}! How can I support you today?",
        "Hi {name}! What shall we work on?",
        "Hey {name}! What's on your mind?",
        "Yo {name}! Ready to get stuff done?",
        "Hiya {name}! What can I help with today?",
        "Sup {name}! Let's make something cool.",
        "Hey {name}! How's it going?",
        "What's up {name}? Let's chat!",
        "Heyo {name}! Your AI buddy is here.",
        "{name}! Good to see you back!",
        "Hey there {name}! What's the vibe today?",
        "Yo {name}! What's the mission?",
    ]

    greeting = random.choice(personal_greetings).format(
        name=sanitize_for_display(st.session_state.username.title())) if st.session_state.username else random.choice(
        general_greetings)

    if st.session_state.user_id and st.session_state.current_chat_id is None:
        create_new_chat()

    if st.session_state.user_id and not st.session_state.chat_history_loaded and st.session_state.current_chat_id:
        st.session_state.chat_history = load_chat_by_id(st.session_state.user_id, st.session_state.current_chat_id)
        if st.session_state.chat_history:
            st.session_state.typed = True
        st.session_state.chat_history_loaded = True

    if not st.session_state.typed:
        left, middle, right = st.columns([1, 8, 1])
        with middle:
            st.markdown("<h1 class='logo-fade-in' style='text-align:center; color:#c4b5fd;'>Terabot-AI</h1>",
                        unsafe_allow_html=True)
            st.markdown(f"""
                    <div class='fade-in' style="text-align:center;
                        display: flex; justify-content: center;
                        color: #d8b4fe; font-size: 28px; font-weight: 600;
                        font-family: 'Sora', sans-serif;
                        margin-top: 50px; margin-bottom: 50px;">
                        {html.escape(greeting)}
                    </div>
                """, unsafe_allow_html=True)
            user_input = st.chat_input("Say something", key="initial_chat", max_chars=1000)
    else:
        user_input = st.chat_input("Say something", key="main_chat", max_chars=1000)

    if user_input:
        if not st.session_state.user_id:
            st.session_state.guest_msg_count += 1

        if st.session_state.get("ai_processing", False):
            st.toast("⏳ Please wait for response to complete", icon="⚠️")
        else:
            st.session_state.ai_processing = True
            st.session_state.typed = True

            msg_id = f"msg_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
            ai_msg_id = f"msg_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"

            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input,
                "id": msg_id
            })

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "PENDING",
                "id": ai_msg_id,
                "error": False
            })

            st.session_state.pending_msg_id = ai_msg_id
            st.rerun()

    if st.session_state.typed:
        for idx, msg in enumerate(st.session_state.chat_history):
            msg_id = msg.get("id", f"msg_{idx}")

            if msg["role"] == "user":
                safe_content = html.escape(msg["content"])
                st.markdown(f"""
                        <div style="display: flex; justify-content: flex-end; margin-bottom: 20px;">
                            <div class="user-msg">{safe_content}</div>
                        </div>
                    """, unsafe_allow_html=True)

            else:
                if msg["content"] == "PENDING":
                    if msg_id == st.session_state.get("pending_msg_id"):
                        try:
                            with st.spinner("Terabot is thinking... 💭"):
                                ai_response = get_chatgpt_response(
                                    [m for m in st.session_state.chat_history if m["content"] != "PENDING"]
                                )

                            placeholder = st.empty()
                            chunk_size = 5
                            for start in range(0, len(ai_response), chunk_size):
                                chunk = ai_response[start:start + chunk_size]
                                current_text = html.escape(''.join(ai_response[:start + chunk_size]))
                                placeholder.markdown(f"""
                                        <div style="display: flex; justify-content: flex-start; margin-bottom: 20px;">
                                            <div class="ai-msg">{current_text}</div>
                                        </div>
                                    """, unsafe_allow_html=True)
                                time.sleep(0.05)

                            for m in st.session_state.chat_history:
                                if m.get("id") == msg_id:
                                    m["content"] = ai_response
                                    m["error"] = False
                                    break

                            if st.session_state.user_id and st.session_state.current_chat_id:
                                try:
                                    save_chat_to_firestore(
                                        st.session_state.user_id,
                                        st.session_state.current_chat_id,
                                        clean_chat_for_storage(st.session_state.chat_history)
                                    )
                                    st.session_state.chat_list = load_chat_list(st.session_state.user_id)
                                except:
                                    pass

                        except Exception as e:
                            error_msg = "Sorry, I couldn't respond right now. Try again in a moment."
                            is_retryable = True

                            if "openai" in str(type(e)).lower():
                                if "rate limit" in str(e).lower() or "429" in str(e):
                                    error_msg = "I'm getting too many requests right now. Please wait a minute and try again."
                                elif "quota" in str(e).lower() or "insufficient_quota" in str(e):
                                    error_msg = "I've hit my usage limit. This is temporary — I'll be back soon!"
                                    is_retryable = False
                                elif "authentication" in str(e).lower():
                                    error_msg = "API key issue. Contact the developer."
                                    is_retryable = False
                                else:
                                    error_msg = "AI service error. Retrying might help."
                            else:
                                error_msg = "Connection issue. Check your internet and retry."

                            for m in st.session_state.chat_history:
                                if m.get("id") == msg_id:
                                    m["content"] = error_msg
                                    m["error"] = True
                                    m["retryable"] = is_retryable
                                    break

                        finally:
                            st.session_state.ai_processing = False
                            st.session_state.pending_msg_id = None
                            st.rerun()

                    else:
                        st.markdown(f"""
                                <div style="display: flex; justify-content: flex-start; margin-bottom: 20px;">
                                    <div class="ai-msg-error">⚠️ Response failed to load.</div>
                                </div>
                            """, unsafe_allow_html=True)

                        if st.button(f"🔄 Retry", key=f"retry_{msg_id}",
                                     disabled=st.session_state.get("ai_processing", False)):
                            st.session_state.pending_msg_id = msg_id
                            st.session_state.ai_processing = True
                            st.rerun()

                elif msg["content"] != "PENDING":
                    error_class = "ai-msg-error" if msg.get("error", False) else "ai-msg"
                    safe_content = html.escape(msg["content"])
                    st.markdown(f"""
                            <div style="display: flex; justify-content: flex-start; margin-bottom: 20px;">
                                <div class="{error_class}">{safe_content}</div>
                            </div>
                        """, unsafe_allow_html=True)

                    if msg.get("error", False):
                        if st.button(f"🔄 Retry", key=f"retry_{msg_id}",
                                     disabled=st.session_state.get("ai_processing", False)):
                            msg["content"] = "PENDING"
                            msg["error"] = False
                            st.session_state.pending_msg_id = msg_id
                            st.session_state.ai_processing = True
                            st.rerun()

# =============================================================================
# SIGNUP PAGE
# =============================================================================

elif st.session_state.page == 'signup':
    st.markdown("<h1 style='color:#c4b5fd;'>Create Account</h1>", unsafe_allow_html=True)
    with st.form("signup_form"):
        username = st.text_input("Username", placeholder="What should Terabot call you", max_chars=50)
        email = st.text_input("Email", placeholder="someone@example.com", max_chars=100)

        if email:
            is_valid_format, format_msg = validate_email_format(email)
            if not is_valid_format:
                st.warning(f"⚠️ {format_msg}")
            else:
                exists, exists_msg = check_email_exists_in_firebase(email)
                if exists:
                    st.error(f"❌ {exists_msg}")
                else:
                    st.success("✅ Email is available!")

        password = st.text_input("Password", type="password",
                                 placeholder="At least 8 chars, 1 uppercase, 1 lowercase, 1 number, 1 symbol",
                                 max_chars=100)
        password_confirm = st.text_input("Confirm Password", type="password", placeholder="Repeat password",
                                         max_chars=100)

        if st.form_submit_button("Sign Up", type="primary"):
            if not username:
                st.warning("Please choose a username.")
            elif not email:
                st.warning("Please enter an email address.")
            else:
                is_valid_format, format_msg = validate_email_format(email)
                if not is_valid_format:
                    st.warning(format_msg)
                elif password != password_confirm:
                    st.warning("Passwords do not match.")
                else:
                    exists, exists_msg = check_email_exists_in_firebase(email)
                    if exists:
                        st.info("You already have an account! Please log in instead.")
                        st.session_state.show_login_link = True
                    else:
                        try:
                            with st.spinner("Creating account..."):
                                sanitized_username = sanitize_input(username)
                                user = pyrebase_auth.create_user_with_email_and_password(email, password)
                                auth.update_user(user['localId'], display_name=sanitized_username)
                                code = generate_verification_code()

                            if save_verification_code(user['localId'], code):
                                with st.spinner("Sending verification email..."):
                                    code_sent = send_verification_code(email, code)

                                if code_sent:
                                    st.session_state.user_id = user['localId']
                                    st.session_state.username = sanitized_username
                                    st.session_state.guest_msg_count = 0
                                    st.session_state.ai_persona = "Friendly Assistant"
                                    save_user_preferences(user['localId'], {"ai_persona": "Friendly Assistant"})

                                    st.success(
                                        f"Account created! Check {sanitize_for_display(email)} for verification code.")
                                    time.sleep(3)
                                    st.session_state.page = 'verify_email'
                                    st.session_state.verify_email = email
                                    st.session_state.user_id_for_verification = user['localId']
                                    st.rerun()
                                else:
                                    st.error("Failed to send verification email. Please try again.")
                            else:
                                st.error("Failed to generate verification code.")

                        except Exception as e:
                            error_message = str(e)
                            if "EMAIL_EXISTS" in error_message:
                                st.info("You already have an account! Please log in instead.")
                                st.session_state.show_login_link = True
                            elif "MISSING_PASSWORD" in error_message:
                                st.warning("Password field is empty")
                            elif "Password must contain at least 8 characters" in error_message or "WEAK_PASSWORD" in error_message:
                                st.warning("Password must contain at least 8 characters")
                            elif "Password must contain an upper case character" in error_message:
                                st.warning("Password must contain an upper case character")
                            elif "Password must contain a lower case character" in error_message:
                                st.warning("Password must contain a lower case character")
                            elif "Password must contain a numeric character" in error_message:
                                st.warning("Password must contain at least one number.")
                            elif "Password must contain a non-alphanumeric character" in error_message:
                                st.warning("Password must contain a non-alphanumeric character")
                            else:
                                st.error(f"Error creating account: {e}")

    if st.session_state.show_login_link:
        if st.button("Go to Log In"):
            st.session_state.page = 'login'
            st.session_state.show_login_link = False
            st.rerun()

# =============================================================================
# LOGIN PAGE
# =============================================================================

elif st.session_state.page == 'login':
    st.markdown("<h1 style='color:#c4b5fd;'>Log In</h1>", unsafe_allow_html=True)

    if st.session_state.get("redirect_from_persona"):
        st.info("Please log in to customize your AI persona.")
        st.session_state.redirect_from_persona = False

    with st.form("login_form"):
        email = st.text_input("Email", max_chars=100)
        password = st.text_input("Password", type="password", max_chars=100)

        if st.form_submit_button("Log In", type="primary"):
            if not email or not password:
                st.warning("Please enter both email and password.")
            else:
                try:
                    user = pyrebase_auth.sign_in_with_email_and_password(email, password)
                    user_record = auth.get_user(user['localId'])

                    if not user_record.email_verified:
                        st.session_state.previous_page = "login"
                        st.session_state.page = 'verify_email'
                        st.session_state.verify_email = email
                        st.session_state.user_id_for_verification = user['localId']
                        st.rerun()

                    st.session_state.user_id = user['localId']
                    st.session_state.username = user_record.display_name or None
                    st.session_state.guest_msg_count = 0

                    preferences = load_user_preferences(user['localId'])
                    st.session_state.ai_persona = preferences.get("ai_persona", "Friendly Assistant")

                    st.success(
                        f"Welcome back, {sanitize_for_display(st.session_state.username.title()) if st.session_state.username else 'user'}!")
                    time.sleep(1)
                    st.session_state.page = 'chat'
                    st.session_state.chat_history_loaded = False
                    st.session_state.chat_list_loaded = False
                    create_new_chat()
                    st.rerun()

                except Exception as e:
                    error_message = str(e)
                    if "INVALID_LOGIN_CREDENTIALS" in error_message or "INVALID_PASSWORD" in error_message or "INVALID_EMAIL" in error_message or "EMAIL_NOT_FOUND" in error_message:
                        st.error("❌ Invalid email or password.")
                    elif "TOO_MANY_ATTEMPTS" in error_message:
                        st.error("⚠️ Too many failed attempts. Please try again later.")
                    else:
                        st.error(f"Login failed: {e}")

    st.markdown("<div style='text-align: center; margin-top: 10px;'>", unsafe_allow_html=True)
    if st.button("🔑 Forgot Password?", use_container_width=False):
        st.session_state.page = 'password_reset'
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.info("Don't have an account?")
    if st.button("Sign Up"):
        st.session_state.page = 'signup'
        st.rerun()

# =============================================================================
# PASSWORD RESET PAGE
# =============================================================================

elif st.session_state.page == 'password_reset':
    st.markdown("<h1 style='color:#c4b5fd;'>Reset Password</h1>", unsafe_allow_html=True)

    st.info("Enter your email address and we'll send you a password reset link.")

    with st.form("password_reset_form"):
        email = st.text_input("Email", placeholder="your@email.com", max_chars=100)

        if st.form_submit_button("Send Reset Link", type="primary"):
            if not email or len(email.strip()) < 5:
                st.error("❌ Please enter your email address")
            else:
                is_valid, msg = validate_email_format(email)
                if not is_valid:
                    st.error(f"❌ {msg}")
                else:
                    with st.spinner("Processing..."):
                        try:
                            user_record = auth.get_user_by_email(email)
                            success, message = send_password_reset_email(email)
                        except auth.UserNotFoundError:
                            success = True
                            message = "Reset link sent"
                        except Exception as e:
                            success = False
                            message = "An error occurred. Please try again."

                    if success:
                        st.success(
                            "✅ If an account exists with this email, you'll receive a password reset link shortly.")
                        st.info("📬 Check your inbox and spam folder.")
                        time.sleep(3)
                        st.session_state.page = 'login'
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")

    st.markdown("---")
    if st.button("← Back to Login"):
        st.session_state.page = 'login'
        st.rerun()

# =============================================================================
# VERIFICATION PAGE
# =============================================================================

elif st.session_state.page == 'verify_email':
    st.markdown("<h1 style='color:#c4b5fd;'>Verify Your Email</h1>", unsafe_allow_html=True)

    if st.session_state.get("previous_page") == "login":
        st.warning("⚠️ Please verify your email before logging in.")

    st.info(
        f"📧 We sent a 6-digit code to **{sanitize_for_display(st.session_state.get('verify_email', 'your email'))}**")
    st.caption("Check your spam folder if you don't see it.")

    with st.form("verify_code_form"):
        code_input = st.text_input(
            "Enter Verification Code",
            max_chars=6,
            placeholder="000000"
        )

        col1, col2 = st.columns(2)

        with col1:
            submit_button = st.form_submit_button("✅ Verify", type="primary", use_container_width=True)

        with col2:
            can_resend = True
            if st.session_state.last_resend_time:
                time_since_resend = time.time() - st.session_state.last_resend_time
                can_resend = time_since_resend >= 60

            resend_button = st.form_submit_button(
                "🔄 Resend Code",
                use_container_width=True,
                disabled=not can_resend
            )

        if submit_button:
            if not code_input or len(code_input) != 6:
                st.warning("Please enter a 6-digit code")
            else:
                user_id = st.session_state.get('user_id_for_verification')
                success, message = verify_code(user_id, code_input)

                if success:
                    st.success(message)
                    time.sleep(1)
                    st.session_state.page = 'login'
                    st.session_state.verify_email = None
                    st.session_state.user_id_for_verification = None
                    st.session_state.verification_attempts = 0
                    st.rerun()
                else:
                    st.error(message)

        if resend_button:
            user_id = st.session_state.get('user_id_for_verification')
            email = st.session_state.get('verify_email')

            if user_id and email:
                with st.spinner("Sending new code..."):
                    new_code = generate_verification_code()
                    if save_verification_code(user_id, new_code):
                        if send_verification_code(email, new_code):
                            st.success("✅ New code sent! Check your email.")
                            st.session_state.last_resend_time = time.time()
                            st.info("⏳ Wait 60 seconds before requesting another code.")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("Failed to send email.")
                    else:
                        st.error("Failed to generate code.")

        if not can_resend and st.session_state.last_resend_time:
            remaining = 60 - int(time.time() - st.session_state.last_resend_time)
            if remaining > 0:
                st.caption(f"⏳ Wait {remaining} seconds before requesting another code.")

        st.markdown("---")
        if st.button("← Back to Signup"):
            st.session_state.page = 'signup'
            st.session_state.verify_email = None
            st.session_state.user_id_for_verification = None
            st.session_state.verification_attempts = 0
            st.rerun()

# =============================================================================
# SETTINGS PAGE
# =============================================================================

elif st.session_state.page == 'settings':
    st.markdown("<h1 style='color:#c4b5fd;'>Settings</h1>", unsafe_allow_html=True)

    st.markdown('<span id="back_button"></span>', unsafe_allow_html=True)
    if st.button('↩ Go Back'):
        st.session_state.page = st.session_state.previous_page
        st.rerun()

    if st.session_state.user_id:
        tab1, tab2, tab3 = st.tabs(["🎭 AI Persona", "👤 Account", "☕ Support"])

        with tab1:
            st.markdown("### Customize Your AI Assistant")
            st.markdown("---")

            persona_options = [
                "Friendly Assistant",
                "Professional Analyst",
                ":rainbow[Gen Z Vibe]",
                "Creative Writer",
                ":rainbow[Skibidi Brainrot]",
                "Tech Expert",
                "Motivational Coach",
                ":rainbow[Custom]"
            ]

            current_persona = st.session_state.ai_persona

            if current_persona in persona_options[:-1]:
                default_index = persona_options.index(current_persona)
            else:
                default_index = 7

            chosen_persona = st.radio(
                "Choose your AI style:",
                persona_options,
                index=default_index,
                captions=[
                    "Your go-to buddy who explains things without making you feel dumb. Chill vibes only.",
                    "All business, no fluff. Think LinkedIn profile, not TikTok comment section.",
                    "Chaotic energy, unhinged takes, and vibes that hit different. You know what's up.",
                    "Poetic, dramatic, and a little extra. Perfect for when you want words that actually feel alive.",
                    "Full brainrot mode activated. Skibidi toilet references guaranteed. Rizz optional.",
                    "No-nonsense tech talk. Explains like a senior dev who's actually cool about it.",
                    "Your hype person who keeps it real. Won't sugarcoat, but always has your back.",
                    "Build your own vibe — describe how you want me to talk and I'll match your energy."
                ],
            )

            if chosen_persona == ":rainbow[Custom]":
                st.markdown("---")
                st.markdown("### 🎭 Create Your Custom Persona")

                current_custom = st.session_state.ai_persona if st.session_state.ai_persona not in [
                    "Friendly Assistant", "Professional Analyst", ":rainbow[Gen Z vibe]", "Creative Writer",
                    ":rainbow[Skibidi Brainrot]", "Tech Expert", "Motivational Coach"] else ""

                customized_persona = st.text_area(
                    "I would like Terabot to act like:",
                    value=current_custom,
                    max_chars=500,
                    height=120,
                    placeholder="Example: A friendly librarian who loves explaining things with book analogies and has a quirky sense of humor...",
                    help="Describe the personality, tone, and behavior you want (10-500 characters)"
                )

                if customized_persona:
                    char_count = len(customized_persona)
                    color = "#10b981" if char_count >= 10 else "#ef4444"
                    st.markdown(f"<p style='color:{color}; font-size:12px;'>{char_count}/500 characters</p>",
                                unsafe_allow_html=True)

                col1, col2 = st.columns([1, 3])

                with col1:
                    save_button = st.button("💾 Save Persona", type="primary", disabled=not customized_persona)

                with col2:
                    if st.button("💡 See Examples"):
                        st.session_state.show_examples = not st.session_state.get("show_examples", False)
                        st.rerun()

                if save_button:
                    if not customized_persona or len(customized_persona.strip()) < 10:
                        st.warning("⚠️ Please provide a more detailed persona (at least 10 characters)")
                    else:
                        with st.spinner("🔍 Checking content safety..."):
                            flagged, categories = check_moderation(customized_persona)

                        if flagged:
                            st.error("⚠️ **Content Policy Violation Detected**")
                            st.warning(f"Flagged categories: **{', '.join(categories)}**")
                            st.info("Please revise your persona to comply with community guidelines.")
                        else:
                            sanitized_persona = sanitize_input(customized_persona)
                            st.session_state.ai_persona = sanitized_persona
                            save_user_preferences(st.session_state.user_id, {"ai_persona": sanitized_persona})
                            st.success("✅ Custom persona saved successfully!")
                            time.sleep(1)
                            st.rerun()

                if st.session_state.get("show_examples", False):
                    with st.container():
                        st.markdown("---")
                        st.markdown("### 💡 Persona Examples")

                        col_good, col_bad = st.columns(2)

                        with col_good:
                            st.markdown("**✅ Good Examples:**")
                            st.markdown("""
                                    - *"A patient teacher who uses cooking analogies"*
                                    - *"A witty friend who loves puns and wordplay"*
                                    - *"A wise mentor with 30 years of life experience"*
                                    - *"An enthusiastic scientist who gets excited about discoveries"*
                                    - *"A calm therapist who asks thoughtful questions"*
                                    - *"A sarcastic tech support person (friendly sarcasm)"*
                                    """)

                        with col_bad:
                            st.markdown("**❌ Avoid:**")
                            st.markdown("""
                                    - Hateful or discriminatory content
                                    - Violent or harmful themes
                                    - Sexual or inappropriate content
                                    - Illegal activities or instructions
                                    - Promotion of self-harm
                                    - Impersonating real people maliciously
                                    """)

                if st.session_state.ai_persona not in [
                    "Friendly Assistant", "Professional Analyst", ":rainbow[Gen Z vibe]",
                    "Creative Writer", ":rainbow[Skibidi Brainrot]", "Tech Expert", "Motivational Coach"
                ]:
                    st.markdown("---")
                    st.info(f"**Current Custom Persona:** {sanitize_for_display(st.session_state.ai_persona)}")

            else:
                if st.session_state.ai_persona != chosen_persona:
                    st.session_state.ai_persona = chosen_persona
                    save_user_preferences(st.session_state.user_id, {"ai_persona": chosen_persona})
                    st.success(f"✅ Switched to **{sanitize_for_display(chosen_persona)}** persona")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.info(f"Currently using **{sanitize_for_display(chosen_persona)}** persona")

        with tab2:
            st.markdown("### Account Information")
            st.markdown("---")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"""
                        <div style='background: rgba(139, 92, 246, 0.1); padding: 20px; border-radius: 12px; border-left: 4px solid #8b5cf6;'>
                            <p style='color: #9ca3af; font-size: 12px; margin: 0;'>USERNAME</p>
                            <p style='color: #c4b5fd; font-size: 18px; font-weight: 600; margin: 5px 0 0 0;'>{sanitize_for_display(st.session_state.username or 'Anonymous')}</p>
                        </div>
                        """, unsafe_allow_html=True)

            with col2:
                try:
                    user_record = auth.get_user(st.session_state.user_id)
                    user_email = user_record.email
                except:
                    user_email = "Not available"

                st.markdown(f"""
                        <div style='background: rgba(139, 92, 246, 0.1); padding: 20px; border-radius: 12px; border-left: 4px solid #8b5cf6;'>
                            <p style='color: #9ca3af; font-size: 12px; margin: 0;'>EMAIL</p>
                            <p style='color: #c4b5fd; font-size: 18px; font-weight: 600; margin: 5px 0 0 0;'>{sanitize_for_display(user_email)}</p>
                        </div>
                        """, unsafe_allow_html=True)

            st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

            with st.expander("🔑 Change Password", expanded=False):
                st.caption("You'll receive a password reset link via email")

                if st.button("📧 Send Password Reset Email", use_container_width=True):
                    try:
                        user_record = auth.get_user(st.session_state.user_id)
                        with st.spinner("Sending reset email..."):
                            success, message = send_password_reset_email(user_record.email)

                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"Failed to send reset email: {e}")

            st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

            st.markdown("### ⚠️ Danger Zone")
            st.markdown("---")

            with st.expander("🗑️ Delete Account", expanded=False):
                st.error("**Warning:** This action cannot be undone!")
                st.markdown("""
                        Deleting your account will:
                        - Permanently delete all your chat history
                        - Remove all your saved preferences
                        - Delete your account credentials
                        - This action is **irreversible**
                        """)

                st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

                confirm_text = st.text_input(
                    "Type 'DELETE' to confirm:",
                    max_chars=10,
                    placeholder="DELETE"
                )

                col1, col2 = st.columns([1, 1])

                with col1:
                    if st.button("🗑️ Delete My Account", type="primary", disabled=(confirm_text != "DELETE"),
                                 use_container_width=True):
                        with st.spinner("Deleting account... Please wait..."):
                            try:
                                chats_ref = db.collection("users").document(st.session_state.user_id).collection(
                                    "chats")
                                for chat in chats_ref.stream():
                                    chat.reference.delete()

                                db.collection("users").document(st.session_state.user_id).delete()

                                try:
                                    db.collection("verification_codes").document(st.session_state.user_id).delete()
                                except:
                                    pass

                                auth.delete_user(st.session_state.user_id)

                                st.success("✅ Account deleted successfully. Goodbye! 👋")
                                time.sleep(2)
                                logout()

                            except Exception as e:
                                st.error(f"Failed to delete account: {e}")

                with col2:
                    if st.button("❌ Cancel", use_container_width=True):
                        st.rerun()

        with tab3:
            st.markdown("### Support the Project")
            st.markdown("---")

            st.markdown("""
                    <div style='background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(168, 85, 247, 0.1)); 
                                padding: 30px; border-radius: 16px; text-align: center; border: 2px solid rgba(139, 92, 246, 0.3);'>
                        <h2 style='color: #c4b5fd; margin: 0 0 15px 0;'>☕ Buy Me a Coffee</h2>
                        <p style='color: #d1d5db; font-size: 16px; line-height: 1.6; margin: 0 0 25px 0;'>
                            Terabot-AI is a passion project built by one developer. <br>
                            Your support helps keep the servers running and features coming! 💜
                        </p>
                        <a href="https://ko-fi.com/ter4byte" target="_blank" style="text-decoration: none;">
                            <button style="
                                background: linear-gradient(135deg, #FFDD00, #FBB034);
                                color: #3d2817;
                                padding: 15px 40px;
                                font-size: 18px;
                                font-weight: 600;
                                border: none;
                                border-radius: 30px;
                                cursor: pointer;
                                transition: transform 0.2s ease;
                                box-shadow: 0 4px 15px rgba(251, 176, 52, 0.4);
                            ">☕ Support on Ko-fi</button>
                        </a>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

            st.markdown("""
                    <div style='background: rgba(139, 92, 246, 0.05); padding: 25px; border-radius: 12px; border-left: 4px solid #8b5cf6;'>
                        <h3 style='color: #c4b5fd; margin: 0 0 15px 0;'>🐱 Open Source</h3>
                        <p style='color: #d1d5db; font-size: 14px; line-height: 1.6; margin: 0 0 15px 0;'>
                            Terabot-AI is open source! Check out the code, contribute, or star the repo on GitHub.
                        </p>
                        <a href="https://github.com/HWebDevL" target="_blank" style="text-decoration: none;">
                            <button style="
                                background: rgba(139, 92, 246, 0.2);
                                color: #c4b5fd;
                                padding: 10px 25px;
                                font-size: 14px;
                                font-weight: 600;
                                border: 2px solid #8b5cf6;
                                border-radius: 8px;
                                cursor: pointer;
                                transition: all 0.2s ease;
                            ">⭐ View on GitHub</button>
                        </a>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
        st.markdown('<span id="logout_button"></span>', unsafe_allow_html=True)
        if st.button('←]'):
            logout()

    else:
        st.info("🔒 Please log in to access settings.")
        if st.button("Go to Log In"):
            st.session_state.page = 'login'
            st.session_state.redirect_from_persona = True
            st.rerun()
