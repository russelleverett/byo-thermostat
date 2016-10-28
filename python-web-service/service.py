import web
import os
import redis
import jsonpickle

urls = (
    '/', 'Index',
    '/power', 'PowerController',
    '/temp', 'TempController',
    '/mode', 'ModeController',
    '/settings', 'SettingsController'
)

r = redis.Redis(host='127.0.0.1', port=6379)
template_dir = os.path.abspath(os.path.dirname(__file__)) + '/templates'
renderer = web.template.render(template_dir)
application = web.application(urls, globals())

setting_keys = [
    'system_power',
    'system_mode',
    'system_threshold',
    'system_variance'
]
report_keys = [
    'system_power',
    'system_mode',
    'system_threshold',
    'system_variance',
    'system_state',
    'fan_status',
    'ac_status',
    'heat_status',
    'hp_status',
    'temp_f',
    'temp_c'
]


class BaseController(object):
    _post_data = None

    @property
    def post_data(self):
        if self._post_data is None:
            data = web.data()
            if data is not None:
                self._post_data = jsonpickle.decode(data)
        return self._post_data

    def status_response(self):
        rvalue = ""
        for setting in report_keys:
            rvalue += '"%s": %s,' % (self.to_camel_case(setting), r.get(setting))
        return '{%s}' % rvalue[:-1]

    @staticmethod
    def to_camel_case(name):
        components = name.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])


class Index(BaseController):
    def GET(self):
        return self.status_response()


class SettingsController(BaseController):
    setting_keys = ['system_power', 'system_mode', 'system_threshold', 'system_variance']

    def POST(self):
        settings = self.post_data
        for key in self.setting_keys:
            if key in settings:
                print key, type(settings[key])
                r.set(key, settings[key])
        return self.status_response()


class PowerController(BaseController):
    def GET(self):
        user_data = web.input(value=True)
        r.set('system_power', user_data.value)
        return self.status_response()


class TempController(BaseController):
    def GET(self):
        user_data = web.input()
        if user_data.value is not None:
            r.set('system_threshold', int(user_data.value))
        return self.status_response()


class ModeController(BaseController):
    def GET(self):
        user_data = web.input()
        if user_data.value is not None:
            r.set('system_mode', int(user_data.value))
        return self.status_response()

if __name__ == '__main__':
    application.run()
else:
    application = application.wsgifunc()

