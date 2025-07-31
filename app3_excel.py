import streamlit as st
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

# ---------------------------
# CONFIG FROM STREAMLIT SECRETS
# ---------------------------
EMAIL_SENDER = "dericvictor2@gmail.com"
EMAIL_PASSWORD = "wlrf tvsn mesm hppn"
ADMIN_PASS = "Immanuel123"

BOOKINGS_FILE = "bookings.xlsx"

# Initialize Excel if not exists
if not os.path.exists(BOOKINGS_FILE):
    df = pd.DataFrame(columns=[
        "Name", "Gender", "Age", "Phone", "Email", "Bus Route",
        "Travel Date", "Booking Date", "Seat Number"
    ])
    df.to_excel(BOOKINGS_FILE, index=False)

# Bus details
buses = {
    "Trichy → Chennai": {"total": 10},
    "Trichy → Coimbatore": {"total": 10},
    "Trichy → Madurai": {"total": 10}
}

# ---------------------------
# HELPER FUNCTIONS
# ---------------------------
def load_bookings():
    return pd.read_excel(BOOKINGS_FILE)

def save_booking(data_list):
    df = load_bookings()
    df = pd.concat([df, pd.DataFrame(data_list)], ignore_index=True)
    df.to_excel(BOOKINGS_FILE, index=False)

def delete_booking(email, travel_date):
    df = load_bookings()
    df = df[~((df["Email"] == email) & (df["Travel Date"] == travel_date))]
    df.to_excel(BOOKINGS_FILE, index=False)

def get_booked_seats(bus_route, travel_date):
    df = load_bookings()
    booked = df[(df["Bus Route"] == bus_route) & (df["Travel Date"] == str(travel_date))]["Seat Number"].tolist()
    return booked

def send_email(to_email, subject, body):
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_SENDER
        msg["To"] = to_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
        st.success(f"✅ Email sent to {to_email}")
    except Exception as e:
        st.error(f"❌ Email sending failed: {e}")

# ---------------------------
# STREAMLIT UI
# ---------------------------
st.set_page_config(page_title="IMMANUEL Travels", page_icon="🚌", layout="centered")
st.title("🚌 IMMANUEL Travels - Bus Booking System")

# ---------------------------
# BOOKING SECTION
# ---------------------------
bus_route = st.selectbox("Select Bus Route", list(buses.keys()))
travel_date = st.date_input("Select Travel Date")
total_seats = buses[bus_route]["total"]
booked_seats = get_booked_seats(bus_route, travel_date)

# Seat layout
st.markdown("### Select Your Seats")
cols = st.columns(5)
selected_seats = []

for seat in range(1, total_seats + 1):
    col = cols[(seat - 1) % 5]
    if seat in booked_seats:
        col.button(f"Seat {seat}", disabled=True)
    else:
        if col.checkbox(f"Seat {seat}"):
            selected_seats.append(seat)

if selected_seats:
    st.success(f"Selected seats: {selected_seats}")
    passenger_data = []
    for seat in selected_seats:
        st.write(f"Passenger for Seat {seat}")
        name = st.text_input(f"Name (Seat {seat})", key=f"name_{seat}")
        gender = st.radio(f"Gender (Seat {seat})", ["Male", "Female", "Other"], key=f"gender_{seat}", horizontal=True)
        age = st.number_input(f"Age (Seat {seat})", min_value=1, max_value=100, key=f"age_{seat}")
        phone = st.text_input(f"Phone (Seat {seat})", key=f"phone_{seat}")

        passenger_data.append({
            "Name": name,
            "Gender": gender,
            "Age": age,
            "Phone": phone,
            "Seat Number": seat
        })

    common_email = st.text_input("Common Email for Ticket Confirmation")

    if st.button("Confirm Booking"):
        if all(d["Name"] and d["Phone"] for d in passenger_data) and common_email:
            for d in passenger_data:
                d.update({
                    "Email": common_email,
                    "Bus Route": bus_route,
                    "Travel Date": str(travel_date),
                    "Booking Date": datetime.now().strftime("%Y-%m-%d")
                })
            save_booking(passenger_data)
            email_body = f"Your booking is confirmed for {bus_route} on {travel_date}.\n\n"
            for d in passenger_data:
                email_body += f"Seat {d['Seat Number']} - {d['Name']} ({d['Gender']}, {d['Age']})\n"
            email_body += "\nThank you for choosing IMMANUEL Travels."
            send_email(common_email, "Booking Confirmation - IMMANUEL Travels", email_body)
        else:
            st.error("Fill details for all passengers and email.")

# ---------------------------
# CANCELLATION
# ---------------------------
st.markdown("---")
st.subheader("Cancel Booking")
with st.form("cancel_form"):
    cancel_email = st.text_input("Enter Email")
    cancel_date = st.date_input("Travel Date")
    cancel_submit = st.form_submit_button("Cancel Booking")

if cancel_submit:
    df = load_bookings()
    booking = df[(df["Email"] == cancel_email) & (df["Travel Date"] == str(cancel_date))]
    if booking.empty:
        st.error("No booking found.")
    else:
        travel_time = datetime.strptime(str(cancel_date), "%Y-%m-%d")
        if (travel_time - datetime.now()) < timedelta(hours=12):
            st.error("Cannot cancel within 12 hours.")
        else:
            seats = booking["Seat Number"].tolist()
            delete_booking(cancel_email, str(cancel_date))
            st.success(f"Canceled seats {seats}. Email sent.")
            send_email(cancel_email, "Booking Canceled", f"Your booking for {bus_route} on {cancel_date} is canceled.")

# ---------------------------
# ADMIN PANEL
# ---------------------------
st.markdown("---")
st.subheader("Admin Login")
admin_password = st.text_input("Enter Admin Password", type="password")

if admin_password == ADMIN_PASS:
    st.success("Welcome, Admin!")
    df = load_bookings()
    st.dataframe(df)
    st.download_button("Download All Bookings (Excel)", data=open(BOOKINGS_FILE, "rb"), file_name="bookings.xlsx")
elif admin_password:
    st.error("Incorrect password!")
