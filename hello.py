# standard library imports
import time

# web.py
import web

# my imports
import forms


urls = (
    '/', 'index',
    '/family/(.*)', 'family',
    '/pt/(.*)/', 'patient',
    '/pt/(.*)', 'patient_bounce',
    '/pt/(.*)/new/address', 'new_address',
    '/edit/(.*)/', 'edit_patient',
    '/edit/(.*)', 'edit_patient',
    '/newpt', 'edit_patient',
)
app = web.application(urls, globals())
render = web.template.render('templates/', globals=globals()) #lazy!
db = web.database(dbn='sqlite', db='dp.sqlite')


# how to search for patients ... can come from multiple places

def pt_search(q):
    q = q.replace(',','%,').replace(', ',',').replace(' ','% ')
    if not q:
        return list()
    else:
        q += '%'
    query = web.db.SQLQuery(["coalesce(lastname,'')||','||coalesce(firstname,'')||' '||coalesce(middlename,'') like ", web.db.sqlquote(q)])
    return list(db.select('patient', where=query))

def POST_search_for_patient():
    f = forms.search()
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
        return render.index(forms.search())

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
        return render.family(forms.search(), pts)

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

        return render.pt(forms.search(), pt, resparty, journal)

    def POST(self, *args):
        return POST_search_for_patient()


# patient edit

class edit_patient:
    def GET(self, id_as_string=''):
        try:
            patientid = int(id_as_string)
            pt = list(db.where('patient', id=patientid))[0]
        except ValueError:
            patientid = None
            pt = None

        f = forms.patient()
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
        f = forms.patient()
        if not f.validates():
            return render.edit_patient(f)
        else:
            #TODO: transaction!

            #TODO: this query is done twice now (here and during validation)
            if f.resparty_text.get_value():
                rp = pt_search(f.resparty_text.get_value())
                resparty = rp[0].id
            else:
                rp = None
                resparty = None

            db.query('insert or replace into patient(id,firstname,middlename,lastname,birthday,resparty) values ($id,$firstname,$middlename,$lastname,$birthday,$resparty)',
                     dict(id=f.id.get_value() or None,
                          firstname=f.firstname.get_value(),
                          middlename=f.middlename.get_value(),
                          lastname=f.lastname.get_value(),
                          birthday=f.birthday.get_value(),
                          resparty=resparty))
            row = list(db.query('select last_insert_rowid() as id'))[0]
            raise web.seeother('/pt/%d/' % row.id)


class new_address:
    def GET(self, id_as_string, kind):
        try:
            patientid = int(id_as_string)
        except ValueError:
            return 'patient id %r not found' % id_as_string
        pt = list(db.where('patient', id=patientid))[0]
        
if __name__ == "__main__":
    app.run()
