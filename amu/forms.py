
from flask import session
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, HiddenField, SelectMultipleField, widgets
from wtforms.validators import DataRequired

class MultiCheckboxField(SelectMultipleField):
	widget = widgets.ListWidget(prefix_label=False)
	option_widget = widgets.CheckboxInput()


class LoginForm(Form):
	username = StringField('username', validators=[DataRequired()], default=lambda : session.get("username", ""))
	password = PasswordField('password', validators=[DataRequired()])
	submit = SubmitField('Log in!')

def get_EditUserForm(group_list):
	class EditUserForm(Form):
		userid = HiddenField('username', validators=[DataRequired()])
		name = StringField('Name')
		surname = StringField('Last Name')
		givenname = StringField('Given Name')

		groups = MultiCheckboxField('Groups', choices = [ (_.dn,_.name) for _ in group_list ] )

		submit = SubmitField('Update!')
		delete = SubmitField('Delete!')
	return EditUserForm