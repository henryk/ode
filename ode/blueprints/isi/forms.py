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
	recipients_raw = FieldList(StringField("Recipients"), min_entries=2)
	sender = TextField('Sender', validators=[DataRequired()])
	text_html = TextField('Invitation text', widget=TextArea())

	save = SubmitField('Save')