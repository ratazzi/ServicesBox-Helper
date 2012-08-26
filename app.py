#!/usr/bin/env python
# coding=utf-8

"""Usage:
    app [--bind=ADDRESS] [--port=PORT] [-v | --verbose] [-d | --debug]

"""

import logging
import traceback
import tornado.web
import tornado.ioloop
import tornado.locale
import tornado.httpserver
# import eventlet
from eventlet.green import os
from jinja2 import Environment, FileSystemLoader
from docopt import docopt

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

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/websocket/.*', handler.ActivityHandler),
            (r'/api/service', handler.ServiceHandler),
            (r'/api/store', handler.StoreHandler),
            (r'/options', handler.OptionsHandler),
            (r'/.*', handler.MainHandler),
        ]
        settings = dict(
            template_path=runtime.path.resources_path('templates'),
            static_path=runtime.path.resources_path('static'),
            cookie_secret='11oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=',
            login_url='/signin/',
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

        self.jinja = Environment(loader=FileSystemLoader(settings['template_path']))
        # self.jinja.filters['timeline'] = timeline
        self.locale = tornado.locale.get('zh_CN')
        self.store = Store()

if __name__ == '__main__':
    options = docopt(__doc__, version='0.1.0')

    try:
        # ctl.do_repair()
        ctl.start_all_services(True)
        http_server = tornado.httpserver.HTTPServer(Application())
        addr = options['--bind'] or '0.0.0.0'
        port = options['--port'] and int(options['--port']) or 8000
        logger.debug("(%d) starting up on http://%s:%d" % (os.getpid(), addr, port))
        http_server.listen(port, addr)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.instance().stop()
        print 'exited.'
    except Exception, e:
        logger.error(e)
        logger.error(traceback.format_exc())
