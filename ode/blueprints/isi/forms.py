from flask_wtf import Form
from wtforms import HiddenField, SubmitField, TextField
from wtforms.widgets import TextArea

class RefreshForm(Form):
	refresh = SubmitField('Refresh!')

class CreateInvitationForm(Form):
	event_id = HiddenField()
	create = SubmitField('')

class EditInvitationForm(Form):
	text_html = TextField('Invitation text', widget=TextArea())

	save = SubmitField('Save')