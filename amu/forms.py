
from flask import session
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, HiddenField, SelectMultipleField, BooleanField, widgets
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
		givenname = StringField('Given Name')
		surname = StringField('Last Name')
		userid = HiddenField('Username', validators=[DataRequired()])
		name = StringField('Full Name')

		groups = MultiCheckboxField('Groups', choices = [ (_.dn,_.name) for _ in group_list ] )

		submit = SubmitField('Update!')

		delete_confirm = BooleanField('Confirm deletion')
		delete = SubmitField('Delete!')
	return EditUserForm

def get_NewUserForm(group_list):
	class NewUserForm(Form):
		givenname = StringField('Given Name', validators=[DataRequired()])
		surname = StringField('Last Name', validators=[DataRequired()])
		password = StringField('Password', validators=[DataRequired()])
		userid = StringField('Username', validators=[DataRequired()])
		name = StringField('Full Name', validators=[DataRequired()])

		groups = MultiCheckboxField('Groups', choices = [ (_.dn,_.name) for _ in group_list ] )

		submit = SubmitField('Create!')

	return NewUserForm
