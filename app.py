from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os

app = Flask(__name__)
app.secret_key = 'Mcoboti@002'

# Email settings
EMAIL_ADDRESS = 'mcoresidence@gmail.com'
EMAIL_PASSWORD = 'lftiiuewhdhfurvs'
RECEIVER_EMAIL = 'mcoresidence@gmail.com'

# Upload settings
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Home page
@app.route('/')
def index():
    images = ['a.JPG', 'b.JPG', 'c.JPG', 'd.JPG', 'e.JPG', 'f.JPG', 'g.JPG', 'h.JPG']
    return render_template('index.html', images=images)

# Booking page
@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        booking_option = request.form['booking_option']
        checkin_date = request.form['checkin_date']
        checkin_time = request.form['checkin_time']
        pickup = request.form['pickup']
        pickup_location = request.form.get('pickup_location')
        special = request.form.get('special')
        checkout_date = None
        nights = 1

        # Calculate total amount
        if booking_option == 'night':
            checkout_date = request.form['checkout_date']
            checkin = datetime.strptime(checkin_date, '%Y-%m-%d')
            checkout = datetime.strptime(checkout_date, '%Y-%m-%d')
            nights = (checkout - checkin).days
            if nights <= 0:
                nights = 1  # Always minimum 1 night
            total_amount = 450 * nights
            booking_option_display = f'Night Stay ({nights} night{"s" if nights > 1 else ""}) - R450 per night'

        elif booking_option == 'hour':
            total_amount = 150
            booking_option_display = '1 Hour (R150)'

        elif booking_option == '2hours':
            total_amount = 250
            booking_option_display = '2 Hours (R250)'

        else:
            total_amount = 0
            booking_option_display = 'Unknown'

        # Calculate checkout time for hourly bookings
        checkout_time = None
        if booking_option in ['hour', '2hours']:
            checkin_datetime = datetime.strptime(f"{checkin_date} {checkin_time}", '%Y-%m-%d %H:%M')
            hours = 1 if booking_option == 'hour' else 2
            checkout_time = (checkin_datetime + timedelta(hours=hours)).strftime('%H:%M')

        # Save booking in session
        session['booking'] = {
            'name': name,
            'email': email,
            'phone': phone,
            'booking_option': booking_option,
            'booking_option_display': booking_option_display,
            'checkin_date': checkin_date,
            'checkout_date': checkout_date,
            'checkin_time': checkin_time,
            'pickup': pickup,
            'pickup_location': pickup_location,
            'special': special,
            'total_amount': total_amount,
            'nights': nights,
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
        payment_method = request.form['payment_method']

        if payment_method == 'online':
            return redirect(
                'https://www.payfast.co.za/eng/process?merchant_id=14070761&merchant_key=t9gho8csdpkwd&amount='
                + str(booking['total_amount'])
            )

        elif payment_method == 'manual':
            if 'proof' not in request.files:
                return "No proof uploaded!", 400
            file = request.files['proof']
            if file.filename == '':
                return "No file selected!", 400
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            send_emails(booking, proof_path=file_path)
            return redirect(url_for('success'))

    return render_template('payment.html', booking=booking)

# Success page
@app.route('/success')
def success():
    return render_template('success.html')

# Email functions
def send_emails(booking, proof_path=None):
    subject = f"Booking Confirmation - {booking['name']}"
    body = f"""
Booking Details:

Name: {booking['name']}
Email: {booking['email']}
Phone: {booking['phone']}
Booking Option: {booking['booking_option_display']}
Check-in Date: {booking['checkin_date']} at {booking['checkin_time']}
"""

    if booking['booking_option'] == 'night':
        body += f"""
Checkout Date: {booking['checkout_date']} (before 11:00 AM)
Number of Nights: {booking['nights']}
"""
    else:
        body += f"Checkout Time: {booking['checkout_time']}"

    if booking['pickup'] == 'yes' and booking['pickup_location']:
        body += f"\nPickup Location: {booking['pickup_location']}"

    if booking['special']:
        body += f"\nSpecial Requests: {booking['special']}"

    body += f"\n\nTotal Amount: R{booking['total_amount']}"

    send_email(booking['email'], subject, body)
    send_email(RECEIVER_EMAIL, subject, body, attachment_path=proof_path)

def send_email(to_email, subject, body, attachment_path=None):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    if attachment_path:
        with open(attachment_path, 'rb') as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
        msg.attach(part)

    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

# Run app
if __name__ == '__main__':
    app.run(debug=True)
