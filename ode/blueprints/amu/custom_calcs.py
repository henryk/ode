import datetime
from datetime import date

def calculate_age(birthdate):
    birthdate = birthdate.strftime("%Y-%m-%d")

    if birthdate != '':
        birthdate = datetime.datetime.strptime(birthdate, "%Y-%m-%d")
        today = date.today()
        return (today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))) + 1
    return None