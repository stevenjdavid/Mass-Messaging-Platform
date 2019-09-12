from flask import Flask, render_template, flash, redirect, url_for, request
from forms import *
import os
from urllib.parse import urlparse
from flask_sqlalchemy import SQLAlchemy
import re
import sys
from tasks import *
from twilio.twiml.messaging_response import Message, MessagingResponse

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
db = SQLAlchemy(app)

def AddMessageToDatabase(message_text, is_scheduled, scheduled_time, completed):
	query = "INSERT INTO messages (message_text,is_scheduled,scheduled_time,completed) VALUES ('" + message_text + "','" + is_scheduled + "','" + scheduled_time + "','" + completed + "') RETURNING id;"
	sql = db.session.execute(query).first()[0]
	db.session.commit()
	return sql

def GenerateDict(raw_data):
	rawToList = raw_data.splitlines()
	if len(rawToList) == 0:
		return False
	goodData = []
	badData = []
	returnData = {}

	for line in rawToList:
		if line == " "or line == "":
			pass
		if re.match('^\d{10}$', line.strip()):
			goodData.append(line.strip())
		else:
			badData.append(line.strip())
	returnData['goodData'] = goodData
	returnData['badData'] = badData
	return returnData

def GetAllFromDB():
	return db.session.execute("SELECT * FROM p_numbers").fetchall()

def GetActivePhonesFromDB():
	return db.session.execute("SELECT Phone FROM p_numbers WHERE Active = 'true'").fetchall()


class PNumbers(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	phone = db.Column(db.String, unique=True, nullable=False)
	active = db.Column(db.String, nullable=False)

class EnterPNumber(db.Model):
	__tablename__ = "p_numbers"
	__table_args__ = {'extend_existing': True} 
	id = db.Column(db.Integer, primary_key=True)
	phone = db.Column(db.String, unique=True)
	active = db.Column(db.String)

	def __init__(self, phone):
		self.phone = phone
		self.active = 'true'

def AddToDB(_list):
	for line in _list:
		try:
			data = EnterPNumber(line)
			db.session.add(data)
			db.session.commit()
		except Exception:
			pass

@app.route('/', methods=['GET'])
def home():
	return render_template('dashboard.html', title='ASV Portal')

@app.route('/webhooks/incoming', methods=['POST'])
def RecieveSMS():
	number = request.form['From'][2:]
	message_body = request.form['Body']
	resp = MessagingResponse()

	if message_body.lower() == "stop":
		query = "SELECT COUNT(*) FROM p_numbers WHERE phone = '" + str(number) + "'"
		result = db.session.execute(query).first()[0]
		if result == 1:
			query = "UPDATE p_numbers SET active = 'false' WHERE phone = '" + str(number) + "'"
			db.session.execute(query)
			db.session.commit()
			resp.message('You have been succesfully unsubcribed from Message Portal.')
		else:
			resp.message('You are not currently subscribed to Message Portal.')
	elif message_body.lower() == "start":
		query = "SELECT COUNT(*) FROM p_numbers WHERE phone = '" + str(number) + "'"
		result = db.session.execute(query).first()[0]
		if result == 1:
			query = "UPDATE p_numbers SET active = 'true' WHERE phone = '" + str(number) + "'"
			db.session.execute(query)
			db.session.commit()
		else:
			data = EnterPNumber(str(number))
			db.session.add(data)
			db.session.commit()
		resp.message('You have been succesfully subscribed to Message Portal.')
	else:
		resp.message("Sorry, that command is not recognized.")
	return str(resp)

@app.route('/messaging/<action>', methods=['GET','POST'])
def messaging(action):
	send_message_form = SendMessage()
	if action == 'create':
		if request.method == 'POST':
			if str(request.form.get('message_text')) != '':
				if (str(request.form.get('scheduled_checkbox')) != 'on'): #if not scheduled
					try:
						SendMessageTwilio.apply_async(args=[str(AddMessageToDatabase("A message from Portal:\n\"" + str(request.form.get('message_text')) + "\"\n\nReply STOP to stop receiving these messages.", '0', "NULL", '1'))])
						flash('Succesfully sent/scheduled message!', 'success')
					except Exception:
						flash('Something went wrong. Try again.', 'danger')
				else:
					flash('Scheduling not supported yet')
			else:
				flash('You cannot send an empty message!', 'danger')
		return render_template('messaging.html', title='Messaging Portal', action='create', form=send_message_form)
	else:
		return 'Error: bad request'

@app.route('/database/<action>', methods=['GET', 'POST'])
def database(action):
	add_form = AddToDatabase()
	returnBackTextForm = ''
	if action == "view":
		if request.method == 'GET':
			return render_template('database.html', title='View Phone Numbers', action='view', phone_table=GetAllFromDB())
		else:
			return 'Error: This URL does not accept ' + str(request.method) +  ' methods'
	elif action == 'add':
		if request.method == 'POST':
			list = GenerateDict(request.form.get('input_text'))
			if list == False:
				flash(f'Error! Empty form', 'danger')
			else:
				errors = list['badData']
				if len(errors) != 0:
					returnBackTextForm = request.form.get('input_text')
					string = "Please fix the following errors: \n\n"
					for error in errors:
						string += '\t\"' + error + '\"\n'
					flash(string, 'danger')
				else:
					AddToDB(list['goodData'])
					flash(f'Succesfully added phone number(s) to database!', 'success')
		return render_template('database.html', title='View Phone Numbers', action='add', form=add_form, form_data=returnBackTextForm)
	else:
		return "Error: bad request"
	return render_template('database.html', title='View Phone Numbers', action='add', form=add_form)
	

if __name__ == '__main__':
	app.run(debug=True)
