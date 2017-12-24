from flask_wtf import Form
from wtforms import HiddenField, SubmitField, StringField, TextField, FieldList, SelectMultipleField
from wtforms.widgets import TextArea
from wtforms.validators import DataRequired
from wtforms_components import read_only

from flask_babel import _

class RefreshForm(Form):
	refresh = SubmitField( _('Refresh!') )

class CreateInvitationForm(Form):
	event_id = HiddenField(validators=[DataRequired()])
	create = SubmitField('')

class SetRecipientStateForm(Form):
	state_yes = SubmitField('')
	state_no = SubmitField('')

class EditInvitationForm(Form):
	subject = StringField( _('Subject'), validators=[DataRequired()])
	recipients_raw = FieldList(StringField( _("Initial recipients") ))
	sender = TextField( _('Sender'), validators=[DataRequired()])
	owners = FieldList(StringField( _("Owners") ))
	text_html = TextField( _('Invitation text'), widget=TextArea())

	save = SubmitField( _('Save') )
	send = SubmitField( _('Send') )

	def __init__(self, *args, **kwargs):
		super(EditInvitationForm, self).__init__(*args, **kwargs)
		self.recipients_raw.label.text = _("Recipients")  # This should not just be the titlecased version of the variable name
		self.owners.label.text = _("Owners")

def get_SendInvitationForm(recipients_):
	choices = [ (str(r.id), r.to_unicode) for r in recipients_ if r.state in (r.state.NEW, r.state.DESELECTED) ]

	class SendInvitationForm(Form):

		sender = TextField( _('Sender'), validators=[DataRequired()])
		recipients = SelectMultipleField(choices=choices, default = [str(r.id) for r in recipients_ if r.state is r.state.NEW])
		subject = StringField( _('Subject'), validators=[DataRequired()])
		text_html = TextField( _('Invitation text'), widget=TextArea())

		back = SubmitField( _('Abort & Back') )
		send = SubmitField( _('Send') )

		def __init__(self, *args, **kwargs):
			super(SendInvitationForm, self).__init__(*args, **kwargs)
			for f in [self.sender, self.subject, self.text_html]:
				read_only(f)
				f.validators = []

	return SendInvitationForm

class EditRSVPForm(Form):
	response_yes = SubmitField( '' )
	response_no  = SubmitField( '' )
