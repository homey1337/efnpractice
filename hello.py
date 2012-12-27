import time

import web


urls = (
    '/', 'index',
    '/family/(.*)', 'family',
    '/pt/(.*)/', 'patient',
    '/pt/(.*)', 'patient_bounce',
    '/edit/(.*)', 'edit_patient',
    '/newpt', 'edit_patient',
)
app = web.application(urls, globals())
render = web.template.render('templates/', globals=globals()) #lazy!
db = web.database(dbn='sqlite', db='dp.sqlite')


# how to search for patients ... can come from multiple places

search_form = web.form.Form(
    web.form.Textbox('query'),
    web.form.Button('submit', type='submit', html='Search')
)

def pt_search(q):
    q = q.replace(',','%,').replace(', ',',').replace(' ','% ') + '%'
    query = web.db.SQLQuery(["coalesce(lastname,'')||','||coalesce(firstname,'')||' '||coalesce(middlename,'') like ", web.db.sqlquote(q)])
    print 'pt_search(%r)' % q
    return list(db.select('patient', where=query))

def POST_search_for_patient():
    f = search_form()
    f.validates()
    q = ' '.join(f.query.get_value().split())
    pts = pt_search(q)
    if len(pts) == 1:
        raise web.seeother('/pt/%d/' % pts[0].id)
    else:
        return render.family(f, pts)


# ye olde index

class index:
    def GET(self):
        # other useful things; recent journal entries
        return render.index(search_form())

    def POST(self, *args):
        return POST_search_for_patient()


# a list of multiple patients ... generally relatives

class family:
    def GET(self, id_as_string):
        try:
            patientid = int(id_as_string)
        except ValueError:
            return 'patient id %r not found' % id_as_string

        pts = list(db.where('patient', resparty=patientid))
        return render.family(search_form(), pts)

    def POST(self, *args):
        return POST_search_for_patient()


# patient display

class patient_bounce:
    def GET(self, x):
        raise web.seeother('/pt/%s/' % x)

class patient:
    def GET(self, id_as_string):
        try:
            patientid = int(id_as_string)
        except ValueError:
            return 'patient id %r not found' % id_as_string

        pt = list(db.where('patient', id=patientid))[0]
        if pt.resparty:
            resparty = list(db.where('patient', id=pt.resparty))[0]
        else:
            resparty = pt
        journal = list(db.where('journal', order='ts DESC', limit=10, patientid=pt.id))

        return render.pt(search_form(), pt, resparty, journal)

    def POST(self, *args):
        return POST_search_for_patient()


# patient edit

not_empty = web.form.regexp(r'.', 'cannot be empty')
looks_like_date = web.form.regexp(r'[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}',
                                  "doesn't look like a date (YYYY-MM-DD)")
def _rp_is_unique_pt(i):
    pts = pt_search(i)
    return len(pts) == 1
names_unique_pt = web.form.Validator("doesn't name a unique patient", _rp_is_unique_pt)

patient_form = web.form.Form(
    web.form.Hidden('id'),
    web.form.Hidden('resparty'),
    web.form.Textbox('firstname', not_empty, description='First name'),
    web.form.Textbox('middlename', description='Middle name'),
    web.form.Textbox('lastname', not_empty, description='Last name'),
    web.form.Textbox('birthday', looks_like_date, description='Birthday'),
    web.form.Textbox('resparty_text', names_unique_pt, description='Responsible Party'),
    web.form.Button('submit', type='submit', html='Save'),
)

class edit_patient:
    def GET(self, id_as_string=''):
        try:
            patientid = int(id_as_string)
            pt = list(db.where('patient', id=patientid))[0]
        except ValueError:
            patientid = None
            pt = None

        f = patient_form()
        if pt:
            f.id.set_value(pt.id)
            f.resparty.set_value(pt.resparty)
            f.firstname.set_value(pt.firstname)
            f.middlename.set_value(pt.middlename)
            f.lastname.set_value(pt.lastname)
            f.birthday.set_value(pt.birthday)

            if pt.resparty:
                rp = list(db.where('patient', id=pt.resparty))[0]
                f.resparty_text.set_value('%s, %s %s' % (rp.lastname or '', rp.firstname or '', rp.middlename or ''))
            else:
                f.resparty_text.set_value('%s, %s %s' % (pt.lastname or '', pt.firstname or '', pt.middlename or ''))

        return render.edit_patient(f)

    def POST(self, *args):
        f = patient_form()
        if not f.validates():
            return render.edit_patient(f)
        else:
            #TODO: transaction!

            #TODO: this query is done twice now (here and during validation)
            rp = pt_search(f.resparty_text.get_value())
            resparty = rp[0].id

            db.query('insert or replace into patient(id,firstname,middlename,lastname,birthday,resparty) values ($id,$firstname,$middlename,$lastname,$birthday,$resparty)',
                     dict(id=f.id.get_value() or None,
                          firstname=f.firstname.get_value(),
                          middlename=f.middlename.get_value(),
                          lastname=f.lastname.get_value(),
                          birthday=f.birthday.get_value(),
                          resparty=resparty))
            row = list(db.query('select last_insert_rowid() as id'))[0]
            raise web.seeother('/pt/%d/' % row.id)


if __name__ == "__main__":
    app.run()
