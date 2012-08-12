#!/usr/bin/env python
# coding=utf-8

import json
import logging
import traceback
import types
import eventlet

tasks = dict()
channels = dict()
channel2task = dict()
channel2queue = dict()

logger = logging.getLogger()

def bootstrap(handlers):
    """register channel_name and function"""
    global channel2task
    channel2task.update(handlers)

def broadcast(channel_name, message):
    """write_message for channel_name all handlers"""
    global channels
    try:
        for handler in channels.get(channel_name, []):
            handler.write_message(json.dumps(message))
    except Exception, e:
        logger.error(e)
        logger.error(traceback.format_exc())

def handle_message(channel_name, message):
    global channel2queue
    queue = channel2queue.get(channel_name, None)
    if queue:
        queue.put(message)

def open_channel(channel_name, handler):
    """open websocket channel"""
    global tasks, channels, channel2task
    try:
        logger.debug('>>> open websocket channel: %s' % channel_name)
        onlines = channels.setdefault(channel_name, set())
        if channel_name not in tasks:
            _exec = channel2task[channel_name]
            if isinstance(_exec, types.TypeType):
                instance = _exec(channel_name, handler)
                channel2queue[channel_name] = instance.recv_queue
                task = eventlet.spawn(instance.run)
            else:
                task = eventlet.spawn(_exec, channel_name, handler)
            tasks[channel_name] = task
        onlines.add(handler)
        logger.debug(onlines)
    except Exception, e:
        logger.error(e)
        logger.error(traceback.format_exc())

def close_channel(channel_name, handler):
    """close websocket channel"""
    global tasks, channels, channel2task
    try:
        onlines = channels.setdefault(channel_name, set())
        logger.info('>>> close websocket channel: %s' % channel_name)
        logger.debug('>>> remove handler %s' % handler)
        onlines.discard(handler)
        if len(onlines) == 0:
            _task = tasks.pop(channel_name, None)
            logger.debug('>>> task: %s' % _task)
            if isinstance(_task, eventlet.greenthread.GreenThread):
                logger.debug('>>> kill task: %s' % _task)
                _task.kill()
        logger.debug("channel `%s' onlines: %s" % (channel_name, onlines))
        logger.debug("channel `%s' tasks: %s" % (channel_name, tasks.get(channel_name, [])))
    except Exception, e:
        logger.error(e)
        logger.error(traceback.format_exc())
