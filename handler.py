#!/usr/bin/env python
# coding=utf-8

import json
import logging
import traceback
import tornado.web
import tornado.websocket

from module import service
from core import activity
from core.greentornado import greenify
from websocket import channel

handlers = {
    'services_activity': activity.ServicesActivity,
}
channel.bootstrap(handlers)

logger = logging.getLogger()

class APIHandler(tornado.web.RequestHandler):
    def get_params(self):
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

    def render(self, template, **kwargs):
        template = self.tpl.get_template(template)
        kwargs['handler'] = self
        kwargs['static_url'] = self.static_url
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
                services = [service.get(params['name'])]
            else:
                services = service.list_all()
            for _service in services:
                if hasattr(_service, '_%s' % method):
                    _exec = getattr(_service, '_%s' % method)
                    _exec()
                    data = {'status': 0, 'message': 'ok'}
        except Exception, e:
            logger.error(e)
            logger.error(traceback.format_exc())
        finally:
            self.to_json(data)

@greenify
class ActivityHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        global channel
        self.channel_name = self.request.path.split('/')[-1]
        logger.debug('open websocket channel: %s' % self.channel_name)
        channel.open_channel(self.channel_name, self)

    def on_message(self, message):
        logger.debug('websocket channel: %s got message' % self.channel_name)
        logger.debug(message)
        channel.handle_message(self.channel_name, message)

    def on_close(self):
        global channel
        logger.debug('close websocket channel: %s' % self.channel_name)
        channel.close_channel(self.channel_name, self)

@greenify
class MainHandler(WebHandler):
    def get(self):
        services = service.list_all()
        self.render('index.html', services=services)
