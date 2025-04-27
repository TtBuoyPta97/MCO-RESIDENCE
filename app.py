from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os

app = Flask(__name__)
app.secret_key = 'Mcoboti@002'

# --------------- Email Settings ---------------
EMAIL_ADDRESS = 'mcoresidence@gmail.com'
EMAIL_PASSWORD = 'lftiiuewhdhfurvs'
RECEIVER_EMAIL = 'mcoresidence@gmail.com'

# --------------- Upload Settings ---------------
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Make sure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --------------- Routes ---------------

# Home Page
@app.route('/')
def index():
    images = ['a.JPG', 'b.JPG', 'c.JPG', 'd.JPG', 'e.JPG', 'f.JPG', 'g.JPG', 'h.JPG']
    return render_template('index.html', images=images)

# Booking Page
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

        # Calculate price
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

        # Checkout time
        checkout_time = None
        if booking_option == 'hour':
            checkin_datetime = datetime.strptime(f"{checkin_date} {checkin_time}", '%Y-%m-%d %H:%M')
            checkout_time = (checkin_datetime + timedelta(hours=1)).strftime('%H:%M')
        elif booking_option == '2hours':
            checkin_datetime = datetime.strptime(f"{checkin_date} {checkin_time}", '%Y-%m-%d %H:%M')
            checkout_time = (checkin_datetime + timedelta(hours=2)).strftime('%H:%M')

        # Save booking session
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

# Payment Page
@app.route('/payment', methods=['GET', 'POST'])
def payment():
    booking = session.get('booking')
    if not booking:
        return redirect(url_for('index'))

    if request.method == 'POST':
        payment_method = request.form['payment_method']

        if payment_method == 'online':
            # Redirect to PayFast portal
            return redirect('https://www.payfast.co.za/eng/process?merchant_id=14070761&merchant_key=t9gho8csdpkwd&amount=' + str(booking['total_amount']))
        
        elif payment_method == 'manual':
            # Manual payment: Upload proof
            if 'proof' not in request.files:
                return "No proof file uploaded!", 400
            file = request.files['proof']
            if file.filename == '':
                return "No selected file!", 400
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            send_emails(booking, file_path)
            return redirect(url_for('success'))

    return render_template('payment.html', booking=booking)

# Success Page
@app.route('/success')
def success():
    return render_template('success.html')

# --------------- Email Functions ---------------

def send_emails(booking, proof_path=None):
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
        body += "\nCheckout: Next Day before 11:00 AM"
    else:
        body += f"\nCheckout Time: {booking['checkout_time']}"

    if booking['pickup'] == 'yes':
        body += f"\nPickup Location: {booking['pickup_location']}"

    if booking['special']:
        body += f"\nSpecial Requests: {booking['special']}"

    body += f"\n\nTotal Amount: R{booking['total_amount']}"

    # Email to client
    send_email(booking['email'], subject, body)
    # Email to owner with proof if manual
    send_email(RECEIVER_EMAIL, subject, body, proof_path)

def send_email(to_email, subject, body, attachment_path=None):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    if attachment_path:
        with open(attachment_path, 'rb') as f:
            file = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
        file['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
        msg.attach(file)

    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

# --------------- Run Server ---------------
if __name__ == '__main__':
    app.run(debug=True)
