import datetime

import pytz
import web

import config

db = web.database(dbn='sqlite', db='dp.sqlite')


# =================================================================
# datetime


def current_time():
    return datetime.datetime.now(pytz.utc)

def local_time():
    return datetime.datetime.now(config.tz)

def input_date(s):
    return datetime.datetime.strptime(s, config.date_fmt).replace(tzinfo=config.tz).astimezone(pytz.utc)

def display_date(dt):
    return dt.astimezone(config.tz).strftime(config.date_fmt)

def input_datetime(s):
    return datetime.datetime.strptime(s, config.datetime_fmt).replace(tzinfo=config.tz).astimezone(pytz.utc)

def display_datetime(dt):
    return dt.astimezone(config.tz).strftime(config.datetime_fmt)

def store_datetime(dt):
    return dt.strftime(config.db_fmt)

def load_datetime(s):
    return datetime.datetime.strptime(s, config.db_fmt).replace(tzinfo=pytz.utc)


# datetime
# =================================================================
# pt


def pt_name(pt, first='firstname'):
    if pt:
        return pt.name
    else:
        return ''

def pt_name_search(q):
    try:
        id = int(q)
        pt = get_pt(id)
        if pt:
            l = list()
            l.append(get_pt(id))
            return l
        else:
            return list()
    except ValueError:
        qs = q.split()
        l = list()
        for q in qs:
            if l:
                l.append(' and ')
            l.append('name like ')
            l.append(web.db.sqlquote('%%%s%%' % q))
        query = web.db.SQLQuery(l)
        return list(db.select('patient', where=query))

def get_pt(id):
    try:
        return db.where('patient', id=id)[0]
    except IndexError:
        return None

def get_family(resparty):
    return db.where('patient', resparty=resparty)

def update_pt(f, resparty):
    d = dict([(k, f[k].get_value())
              for k in 'name','birthday','notes'])
    d['id'] = f.id.get_value() or None
    d['resparty'] = resparty
    db.query('insert or replace into patient (id, name, resparty, birthday, notes) values ($id, $name, $resparty, $birthday, $notes)', d)
    row = db.query('select last_insert_rowid() as id')[0]
    if d['id'] is None and d['resparty'] is None:
        db.update('patient', where='id=%d' % row.id, resparty=row.id)
    return row.id

def get_latest_address(patientid):
    addresses = db.where('journal', kind='address', patientid=patientid, order='ts DESC')
    try:
        return addresses[0]
    except IndexError:
        pt = get_pt(patientid)
        if pt.resparty != pt.id:
            return get_latest_address(pt.resparty)
        else:
            return None


# pt
# =================================================================
# journal


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
        # TODO should appointments in the past be legal? how to fail?
        #  ... transactions!
        dt = input_datetime(form.ts.get_value())
        db.insert('appointment',
                  journalid=journalid,
                  duration=int(form.duration.get_value()),
                  kind=form.kind.get_value(),
                  status=form.status.get_value(),
                  notes=form.notes.get_value())
        db.update('journal', where=('id=%d' % journalid), ts=store_datetime(dt))

def new_journal(pt, kind, f):
    journalid = db.insert('journal',
                          patientid = pt.id,
                          ts = store_datetime(current_time()),
                          kind = kind,
                          summary = f.summary.get_value())
    getattr(new_handlers, kind)(journalid, f)
    return journalid

def get_journal(patientid, **kw):
    d = dict()
    if 'limit' in kw:
        d['limit'] = kw.pop('limit')
    if 'offset' in kw:
        d['offset'] = kw.pop('offset')
    if len(kw):
        raise ValueError('cannot handle keyword arguments other than limit and offset')

    return db.where('journal', order='ts DESC', patientid=patientid, **d).list()

def get_journal_entry(journalid):
    return db.where('journal', id=journalid)[0]

def get_contact(journalid):
    return db.where('contact', journalid=journalid)[0]

def get_progress(journalid):
    return db.where('progress', journalid=journalid)[0]

def get_Rx(journalid):
    return db.where('Rx', journalid=journalid)[0]

def get_appointment(journalid):
    return db.where('appointment', journalid=journalid)[0]


# journal
# =================================================================
# txplan


def get_txplan(patientid):
    return db.where('tx', patientid=patientid)

def tx_status(tx):
    status = list()
    if tx.journalid:
        status.append('posted')
    if tx.appointmentid:
        status.append('scheduled')
    if tx.claimid:
        status.append('filed')
    return ', '.join(status)

def new_tx(patientid, **kw):
    return db.insert('tx', patientid=patientid, **kw)

def get_tx_for_appointment(appointmentid):
    Q = web.db.SQLQuery
    P = web.db.SQLParam
    return db.select('tx',
                     where=Q(['appointmentid=',
                              P(appointmentid),
                              ' or appointmentid is null']),
                     order='appointmentid DESC, id')


# txplan
# =================================================================
# appointment


def update_appt(journalid, form):
    db.update('appointment',
              where='journalid=%d' % journalid,
              duration=int(form.duration.get_value()),
              kind=form.kind.get_value(),
              notes=form.notes.get_value())
    db.update('journal',
              where='id=%d' % journalid,
              ts=store_datetime(input_datetime(form.ts.get_value())),
              summary=form.summary.get_value())

def appts_on_day(dt):
    start_day = dt.replace(hour=0, minute=0, second=0).astimezone(pytz.utc)
    end_day = (dt + datetime.timedelta(seconds=86400)).replace(hour=0, minute=0, second=0).astimezone(pytz.utc)

    Q = web.db.SQLQuery
    P = web.db.SQLParam

    print 'from', start_day
    print 'to', end_day

    return db.select(['journal','appointment'],
                     where=Q(['journal.kind=',P('appointment'),
                              'and ts>',P(store_datetime(start_day)),
                              'and ts<',P(store_datetime(end_day)),
                              'and journal.id=appointment.journalid']),
                     order='ts ASC').list()

def new_appt(patientid, dt, **kw):
    at = dt.replace(second=0, microsecond=0, minute=(dt.minute - dt.minute%10)).astimezone(pytz.utc)
    journalid = db.insert('journal', patientid=patientid, ts=store_datetime(at), kind='appointment', summary=kw.get('summary','test'))
    if 'summary' in kw:
        kw.pop('summary')
    return db.insert('appointment', journalid=journalid, **kw)

def appt_tx_set(appointmentid, txs):
    db.update('tx',
              where='appointmentid = %d' % appointmentid,
              appointmentid=None)
    db.update('tx',
              where='id in %s' % str(tuple(txs)),
              appointmentid=appointmentid)

# appointment
# =================================================================
