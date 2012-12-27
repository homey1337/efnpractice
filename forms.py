from web.form import *

search = Form(
    Textbox('query'),
    Button('submit', type='submit', html='Search')
)

not_empty = regexp(r'.', 'cannot be empty')
looks_like_date = regexp(r'[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}',
                                  "doesn't look like a date (YYYY-MM-DD)")

def _rp_is_unique_pt(i):
    # ugly ...
    import hello
    if i:
        pts = hello.pt_search(i)
        return len(pts) == 1
    else:
        return True
names_unique_pt = Validator("doesn't name a unique patient", _rp_is_unique_pt)

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
        Textarea('disp', not_empty, description='Disp'),
        Textarea('sig', not_empty, description='Sig'),
        Textarea('refills', not_empty, description='Refills', value='0 (zero)'),
        Button('submit', type='submit', html='New')
        ),
    # need to upload files
    doc = Form(
        Textbox('summary', not_empty, description='Description'),
        File('file', description='File'),
        Button('submit', type='submit', html='New')
        ),
    # and this is the elephant in the room
    # probably needs special handling all the way down
    appointment = Form(),
)
