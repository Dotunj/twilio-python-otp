import os
from flask import Flask, request, flash, redirect, url_for, render_template, Response
from dotenv import load_dotenv
from twilio.rest import Client
import requests
load_dotenv()
app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
twilio_client = Client()
base_url = 'https://api.generateotp.com/'


@app.route('/generate', methods=['GET', 'POST'])
def generate():
    if request.method == 'GET':
        return render_template('generate.html')
    phone_number = request.form['phone_number']
    channel = request.form['channel']
    error = None
    if not phone_number:
        error = 'Phone Number is required'
    if channel != 'voice' and channel != 'sms':
        error = 'Invalid channel'
    if error is None:
        otp_code = make_otp_request(phone_number)
        if otp_code:
            send_otp_code(phone_number, otp_code, channel)
            flash('Otp has been generated successfully', 'success')
            return redirect(url_for('validate', phone_number=phone_number))
        error = 'Something went wrong, could not generate OTP'
    flash(error, 'error')
    return redirect(url_for('generate'))


@app.route('/validate', methods=['GET', 'POST'])
def validate():
    if request.method == 'GET':
        return render_template('validate.html')
    phone_number = request.args.get('phone_number')
    otp_code = request.form['otp_code']
    error = None
    if not otp_code:
        error = 'Otp code is required'
    status, message = verify_otp_code(otp_code, phone_number)
    if status == True:
        flash(message, 'success')
        return redirect(url_for('validate', phone_number=phone_number))
    if status == False:
        flash(message, 'error')
        return redirect(url_for('validate', phone_number=phone_number))
    flash('Something went wrong, could not validate OTP', 'error')
    return redirect(url_for('validate', phone_number=phone_number))


def verify_otp_code(otp_code, phone_number):
    r = requests.post(f"{base_url}/validate/{otp_code}/{phone_number}")
    if r.status_code == 200:
        data = r.json()
        status = data["status"]
        message = data["message"]
        return status, message
    return None


def make_otp_request(phone_number):
    r = requests.post(f"{base_url}/generate",
                      data={'initiator_id': phone_number})
    if r.status_code == 201:
        data = r.json()
        otp_code = str(data["code"])
        return otp_code
    return None


def send_otp_code(phone_number, otp_code, channel):
    if channel == 'voice':
        return send_otp_via_voice_call(phone_number, otp_code)
    if channel == 'sms':
        return send_otp_via_sms(phone_number, otp_code)
    return None


def send_otp_via_voice_call(number, code):
    outline_code = split_code(code)
    call = twilio_client.calls.create(
        twiml=f"<Response><Say voice='alice'>Your one time password is {outline_code}</Say><Pause length='1'/><Say>Your one time password is {outline_code}</Say><Pause length='1'/><Say>Goodbye</Say></Response>",
        to=f"+{number}",
        from_=os.getenv('TWILIO_NUMBER')
    )
    return None


def send_otp_via_sms(number, code):
    messages = twilio_client.messages.create(to=f"+{number}", from_=os.getenv(
        'TWILIO_NUMBER'), body=f"Your one time password is {code}")
    return None


def split_code(code):
    items = [char for char in code]
    separator = " "
    return separator.join(items)


if __name__ == '__main__':
    app.run()
