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
# 🔐 GOOGLE SHEETS CONNECTION
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

@st.cache_data
def load_data():
    return pd.DataFrame(q_sheet.get_all_records())

data = load_data()

# -------------------------------
# 🧠 SESSION STATE
# -------------------------------
if "start_time" not in st.session_state:
    st.session_state.start_time = None

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "questions" not in st.session_state:
    st.session_state.questions = None

# -------------------------------
# 🖥️ FULLSCREEN + ANTI-CHEATING
# -------------------------------
html("""
<script>
function startViva() {
    let elem = document.body;
    if (elem.requestFullscreen) {
        elem.requestFullscreen();
    }

    document.getElementById("start_hidden").click();
}

document.addEventListener("visibilitychange", function() {
    if (document.hidden) {
        alert("⚠️ Tab switched! This activity is monitored.");
    }
});
</script>

<button onclick="startViva()" style="
    padding:12px;
    font-size:18px;
    background-color:#4CAF50;
    color:white;
    border:none;
    border-radius:5px;
">
🚀 Start Viva (Full Screen)
</button>
""")

# Hidden Streamlit button
start_clicked = st.button("hidden_start", key="start_hidden")

# -------------------------------
# 🎓 UI
# -------------------------------
st.title("🎓 AI-Based Viva System")

name = st.text_input("Enter Name")
reg_no = st.text_input("Enter Registration Number")

# -------------------------------
# ▶️ START LOGIC
# -------------------------------
if start_clicked:
    if name and reg_no:
        st.session_state.start_time = time.time()

        if data.empty:
            st.error("❌ No questions found in Google Sheet!")
            st.stop()

        st.session_state.questions = data.sample(min(5, len(data)))

    else:
        st.warning("Please enter all details")

# -------------------------------
# ⏱️ TIMER
# -------------------------------
DURATION = 600  # 10 minutes
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
all_answers = []

if st.session_state.questions is not None:
    for i, row in st.session_state.questions.iterrows():
        st.subheader(f"Q{i+1}: {row['question']}")
        ans = st.text_area("Your Answer", key=i)
        answers[row["id"]] = ans
        all_answers.append(f"Q{row['id']}: {ans}")

# -------------------------------
# 🤖 AI EVALUATION (PLACEHOLDER)
# -------------------------------
def evaluate_answer(ans):
    if not ans.strip():
        return 0
    return 6  # placeholder score

# -------------------------------
# 🚀 SUBMIT
# -------------------------------
if st.button("Submit Viva") or st.session_state.submitted:

    if st.session_state.questions is not None:

        total_score = 0
        max_score = 0

        for i, row in st.session_state.questions.iterrows():
            score = evaluate_answer(answers.get(row["id"], ""))
            total_score += score
            max_score += 10

        answers_text = "\n".join(all_answers)

        # ✅ Save ONE ROW ONLY
        r_sheet.append_row([
            str(datetime.now()),
            name,
            reg_no,
            answers_text,
            total_score,
            max_score
        ])

        st.success(f"✅ Submitted! Score: {total_score}/{max_score}")
        st.session_state.submitted = True
        st.stop()
