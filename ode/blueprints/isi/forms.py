from flask_wtf import Form
from wtforms import HiddenField, SubmitField, StringField, TextField, FieldList
from wtforms.widgets import TextArea
from wtforms.validators import DataRequired

class RefreshForm(Form):
	refresh = SubmitField('Refresh!')

class CreateInvitationForm(Form):
	event_id = HiddenField(validators=[DataRequired()])
	create = SubmitField('')

class EditInvitationForm(Form):
	subject = StringField('Subject', validators=[DataRequired()])
	recipients = FieldList(StringField("All recipients"))
	recipients_raw = FieldList(StringField("Initial recipients"))
	sender = TextField('Sender', validators=[DataRequired()])
	text_html = TextField('Invitation text', widget=TextArea())

	save = SubmitField('Save')
	send = SubmitField('Send')

	def __init__(self, *args, **kwargs):
		super(EditInvitationForm, self).__init__(*args, **kwargs)
		self.recipients_raw.label.text = "Recipients"  # This should not just be the titlecased version of the variable name
		self.recipients.label.text = "All recipients" 
