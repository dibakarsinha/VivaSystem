import streamlit as st
import pandas as pd
import gspread
import time
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from streamlit.components.v1 import html

# -------------------------------
# 🎯 PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="AI Viva System", layout="wide")

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# 🔐 GOOGLE SHEETS VIA SECRETS
# -------------------------------
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], scope
)

client = gspread.authorize(creds)

sheet = client.open("VivaSystem")
q_sheet = sheet.worksheet("questions")
r_sheet = sheet.worksheet("responses")

# Load questions
@st.cache_data
def load_data():
    return pd.DataFrame(q_sheet.get_all_records())

data = load_data()
st.write("DEBUG: Rows =", len(data))
st.write(data)
# -------------------------------
# 🖥️ FULLSCREEN + ANTI-CHEATING
# -------------------------------
html("""
<script>
function openFullscreen() {
    let elem = document.documentElement;
    if (elem.requestFullscreen) {
        elem.requestFullscreen();
    }
}

document.addEventListener("visibilitychange", function() {
    if (document.hidden) {
        alert("⚠️ Tab switched! This activity is monitored.");
    }
});
</script>

<button onclick="openFullscreen()" style="padding:10px;font-size:16px;">
Enter Full Screen
</button>
""")

# -------------------------------
# ⏱️ TIMER CONFIG
# -------------------------------
DURATION = 600  # 10 minutes

if "start_time" not in st.session_state:
    st.session_state.start_time = None

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "questions" not in st.session_state:
    st.session_state.questions = None

# -------------------------------
# 🎓 UI
# -------------------------------
st.title("🎓 AI-Based Time-Bound Viva System")

name = st.text_input("Enter Name")
reg_no = st.text_input("Enter Registration Number")

# -------------------------------
# ▶️ START VIVA
# -------------------------------
if st.button("Start Viva"):
    if name and reg_no:
        st.session_state.start_time = time.time()

        if len(data) >= 5:
            st.session_state.questions = data.sample(5)
        elif len(data) > 0:
            st.session_state.questions = data.sample(len(data))
            st.warning(f"Only {len(data)} questions available. Showing all.")
        else:
            st.error("❌ No questions found in Google Sheet!")
            st.stop()

    else:
        st.warning("Please enter all details")

# -------------------------------
# ⏱️ TIMER DISPLAY
# -------------------------------
remaining = None

if st.session_state.start_time:
    elapsed = time.time() - st.session_state.start_time
    remaining = int(DURATION - elapsed)

    if remaining > 0:
        mins = remaining // 60
        secs = remaining % 60
        st.warning(f"⏳ Time Left: {mins:02d}:{secs:02d}")
    else:
        st.error("⛔ Time Over! Auto-submitting...")
        st.session_state.submitted = True

# -------------------------------
# ❓ QUESTIONS
# -------------------------------
answers = {}

if st.session_state.questions is not None:
    for i, row in st.session_state.questions.iterrows():
        st.subheader(f"Q{i+1}: {row['question']}")
        answers[row["id"]] = st.text_area("Your Answer", key=i)

# -------------------------------
# 🤖 AI EVALUATION (PLACEHOLDER)
# -------------------------------
def evaluate_answer(question, model_answer, student_answer):
    if not student_answer.strip():
        return "Score: 0/10 | Feedback: No answer"
    else:
        return "Score: 6/10 | Feedback: Average answer (placeholder)"

# -------------------------------
# 🚀 SUBMIT
# -------------------------------
if st.button("Submit Viva") or st.session_state.submitted:

    if st.session_state.questions is not None:

        for i, row in st.session_state.questions.iterrows():

            student_ans = answers.get(row["id"], "")

            ai_result = evaluate_answer(
                row["question"],
                row.get("model_answer", ""),
                student_ans
            )

            r_sheet.append_row([
                str(datetime.now()),
                name,
                reg_no,
                row["id"],
                row["question"],
                student_ans,
                ai_result,
                "",  # faculty score
                ""   # remarks
            ])

        st.success("✅ Viva Submitted Successfully!")
        st.session_state.submitted = True
        st.stop()
