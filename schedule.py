import hello
import model

import web


class oneday:
    def GET(self, dtstring):
        dt = model.from_dt_string(dtstring, '%Y-%m-%d', model.tz)
        appts = model.appts_on_day(dt)
        pts = dict()
        ps = list()
        for a in appts:
            if a.patientid not in pts:
                p = model.get_pt(a.patientid)
                pts[a.patientid] = p
            ps.append(pts[a.patientid])
        return hello.render.oneday(dt,appts,ps)
