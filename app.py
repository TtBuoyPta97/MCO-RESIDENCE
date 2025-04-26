from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import random

app = Flask(__name__)

# Secret key for session management (flash messages, etc.)
app.secret_key = 'Mcoboti@002'

# -------------------------
# 📧 Email Configuration
# -------------------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # SMTP server
app.config['MAIL_PORT'] = 587                 # Port for TLS
app.config['MAIL_USE_TLS'] = True             # Use TLS
app.config['MAIL_USERNAME'] = 'mcoresidence@gmail.com'  # Your email
app.config['MAIL_PASSWORD'] = 'lftiiuewhdhfurvs'     # App password or real password

mail = Mail(app)

# -------------------------
# 🏠 Home Route
# -------------------------
@app.route('/')
def home():
    return render_template('index.html')

# -------------------------
# 📝 Booking Route
# -------------------------
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
        pickup = request.form.get('pickup', 'no')
        pickup_location = request.form.get('pickup_location', '')
        special = request.form.get('special', '')

        # Combine check-in date and time into a datetime object
        checkin_datetime = datetime.strptime(f"{checkin_date} {checkin_time}", "%Y-%m-%d %H:%M")

        # -------------------------
        # 💰 Calculate Amount & Checkout Time
        # -------------------------
        if booking_option == "night":
            amount_due = 450
            checkout_time = checkin_datetime.replace(hour=11, minute=0) + timedelta(days=1)
            show_checkout = True
        elif booking_option == "hour":
            amount_due = 150
            checkout_time = checkin_datetime + timedelta(hours=1)
            show_checkout = False
        elif booking_option == "3hours":
            amount_due = 250
            checkout_time = checkin_datetime + timedelta(hours=3)
            show_checkout = False
        else:
            amount_due = 0
            checkout_time = None
            show_checkout = False

        # Generate a reference number
        reference = f"MCO{random.randint(1000, 9999)}"

        # Store data in session or pass it through POST if preferred
        return render_template(
            'payment.html',
            name=name,
            email=email,
            phone=phone,
            booking_option=booking_option,
            checkin=checkin_datetime.strftime("%Y-%m-%d %H:%M"),
            checkout=checkout_time.strftime("%Y-%m-%d %H:%M"),
            pickup=pickup,
            pickup_location=pickup_location,
            special=special,
            amount=amount_due,
            reference=reference,
            show_checkout=show_checkout
        )

    # If GET request, show empty booking form
    return render_template('booking.html')

# -------------------------
# 💳 Payment Route
# -------------------------
@app.route('/payment', methods=['POST'])
def payment():
    # Collect posted data from the payment form
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    booking_option = request.form['booking_option']
    checkin = request.form['checkin']
    checkout = request.form['checkout']
    pickup = request.form['pickup']
    pickup_location = request.form['pickup_location']
    special = request.form['special']
    amount = request.form['amount']
    reference = request.form['reference']

    # -------------------------
    # ✉️ Send Email to Client
    # -------------------------
    try:
        client_message = Message(
            subject=f"Booking Confirmation - {reference}",
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )
        client_message.body = f"""
Hi {name},

Thank you for booking with MCO Guest Residencies.

Here are your booking details:
- Booking Option: {booking_option}
- Check-in: {checkin}
- {'Check-out: ' + checkout if checkout else ''}
- Pickup: {pickup} ({pickup_location})
- Special Requests: {special}
- Total Amount: R{amount}
- Reference Number: {reference}

We look forward to welcoming you!

Best regards,
MCO Residencies
"""
        mail.send(client_message)

        # -------------------------
        # ✉️ Send Email to Owner
        # -------------------------
        owner_message = Message(
            subject=f"New Booking Received - {reference}",
            sender=app.config['MAIL_USERNAME'],
            recipients=[app.config['MAIL_USERNAME']]  # Send to yourself
        )
        owner_message.body = f"""
NEW BOOKING RECEIVED:

Name: {name}
Email: {email}
Phone: {phone}
Booking Option: {booking_option}
Check-in: {checkin}
{'Check-out: ' + checkout if checkout else ''}
Pickup: {pickup} ({pickup_location})
Special Requests: {special}
Total Amount: R{amount}
Reference: {reference}
"""

        mail.send(owner_message)

        return redirect(url_for('success'))

    except Exception as e:
        flash(f"Error sending emails: {str(e)}")
        return redirect(url_for('home'))

# -------------------------
# ✅ Booking Success Page
# -------------------------
@app.route('/success')
def success():
    return render_template('success.html')

# -------------------------
# 🚀 Run Flask App
# -------------------------
if __name__ == '__main__':
    app.run(debug=True)
