import streamlit as st
import pandas as pd
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import openai  # or Gemini

# 🔐 Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

sheet = client.open("VivaSystem")
q_sheet = sheet.worksheet("questions")
r_sheet = sheet.worksheet("responses")

data = pd.DataFrame(q_sheet.get_all_records())

# 🎯 Generate random questions
if "questions" not in st.session_state:
    st.session_state.questions = data.sample(5)

st.title("🎓 AI-Based Viva System")

# 👤 Student info
name = st.text_input("Student Name")
reg_no = st.text_input("Registration Number")

answers = {}

# 📌 Display questions
for i, row in st.session_state.questions.iterrows():
    st.subheader(f"Q{i+1}: {row['question']}")
    answers[row["id"]] = st.text_area("Your Answer", key=i)

# 🤖 AI Evaluation Function
def evaluate_answer(question, model_answer, student_answer):
    prompt = f"""
    Evaluate the student's answer.

    Question: {question}
    Model Answer: {model_answer}
    Student Answer: {student_answer}

    Give:
    Score out of 10
    Feedback in 2 lines
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role":"user","content":prompt}]
    )

    return response['choices'][0]['message']['content']

# 🚀 Submit
if st.button("Submit Viva"):
    for i, row in st.session_state.questions.iterrows():

        ai_result = evaluate_answer(
            row["question"],
            row["model_answer"],
            answers[row["id"]]
        )

        r_sheet.append_row([
            str(datetime.now()),
            name,
            reg_no,
            row["id"],
            row["question"],
            answers[row["id"]],
            ai_result,   # AI output
            "",          # final score (faculty)
            ""           # remarks
        ])

    st.success("✅ Viva submitted & AI evaluated!")
