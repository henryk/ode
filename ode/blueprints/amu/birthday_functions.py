from datetime import date, datetime
import uuid
import socket

def create_ical(user_list, group_list):    
    event = ''

    for user in user_list:
        summary = _('Birthday from {}').format(user.name)
        date = user.birthdate.strftime("%Y%m%d")
        groups = ''

        for group in group_list:
            if user.dn in group.members:
                groups += '{} '.format(group.name)

        uuid = "{}-{}-{}@{}".format(user.name.replace(' ', '-'), date, 'amu', socket.gethostname().lower())
        if date != '':
            event += 'BEGIN:VEVENT\rSUMMARY:{}\rDTSTART;VALUE=DATE:{}\rUID:{}\rDESCRIPTION:{}\rPRIORITY:5\rRRULE:FREQ=YEARLY;INTERVAL=1\rEND:VEVENT\r'.format(summary, date, str(uuid), groups)

    if event != '':
        cal = 'BEGIN:VCALENDAR\r{}END:VCALENDAR'.format(event)
        return cal
    return None 
    