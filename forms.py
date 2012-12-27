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
