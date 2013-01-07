import hello
import model

import web


class oneday:
    def GET(self, dtstring):
        dt = model.input_date(dtstring)
        appts = model.appts_on_day(dt)
        pts = dict()
        ps = list()
        for a in appts:
            if a.patientid not in pts:
                p = model.get_pt(a.patientid)
                pts[a.patientid] = p
        return hello.render.oneday(dt,appts,pts)


class today:
    def GET(self):
        raise web.seeother('/oneday/%s' % model.display_date(model.current_time()))
