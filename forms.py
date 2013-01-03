import datetime

import model

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
looks_like_date = dateformat('%Y-%m-%d', "doesn't look like a date (YYYY-MM-DD)")
looks_like_dt = dateformat('%Y-%m-%d %H:%M',
                           "doesn't look like a date and time (YYYY-MM-DD HH:MM)")
looks_like_number = regexp(r'[0-9]+',"doesn't look like a number")

def _rp_is_unique_pt(i):
    if i:
        pts = model.pt_name_search(i)
        return len(pts) == 1
    else:
        return True
names_unique_pt = Validator("doesn't name a unique patient", _rp_is_unique_pt)

newappt = Form(
    Textbox('pt', names_unique_pt, description='Patient'),
    Textbox('summary', not_empty, description='Summary'),
    Textbox('dt', looks_like_dt, description='When'),
    Textbox('duration', looks_like_number, description='Length'),
    Textbox('kind', not_empty, description='Kind'),
    Textarea('notes', description='Note'),
    Button('submit', type='submit', html='New')
)

patient = Form(
    Hidden('id'),
    Hidden('resparty'),
    Textbox('firstname', not_empty, description='First name'),
    Textbox('middlename', description='Middle name'),
    Textbox('lastname', not_empty, description='Last name'),
    Textbox('birthday', looks_like_date, description='Birthday'),
    Textbox('resparty_text', names_unique_pt, description='Responsible Party'),
    Button('submit', type='submit', html='Save'),
)


journal = dict(
    # these are just text fields
    address = Form(
        Textarea('summary', not_empty, description='Address'),
        Button('submit', type='submit', html='New')
        ),
    phone = Form(
        Textbox('summary', not_empty, description='Phone'),
        Button('submit', type='submit', html='New')
        ),
    email = Form(
        Textbox('summary', not_empty, description='Email'),
        Button('submit', type='submit', html='New')
        ),
    contact = Form(
        Textbox('summary', not_empty, description='Summary'),
        Textarea('details', not_empty, description='Details'),
        Button('submit', type='submit', html='New')
        ),
    progress = Form(
        Textbox('summary', not_empty, description='Summary'),
        Textarea('sub', not_empty, description='S'),
        Textarea('obj', not_empty, description='O'),
        Textarea('ass', not_empty, description='A'),
        Textarea('pln', not_empty, description='P'),
        Button('submit', type='submit', html='New')
        ),
    # nice to have some templates to select from
    # should allow free entry too
    Rx = Form(
        Textbox('summary', not_empty, description='Drug'),
        Textbox('disp', not_empty, description='Disp'),
        Textbox('sig', not_empty, description='Sig'),
        Textbox('refills', not_empty, description='Refills', value='0 (zero)'),
        Button('submit', type='submit', html='New')
        ),
    # need to upload files
    doc = Form(
        Textbox('summary', not_empty, description='Description'),
        File('file', description='File'),
        Button('submit', type='submit', html='New')
        ),
    appointment = Form(
        Textbox('summary', not_empty, description='Summary'),
        Textbox('dt', looks_like_dt, description='When'),
        Textbox('duration', looks_like_number, description='Length'),
        Textbox('kind', not_empty, description='Kind'),
        Button('submit', type='submit', html='New')
        ),
)

newtx = Form(
    Textbox('tx', not_empty, description='Treatment'),
    Button('submit', type='submit', html='Tx'),
)
