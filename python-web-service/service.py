import web
import os
import glob
import time
import redis

urls = (
    '/', 'Index',
    '/power', 'PowerController',
    '/temp', 'TempController',
    '/mode', 'ModeController'
)

r = redis.Redis(host='127.0.0.1', port=6379)
template_dir = os.path.abspath(os.path.dirname(__file__)) + '/templates'
renderer = web.template.render(template_dir)
application = web.application(urls, globals())


class BaseController(object):
    def status_response(self):
        curr_temp = int(float(r.get('temp_f')))
        system_threshold = int(r.get('system_threshold'))
        system_power = r.get('system_power')
        system_mode = r.get('system_mode')
        system_state = r.get('system_state')
        fan_status = r.get('fan_status')
        ac_status = r.get('ac_status')
        hp_status = r.get('hp_status')
        heat_status = r.get('heat_status')
        return '{"currentTemp": %s, "systemThreshold": %s, "systemPower": %s, "systemMode": %s, "systemState": %s, "fanStatus": %s, "acStatus": %s, "hpStatus": %s, "heatStatus": %s}' % (curr_temp, system_threshold, system_power, system_mode, system_state, fan_status, ac_status, hp_status, heat_status)


class Index(BaseController):
    def GET(self):
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

