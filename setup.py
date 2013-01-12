import forms
import hello
import model


class carriers:
    def GET(self):
        return hello.render.carriers(model.get_carriers(), forms.carrier())

    def POST(self):
        form = forms.carrier()
        if not form.validates():
            return hello.render.carriers(model.get_carriers(), form)
        model.new_carrier(form)
        return hello.render.carriers(model.get_carriers(), form)
