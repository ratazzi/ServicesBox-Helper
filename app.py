#!/usr/bin/env python
# coding=utf-8

import tornado.web
import tornado.ioloop
import tornado.httpserver

from jinja2 import Environment, FileSystemLoader

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("It's running.")

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/.*', MainHandler),
        ]
        settings = dict(
            template_path='templates',
            static_path='static',
            cookie_secret='11oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=',
            login_url='/signin/',
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

        self.jinja = Environment(loader=FileSystemLoader(settings['template_path']))
        # self.jinja.filters['timeline'] = timeline

def main():
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(8080)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.instance().stop()
        print 'exited.'
