# standard library imports
import time

# web.py
import web

# my imports
import forms


urls = (
    '/', 'index',
    '/family/(.*)', 'family',
    '/pt/(.*)/new/(.*)', 'new_journal',
    '/pt/(.*)/', 'patient',
    '/pt/(.*)', 'patient_bounce',
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

    def POST(self):
        return POST_search_for_patient()


# a list of multiple patients ... generally relatives

class family:
    def GET(self, patientid):
        pts = list(db.where('patient', resparty=patientid))
        return render.family(forms.search(), pts)

    def POST(self, patientid):
        return POST_search_for_patient()


# patient display

class patient_bounce:
    def GET(self, x):
        raise web.seeother('/pt/%s/' % x)

class patient:
    def GET(self, patientid):
        pt = list(db.where('patient', id=patientid))[0]
        if pt.resparty:
            resparty = list(db.where('patient', id=pt.resparty))[0]
        else:
            resparty = pt
        journal = list(db.where('journal', order='ts DESC', limit=10, patientid=pt.id))

        return render.pt(forms.search(), pt, resparty, journal)

    def POST(self, patientid):
        return POST_search_for_patient()


# patient edit

class edit_patient:
    def GET(self, patientid=''):
        if patientid:
            pt = list(db.where('patient', id=patientid))[0]
        else:
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

    def POST(self, patientid=''):
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


class new_handlers (web.storage):
    @staticmethod
    def address(journalid, form):
        pass

    @staticmethod
    def phone(journalid, form):
        pass

    @staticmethod
    def contact(journalid, form):
        # insert detailed information into auxiliary table
        pass

    @staticmethod
    def progress(journalid, form):
        # insert detailed information into auxiliary table
        pass

    @staticmethod
    def Rx(journalid, form):
        # insert detailed information into auxiliary table
        pass

    @staticmethod
    def doc(journalid, form):
        # save uploaded document
        pass

    @staticmethod
    def appointment(journalid, form):
        # will probably need a more specialized handler
        pass


class new_journal:
    def GET(self, patientid, kind):
        pt = list(db.where('patient', id=patientid))[0]
        return render.journal(pt, kind, forms.journal[kind]())

    def POST(self, patientid, kind):
        pt = list(db.where('patient', id=patientid))[0]
        f = forms.journal[kind]()
        if f.validates():
            # make the row in journal
            journalid = db.insert('journal',
                                  patientid=pt.id,
                                  ts=web.db.sqlliteral("strftime('%s','now')"),
                                  kind=kind,
                                  summary=f.summary.get_value())
            # pass it off for further processing
            getattr(new_handlers, kind)(journalid, f)
            raise web.seeother('/pt/%d/' % pt.id)
        else:
            return render.journal(pt, kind, f)

        
if __name__ == "__main__":
    app.run()
