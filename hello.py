import time

import web


urls = (
    '/', 'index',
    '/pt/(.*)/', 'patient',
    '/pt/(.*)', 'patient_bounce',
)
app = web.application(urls, globals())
render = web.template.render('templates/', globals=globals()) #lazy!
db = web.database(dbn='sqlite', db='dp.sqlite')


class index:
    def GET(self):
        return 'Hello, world!'


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

        return render.pt(pt, resparty, journal)


if __name__ == "__main__":
    app.run()
