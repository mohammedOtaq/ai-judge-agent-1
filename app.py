import streamlit as st
from dotenv import load_dotenv
import os
import openai
from docx import Document
import fitz  # PyMuPDF
from datetime import datetime, timedelta

# ✅ إعداد صفحة Streamlit
st.set_page_config(page_title="⚖️ Smart Judge | القاضي الذكي", layout="centered")

# تحميل المتغيرات البيئية
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ ⏰ التايمر يبدأ عند أول دخول للجلسة
if "start_time" not in st.session_state:
    st.session_state.start_time = datetime.utcnow()

# تحديد نهاية الوقت
end_time = st.session_state.start_time + timedelta(hours=1)
remaining_time = end_time - datetime.utcnow()

if remaining_time.total_seconds() > 0:
    mins, secs = divmod(int(remaining_time.total_seconds()), 60)
    st.info(f"🕒 Free time left: {mins} minutes and {secs} seconds")
else:
    st.error("⛔ Your free usage time is over. Please upgrade to continue.")
    st.stop()

# 🧠 دالة استدعاء GPT
def ask_judge_agent(user_input, lang):
    if lang == "Arabic":
        prompt = f"""
أنت قاضٍ مدني محترف تصدر الأحكام بأسلوب قانوني منضبط.
اقرأ القضية التالية التي قدمها المستخدم، ثم أصدِر حكمك الكامل متضمنًا:
- القرار القضائي
- الحيثيات القانونية والواقعية
- الاستناد إلى السوابق إن أمكن

نص الدعوى:
{user_input}

الحكم:
"""
    else:
        prompt = f"""
You are a professional civil judge. 
Read the following case submitted by the user and issue a full judgment including:
- The final decision
- Legal and factual reasoning
- Reference to precedents if possible

Case text:
{user_input}

Judgment:
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Error connecting to OpenAI:\n{e}"

# 📄 قراءة ملفات PDF
def extract_text_from_pdf(uploaded_file):
    text = ""
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

# 📄 قراءة ملفات Word
def extract_text_from_docx(uploaded_file):
    doc = Document(uploaded_file)
    return "\n".join([para.text for para in doc.paragraphs])

# 🖥️ واجهة Streamlit
st.title("⚖️ Smart Judge | القاضي الذكي")

# ✅ اختيار اللغة
lang = st.radio("🌐 Choose Language | اختر اللغة:", ["English", "Arabic"])

# اختيار طريقة الإدخال
input_method = st.radio("📎 Select input method:", ["Manual typing", "Upload PDF / Word"])

user_input = ""

# الكتابة اليدوية
if input_method == "Manual typing":
    placeholder = "✍️ Write your case here..." if lang == "English" else "✍️ اكتب هنا وقائع القضية أو النزاع:"
    user_input = st.text_area(placeholder, height=300)

# رفع الملفات
else:
    uploaded_file = st.file_uploader("📄 Upload PDF or Word file", type=["pdf", "docx"])
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            user_input = extract_text_from_pdf(uploaded_file)
        elif uploaded_file.type in [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword"
        ]:
            user_input = extract_text_from_docx(uploaded_file)

        if user_input:
            st.success("✅ Case text extracted successfully.")
            st.text_area("📄 Extracted case text:", user_input, height=300)

# 🧠 إصدار الحكم
if st.button("🧠 Get Judgment"):
    if not user_input.strip():
        st.warning("Please enter or upload a case text." if lang == "English" else "يرجى كتابة أو رفع نص القضية.")
    else:
        with st.spinner("📚 Analyzing case..." if lang == "English" else "📚 يتم تحليل القضية..."):
            result = ask_judge_agent(user_input, lang)
            st.session_state['judgment'] = result
            st.success("✅ Judgment issued.")
            st.subheader("📜 Judgment:")
            st.text_area("📜 Result:", result, height=400)

# 🔄 التفاعل مع الحكم
if "judgment" in st.session_state:
    st.markdown("---")
    st.subheader("🔄 Do you agree with the judgment? Add a clarification:" if lang == "English" else "🔄 هل توافق على الحكم؟ أو لديك توضيح إضافي؟")

    with st.form("response_form"):
        user_reply = st.text_area("🗣️ Your comment:" if lang == "English" else "🗣️ اكتب ملاحظتك أو اعتراضك هنا:", height=150)
        submitted = st.form_submit_button("📨 Submit")

        if submitted:
            with st.spinner("🤖 Reviewing your comment..." if lang == "English" else "🤖 يتم مراجعة ملاحظتك..."):
                follow_up_prompt = f"""
Previous judgment:
{st.session_state['judgment']}

User comment:
{user_reply}

Please review and revise or clarify the judgment if needed.
"""
                follow_up = ask_judge_agent(follow_up_prompt, lang)
                st.success("✅ Review complete.")
                st.subheader("📌 Judge's Response:")
                st.text_area("📬 Response:", follow_up, height=300)
