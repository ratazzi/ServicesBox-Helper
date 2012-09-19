#!/usr/bin/env python
# coding=utf-8

import json
import logging
import traceback
import psutil
import tornado.web

import storage
from ctl import gen_config
from module import service
from module.schema import Service, Option, all_services_exe
# from core import activity
# from websocket import channel
from core.greentornado import greenify
from tornadio2 import SocketConnection, TornadioRouter, SocketServer, event

# handlers = {
#     'services_activity': activity.ServicesActivity,
# }
# channel.bootstrap(handlers)

logger = logging.getLogger()
store = storage.get_store()

class APIHandler(tornado.web.RequestHandler):
    def get_params(self):
        if 'application/json' in self.request.headers.get('Content-Type', ''):
            items = json.loads(self.request.body)
        else:
            items = dict()
            for k in self.request.arguments.keys():
                items[k] = self.get_argument(k)
        return items

    def to_json(self, data):
        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(data))

class WebHandler(tornado.web.RequestHandler):
    @property
    def tpl(self):
        return self.application.jinja

    def get_params(self):
        items = dict()
        for k in self.request.arguments.keys():
            items[k] = self.get_argument(k)
        return items

    def render(self, template, **kwargs):
        template = self.tpl.get_template(template)
        kwargs['handler'] = self
        kwargs['static_url'] = self.static_url
        kwargs['_'] = self.application.locale.translate
        self.write(template.render(**kwargs))

@greenify
class ServiceHandler(APIHandler):
    def post(self):
        params = self.get_params()
        logger.debug(params)

        data = {'status': 1, 'message': 'error'}
        try:
            method = params['method']
            if params['name'] != 'all':
                services = [store.find(Service, Service.name == params['name']).one()]
            else:
                services = store.find(Service)
            for _service in services:
                if hasattr(_service, '_%s' % method):
                    _exec = getattr(_service, '_%s' % method)
                    data = _exec(**params) or dict(status=0, message='ok')
        except Exception, e:
            logger.error(e)
            logger.error(traceback.format_exc())
        finally:
            logger.debug(data)
            self.to_json(data)

# @greenify
class SocketIOHandler(SocketConnection):
    @event
    def services_activity(self):
        try:
            items = dict()
            for _service in store.find(Service):
                items[_service.name] = {
                    'name': _service.name,
                    'description': _service.description,
                    'running': False,
                }

            services2exe = all_services_exe()
            exe2services = dict([(v, k) for k, v in services2exe.items()])
            for p in psutil.process_iter():
                try:
                    _exe = p.exe
                    if _exe in exe2services:
                        items[exe2services.get(_exe)]['running'] = True
                except (psutil.error.AccessDenied, psutil.error.NoSuchProcess):
                    pass
                except Exception, e:
                    logger.error(e)
            return items
        except Exception, e:
            logger.error(e)
            logger.error(traceback.format_exc())

@greenify
class MainHandler(WebHandler):
    def get(self):
        services = store.find(Service)
        runnings = service.list_running_services()
        self.render('index.html', services=services, runnings=runnings)

@greenify
class OptionsHandler(WebHandler):
    def get(self):
        options = store.find(Option)
        auto_regen = self.application.store['auto_regen']
        auto_regen = auto_regen and bool(int(auto_regen.value)) or False
        self.render('options.html', options=options, auto_regen=auto_regen)

    def post(self):
        params = self.get_params()
        try:
            _option = store.find(Option, Option.id == int(params['id'])).one()
            _option.value = params['value']
            store.add(_option)
            store.commit()
            auto_regen = self.application.store['auto_regen']
            auto_regen = auto_regen and bool(int(auto_regen.value)) or False
            if auto_regen:
                gen_config()
            self.write(params['value'])
        except Exception, e:
            logger.error(e)
            logger.error(traceback.format_exc())
            self.write(json.dumps({'status': 1, 'message': 'failed'}))

@greenify
class StoreHandler(APIHandler):
    def post(self):
        params = self.get_params()
        if 'key' in params and 'value' in params:
            self.application.store[params['key']] = params['value']
            data = {'status': 0, 'message': 'ok'}
        else:
            data = {'status': 1, 'message': 'failed'}
        self.to_json(data)
