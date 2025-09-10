import os
import threading
from vk_client import VKClient
from db import DB
from handlers import Handlers
from config import Config

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

def main():
    config = Config.from_env()
    token = config.vk_token
    vk = VKClient(token)
    db = DB(config.database_path)
    handlers = Handlers(vk, db, config)

    # health server
    from http.server import HTTPServer, BaseHTTPRequestHandler
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
    port = int(os.getenv("PORT", 10000))
    def run_server():
        server = HTTPServer(("0.0.0.0", port), H)
        server.serve_forever()
    t = threading.Thread(target=run_server, daemon=True)
    t.start()

    session = vk_api.VkApi(token=token)
    longpoll = VkBotLongPoll(session, config.group_id)
    print("Bot started")
    for event in longpoll.listen():
        try:
            if event.type == VkBotEventType.MESSAGE_NEW:
                handlers.handle_event(event)
        except Exception as e:
            print("Event handling error:", e)
            continue

if __name__ == "__main__":
    main()
