import streamlit as st
import sqlite3
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# ---------------------------
# DATABASE SETUP
# ---------------------------
def init_db():
    conn = sqlite3.connect("travels.db")
    c = conn.cursor()
    
    # Customers Table
    c.execute('''CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT, gender TEXT, age INTEGER, phone TEXT UNIQUE, email TEXT UNIQUE)''')
    
    # Buses Table
    c.execute('''CREATE TABLE IF NOT EXISTS buses (
                    id INTEGER PRIMARY KEY,
                    route TEXT, total_seats INTEGER, available_seats INTEGER)''')
    
    # Bookings Table
    c.execute('''CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER, bus_id INTEGER, seat_number INTEGER,
                    booking_date TEXT, travel_date TEXT,
                    FOREIGN KEY(customer_id) REFERENCES customers(id),
                    FOREIGN KEY(bus_id) REFERENCES buses(id))''')
    
    # Insert buses if not exist
    buses = [(1, "Trichy → Chennai", 5, 5),
             (2, "Trichy → Coimbatore", 5, 5),
             (3, "Trichy → Madurai", 5, 5)]
    for bus in buses:
        c.execute("INSERT OR IGNORE INTO buses (id, route, total_seats, available_seats) VALUES (?, ?, ?, ?)", bus)
    
    conn.commit()
    conn.close()

init_db()

# ---------------------------
# DATABASE FUNCTIONS
# ---------------------------
def get_customer(email):
    conn = sqlite3.connect("travels.db")
    c = conn.cursor()
    c.execute("SELECT * FROM customers WHERE email=?", (email,))
    result = c.fetchone()
    conn.close()
    return result

def add_customer(name, gender, age, phone, email):
    conn = sqlite3.connect("travels.db")
    c = conn.cursor()
    c.execute("INSERT INTO customers (name, gender, age, phone, email) VALUES (?, ?, ?, ?, ?)",
              (name, gender, age, phone, email))
    conn.commit()
    customer_id = c.lastrowid
    conn.close()
    return customer_id

def get_bus(bus_id):
    conn = sqlite3.connect("travels.db")
    c = conn.cursor()
    c.execute("SELECT * FROM buses WHERE id=?", (bus_id,))
    result = c.fetchone()
    conn.close()
    return result

def book_seat(customer_id, bus_id, travel_date):
    conn = sqlite3.connect("travels.db")
    c = conn.cursor()
    
    # Check available seats
    c.execute("SELECT available_seats FROM buses WHERE id=?", (bus_id,))
    seats = c.fetchone()[0]
    if seats > 0:
        seat_number = (5 - seats) + 1  # Assign seat
        booking_date = datetime.now().strftime("%Y-%m-%d")
        c.execute("INSERT INTO bookings (customer_id, bus_id, seat_number, booking_date, travel_date) VALUES (?, ?, ?, ?, ?)",
                  (customer_id, bus_id, seat_number, booking_date, travel_date))
        # Update available seats
        c.execute("UPDATE buses SET available_seats = available_seats - 1 WHERE id=?", (bus_id,))
        conn.commit()
        conn.close()
        return seat_number
    else:
        conn.close()
        return None

def get_available_seats():
    conn = sqlite3.connect("travels.db")
    c = conn.cursor()
    c.execute("SELECT route, available_seats FROM buses")
    data = c.fetchall()
    conn.close()
    return data

# ---------------------------
# EMAIL FUNCTION
# ---------------------------
def send_email(to_email, subject, body):
    sender_email = "dericvictor2@gmail.com"
    sender_password = "wlrf tvsn mesm hppn"  # Use App Password (for Gmail)
    
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
    except Exception as e:
        st.error(f"Email not sent: {e}")

# ---------------------------
# STREAMLIT UI
# ---------------------------
st.set_page_config(page_title="IMMANUEL Travels", page_icon="🚌", layout="centered")
st.title("🚌 IMMANUEL Travels - Bus Booking System")

# Show Available Seats
st.subheader("Available Seats")
seats_data = get_available_seats()
for route, seats in seats_data:
    st.write(f"**{route}: {seats} seats available**")

st.markdown("---")

# Booking Form
st.subheader("Book Your Seat")
with st.form("booking_form"):
    name = st.text_input("Full Name")
    gender = st.radio("Gender", ["Male", "Female", "Other"])
    age = st.number_input("Age", min_value=1, max_value=100)
    phone = st.text_input("Phone Number")
    email = st.text_input("Email")
    bus_option = st.selectbox("Choose Bus Route", ["Trichy → Chennai", "Trichy → Coimbatore", "Trichy → Madurai"])
    travel_date = st.date_input("Date of Travel")
    submit = st.form_submit_button("Book Now")

if submit:
    if name and email and phone:
        bus_id = {"Trichy → Chennai": 1, "Trichy → Coimbatore": 2, "Trichy → Madurai": 3}[bus_option]
        customer = get_customer(email)
        if customer:
            customer_id = customer[0]
        else:
            customer_id = add_customer(name, gender, age, phone, email)
        
        seat_number = book_seat(customer_id, bus_id, str(travel_date))
        if seat_number:
            st.success(f"Booking Confirmed! Your seat number is {seat_number}. A confirmation email has been sent.")
            email_body = f"""
Dear {name},

Your booking is confirmed!

Route: {bus_option}
Date of Travel: {travel_date}
Seat Number: {seat_number}

Thank you for choosing IMMANUEL Travels.
"""
            send_email(email, "Booking Confirmation - IMMANUEL Travels", email_body)
        else:
            st.error("Sorry, no seats available for this bus.")
    else:
        st.error("Please fill all details.")
