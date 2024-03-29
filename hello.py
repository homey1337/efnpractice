# standard library imports
import datetime
import mimetypes
import os
import re
import time
import urllib

# nonstandard libraries
import magic
import pytz
import web

# my imports
import config
import forms
import model


#TODO: transactions?


urls = (
    '/', 'index',
    # some form targets
    '/searchpt', 'searchpt',
    '/gotoday', 'gotoday',
    # patients and families
    '/family/(.*)', 'family',
    '/patient/(.*)', 'edit_patient',
    '/new/patient', 'edit_patient',
    # appointments
    '/new/appointment', 'show_journal',
    # other journal entries
    '/new/(.*)', 'edit_journal',
    '/journal/(.*)', 'show_journal',
    # treatment plan
    '/txplan/(.*)', 'txplan.show',
    # schedule
    '/oneday/(.*)', 'schedule.oneday',
    '/today', 'schedule.oneday',
    '/days', 'schedule.days',
    # carriers
    '/setup/carriers', 'setup.carriers',
    # claims
    '/update_claim/(.*)', 'claim.update_claim',
)
app = web.application(urls, globals())
render = web.template.render('templates/', globals=globals()) #lazy!


# ye olde index

class index:
    def GET(self):
        # other useful things; recent journal entries
        return render.index()


class searchpt:
    def POST(self):
        f = web.input()
        q = ' '.join(f.query.split())
        if q:
            pts = model.pt_name_search(q)
            if len(pts) == 0:
                return 'no patient found'
            elif len(pts) == 1:
                raise web.seeother('/patient/%d' % pts[0].id)
            else:
                return render.family(pts)
        else:
            return render.family(model.db.select('patient'))

class gotoday:
    def POST(self):
        f = web.input()
        d = model.input_date(f.date)
        raise web.seeother('/oneday/%s' % model.display_date(d))


# a list of multiple patients ... generally relatives

class family:
    def GET(self, patientid):
        return render.family(model.get_family(patientid))


# patient edit

class edit_patient:
    def GET(self, patientid=''):
        ptform = forms.patient()

        if patientid:
            patientid = int(patientid)
            journal = model.get_journal(patientid)
            pt = model.get_pt(patientid)
            for key in pt:
                ptform[key].set_value(pt[key])

            if pt.resparty:
                rp = model.get_pt(pt.resparty)
                ptform.resparty_text.set_value(model.pt_name(rp, first='lastname'))
            else:
                rp = None
                ptform.resparty_text.set_value(model.pt_name(pt, first='lastname'))
        else:
            pt = None
            journal = None
            rp = None

        return render.patient(pt, ptform, rp, journal)

    def POST(self, patientid=''):
        f = forms.patient()
        if not f.validates():
            return render.edit_patient(f)
        else:
            if f.resparty_text.get_value():
                #TODO: this query is done twice now (here and during validation)
                # validation already established that this mapping is unique
                # so we do not need to check it here
                rp = model.pt_name_search(f.resparty_text.get_value())
                resparty = rp[0].id
            else:
                rp = None
                resparty = None

            newid = model.update_pt(f, resparty)
            raise web.seeother('/patient/%d' % newid)


class edit_journal:
    def GET(self, kind):
        inp = web.input(pt=0, secondaryto=None)
        patientid = int(inp.pt)
        form = forms.journal[kind]
        pt = model.get_pt(patientid)
        form.patientid.set_value(pt.id)
        if inp.secondaryto:
            form.secondaryto.set_value(inp.secondaryto)
        return render.journal(pt, kind, form)

    def POST(self, kind):
        f = forms.journal[kind]()
        if f.validates():
            pt = model.get_pt(int(f.patientid.get_value()))
            model.new_journal(pt, kind, f)
            raise web.seeother('/patient/%d' % pt.id)
        else:
            inp = web.input(pt=0)
            pt = model.get_pt(inp.pt)
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
    def plan(journal):
        plan = model.get_plan(journal.id)
        pt = model.get_pt(journal.patientid)
        carrier = model.get_carrier(plan.carrierid)
        insured = model.get_pt(plan.insuredid)
        if plan.secondaryto:
            primary = model.get_plan(plan.secondaryto)
        else:
            primary = None
        return render.plan(journal, plan, pt, carrier, insured, primary)

    @staticmethod
    def claim(journal):
        pt = model.get_pt(journal.patientid)
        claim = model.get_claim(journal.id)
        form = forms.claim()
        form.summary.set_value(journal.summary)
        form.notes.set_value(claim.notes)
        plan = model.get_plan(claim.planid)
        txs = model.get_tx_for_claim(claim.journalid)
        return render.claim(pt, claim, form, plan, txs)

    @staticmethod
    def Rx(journal):
        Rx = model.get_Rx(journal.id)
        pt = model.get_pt(journal.patientid)
        address = model.get_latest_address(pt.id)
        return render.Rx(journal, Rx, pt, address)

    @staticmethod
    def tx(journal):
        txs = model.get_posted_tx(journal.id)
        pt = model.get_pt(journal.patientid) # or tx.patientid
        appointments = dict()
        claims = dict()
        for tx in txs:
            if tx.appointmentid and tx.appointmentid not in appointments:
                appointments[tx.appointmentid] = model.get_appointment(tx.appointmentid)
            if tx.claimid and tx.claimid not in claims:
                claims[tx.claimid] = model.get_claim(tx.claimid)
        return render.tx(journal, pt, txs, appointments, claims)

    @staticmethod
    def appointment(journal, form=None):
        if journal:
            appt = model.get_appointment(journal.id)
            pt = model.get_pt(journal.patientid)
            txs = model.get_tx_for_appointment(appt.journalid)
        else:
            inp = web.input(pt=0)
            appt = None
            pt = model.get_pt(int(inp.pt))
            txs = model.get_txplan(int(inp.pt))
        if not form:
            form = forms.journal['appointment']()
            if journal:
                form['patientid'].set_value(str(pt.id))
                form['journalid'].set_value(str(journal.id))
                form['ts'].set_value(model.display_datetime(model.load_datetime(journal.ts)))
                form['summary'].set_value(journal.summary)
                form['status'].set_value(appt.status)
                form['notes'].set_value(appt.notes)
                form['kind'].set_value(appt.kind)
                form['duration'].set_value(appt.duration)
        return render.appointment(journal, appt, pt, form, txs)

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
    def GET(self, id=''):
        if id:
            journal = model.get_journal_entry(int(id))
            return getattr(view_handlers, journal.kind)(journal)
        else:
            return getattr(view_handlers, 'appointment')(None)

    def POST(self, id=''):
        if id:
            journal = model.get_journal_entry(int(id))
        else:
            journal = None
        if not journal or journal.kind == 'appointment':
            inp = web.input(txs=list()) # to pickup the custom txs field
            form = forms.journal['appointment']()
            if form.validates():
                if journal:
                    appt = model.get_appointment(journal.id)
                    if appt.status == 'posted':
                        form.status.note = 'cannot modify posted appointments'
                        return view_handlers.appointment(journal, form)
                if id:
                    model.update_appt(journal.id, form)
                else:
                    pt = model.get_pt(int(form.patientid.get_value()))
                    journalid = model.new_journal(pt, 'appointment', form)
                    journal = model.get_journal_entry(journalid)
                txs = list()
                for txid in inp.txs:
                    txs.append(int(txid))
                model.appt_tx_set(journal.id, txs)
                if inp.submit == 'post':
                    if model.load_datetime(journal.ts) > model.current_time():
                        form.ts.note = 'cannot post appointments in the future'
                        return view_handlers.appointment(journal, form)
                    model.post_appointment(appt, journal, map(int, txs))
                return view_handlers.appointment(model.get_journal_entry(journal.id))
            else:
                return view_handlers.appointment(journal, form)
        else:
            return getattr(view_handlers, journal.kind)(journal)


if __name__ == "__main__":
    app.run()
