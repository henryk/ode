from wtforms.validators import ValidationError
import datetime

from flask_babel import _

def ISODate(form, field):
    try:
        datetime.datetime.strptime(field.data, '%Y-%m-%d')
    except:    
        raise ValidationError(_('Incorrect data format, should be YYYY-MM-DD.'))
