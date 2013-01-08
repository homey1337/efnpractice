import datetime
import random

import model
import txplan

db = model.db


consonants = 'bdfjklmnpstvwyz'
vowels = 'aeiou'
surfaces = 'modbl'


def random_syllable():
    return '%s%s' % (random.choice(consonants), random.choice(vowels))
    
def random_name():
    r = 4
    l = random.randrange(r)
    while not l:
        r += 2
        l = random.randrange(r)
    return ''.join([random_syllable() for s in range(l)])

def random_given_names():
    m = random.randrange(12)
    if not m:
        return ' '.join([random_name() for s in range(3)])
    else:
        return ' '.join([random_name() for s in range(2)])


def make_person(name, age, resparty):
    month = random.randrange(1, 13)
    day = random.randrange(1, 29)
    year = 2013 - age
    birthday = '%d-%d-%d' % (2013-age,
                             random.randrange(1, 13),
                             random.randrange(1, 29))
    return db.insert('patient',
                     name = name,
                     resparty = resparty,
                     birthday = birthday)

def RN(fn):
    return '%s %s' % (random_given_names(), fn)

def make_family():
    r = 2
    n = random.randrange(r)
    while not n:
        r += 2
        n = random.randrange(r)
    family_name = random_name()
    resparty = make_person(RN(family_name), random.randrange(30, 60), None)
    db.update('patient', where='id=%d'%resparty, resparty=resparty)
    spouse = make_person(RN(family_name), random.randrange(30, 60), resparty)
    for i in range(n):
        make_person(RN(family_name), random.randrange(20), resparty)
    return resparty, n

def random_tx(patientid, appointmentid):
    if random.random() < .8:
        tooth = random.randrange(32) + 1
        if random.random() < .8:
            nsurf = random.randrange(3)+1
            surf = set()
            while len(surf) < nsurf:
                surf.add(random.choice(surfaces))
            txplan.new_tx(patientid, '#%d %s' % (tooth, ''.join(surf)), appointmentid)
        else:
            if random.random() < .8:
                txplan.new_tx(patientid, '#%d r p c' % tooth, appointmentid)
            else:
                txplan.new_tx(patientid, '#%d e' % tooth, appointmentid)
    else:
        txplan.new_tx(patientid, random.choice(['srp', 'seal', 'newpt']), appointmentid)

def fill_schedule(npatients, date):
    hour = 8
    while hour < 17:
        if hour == 12:
            hour += 1
            continue
        patientid = random.randrange(npatients) + 1
        journalid = db.insert('journal',
                              patientid=patientid,
                              ts=model.store_datetime(model.input_datetime('%s %d:00' % (date, hour))),
                              kind='appointment',
                              summary=random_name())
        appointmentid = db.insert('appointment',
                                  journalid=journalid,
                                  duration=60,
                                  kind=random.choice(['test','tx','newpt']),
                                  status=random_name(),
                                  notes=' '.join([random_name() for i in range(random.randrange(5,10))]))
        for i in range(random.randrange(1, 4)):
            random_tx(patientid, appointmentid)

        hour += 1


if __name__ == '__main__':
    # make some patients
    for i in range(120):
        make_family()
    npatients = db.query('select last_insert_rowid() as m')[0].m
    c = datetime.date.today() - datetime.timedelta(90)
    d = c
    e = d + datetime.timedelta(180)
    while d <= e:
        fill_schedule(npatients, d.strftime('%Y-%m-%d'))
        d += datetime.timedelta(1)
    print 'http://localhost:8080/days?first=%s&last=%s' % (c.strftime('%Y-%m-%d'), e.strftime('%Y-%m-%d'))
