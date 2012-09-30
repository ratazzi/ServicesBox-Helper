#!/usr/bin/env python
# coding=utf-8

"""Usage:
    dashboard [--bind=ADDRESS] [--port=PORT] [-v | --verbose] [-d | --debug]

"""

import logging
import locale
import traceback
import tornado.web
import tornado.locale
from eventlet.green import os
from jinja2 import Environment, FileSystemLoader
from docopt import docopt
from tornadio2 import TornadioRouter, SocketServer

logger = logging.getLogger()
console = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(name)s %(lineno)s %(message)s')
console.setFormatter(formatter)
console.setLevel(logging.DEBUG)
logger.addHandler(console)
logger.setLevel(logging.DEBUG)

import runtime.path
runtime.path.bootstrap()
import storage
storage.init()
import ctl
import handler
from runtime import env
from module.store import Store

tornado.locale.load_translations(runtime.path.resources_path('i18n', True))

class SocketIOApplication(tornado.web.Application):
    def __init__(self, **settings):
        params = dict(
            enabled_protocols=['websocket', 'xhr-polling', 'jsonp-polling', 'htmlfile']
        )
        router = TornadioRouter(handler.SocketIOHandler, params)
        handlers = router.apply_routes([
            (r'/api/service', handler.ServiceHandler),
            (r'/api/store', handler.StoreHandler),
            (r'/options', handler.OptionsHandler),
            (r'/', handler.MainHandler),
        ])
        tornado.web.Application.__init__(self, handlers, **settings)

        self.jinja = Environment(loader=FileSystemLoader(settings['template_path']))
        tornado.locale.set_default_locale('en_US')
        self.locale = tornado.locale.get(locale.getdefaultlocale()[0])
        self.store = Store()

if __name__ == '__main__':
    options = docopt(__doc__, version='0.1.0')

    try:
        # ctl.do_repair()
        ctl.start_all_services(True)
        addr = options['--bind'] or '0.0.0.0'
        port = options['--port'] and int(options['--port']) or 8000

        settings = dict(
            template_path=runtime.path.resources_path('templates'),
            static_path=runtime.path.resources_path('static'),
            cookie_secret='11oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=',
            flash_policy_port=1843,
            # flash_policy_file=,
            socket_io_port=port,
            debug=True,
        )
        app = SocketIOApplication(**settings)
        SocketServer(app)
    except KeyboardInterrupt:
        print 'exited.'
    except Exception, e:
        logger.error(e)
        logger.error(traceback.format_exc())
