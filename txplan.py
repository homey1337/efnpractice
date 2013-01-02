from hello import render
import forms
import model

import web

def new_tx(patientid, summary):
    tokens = [x.lower() for x in summary.split()]
    txs = list()
    if tokens[0].startswith('#'):
        tooth = int(tokens[0][1:])
        for thing in tokens[1:]:
            # TODO: lookup fees from a schedule
            if thing.startswith('c'):
                txs.append(('#%s %s' % (tooth, 'crown'),
                            2740, tooth, None, 1000.00))
            elif thing.startswith('b'):
                txs.append(('#%s %s' % (tooth, 'buildup'),
                            2950, tooth, None, 250.00))
            elif thing.startswith('p'):
                txs.append(('#%s %s' % (tooth, 'post'),
                            2954, tooth, None, 300.00))
            elif thing.startswith('r'):
                code = fee = None
                if tooth in (6, 7, 8, 9, 10, 11, 22, 23, 24, 25, 26, 27):
                    code = 3310
                    fee = 500.00
                elif tooth in (4, 5, 12, 13, 20, 21, 28, 29):
                    code = 3320
                    fee = 600.00
                elif tooth in (1, 2, 3, 14, 15, 16, 17, 18, 19, 30, 31, 32):
                    code = 3330
                    fee = 800.00
                txs.append(('#%s %s' % (tooth, 'rct'),
                            code, tooth, None, fee))
            elif thing.startswith('e'):
                txs.append(('#%s %s' % (tooth, 'ext'),
                            7210, tooth, None, fee))
            else:
                for c in thing:
                    if c not in 'moidbfl':
                        raise ValueError("invalid surface '%s'" % c)
                code = fee = None
                if tooth in (6, 7, 8, 9, 10, 11, 22, 23, 24, 25, 26, 27):
                    code = 2330 + len(thing) - 1
                    if 'i' in thing:
                        code = 2335
                    fee = 200.0 + 30*len(thing)
                else:
                    code = 2390 + len(thing)
                    fee = 200.0 + 30*len(thing)
                txs.append(('#%s %s' % (tooth, thing),
                            code, tooth, thing, fee))
    else:
        if tokens[0] == 'srp':
            if len(tokens) == 1:
                tokens[1:] = 'lr','ur','ll','ul'
            for area in tokens[1:]:
                txs.append(('%s %s' % ('srp', area),
                            4341, area, None, 200.00))
        elif tokens[0] == 'seal':
            if len(tokens) == 1:
                tokens[1:] = map(str, [3, 14, 19, 30])
            for tooth in tokens[1:]:
                if tooth.startswith('#'):
                    tooth = tooth[1:]
                txs.append(('%s #%s' % ('seal', tooth),
                            1351, int(tooth), None, 50.00))
        elif tokens[0] == 'newpt':
            for code,summary,fee in ((150,'exam',70.00),
                                     (274,'bitewings',65.00),
                                     (330,'pano',100.00),
                                     (1110,'prophy',75.00)):
                txs.append((summary, code, None, None, fee))
        elif tokens[0] == 'pa':
            code = 220
            fee = 25.00
            for tooth in tokens[1:]:
                if tooth.startswith('#'):
                    tooth = tooth[1:]
                txs.append(('%s #%s' % ('pa', tooth),
                            code, int(tooth), None, fee))
                code = 230
                fee = 20.00
        else:
            raise ValueError('could not understand')

    for summary, code, tooth, surf, fee in txs:
        model.new_tx(patientid,
                     summary=summary,
                     code=code,
                     tooth=tooth,
                     surf=surf,
                     fee=fee)
                

class show:
    def GET(self, id):
        pt = model.get_pt(id)
        newtx = forms.newtx()
        txplan = model.get_txplan(pt.id)
        return render.txplan(pt, newtx, txplan)

    def POST(self, id):
        pt = model.get_pt(id)
        newtx = forms.newtx()
        if newtx.validates():
            try:
                new_tx(pt.id, newtx.tx.get_value())
            except ValueError, e:
                newtx.inputs[0].note = e.message
        txplan = model.get_txplan(pt.id)
        return render.txplan(pt, newtx, txplan)


class edit_appt:
    def GET(self, id):
        journal = model.get_journal_entry(id)
        appointment = model.get_appointment(journal.id)
        pt = model.get_pt(journal.patientid)
        txs = model.get_txplan(pt.id)
        return render.edit_appt(journal, appointment, pt, txs)

    def POST(self, id):
        inp = web.input(txs=list())
        id = int(id)
        model.appt_tx_clear(id)
        txs = list()
        for tx in inp.txs:
            txs.append(int(tx))
        model.appt_tx_set(id, txs)
        raise web.seeother('/appointment/%s' % id)
