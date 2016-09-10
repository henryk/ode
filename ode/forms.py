from flask import session
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from flask_babel import _

class LoginForm(Form):
	username = StringField('username', validators=[DataRequired()], default=lambda : session.get("username", ""))
	password = PasswordField('password', validators=[DataRequired()])
	submit = SubmitField( _('Log in!') )

