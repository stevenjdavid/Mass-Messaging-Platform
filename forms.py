from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Regexp

class AddToDatabase(FlaskForm):
	phone_list = StringField('Enter Phone Number(s)')
	submit = SubmitField('Submit')

class SendMessage(FlaskForm):
	body = TextAreaField('body')
	scheduled = BooleanField('scheduled')
	date = StringField('date')
	time = StringField('time')
	submit = SubmitField('Submit')

