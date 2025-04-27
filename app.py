from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'Mcoboti@002'  # Secret key for sessions

# Email settings
EMAIL_ADDRESS = 'mcoresidence@gmail.com'
EMAIL_PASSWORD = 'lftiiuewhdhfurvs'
RECEIVER_EMAIL = 'mcoresidence@gmail.com'

# Upload settings
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Home page
@app.route('/')
def index():
    images = ['a.JPG', 'b.JPG', 'c.JPG', 'd.JPG', 'e.JPG', 'f.JPG', 'g.JPG', 'h.JPG']
    return render_template('index.html', images=images)

# Booking page
@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'POST':
        # Get form data
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
        elif booking_option == '2hours':
            total_amount = 250
            booking_option_display = '2 Hours (R250)'
        else:
            total_amount = 0
            booking_option_display = 'Unknown'

        # Calculate checkout time if needed
        checkout_time = None
        if booking_option == 'hour':
            checkin_datetime = datetime.strptime(f"{checkin_date} {checkin_time}", '%Y-%m-%d %H:%M')
            checkout_time = (checkin_datetime + timedelta(hours=1)).strftime('%H:%M')
        elif booking_option == '2hours':
            checkin_datetime = datetime.strptime(f"{checkin_date} {checkin_time}", '%Y-%m-%d %H:%M')
            checkout_time = (checkin_datetime + timedelta(hours=2)).strftime('%H:%M')

        # Save booking to session
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
        payment_method = request.form.get('payment_method')

        if payment_method == 'online':
            # Redirect to PayFast
            payfast_link = "https://www.payfast.co.za/eng/process?merchant_id=14070761&merchant_key=t9gho8csdpkwd&amount={}&item_name=Booking".format(booking['total_amount'])
            return redirect(payfast_link)

        elif payment_method == 'manual':
            # Handle manual proof upload
            file = request.files['proof_file']
            if file:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)

                send_manual_payment_email(booking, filepath)

                # Optional: delete after sending
                os.remove(filepath)

            return redirect(url_for('success'))

    return render_template('payment.html', booking=booking)

# Success page
@app.route('/success')
def success():
    return render_template('success.html')

# Send normal booking email
def send_emails(booking):
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
    # Email to owner
    send_email(RECEIVER_EMAIL, subject, body)

# Send manual payment email (with attachment)
def send_manual_payment_email(booking, filepath):
    subject = f"Manual Payment Proof - {booking['name']}"
    body = f"""
    Manual Payment Received:

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

    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    with open(filepath, 'rb') as f:
        from email.mime.application import MIMEApplication
        part = MIMEApplication(f.read(), Name=os.path.basename(filepath))
        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(filepath)}"'
        msg.attach(part)

    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

# Actual email sender
def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

# Run app
if __name__ == '__main__':
    app.run(debug=True)
