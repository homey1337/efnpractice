# standard library imports
import mimetypes
import os
import re
import time
import urllib

# nonstandard libraries
import magic
import web

# my imports
import forms


#TODO: transactions?


urls = (
    '/', 'index',
    '/family/(.*)', 'family',
    '/pt/(.*)/new/(.*)', 'new_journal',
    '/pt/(.*)/', 'patient',
    '/pt/(.*)', 'patient_bounce',
    '/edit/(.*)/', 'edit_patient',
    '/edit/(.*)', 'edit_patient',
    '/newpt', 'edit_patient',
    '/journal/(.*)', 'show_journal',
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
    def email(journalid, form):
        pass

    @staticmethod
    def phone(journalid, form):
        pass

    @staticmethod
    def contact(journalid, form):
        db.insert('contact', journalid=journalid, details=form.details.get_value())

    @staticmethod
    def progress(journalid, form):
        db.insert('progress',
                  journalid=journalid,
                  sub=form.sub.get_value(),
                  obj=form.obj.get_value(),
                  ass=form.ass.get_value(),
                  pln=form.pln.get_value())

    @staticmethod
    def Rx(journalid, form):
        db.insert('rx',
                  journalid=journalid,
                  disp=form.disp.get_value(),
                  sig=form.sig.get_value(),
                  refills=form.refills.get_value())

    @staticmethod
    def doc(journalid, form):
        filedir = 'upload'
        data = form.file.get_value()
        mime = magic.from_buffer(data, mime=True)
        ext = mimetypes.guess_extension(mime) #includes the leading dot
        fout = open('%s/%s%s' % (filedir, journalid, ext), 'wb')
        fout.write(data)
        fout.close()

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


class view_handlers (web.storage):
    @staticmethod
    def address(journal):
        address = journal.summary
        raise web.seeother('http://maps.google.com/search?'
                           + urllib.urlencode(dict(q=address)))

    @staticmethod
    def email(journal):
        entry = list(db.where('journal', id=id))[0]
        email = entry.summary
        raise web.seeother('mailto:%s' % email)

    @staticmethod
    def phone(journal):
        phone = journal.summary
        q = phone.split(':')
        if len(q) == 1:
            raise web.seeother('tel:%s' % q[0].replace(' ',''))
        elif len(q) == 2:
            raise web.seeother('tel:%s' % q[1].replace(' ',''))
        else:
            return 'unintelligible phone entry %r' % phone

    @staticmethod
    def contact(journal):
        contact = list(db.where('contact', journalid=journal.id))[0]
        pt = list(db.where('patient', id=journal.patientid))[0]
        return render.contact(journal, contact, pt)

    @staticmethod
    def progress(journal):
        progress = list(db.where('progress', journalid=journal.id))[0]
        pt = list(db.where('patient', id=journal.patientid))[0]
        return render.progress(journal, progress, pt)

    @staticmethod
    def Rx(journal):
        Rx = list(db.where('Rx', journalid=journal.id))[0]
        pt = list(db.where('patient', id=journal.patientid))[0]
        address = list(db.where('journal', kind='address', patientid=pt.id, order='ts desc'))[0]
        return render.Rx(journal, Rx, pt, address)

    @staticmethod
    def doc(journal):
        files = os.listdir('upload')
        r = re.compile(r'%s\.' % journal.id)
        files = filter(r.match, files)
        if len(files) != 1:
            raise ValueError("multiple filename matches for %r" % entry.id)
        else:
            filename = files[0]
            mimetype = mimetypes.guess_type(filename)[0]
            web.header('Content-Type', mimetype)
            return file('upload/%s' % filename, 'rb')

    @staticmethod
    def appointment(journal):
        # will probably need a more specialized handler
        pass


class show_journal:
    def GET(self, id):
        journal = list(db.where('journal', id=id))[0]
        return getattr(view_handlers, journal.kind)(journal)


if __name__ == "__main__":
    app.run()
