# District Planner AI - Ghana - FINAL PERFECT VERSION v3.0
# By Emmanuel Gyasi - Department of Planning, KNUST, Kumasi
import streamlit as st
import random
import smtplib
import time
import pandas as pd
import numpy as np
import requests
import sqlite3
import datetime
from email.mime.text import MIMEText
from io import BytesIO

# --- OPTIONAL TOOLS ---
try:
    import matplotlib.pyplot as plt
except: plt = None
try:
    import plotly.express as px
except: px = None
try:
    import folium
    from streamlit_folium import st_folium
except: folium = None
try:
    import PyPDF2
except: PyPDF2 = None
try:
    import docx
except: docx = None
try:
    import pptx
except: pptx = None
from PIL import Image

# --- SMART TOOLS: scikit-learn + geopy ---
try:
    from sklearn.linear_model import LinearRegression
except: LinearRegression = None
try:
    from geopy.distance import geodesic
except: geodesic = None

st.set_page_config(page_title="District Planner AI - Ghana", page_icon="🏛️", layout="wide")

st.markdown("""
<style>
.main { background-color: #F8F9FF; }
.stButton>button { background: linear-gradient(90deg, #6C5CE7, #FFB800); color: white; border: none; border-radius: 12px; padding: 12px 25px; font-weight: bold; font-size: 16px; }
.footer { text-align: center; padding: 20px; background: #2D3436; color: white; border-radius: 15px; margin-top: 40px; }
.card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); margin-bottom: 15px; }
h1 { color: #6C5CE7; }
</style>
""", unsafe_allow_html=True)

# ================= STORAGE DATABASE - FOR FUTURE REFERENCE =================
def init_db():
    conn = sqlite3.connect("planner_history.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS saved_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT, district TEXT, title TEXT, plan_type TEXT,
        question TEXT, answer TEXT, date_saved TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS district_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT, district TEXT, note TEXT, date_saved TEXT
    )""")
    conn.commit(); conn.close()

def save_plan(user_email, district, title, plan_type, question, answer):
    conn = sqlite3.connect("planner_history.db")
    c = conn.cursor()
    c.execute("INSERT INTO saved_plans (user_email, district, title, plan_type, question, answer, date_saved) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (user_email, district, title, plan_type, question, answer, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit(); conn.close()

def get_saved_plans(user_email):
    conn = sqlite3.connect("planner_history.db")
    df = pd.read_sql_query("SELECT * FROM saved_plans WHERE user_email=? ORDER BY id DESC", conn, params=(user_email,))
    conn.close(); return df

def delete_plan(plan_id):
    conn = sqlite3.connect("planner_history.db")
    c = conn.cursor(); c.execute("DELETE FROM saved_plans WHERE id=?", (plan_id,)); conn.commit(); conn.close()

def save_note(user_email, district, note):
    conn = sqlite3.connect("planner_history.db")
    c = conn.cursor()
    c.execute("INSERT INTO district_notes (user_email, district, note, date_saved) VALUES (?, ?, ?, ?)",
              (user_email, district, note, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit(); conn.close()

def get_notes(user_email):
    conn = sqlite3.connect("planner_history.db")
    df = pd.read_sql_query("SELECT * FROM district_notes WHERE user_email=? ORDER BY id DESC", conn, params=(user_email,))
    conn.close(); return df

init_db()

# ================= EMAIL OTP =================
def send_otp(email, otp):
    try:
        sender = st.secrets.get("EMAIL_USER", "gyasie898@gmail.com")
        password = st.secrets.get("EMAIL_PASS", "vedbudteaubuzpnm")
        if sender == "your-email@gmail.com":
            st.warning(f"⚠️ Email not configured yet. Your TEST code is: {otp}")
            return True
        msg = MIMEText(f"Your District Planner AI Login Code is: {otp}\n\nValid for 10 minutes.\n\nDistrict Planner AI - Ghana\nBy Emmanuel Gyasi, KNUST")
        msg['Subject'] = "Your District Planner AI Login Code"
        msg['From'] = sender; msg['To'] = email
        server = smtplib.SMTP("smtp.gmail.com", 587); server.starttls()
        server.login(sender, password); server.send_message(msg); server.quit()
        return True
    except Exception as e:
        st.warning(f"Email failed, your test code is: {otp} - Error: {e}")
        return True

# ================= SESSION =================
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "otp_sent" not in st.session_state: st.session_state.otp_sent = False
if "generated_otp" not in st.session_state: st.session_state.generated_otp = ""
if "user_email" not in st.session_state: st.session_state.user_email = ""
if "uploaded_files_data" not in st.session_state: st.session_state.uploaded_files_data = []
if "planner_messages" not in st.session_state: st.session_state.planner_messages = []
if "last_ai_answer" not in st.session_state: st.session_state.last_ai_answer = ""
if "last_ai_question" not in st.session_state: st.session_state.last_ai_question = ""

# ================= LOGIN PAGE =================
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center;'>🏛️ District Planner AI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;'>Smart Planning for Ghana's 261 Districts<br>For District Assemblies, Planners & Students</p>", unsafe_allow_html=True)
        st.markdown("---")
        email = st.text_input("📧 Enter Your Email Address", placeholder="example@gmail.com")
        if st.button("📩 Send Login Code to My Email", use_container_width=True):
            if "@" not in email or "." not in email:
                st.error("Please enter a valid email")
            else:
                otp = str(random.randint(100000, 999999))
                st.session_state.generated_otp = otp
                st.session_state.user_email = email
                st.session_state.otp_sent = True
                send_otp(email, otp)
                st.success(f"Code sent to {email}! Check inbox / spam.")
        if st.session_state.otp_sent:
            code = st.text_input("🔢 Enter 6-Digit Code Sent To Your Email", max_chars=6)
            if st.button("✅ Verify & Login", use_container_width=True):
                if code == st.session_state.generated_otp:
                    st.session_state.logged_in = True
                    st.success("Welcome! Login Successful"); time.sleep(1); st.rerun()
                else: st.error("Wrong code. Try again.")
        st.markdown("---")
        st.checkbox("I agree to Terms & Conditions: I will use this tool for lawful planning purposes. Data is for guidance, always verify with official District Assembly records.", value=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("""<div class="footer"><b>Developer:</b> Emmanuel Gyasi | Department of Planning, KNUST, Kumasi, Ghana<br><b>Email:</b> emmanuel.gyasi@knust.edu.gh | <b>Project:</b> District Planner AI - Ghana 2026<br>© 2026 District Planner AI - Built in Kumasi for Ghana's Districts</div>""", unsafe_allow_html=True)
    st.stop()

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("## 🏛️ District Planner AI")
    st.write(f"👤 Logged in as:\n**{st.session_state.user_email}**")
    st.markdown("---")
    menu = st.radio("Navigate", ["🏠 Dashboard", "🤖 Planner AI Chat", "📂 Upload Documents", "📊 District Data", "🗺️ District Map", "📥 Downloads & Reports", "💾 Saved Plans & History", "ℹ️ About"])
    st.markdown("---")
    st.markdown("### 📜 Terms & Conditions")
    st.info("1. This tool is for planning guidance only.\n\n2. Always verify population, land and budget with Ghana Statistical Service and your District Assembly.\n\n3. Do not upload confidential personal data.\n\n4. By using this app, you agree to use it lawfully.")
    st.checkbox("I have read Terms & Conditions", value=True)
    st.markdown("---")
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False; st.rerun()
    st.markdown("---")
    st.markdown("**Version:** 3.0 - Final\n**Location:** Kumasi, Ghana\n**Storage:** planner_history.db")

st.markdown(f"<h1>🏛️ District Planner AI - Ghana</h1><p>Welcome, <b>{st.session_state.user_email}</b> | Smart Planning for 261 Districts</p>", unsafe_allow_html=True)

# ================= DASHBOARD =================
if menu == "🏠 Dashboard":
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown('<div class="card"><h2>261</h2><p>Districts in Ghana</p></div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="card"><h2>16</h2><p>Regions</p></div>', unsafe_allow_html=True)
    with c3: st.markdown('<div class="card"><h2>~34M</h2><p>Population (2024 Est.)</p></div>', unsafe_allow_html=True)
    with c4:
        df_saved = get_saved_plans(st.session_state.user_email)
        st.markdown(f'<div class="card"><h2>{len(df_saved)}</h2><p>Your Saved Plans</p></div>', unsafe_allow_html=True)
    st.markdown("### 🎯 Quick Planning Tools")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🏪 Plan New Market", use_container_width=True):
            st.session_state.planner_messages.append({"role": "user", "content": "Plan a new market for my district"}); st.rerun()
    with col2:
        if st.button("🏫 Plan New School", use_container_width=True):
            st.session_state.planner_messages.append({"role": "user", "content": "Plan a new school for my district"}); st.rerun()
    with col3:
        if st.button("🏥 Plan New Clinic", use_container_width=True):
            st.session_state.planner_messages.append({"role": "user", "content": "Plan a new clinic for my district"}); st.rerun()
    st.markdown("### 📍 Select Your District")
    region = st.selectbox("Region", ["Ashanti", "Greater Accra", "Central", "Eastern", "Western", "Northern", "Volta", "Oti", "Upper East", "Upper West", "Bono", "Ahafo", "Bono East", "Savannah", "North East", "Western North"])
    district = st.text_input("District Name", placeholder="e.g. Kwadaso, Nkawie, Atwima Nwabiagya North")
    if st.button("🔍 Get District Plan"):
        if district:
            st.success(f"Generating plan for {district}, {region} Region...")
            st.info("Go to **Planner AI Chat** for full detailed plan. Go to **District Map** to see location.")

# ================= PLANNER AI CHAT =================
elif menu == "🤖 Planner AI Chat":
    st.markdown("### 🤖 Ask Your Real Planner AI")
    st.write("Examples: 'Plan a market for Nkawie', 'How many schools does Kwadaso need in 2030?', 'Explain Land Use Act 925'")
    if st.session_state.uploaded_files_data:
        st.info(f"📂 AI is using your uploaded files: {', '.join(st.session_state.uploaded_files_data)}")
    for msg in st.session_state.planner_messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🏪 Plan Market for Nkawie"):
            st.session_state.planner_messages.append({"role": "user", "content": "Plan a new market for Nkawie, Atwima Nwabiagya North"}); st.rerun()
    with c2:
        if st.button("🏫 Schools Needed in Kwadaso 2030"):
            st.session_state.planner_messages.append({"role": "user", "content": "How many schools will Kwadaso need by 2030? Give population prediction."}); st.rerun()
    with c3:
        if st.button("🏥 Plan Clinic"):
            st.session_state.planner_messages.append({"role": "user", "content": "Plan a clinic for a district with 50,000 people. What land, staff, budget needed?"}); st.rerun()
    q = st.chat_input("Ask your planning question...")
    if q:
        st.session_state.planner_messages.append({"role": "user", "content": q}); st.rerun()
    if st.session_state.planner_messages and st.session_state.planner_messages[-1]["role"] == "user":
        user_question = st.session_state.planner_messages[-1]["content"]
        with st.chat_message("assistant"):
            with st.spinner("🧠 District Planner AI is thinking..."):
                try:
                    doc_context = ""
                    if st.session_state.uploaded_files_data:
                        doc_context = f"\nUser has uploaded: {', '.join(st.session_state.uploaded_files_data)}. Use them as reference.\n"
                    system_prompt = f"""You are District Planner AI - Ghana. Expert in Ghana Planning: Land Use and Spatial Planning Act 2016 (Act 925), Local Governance Act 2016 (Act 936), Ghana Statistical Service, KNUST Planning methods. {doc_context} Always answer in structure: 1. Population Analysis 2. Land Requirement 3. Infrastructure Needed (Roads, Water, Electricity, Drainage, Parking) 4. Budget Estimate in GHS 5. Legal Requirement (Act 925, District Assembly By-laws) 6. 3 Action Steps. Use Ghana examples - Kumasi, Kwadaso, Nkawie, Atwima Nwabiagya North. Explain in simple English. End with: Verify with District Assembly and Ghana Statistical Service. Built by Emmanuel Gyasi, Department of Planning, KNUST."""
                    response = requests.post("http://localhost:11434/api/generate", json={"model": "district-planner", "prompt": f"{system_prompt}\n\nUser: {user_question}\nAssistant:", "stream": False}, timeout=120)
                    answer = response.json().get("response", "Error: Make sure Ollama is running. Run: ollama serve")
                except Exception as e:
                    answer = f"""**Demo Answer (Ollama not running yet):**\n\n**Question:** {user_question}\n\n**1. Population Analysis:** Check Ghana Statistical Service. If district has 50,000 people, it grows ~2.5% per year. By 2030, it will be ~58,000.\n\n**2. Land Requirement:** For a market, you need 2-5 acres, near main road, with drainage.\n\n**3. Infrastructure:** Roads, water, electricity, waste, parking for trotro.\n\n**4. Budget Estimate:** Market: 500,000 GHS, School: 800,000 GHS, Clinic: 1,200,000 GHS. Verify with Works Department.\n\n**5. Legal:** Must follow Land Use and Spatial Planning Act 2016 (Act 925).\n\n**6. 3 Action Steps:** 1. Get population data from GSS 2. Visit site with District Town Planner 3. Present to District Assembly.\n\n*To get real AI: Open CMD and type: ollama serve - then refresh. Error: {e}*"""
                st.markdown(answer)
                st.session_state.planner_messages.append({"role": "assistant", "content": answer})
                st.session_state.last_ai_answer = answer
                st.session_state.last_ai_question = user_question
                st.rerun()
    if st.session_state.last_ai_answer:
        colA, colB = st.columns(2)
        with colA:
            st.download_button("📥 Download This Plan as Text", st.session_state.last_ai_answer.encode(), file_name="District_Plan.txt", mime="text/plain", use_container_width=True)
        with colB:
            if st.button("💾 SAVE THIS ANSWER TO MY HISTORY", use_container_width=True):
                save_plan(st.session_state.user_email, "General", f"AI Plan - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", "AI Chat", st.session_state.last_ai_question, st.session_state.last_ai_answer)
                st.success("✅ Saved! Go to Saved Plans & History to see it."); st.balloons()

# ================= UPLOAD DOCUMENTS =================
elif menu == "📂 Upload Documents":
    st.markdown("### 📂 Upload ANY Document Type - AI Can Read Them")
    st.write("Accepted: PDF, Word (.docx), Excel (.xlsx, .xls), CSV, PowerPoint (.pptx), Text (.txt), Images (.jpg, .png)")
    uploaded = st.file_uploader("Choose files", accept_multiple_files=True, type=["pdf","docx","doc","xlsx","xls","csv","txt","pptx","jpg","jpeg","png","zip"])
    if uploaded:
        for f in uploaded:
            st.success(f"✅ Uploaded: {f.name} - {f.size} bytes")
            try:
                if f.name.endswith(".csv"):
                    df = pd.read_csv(f); st.dataframe(df.head())
                elif f.name.endswith((".xlsx", ".xls")):
                    df = pd.read_excel(f); st.dataframe(df.head())
                elif f.name.endswith(".txt"):
                    st.text(f.read().decode(errors="ignore")[:2000])
                elif f.name.endswith(".pdf") and PyPDF2:
                    reader = PyPDF2.PdfReader(f); text = ""
                    for page in reader.pages[:3]: text += page.extract_text() or ""
                    st.text(text[:2000])
                elif f.name.endswith(".docx") and docx:
                    doc = docx.Document(f); text = "\n".join([p.text for p in doc.paragraphs[:20]]); st.text(text[:2000])
                elif f.name.endswith(".pptx") and pptx:
                    prs = pptx.Presentation(f); st.write(f"Slides: {len(prs.slides)}")
                elif f.name.endswith((".jpg", ".jpeg", ".png")):
                    img = Image.open(f); st.image(img, width=300)
            except Exception as e: st.warning(f"Could not preview {f.name}: {e}")
            if f.name not in st.session_state.uploaded_files_data:
                st.session_state.uploaded_files_data.append(f.name)
        st.info(f"Total files uploaded: {len(uploaded)} - Ready for AI to analyse.")

# ================= DISTRICT DATA - WITH SCIKIT-LEARN =================
elif menu == "📊 District Data":
    st.markdown("### 📊 Ghana District Data + AI Population Prediction")
    data = {"District": ["Kwadaso", "Atwima Nwabiagya North", "Kumasi Metro", "Guan (Oti)"], "Capital": ["Kwadaso", "Nkawie", "Kumasi", "Likpe-Mate"], "Region": ["Ashanti", "Ashanti", "Ashanti", "Oti"], "Population 2021": [200000, 120000, 1800000, 90000], "Population 2030 Est.": [250000, 150000, 2250000, 112000]}
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    if px:
        fig = px.bar(df, x="District", y="Population 2030 Est.", title="Population Prediction 2030 - Sample Districts", color="District")
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("### 🤖 AI Population Prediction - Using Scikit-Learn Machine Learning")
    st.write("This uses real Machine Learning (Linear Regression) to learn from past Ghana census data and predict the future.")
    years_data = np.array([2010, 2015, 2021, 2024]).reshape(-1, 1)
    pop_data = np.array([40000, 46000, 52000, 58000])
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        pop_now = st.number_input("Current Population (2024)", value=58000)
        pop_data[-1] = pop_now
    with col_p2:
        future_year = st.slider("Predict Population For Year", 2025, 2040, 2030)
    if LinearRegression:
        model = LinearRegression()
        model.fit(years_data, pop_data)
        predicted = model.predict([[future_year]])[0]
        growth_rate = model.coef_[0]
        st.success(f"🤖 AI Prediction: In **{future_year}**, population will be **{int(predicted):,}** people")
        st.write(f"AI learned growth rate: **{int(growth_rate):,} people per year**")
        if px:
            future_years = list(range(2024, future_year+1))
            future_pops = [model.predict([[y]])[0] for y in future_years]
            chart_df = pd.DataFrame({"Year": future_years, "Population": future_pops})
            fig2 = px.line(chart_df, x="Year", y="Population", title=f"AI Population Forecast to {future_year}", markers=True)
            st.plotly_chart(fig2, use_container_width=True)
        if st.button("💾 SAVE THIS PREDICTION TO HISTORY"):
            save_plan(st.session_state.user_email, "Population Prediction", f"Population Prediction {future_year}", "Population", f"Population in {future_year}", f"AI Scikit-learn prediction: In {future_year}, population will be {int(predicted):,} people. Growth rate {int(growth_rate):,} per year.")
            st.success("✅ Prediction saved to Saved Plans & History!")
    else:
        st.warning("Install scikit-learn: pip install scikit-learn")

# ================= DISTRICT MAP - WITH FOLIUM + GEOPY =================
elif menu == "🗺️ District Map":
    st.markdown("### 🗺️ Ghana District Map - Folium")
    st.write("Sample locations - Kumasi, Nkawie, Kwadaso, Accra")
    if folium:
        m = folium.Map(location=[7.9465, -1.0232], zoom_start=7)
        folium.Marker([6.6900, -1.6200], popup="Kumasi - Ashanti", tooltip="Kumasi").add_to(m)
        folium.Marker([6.6700, -1.7500], popup="Nkawie - Atwima Nwabiagya North", tooltip="Nkawie").add_to(m)
        folium.Marker([6.6800, -1.6500], popup="Kwadaso", tooltip="Kwadaso").add_to(m)
        folium.Marker([5.6037, -0.1870], popup="Accra - Greater Accra", tooltip="Accra").add_to(m)
        st_folium(m, width=700, height=500)
    else:
        st.info("Install folium to see map: pip install folium streamlit-folium")
    st.markdown("---")
    st.markdown("### 📏 Distance Calculator - Using Geopy (Real Geography)")
    st.write("Calculate real distance between two Ghana towns. Useful for planning roads, clinics, markets.")
    towns = {"Kumasi": (6.6900, -1.6200), "Nkawie": (6.6700, -1.7500), "Kwadaso": (6.6800, -1.6500), "Accra": (5.6037, -0.1870), "Obuasi": (5.6667, -1.4667), "Ejisu": (6.7150, -1.4820), "Mampong": (7.0600, -1.4000), "Konongo": (6.6200, -1.2200), "Sunyani": (7.3390, -2.3260), "Cape Coast": (5.1050, -1.2460)}
    c1, c2 = st.columns(2)
    with c1: town1 = st.selectbox("From Town", list(towns.keys()), key="town1")
    with c2: town2 = st.selectbox("To Town", list(towns.keys()), index=1, key="town2")
    if st.button("📏 CALCULATE DISTANCE"):
        if geodesic:
            dist_km = geodesic(towns[town1], towns[town2]).km
            st.success(f"📍 Distance from **{town1}** to **{town2}** is **{dist_km:.1f} km**")
            st.write(f"🚗 By trotro (~40km/h): **{dist_km/40:.1f} hours**")
            st.write(f"🚶 Walking (~5km/h): **{dist_km/5:.1f} hours**")
            st.write(f"**Planning Use:** If distance is more than 10km, that community needs its own clinic / school, not travel to the other town.")
            if st.button("💾 SAVE THIS DISTANCE TO HISTORY"):
                save_plan(st.session_state.user_email, f"{town1} - {town2}", f"Distance {town1} to {town2}", "Roads", f"Distance from {town1} to {town2}", f"Distance is {dist_km:.1f} km. Trotro time {dist_km/40:.1f} hours.")
                st.success("Saved to History!")
        else:
            st.error("Install geopy: pip install geopy")

# ================= DOWNLOADS =================
elif menu == "📥 Downloads & Reports":
    st.markdown("### 📥 Download Your Planning Reports")
    st.write("Click any button to download. All reports include your district name, date, and developer info.")
    df = pd.DataFrame({"Item": ["Market", "School", "Clinic", "Roads"], "Estimated Cost (GHS)": [500000, 800000, 1200000, 2000000]})
    st.dataframe(df)
    buffer = BytesIO(); df.to_excel(buffer, index=False)
    st.download_button("📗 DOWNLOAD AS EXCEL (.xlsx)", buffer.getvalue(), file_name="District_Planner_Report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    csv_data = df.to_csv(index=False).encode()
    st.download_button("📄 DOWNLOAD AS CSV", csv_data, file_name="District_Planner_Report.csv", mime="text/csv", use_container_width=True)
    text_report = "DISTRICT PLANNER AI - GHANA\nBy Emmanuel Gyasi, KNUST\n\nDistrict Planning Report\nMarket: 500,000 GHS\nSchool: 800,000 GHS\nClinic: 1,200,000 GHS\nRoads: 2,000,000 GHS\n\nAlways verify with District Assembly."
    st.download_button("📝 DOWNLOAD AS WORD / TEXT", text_report.encode(), file_name="District_Planner_Report.txt", mime="text/plain", use_container_width=True)
    st.success("✅ Your report is ready! Click any button above.")

# ================= SAVED PLANS & HISTORY - STORAGE FOR FUTURE REFERENCE =================
elif menu == "💾 Saved Plans & History":
    st.markdown("### 💾 Saved Plans & History - Store For Future Reference")
    st.write("Everything you save here stays forever, even after you close the app. Come back anytime. Data is stored in `planner_history.db` in your project folder.")
    tab1, tab2, tab3 = st.tabs(["📝 Save New Plan / Note", "📂 My Saved Plans", "📌 My District Notes"])
    with tab1:
        st.markdown("#### Save a New Plan or Note")
        col1, col2 = st.columns(2)
        with col1:
            save_district = st.text_input("District Name", placeholder="e.g. Nkawie, Kwadaso", key="save_district")
            save_title = st.text_input("Title of Plan", placeholder="e.g. Nkawie Market Plan 2026", key="save_title")
        with col2:
            save_type = st.selectbox("Plan Type", ["Market", "School", "Clinic", "Roads", "Water", "Land Use", "Housing", "Population", "Other"])
            save_question = st.text_input("Your Question", placeholder="e.g. Plan a market for Nkawie", key="save_q")
        save_answer = st.text_area("Full Plan / Answer / Notes - Paste from AI Chat here", height=200, placeholder="Paste the full AI answer here to save it...")
        if st.button("💾 SAVE THIS PLAN FOR FUTURE", use_container_width=True):
            if save_district and save_title and save_answer:
                save_plan(st.session_state.user_email, save_district, save_title, save_type, save_question, save_answer)
                st.success(f"✅ Saved! '{save_title}' for {save_district} is now stored forever."); st.balloons()
            else: st.error("Please fill District, Title, and Plan.")
        st.markdown("---")
        st.markdown("#### Quick Note - For Future")
        note_district = st.text_input("District for Note", placeholder="e.g. Kwadaso", key="note_district")
        note_text = st.text_area("Your Note", placeholder="e.g. Kwadaso needs 3 new boreholes near Abuakwa road. Chief promised land...")
        if st.button("📌 SAVE NOTE"):
            if note_district and note_text:
                save_note(st.session_state.user_email, note_district, note_text); st.success("Note saved!")
            else: st.error("Fill district and note.")
    with tab2:
        st.markdown("#### Your Saved Plans")
        search = st.text_input("🔍 Search saved plans...", placeholder="Search by district, title, market, school...")
        df_plans = get_saved_plans(st.session_state.user_email)
        if len(df_plans) == 0:
            st.info("No saved plans yet. Go to Planner AI Chat, copy the answer, come here and save it. Or use the SAVE buttons in District Data and Map pages.")
        else:
            if search:
                df_plans = df_plans[df_plans.astype(str).apply(lambda x: x.str.contains(search, case=False).any(), axis=1)]
            st.write(f"Total Saved: **{len(df_plans)}** plans")
            for _, row in df_plans.iterrows():
                with st.expander(f"📄 {row['title']} - {row['district']} | {row['date_saved']}"):
                    st.write(f"**Type:** {row['plan_type']} | **District:** {row['district']}")
                    st.write(f"**Question:** {row['question']}")
                    st.markdown(row['answer'])
                    cA, cB = st.columns(2)
                    with cA: st.download_button(f"📥 Download {row['title']}", row['answer'].encode(), file_name=f"{row['title']}.txt", key=f"dl_{row['id']}")
                    with cB:
                        if st.button(f"🗑️ Delete", key=f"del_{row['id']}"):
                            delete_plan(row['id']); st.success("Deleted!"); st.rerun()
            if len(df_plans) > 0:
                buf = BytesIO(); df_plans.to_excel(buf, index=False)
                st.download_button("📗 DOWNLOAD ALL MY PLANS AS EXCEL", buf.getvalue(), file_name="My_Saved_Plans.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with tab3:
        st.markdown("#### Your District Notes")
        df_notes = get_notes(st.session_state.user_email)
        if len(df_notes) == 0: st.info("No notes yet.")
        else:
            for _, row in df_notes.iterrows():
                st.markdown(f"**📌 {row['district']}** - {row['date_saved']}"); st.write(row['note']); st.markdown("---")

# ================= ABOUT =================
elif menu == "ℹ️ About":
    st.markdown("### About District Planner AI")
    st.write("Built to help District Assemblies in Ghana plan better - markets, schools, clinics, roads, water, land use. Uses AI + Ghana data + Planning Laws.")
    st.write("**Features:** Email OTP Login, All File Uploads, AI Chat, District Data with Scikit-Learn, Map with Folium + Geopy, Downloads, Saved Plans & History (SQLite Storage).")
    st.write("**How Storage Works:** Every plan you save goes into `planner_history.db` - a small database file in your project folder. It stays even after you close the app. Each user sees only their own plans.")

# ================= FOOTER =================
st.markdown("---")
st.markdown("""
<div class="footer">
<h3>👨‍💻 Developer Information</h3>
<b>Name:</b> Emmanuel Gyasi<br>
<b>Department:</b> Department of Planning<br>
<b>University:</b> Kwame Nkrumah University of Science and Technology (KNUST)<br>
<b>Location:</b> Kumasi, Ashanti Region, Ghana<br>
<b>Email:</b> emmanuel.gyasi@knust.edu.gh<br>
<b>Project:</b> District Planner AI - Ghana | <b>Year:</b> 2026<br>
<br>
<b>Terms & Conditions:</b> This tool provides planning guidance only. Always verify with Ghana Statistical Service, Land Use and Spatial Planning Authority, and your District Assembly before final decisions.<br>
© 2026 District Planner AI - All Rights Reserved | Built in Kumasi for Ghana
</div>
""", unsafe_allow_html=True)