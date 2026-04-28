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
#MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# 🔐 GOOGLE SHEETS CONNECTION
# -------------------------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], scope
)

client = gspread.authorize(creds)

sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1bz09BMyKLJ7YZRobi9cP2ltjiYwLM05ouu4KYkpBX-s"
)

q_sheet = sheet.worksheet("questions")
r_sheet = sheet.worksheet("responses")

@st.cache_data
def load_data():
    return pd.DataFrame(q_sheet.get_all_records())

data = load_data()

# -------------------------------
# 🧠 SESSION STATE
# -------------------------------
for key, default in {
    "start_time": None,
    "submitted": False,
    "questions": None,
    "tab_switch_count": 0
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# -------------------------------
# 🔁 CAPTURE TAB SWITCH FROM URL
# -------------------------------
params = st.query_params

if "tab_switch" in params:
    try:
        new_val = int(params["tab_switch"])
        if new_val > st.session_state.tab_switch_count:
            st.session_state.tab_switch_count = new_val
    except:
        pass

# -------------------------------
# 🎓 STUDENT INFO
# -------------------------------
st.title("🎓 AI-Based Viva System")

name = st.text_input("Enter Name")
reg_no = st.text_input("Enter Registration Number")

# -------------------------------
# 🖥️ FULLSCREEN + TAB TRACKING JS
# -------------------------------
html("""
<script>
// init counter
if (!localStorage.getItem("tabSwitchCount")) {
    localStorage.setItem("tabSwitchCount", "0");
}

function startViva() {
    let elem = document.body;
    if (elem.requestFullscreen) elem.requestFullscreen();

    const buttons = window.parent.document.querySelectorAll("button");
    buttons.forEach(btn => {
        if (btn.innerText === "Start Viva Hidden") btn.click();
    });
}

// 🔥 RELIABLE TAB TRACKING
document.addEventListener("visibilitychange", function() {
    if (document.hidden) {
        let count = parseInt(localStorage.getItem("tabSwitchCount") || "0");
        count += 1;
        localStorage.setItem("tabSwitchCount", count);

        alert("⚠️ Tab switched! Count: " + count);

        // reload with param
        window.location.href = window.location.pathname + "?tab_switch=" + count;
    }
});
</script>

<button onclick="startViva()" style="padding:12px;font-size:18px;background:#4CAF50;color:white;border:none;border-radius:5px;">
🚀 Start Viva (Full Screen)
</button>
""", height=90)

# hidden trigger
start_clicked = st.button("Start Viva Hidden")

# -------------------------------
# ▶️ START LOGIC
# -------------------------------
if start_clicked:
    if name and reg_no:
        st.session_state.start_time = time.time()

        if data.empty:
            st.error("❌ No questions found!")
            st.stop()

        st.session_state.questions = data.sample(min(5, len(data)))
    else:
        st.warning("Please enter all details")

# -------------------------------
# ⏱️ TIMER
# -------------------------------
DURATION = 300

if st.session_state.start_time:
    elapsed = time.time() - st.session_state.start_time
    remaining = int(DURATION - elapsed)

    st.warning(f"⚠️ Tab Switch Count: {st.session_state.tab_switch_count}")

    if remaining > 0:
        st.warning(f"⏳ Time Left: {remaining//60:02d}:{remaining%60:02d}")
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
# 🧠 SCORING
# -------------------------------
def evaluate_answer(ans, keywords):
    if not ans.strip():
        return 0

    keyword_score = sum(
        1 for k in keywords.split(",")
        if k.strip().lower() in ans.lower()
    )

    length_score = min(len(ans.split()) // 5, 5)

    return min(keyword_score + length_score, 10)

# -------------------------------
# 🚀 SUBMIT
# -------------------------------
if st.button("Submit Viva") or st.session_state.submitted:

    if st.session_state.questions is not None:

        total_score = 0
        max_score = 0
        all_answers = []

        for _, row in st.session_state.questions.iterrows():
            student_ans = answers.get(row["id"], "")
            keywords = row.get("keywords", "")

            score = evaluate_answer(student_ans, keywords)

            total_score += score
            max_score += 10
            all_answers.append(f"Q{row['id']}: {student_ans}")

        answers_text = "\n".join(all_answers)

        final_tab_count = st.session_state.tab_switch_count

        r_sheet.append_row([
            str(datetime.now()),
            name,
            reg_no,
            answers_text,
            total_score,
            max_score,
            final_tab_count
        ])

        st.success(f"✅ Submitted! Score: {total_score}/{max_score}")
        st.session_state.submitted = True
        st.stop()
