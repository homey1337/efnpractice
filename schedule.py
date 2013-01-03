import hello
import model

import web


class oneday:
    def GET(self, dtstring):
        dt = model.from_dt_string(dtstring, '%Y-%m-%d', model.tz)
        appts = model.appts_on_day(dt)
        journals = list()
        pts = list()
        for a in appts:
            j = model.get_journal_entry(a.journalid)
            p = model.get_pt(j.patientid)
            journals.append(j)
            pts.append(p)
        return hello.render.oneday(journals,appts,pts)
