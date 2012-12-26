import time

import web


urls = (
    '/', 'index',
    '/family/(.*)', 'family',
    '/pt/(.*)/', 'patient',
    '/pt/(.*)', 'patient_bounce',
)
app = web.application(urls, globals())
render = web.template.render('templates/', globals=globals()) #lazy!
db = web.database(dbn='sqlite', db='dp.sqlite')


class index:
    def GET(self):
        # TODO: something useful
        # list of patients? recent journal entries?
        raise web.seeother('/pt/1/')


# a list of multiple patients ... generally relatives

class family:
    def GET(self, id_as_string):
        try:
            patientid = int(id_as_string)
        except ValueError:
            return 'patient id %r not found' % id_as_string

        pts = list(db.where('patient', resparty=patientid))
        return render.family(pts)


# patient display

search_form = web.form.Form(
    web.form.Textbox('query'),
    web.form.Button('submit', type='submit', html='Search')
)

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
        f = search_form()
        f.validates()
        #TODO: lazy, SQL injection vector
        pts = list(db.select('patient', where='lastname like "%s%%"' % f.query.get_value()))
        if len(pts) == 1:
            raise web.seeother('/pt/%d/' % pts[0].id)
        elif len(pts) == 0:
            return 'no patient found'
        else:
            return render.family(pts)


if __name__ == "__main__":
    app.run()
