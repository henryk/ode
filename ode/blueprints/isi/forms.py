from flask_wtf import Form
from wtforms import SubmitField

class RefreshForm(Form):
	refresh = SubmitField('Refresh!')

