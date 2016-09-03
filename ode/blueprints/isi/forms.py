from flask_wtf import Form
from wtforms import HiddenField, SubmitField, StringField, TextField, FieldList, SelectMultipleField
from wtforms.widgets import TextArea
from wtforms.validators import DataRequired
from wtforms_components import read_only

class RefreshForm(Form):
	refresh = SubmitField('Refresh!')

class CreateInvitationForm(Form):
	event_id = HiddenField(validators=[DataRequired()])
	create = SubmitField('')

class EditInvitationForm(Form):
	subject = StringField('Subject', validators=[DataRequired()])
	recipients_raw = FieldList(StringField("Initial recipients"))
	sender = TextField('Sender', validators=[DataRequired()])
	text_html = TextField('Invitation text', widget=TextArea())

	save = SubmitField('Save')
	send = SubmitField('Send')

	def __init__(self, *args, **kwargs):
		super(EditInvitationForm, self).__init__(*args, **kwargs)
		self.recipients_raw.label.text = "Recipients"  # This should not just be the titlecased version of the variable name

def get_SendInvitationForm(recipients_):
	choices = [ (str(r.id), r.to_unicode) for r in recipients_ if r.state in (r.state.NEW, r.state.DESELECTED) ]

	class SendInvitationForm(Form):

		sender = TextField('Sender', validators=[DataRequired()])
		recipients = SelectMultipleField(choices=choices, default = [str(r.id) for r in recipients_ if r.state is r.state.NEW])
		subject = StringField('Subject', validators=[DataRequired()])
		text_html = TextField('Invitation text', widget=TextArea())

		back = SubmitField('Abort & Back')
		send = SubmitField('Send')

		def __init__(self, *args, **kwargs):
			super(SendInvitationForm, self).__init__(*args, **kwargs)
			read_only(self.sender)
			read_only(self.subject)
			read_only(self.text_html)

	return SendInvitationForm
