import datetime

import pytz
import web


db = web.database(dbn='sqlite', db='dp.sqlite')

# TODO: belongs in config file
tz = pytz.timezone('US/Central')
db_fmt = '%Y-%m-%d %H:%M:%S.%f'
display_fmt = '%Y-%m-%d %H:%M (%Z)'


# =================================================================
# schema


schema = [
    # makes extensive use of automatic string concatenation by the parser
    'create table if not exists patient'
    ' (id integer primary key,'
    '  firstname string,'
    '  middlename string,'
    '  lastname string,'
    '  resparty integer references patient(id),'
    '  birthday date)',

    'create table if not exists journal'
    ' (id integer primary key,'
    '  patientid integer references patient(id),'
    '  ts datetime,'
    '  kind string,'
    '  summary text,'
    '  money currency)',

    'create table if not exists contact'
    ' (journalid integer primary key,'
    '  details text)',

    'create table if not exists appointment'
    ' (journalid integer primary key,'
    '  duration integer,'
    '  status string,'
    '  kind string)',

    'create table if not exists progress'
    ' (journalid integer primary key,'
    '  sub text,'
    '  obj text,'
    '  ass text,'
    '  pln text)',

    'create table if not exists rx'
    ' (journalid integer primary key,'
    '  disp string,'
    '  sig string,'
    '  refills string)',

    'create table if not exists tx'
    ' (id integer primary key,'
    '  journalid integer references journal(id),'
    '  patientid integer references patient(id),'
    '  appointmentid integer references appointment(id),'
    '  claimid integer references claim(id),'
    '  summary string,'
    '  code integer,'
    '  tooth string,'
    '  surf string,'
    '  fee currency)',
]

def create_schema():
    for q in schema:
        db.query(q)


def current_time():
    return datetime.datetime.now(pytz.utc)

def to_dt_string(dt):
    return dt.strftime(db_fmt)

def from_dt_string(s):
    return datetime.datetime.strptime(s, db_fmt).replace(tzinfo=pytz.utc)

def display_dt_string(dt):
    return dt.astimezone(tz).strftime(display_fmt)


# schema
# =================================================================
# pt


def pt_name(pt, first='firstname'):
    if first == 'lastname':
        return '%s, %s %s' % (pt.lastname or '', pt.firstname or '', pt.middlename or '')
    else:
        return '%s %s %s' % (pt.firstname or '', pt.middlename or '', pt.lastname or '')

def pt_name_search(q):
    q = q.replace(',','%,').replace(', ',',').replace(' ','% ')
    if not q:
        return list()
    else:
        q += '%'
    query = web.db.SQLQuery(["coalesce(lastname,'')||','||coalesce(firstname,'')||' '||coalesce(middlename,'') like ", web.db.sqlquote(q)])
    return list(db.select('patient', where=query))

def get_pt(id):
    try:
        return db.where('patient', id=id)[0]
    except IndexError:
        return None

def get_family(resparty):
    # TODO should include the resparty if their resparty entry is blank
    #  ... it would be nice to avoid this by always putting a resparty in
    #  ... but that's nontrivial for new patients :/
    return db.where('patient', resparty=resparty)

def update_pt(f, resparty):
    d = dict([(k, f[k].get_value())
              for k in 'firstname','middlename','lastname','birthday'])
    d['id'] = f.id.get_value() or None
    d['resparty'] = resparty
    db.query('insert or replace into patient values ($id, $firstname, $middlename, $lastname, $resparty, $birthday)', d)
    row = db.query('select last_insert_rowid() as id')[0]
    return row.id

def get_latest_address(patientid):
    # TODO: should go to responsible party if pt doesn't have an address
    addresses = db.where('journal', kind='address', patientid=patientid, order='id DESC')
    try:
        return addresses[0]
    except IndexError:
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
        # will probably need a more specialized handler
        pass


def new_journal(pt, kind, f):
    journalid = db.insert('journal',
                          patientid = pt.id,
                          ts = to_dt_string(current_time()),
                          kind = kind,
                          summary = f.summary.get_value())
    getattr(new_handlers, kind)(journalid, f)

def get_journal(patientid, **kw):
    # TODO: make sure the only keys in kw are limit and offset
    return db.where('journal', order='id DESC', patientid=patientid, **kw).list()

def get_journal_entry(journalid):
    return db.where('journal', id=journalid)[0]

def get_contact(journalid):
    return db.where('contact', journalid=journalid)[0]

def get_progress(journalid):
    return db.where('progress', journalid=journalid)[0]

def get_Rx(journalid):
    return db.where('Rx', journalid=journalid)[0]


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


# txplan
# =================================================================
