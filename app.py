from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = 'Mcoboti@002'  # Important for saving user info during booking

# ---------------------------
# Email settings
# ---------------------------
EMAIL_ADDRESS = 'mcoresidence@gmail.com'
EMAIL_PASSWORD = 'lftiiuewhdhfurvs'
RECEIVER_EMAIL = 'mcoresidence@gmail.com'  # where you receive the bookings

# ---------------------------
# Routes
# ---------------------------

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Booking page (GET to show form, POST to handle form data)
@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'POST':
        # Collect form data
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        booking_option = request.form['booking_option']
        checkin_date = request.form['checkin_date']
        checkin_time = request.form['checkin_time']
        pickup = request.form['pickup']
        pickup_location = request.form.get('pickup_location')
        special = request.form.get('special')

        # Calculate total amount
        if booking_option == 'night':
            total_amount = 450
            booking_option_display = 'Night (R450)'
        elif booking_option == 'hour':
            total_amount = 150
            booking_option_display = '1 Hour (R150)'
        elif booking_option == '3hours':
            total_amount = 250
            booking_option_display = '3 Hours (R250)'
        else:
            total_amount = 0
            booking_option_display = 'Unknown'

        # Calculate automatic checkout time if needed
        checkout_time = None
        if booking_option == 'hour':
            checkin_datetime = datetime.strptime(f"{checkin_date} {checkin_time}", '%Y-%m-%d %H:%M')
            checkout_time = (checkin_datetime + timedelta(hours=1)).strftime('%H:%M')
        elif booking_option == '3hours':
            checkin_datetime = datetime.strptime(f"{checkin_date} {checkin_time}", '%Y-%m-%d %H:%M')
            checkout_time = (checkin_datetime + timedelta(hours=3)).strftime('%H:%M')

        # Save booking in session
        session['booking'] = {
            'name': name,
            'email': email,
            'phone': phone,
            'booking_option': booking_option,
            'booking_option_display': booking_option_display,
            'checkin_date': checkin_date,
            'checkin_time': checkin_time,
            'pickup': pickup,
            'pickup_location': pickup_location,
            'special': special,
            'total_amount': total_amount,
            'checkout_time': checkout_time
        }

        return redirect(url_for('payment'))

    return render_template('booking.html')

# Payment page
@app.route('/payment', methods=['GET', 'POST'])
def payment():
    booking = session.get('booking')

    if not booking:
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Payment confirmed
        send_emails(booking)
        return redirect(url_for('success'))

    return render_template('payment.html', booking=booking)

# Success page
@app.route('/success')
def success():
    return render_template('success.html')

# ---------------------------
# Helper: Send emails
# ---------------------------
def send_emails(booking):
    # Create the email content
    subject = f"Booking Confirmation - {booking['name']}"
    body = f"""
    Booking Details:

    Name: {booking['name']}
    Email: {booking['email']}
    Phone: {booking['phone']}
    Booking Option: {booking['booking_option_display']}
    Check-in: {booking['checkin_date']} at {booking['checkin_time']}
    """

    if booking['booking_option'] == 'night':
        body += "\nCheckout Time: Before 11:00 AM"
    else:
        body += f"\nCheckout Time: {booking['checkout_time']}"

    if booking['pickup'] == 'yes':
        body += f"\nPickup Location: {booking['pickup_location']}"

    if booking['special']:
        body += f"\nSpecial Requests: {booking['special']}"

    body += f"\n\nTotal Amount: R{booking['total_amount']}"

    # Email to client
    send_email(booking['email'], subject, body)

    # Email to you
    send_email(RECEIVER_EMAIL, subject, body)

# ---------------------------
# Helper: Actually send an email
# ---------------------------
def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    # Connect and send
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

# ---------------------------
# Run the app
# ---------------------------
if __name__ == '__main__':
    app.run(debug=True)
