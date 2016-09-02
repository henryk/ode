from flask_wtf import Form
from wtforms import HiddenField, SubmitField, StringField, TextField, FieldList
from wtforms.widgets import TextArea

class RefreshForm(Form):
	refresh = SubmitField('Refresh!')

class CreateInvitationForm(Form):
	event_id = HiddenField()
	create = SubmitField('')

class EditInvitationForm(Form):
	subject = StringField('Subject')
	recipients_raw = FieldList(StringField("Recipients"))
	sender = TextField('Sender')
	text_html = TextField('Invitation text', widget=TextArea())

	save = SubmitField('Save')