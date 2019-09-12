from celery import Celery
from main import *
from twilio.rest import Client

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
twilio_number = os.environ['TWILIO_NUMBER']
client = Client(account_sid, auth_token)

app = Celery()
app.config_from_object('celery_settings')

@app.task()
def SendMessageTwilio(id_):
	query = "SELECT message_text FROM messages WHERE id = " + id_
	body = db.session.execute(query).first()[0]
	for p_number in GetActivePhonesFromDB():
		to = '+1' + str(p_number[0])
		client.messages.create(to, from_=twilio_number, body=body)


