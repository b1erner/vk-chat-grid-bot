from __future__ import annotations
from loguru import logger
from config import Config
from db import DB
from vk_client import VK
from permissions import Guard
from handlers import Handlers

import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.getenv('PORT', '10000'))

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(b'OK')

def start_health_server(host: str, port: int):
    httpd = HTTPServer((host, port), HealthHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    logger.info(f"Health server listening on {host}:{port}")
    return httpd

def main():
    cfg = Config.from_env()
    db = DB(cfg.db_path)
    start_health_server(cfg.host, cfg.port)

    if not cfg.vk_token:
        logger.error("VK token is empty. Exiting.")
        return

    vk = VK(cfg.vk_token)
    guard = Guard(vk, cfg.owner_id or 0)
    handlers = Handlers(vk, db, guard)

    logger.info("Bot started. Listening Long Poll…")
    if not vk.longpoll:
        logger.error("Vk longpoll not initialized. Check token/group id.")
        return

    for event in vk.longpoll.listen():
        try:
            handlers.handle_event(event)
        except Exception as e:
            logger.exception(e)

if __name__ == "__main__":
    main()
