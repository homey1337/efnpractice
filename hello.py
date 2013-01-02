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
import model


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
    '/txplan/(.*)', 'txplan.show',
)
app = web.application(urls, globals())
render = web.template.render('templates/', globals=globals()) #lazy!


# how to search for patients ... can come from multiple places

def POST_search_for_patient():
    f = forms.search()
    f.validates()
    q = ' '.join(f.query.get_value().split())
    pts = model.pt_name_search(q)
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
        return render.family(forms.search(), model.get_family(patientid))

    def POST(self, patientid):
        return POST_search_for_patient()


# patient display

class patient_bounce:
    def GET(self, x):
        raise web.seeother('/pt/%s/' % x)

class patient:
    def GET(self, patientid):
        pt = model.get_pt(patientid)
        if pt.resparty:
            resparty = model.get_pt(pt.resparty)
        else:
            resparty = pt
        journal = model.get_journal(pt.id)

        return render.pt(forms.search(), pt, resparty, journal)

    def POST(self, patientid):
        return POST_search_for_patient()


# patient edit

class edit_patient:
    def GET(self, patientid=''):
        if patientid:
            pt = model.get_pt(patientid)
        else:
            pt = None

        f = forms.patient()
        if pt:
            for key in pt:
                f[key].set_value(pt[key])

            if pt.resparty:
                rp = model.get_pt(pt.resparty)
                f.resparty_text.set_value(model.pt_name(rp, first='lastname'))
            else:
                f.resparty_text.set_value(model.pt_name(pt, first='lastname'))

        return render.edit_patient(f)

    def POST(self, patientid=''):
        f = forms.patient()
        if not f.validates():
            return render.edit_patient(f)
        else:
            #TODO: this query is done twice now (here and during validation)
            if f.resparty_text.get_value():
                # validation already established that this mapping is unique
                # so we do not need to check it here
                rp = model.pt_name_search(f.resparty_text.get_value())
                resparty = rp[0].id
            else:
                rp = None
                resparty = None

            newid = model.update_pt(f, resparty)
            raise web.seeother('/pt/%d/' % newid)


class new_journal:
    def GET(self, patientid, kind):
        pt = model.get_pt(patientid)
        return render.journal(pt, kind, forms.journal[kind]())

    def POST(self, patientid, kind):
        pt = model.get_pt(patientid)
        f = forms.journal[kind]()
        if f.validates():
            model.new_journal(pt, kind, f)
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
        email = journal.summary
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
        contact = model.get_contact(journal.id)
        pt = model.get_pt(journal.patientid)
        return render.contact(journal, contact, pt)

    @staticmethod
    def progress(journal):
        progress = model.get_progress(journal.id)
        pt = model.get_pt(journal.patientid)
        return render.progress(journal, progress, pt)

    @staticmethod
    def Rx(journal):
        Rx = model.get_Rx(journal.id)
        pt = model.get_pt(journal.patientid)
        address = model.get_latest_address(pt.id)
        return render.Rx(journal, Rx, pt, address)

    @staticmethod
    def appointment(journal):
        appt = model.get_appointment(journal.id)
        pt = model.get_pt(journal.patientid)
        txs = model.get_tx_for_appointment(appt.journalid)
        return render.appointment(journal, appt, pt, txs)

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


class show_journal:
    def GET(self, id):
        journal = model.get_journal_entry(id)
        return getattr(view_handlers, journal.kind)(journal)


if __name__ == "__main__":
    app.run()
