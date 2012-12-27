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


# how to search for patients ... can come from multiple places

search_form = web.form.Form(
    web.form.Textbox('query'),
    web.form.Button('submit', type='submit', html='Search')
)

def POST_search_for_patient():
    f = search_form()
    f.validates()
    query = web.db.SQLQuery(['lastname like ', web.db.sqlquote(f.query.get_value() + '%')])
    pts = list(db.select('patient', where=query))
    if len(pts) == 1:
        raise web.seeother('/pt/%d/' % pts[0].id)
    elif len(pts) == 0:
        return 'no patient found'
    else:
        return render.family(pts)


# ye olde index

class index:
    def GET(self):
        return render.index(search_form())

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
        return render.family(pts)


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

        return render.pt(search_form(), pt, resparty, journal)

    def POST(self, *args):
        return POST_search_for_patient()


if __name__ == "__main__":
    app.run()
