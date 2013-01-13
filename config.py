import pytz


tz = pytz.timezone('US/Central')
date_fmt = '%Y-%m-%d'
datetime_fmt = '%Y-%m-%d %H:%M'
db_fmt = '%Y-%m-%d %H:%M:%S.%f'


class office:
    name = 'McNair Family Dentistry LLC'
    address = '125 E 3rd St Ste A\nEdmond OK 73034'
    npi = '1609155217'
    license = '6056'
    tin = '01-0912177'
    phone = '405-703-5344'
    additional_id = ''

class provider:
    name = 'Daniel S McNair'
    dea = 'FM0951310'
    npi = '1508029331'
    license = '6056'
    address = '125 E 3rd St Ste A\nEdmond OK 73034'
    specialty = '1223G0001X'
    phone = '405-703-5344'
    additional_id = ''


class hours:
    start = 8
    lunch = 12
    resume = 13
    end = 17
