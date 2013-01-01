from hello import render
import forms
import model


class show:
    def GET(self, id):
        pt = model.get_pt(id)
        newtx = forms.newtx()
        txplan = model.get_txplan(pt.id)
        return render.txplan(pt, newtx, txplan)

    def POST(self, id):
        pt = model.get_pt(id)
        newtx = forms.newtx()
        if not newtx.validates():
            txplan = model.get_txplan(pt.id)
            return render.txplan(pt, newtx, txplan)
        else:
            model.new_tx(pt.id, summary=newtx.tx.get_value(), fee='10.01')
            txplan = model.get_txplan(pt.id)
            return render.txplan(pt, newtx, txplan)
