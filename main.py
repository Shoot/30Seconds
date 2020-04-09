#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import os
import websockets

from server.controller import controller
from server.server import server

if not os.path.isdir('logs'):
	os.mkdir('logs')

logging.basicConfig(
	filename='logs/server.log',
	format="[%(asctime)s] [%(name)s] %(levelname)s: %(message)s",
	datefmt="%Y-%m-%d %H:%M:%S",
	level=logging.INFO
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(
	logging.Formatter("[%(asctime)s] [%(name)s] %(levelname)s: %(message)s")
)

logging.getLogger('').addHandler(console)
log = logging.getLogger(__name__)

ws_logger = logging.getLogger('websockets')
ws_logger.setLevel(logging.DEBUG)

ws_handler = logging.FileHandler('logs/websockets.log')
ws_handler.setFormatter(
	logging.Formatter("[%(asctime)s] [%(name)s] %(levelname)s: %(message)s")
)

ws_logger.addHandler(ws_handler)
ws_logger.propagate = False

loop = asyncio.get_event_loop()

tasks = asyncio.gather(
	websockets.serve(server, 'localhost', 5000),
	controller()
)

try:
	loop.run_until_complete(tasks)
	loop.run_forever()
finally:
	loop.close()