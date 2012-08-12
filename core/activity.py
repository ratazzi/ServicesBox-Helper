#!/usr/bin/env python
# coding=utf-8

import psutil
import logging
import traceback
import eventlet

logger = logging.getLogger(__name__)

from module import service
from websocket.channel import broadcast

class ServicesActivity(object):
    interval = 2
    recv_queue = eventlet.queue.Queue()
    channel_name = None
    handler = None

    def __init__(self, channel_name, handler):
        self.channel_name = channel_name
        self.handler = handler

    def handle_recv(self):
        while True:
            try:
                message = self.recv_queue.get()
                logger.debug('got message: %s' % message)
            except Exception, e:
                logger.error(e)
                logger.error(traceback.format_exc())
            finally:
                eventlet.sleep(0.2)

    def handle_send(self):
        while True:
            try:
                items = dict()
                for _service in service.list_all():
                    items[_service.name] = {
                        'name': _service.name,
                        'description': _service.description,
                        'running': False,
                    }

                services2exe = service.all_services_exe()
                exe2services = dict([(v, k) for k, v in services2exe.items()])
                for p in psutil.process_iter():
                    try:
                        _exe = p.exe
                        if _exe in exe2services:
                            items[exe2services.get(_exe)]['running'] = True
                    except psutil.error.AccessDenied:
                        pass
                    except psutil.error.NoSuchProcess:
                        pass
                broadcast(self.channel_name, items)
            except Exception, e:
                logger.error(e)
                logger.error(traceback.format_exc())
            finally:
                eventlet.sleep(self.interval)

    def run(self):
        eventlet.spawn(self.handle_recv)
        eventlet.spawn(self.handle_send)
