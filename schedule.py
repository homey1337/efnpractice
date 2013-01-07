import datetime

import config
import hello
import model

import web


class oneday:
    def GET(self, dtstring=''):
        if dtstring:
            dt = model.input_date(dtstring)
        else:
            dt = model.local_time()
        appts = model.appts_on_day(dt)
        pts = dict()
        ps = list()
        for a in appts:
            if a.patientid not in pts:
                p = model.get_pt(a.patientid)
                pts[a.patientid] = p
        return hello.render.oneday(dt, appts, pts)


class days:
    def GET(self):
        inp = web.input(first=model.display_date(model.local_time()),
                        last=model.display_date(model.local_time()))
        first = model.input_date(inp.first)
        last = model.input_date(inp.last)
        if last < first:
            last = first

        curr = first
        days = list()
        pts = dict()
        while curr <= last:
            appts = model.appts_on_day(curr)
            for a in appts:
                if a.patientid not in pts:
                    pts[a.patientid] = model.get_pt(a.patientid)
            days.append((curr, appts))
            curr += datetime.timedelta(days=1)
        return hello.render.days(days, pts)
