import streamlit as st
import os
import sqlite3
import pandas as pd
from datetime import datetime
import folium
import geopandas as gpd
from streamlit_folium import folium_static
import hashlib
import re

def save_uploaded_file(uploadedfile, save_folder):
    if uploadedfile is not None:
        file_path = os.path.join(save_folder, uploadedfile.name)
        with open(file_path, 'wb') as f:
            f.write(uploadedfile.getbuffer())
        return file_path
    return None

DB_PATH = "incident_reports.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS incidents (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              reporter_name TEXT,
              reporter_details TEXT,
              incident_title TEXT,
              incident_description TEXT,
              vehicle_reg_number TEXT,
              owner_name TEXT,
              witness_info TEXT,
              witness_address TEXT,
              weather_conditions TEXT,
              location TEXT,
              road_conditions TEXT,
              injuries_sustained TEXT,
              image_path TEXT,
              video_path TEXT,
              captured_image_path TEXT,
              timestamp TEXT
              )''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def is_valid_email(email):
    return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email)

def signup_user(email, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hash_password(password)))
        conn.commit()
        return True, "Signup successful!"
    except sqlite3.IntegrityError:
        return False, "Email already exists."
    finally:
        conn.close()

def login_user(email, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE email=?", (email,))
    row = c.fetchone()
    conn.close()
    if row and row[0] == hash_password(password):
        return True
    return False

def set_logged_in(email):
    st.session_state["logged_in"] = True
    st.session_state["user_email"] = email

def logout():
    st.session_state["logged_in"] = False
    st.session_state["user_email"] = ""

def save_to_db(reporter_name, reporter_details, incident_title, incident_description, vehicle_reg_number, owner_name, witness_info, witness_address, weather_condition, location, latitude, longitude, image_path, video_path, captured_image_path, timestamp):
    conn = sqlite3.connect("../APPS/incident_reports/incident_reports.db")
    c = conn.cursor()
    c.execute('''INSERT INTO incidents (reporter_name, reporter_details, incident_title, incident_description, vehicle_reg_number, owner_name, witness_info, witness_address, weather_condition, location, latitude, longitude, image_path, video_path, captured_image_path, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
              (reporter_name, reporter_details, incident_title, incident_description, vehicle_reg_number, owner_name, witness_info, witness_address, weather_condition, location, latitude, longitude, image_path, video_path, captured_image_path, timestamp))
    conn.commit()
    conn.close()

init_db()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_email"] = ""

menu = ["Login", "Signup", "Report Incident", "Incidents Map"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Signup":
    st.subheader("Create New Account")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    password2 = st.text_input("Confirm Password", type="password")
    if st.button("Signup"):
        if not is_valid_email(email):
            st.error("Invalid email format.")
        elif password != password2:
            st.error("Passwords do not match.")
        elif len(password) < 6:
            st.error("Password must be at least 6 characters.")
        else:
            success, msg = signup_user(email, password)
            if success:
                st.success(msg)
            else:
                st.error(msg)

elif choice == "Login":
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if login_user(email, password):
            set_logged_in(email)
            st.success(f"Logged in as {email}")
        else:
            st.error("Invalid email or password.")
    if st.session_state["logged_in"]:
        if st.button("Logout"):
            logout()
            st.info("Logged out.")

elif choice == "Report Incident":
    if not st.session_state["logged_in"]:
        st.info("Please login to report an incident.")
    else:
        st.title('Incident Report')
        st.write('Please fill in the details below to report an incident.')
        reporter_name = st.text_input("Your Name")
        reporter_details = st.text_area("Your Contact Details")
        incident_date = st.date_input("Date of Incident")
        incident_title = st.text_input("Incident Title")
        incident_description = st.text_area("Describe the incident in detail")
        vehicle_reg_number = st.text_input("Vehicle Registration Number")
        driver_name = st.text_input("Driver's Name")
        owner_name = st.text_input("Owner's Name")
        driver_contact = st.text_input("Driver's Contact Number")
        witness_info = st.text_area("Witness Information")
        witness_address = st.text_area("Witness Address")
        weather_condition = st.text_area("Weather Conditions")
        road_conditions = st.text_area("Road Conditions")
        injuries_sustained = st.text_area("Injuries Sustained")
        location = st.text_area("Location of Incident")

        image_file = st.file_uploader("Upload an image (optional)", type=["jpg", "jpeg", "png"])
        video_file = st.file_uploader("Upload a video (optional)", type=["mp4", "mov", "avi"])
        captured_image = st.camera_input("Take a picture (optional)")
        save_folder = "incident_reports"
        os.makedirs(save_folder, exist_ok=True)
        captured_image_path = "No picture taken"
        if captured_image is not None:
            captured_image_path = os.path.join(save_folder, "captured_image.png")
            with open(captured_image_path, "wb") as f:
                f.write(captured_image)
            st.image(captured_image_path, caption="Captured Image", use_column_width=True)

        if st.button("Submit Report"):
            st.write(f"**Title:** {incident_title}")
            st.write(f"**Description:** {incident_description}")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"incident_{timestamp}.txt"
            report_path = os.path.join(save_folder, report_filename)
            image_path = save_uploaded_file(image_file, save_folder) if image_file else "No image uploaded"
            video_path = save_uploaded_file(video_file, save_folder) if video_file else "No video uploaded"
            with open(report_path, "w") as report:
                report.write(f"Reporter Name: {reporter_name}\n")
                report.write(f"Reporter Details: {reporter_details}\n")
                report.write(f"Incident Title: {incident_title}\n")
                report.write(f"Description: {incident_description}\n")
                report.write(f"Vehicle Registration Number: {vehicle_reg_number}\n")
                report.write(f"Owner Name: {owner_name}\n")
                report.write(f"Witness Information: {witness_info}\n")
                report.write(f"Witness Address: {witness_address}\n")
                report.write(f"Weather Condition: {weather_condition}\n")
                report.write(f"Location: {location}\n")
                report.write(f"Image: {image_path}\n")
                report.write(f"Video: {video_path}\n")
                report.write(f"Captured Image: {captured_image_path}\n")
                report.write(f"Reported on: {timestamp}\n")
            st.success("✅ Incident report submitted successfully!")
            if image_path != "No image uploaded":
                st.image(image_path, caption="Uploaded Image", use_column_width=True)
            if video_path != "No video uploaded":
                st.video(video_path)
            if captured_image_path != "No picture taken":
                st.image(captured_image_path, caption="Captured Image", use_column_width=True)

elif choice == "Incidents Map":
    st.subheader("Reported Incidents Map")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM incidents", conn)
    conn.close()
    m = folium.Map(location=[0,0], zoom_start=2)
    for index, row in df.iterrows():
        if 'latitude' in row and 'longitude' in row and row['latitude'] and row['longitude']:
            folium.Marker(
                [row['latitude'], row['longitude']],
                popup=f"{row['incident_title']}\n{row['location']}",
                tooltip=row['incident_title']
            ).add_to(m)
    folium_static(m)