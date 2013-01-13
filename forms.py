import datetime

import model
import config

from web.form import *

search = Form(
    Textbox('query'),
    Button('submit', type='submit', html='Search')
)

class dateformat (Validator):
    def __init__(self, fmt, msg=None):
        if msg is None:
            msg = "doesn't match date format (%s)" % fmt
        self.fmt = fmt
        self.msg = msg

    def valid(self, val):
        try:
            dt = datetime.datetime.strptime(val, self.fmt)
            return True
        except ValueError:
            return False

not_empty = regexp(r'.', 'cannot be empty')
not_zero = regexp(r'[^0]|.{2,}', "you didn't select a carrier")
looks_like_date = dateformat(config.date_fmt,
                             "doesn't look like a date (%s)" % config.date_fmt)
looks_like_dt = dateformat(config.datetime_fmt,
                           "doesn't look like a date and time (%s)" % config.datetime_fmt)
looks_like_number = regexp(r'[0-9]+',"doesn't look like a number")
looks_like_phone = regexp(r'[0-9]{3}-[0-9]{3}-[0-9]{4}', "doesn't look like a phone number")
valid_relationship = regexp(r'self|spouse|child|other', "not a recognized relationship (self, spouse, child, other)")
valid_student_status = regexp(r'full-time|part-time|$', "not a recognized status (full-time, part-time, or leave it blank)")
looks_like_gender = regexp(r'm|f|male|female', "not a recognized gender")

def _rp_is_unique_pt(i):
    if i:
        pts = model.pt_name_search(i)
        return len(pts) == 1
    else:
        return True
names_unique_pt = Validator("doesn't name a unique patient", _rp_is_unique_pt)

patient = Form(
    Hidden('id'),
    Hidden('resparty'),
    Textbox('name', not_empty, description='patient'),
    Textbox('birthday', looks_like_date, description='birthdate'),
    Textbox('resparty_text', names_unique_pt, description='responsible party'),
    Textbox('gender', looks_like_gender, description='gender'),
    Textarea('notes', description='notes'),
    Button('submit', type='submit', html='save'),
)

def construct_carrier_dropdown():
    carriers = model.get_carriers()
    l = tuple([('0', 'select a carrier ...')] + [(str(carrier.id), carrier.name) for carrier in carriers])
    print l
    return l

journal = dict(
    # these are just text fields
    address = Form(
        Hidden('patientid'),
        Textarea('summary', not_empty, description='address'),
        Button('submit', type='submit', html='new')
        ),
    phone = Form(
        Hidden('patientid'),
        Textbox('summary', not_empty, description='phone'),
        Button('submit', type='submit', html='new')
        ),
    email = Form(
        Hidden('patientid'),
        Textbox('summary', not_empty, description='email'),
        Button('submit', type='submit', html='new')
        ),
    contact = Form(
        Hidden('patientid'),
        Textbox('summary', not_empty, description='summary'),
        Textarea('details', not_empty, description='details'),
        Button('submit', type='submit', html='new')
        ),
    progress = Form(
        Hidden('patientid'),
        Textbox('summary', not_empty, description='summary'),
        Textarea('sub', not_empty, description='s'),
        Textarea('obj', not_empty, description='o'),
        Textarea('ass', not_empty, description='a'),
        Textarea('pln', not_empty, description='p'),
        Button('submit', type='submit', html='new')
        ),
    plan = Form(
        Hidden('patientid'),
        Hidden('secondaryto'),
        Textbox('summary', not_empty, description='summary'),
        # TODO in production this should be called when the form is requested
        Dropdown('carrier', construct_carrier_dropdown(), not_zero,
                 description='carrier'),
        Textbox('insured', names_unique_pt, description='insured'),
        Textbox('relationship', valid_relationship, description='relationship'),
        Textbox('student_status', valid_student_status, description='student status'),
        Textbox('groupnum', description='group #'),
        Textbox('idnum', not_empty, description='id #'),
        Textbox('employer', description='employer'),
        Textbox('deductible', looks_like_number, description='deductible'),
        Textbox('maximum', looks_like_number, description='annual max'),
        Textbox('prevent', looks_like_number, description='preventative %'),
        Textbox('basic', looks_like_number, description='basic %'),
        Textbox('major', looks_like_number, description='major %'),
        Textarea('notes', description='notes'),
        Button('submit', type='submit', html='new'),
        ),
    claim = Form(
        Hidden('patientid'),
        Hidden('planid'),
        Textbox('summary', not_empty, description='summary'),
        Textarea('notes', description='notes'),
        Button('submit', html='new'),
        ),
    # nice to have some templates to select from
    # should allow free entry too
    Rx = Form(
        Hidden('patientid'),
        Textbox('summary', not_empty, description='drug'),
        Textbox('disp', not_empty, description='disp'),
        Textbox('sig', not_empty, description='sig'),
        Textbox('refills', not_empty, description='refills', value='0 (zero)'),
        Button('submit', type='submit', html='new')
        ),
    # need to upload files
    doc = Form(
        Hidden('patientid'),
        Textbox('summary', not_empty, description='description'),
        File('file', description='file'),
        Button('submit', type='submit', html='new')
        ),
    appointment = Form(
        Hidden('journalid'),
        Hidden('patientid'),
        Textbox('ts', looks_like_dt, description='appointment'),
        Textbox('duration', looks_like_number, description='length'),
        Textbox('summary', not_empty, description='summary'),
        Textbox('kind', not_empty, description='kind'),
        Textbox('status', description='status'),
        Textarea('notes', description='notes'),
        # no submit button, it's in appointment.html manually
    )
)

newtx = Form(
    Textbox('tx', not_empty, description='treatment'),
    Button('submit', type='submit', html='tx'),
)

carrier = Form(
    Textbox('name', not_empty, description='name'),
    Textarea('address', not_empty, description='address'),
    Textbox('phone', looks_like_phone, description='phone'),
    Textbox('web', description='web address'),
    Textbox('eclaim', description='electronic payer id'),
    Button('submit', type='submit', html='new'),
)

claim = Form(
    Textbox('summary', not_empty, description='summary'),
    Textarea('notes', description='notes'),
)
