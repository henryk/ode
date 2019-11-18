#import datetime
from datetime import date, datetime

from icalendar import Calendar

def calculate_age(birthdate):
    birthdate = birthdate.strftime("%Y-%m-%d")

    if birthdate != '':
        birthdate = datetime.strptime(birthdate, "%Y-%m-%d")
        today = date.today()
        return (today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))) + 1
    return None


def create_ical(user_list, group_list):    
    event = ''

    for user in user_list:
        summary = 'Birthday from {}'.format(user.name)
        date = user.birthdate.strftime("%Y%m%d")
        groups = ''

        for group in group_list:
            if user.dn in group.members:
                groups += '{} '.format(group.name)

        if date != '':
            event += 'BEGIN:VEVENT\rSUMMARY:{}\rDTEND;VALUE=DATE:{}\rDTSTART;VALUE=DATE:{}\rUID:{}/27346262376@mxm.dk\rDESCRIPTION:{}\rPRIORITY:5\rEND:VEVENT\r'.format(summary, date, date, date, groups)

    if event != '':
        cal = 'BEGIN:VCALENDAR\r{}END:VCALENDAR'.format(event)
        #f = open('ical/ode_birthdays.ics', 'wb')
        #f.write(cal)
        #f.close()
        #return f
        return cal
    return None