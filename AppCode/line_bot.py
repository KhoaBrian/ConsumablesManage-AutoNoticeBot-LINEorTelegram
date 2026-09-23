"""LINE Messaging API webhook and push-message integration."""

import logging
import re
import threading

try:
    from flask import Flask, abort, request
    from linebot.v3 import WebhookHandler
    from linebot.v3.exceptions import InvalidSignatureError
    from linebot.v3.messaging import (
        ApiClient,
        Configuration,
        MessagingApi,
        PushMessageRequest,
        ReplyMessageRequest,
        TextMessage,
    )
    from linebot.v3.webhooks import MessageEvent, TextMessageContent
except ImportError:                                                                   
    Flask = None


def strip_markdown(text):
    """Remove Telegram formatting markers for LINE plain-text messages."""
    text = str(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\*\*', '', text)
    return re.sub(r'[\*_`]', '', text)


class LineBotServer:
    """Runs a LINE webhook server without blocking the Qt event loop."""

    def __init__(self, channel_access_token, channel_secret, command_handler,
                 group_command_handler=None, host="0.0.0.0", port=8080):
        if Flask is None:
            raise RuntimeError(
                "LINE support requires flask and line-bot-sdk. "
                "Install the project dependencies before enabling LINE."
            )

        self.channel_access_token = channel_access_token
        self.host = host
        self.port = port
        self.command_handler = command_handler
        self.group_command_handler = group_command_handler
        self.configuration = Configuration(access_token=channel_access_token)
        self.handler = WebhookHandler(channel_secret)
        self.app = Flask(__name__)
        self._register_handlers()
        self._thread = None

    def _register_handlers(self):
        @self.app.post("/webhook/line")
        def line_webhook():
            signature = request.headers.get("X-Line-Signature")
            if not signature:
                abort(400)
            body = request.get_data(as_text=True)
            try:
                self.handler.handle(body, signature)
            except InvalidSignatureError:
                abort(400)
            return "OK"

        @self.handler.add(MessageEvent, message=TextMessageContent)
        def handle_text_message(event):
            if event.message.text.strip().lower() == "/setgroup":
                if self.group_command_handler and getattr(event.source, "type", None) == "group":
                    response = self.group_command_handler(event.source.group_id)
                else:
                    response = "Run /setgroup inside a LINE group to register that group."
            else:
                response = self.command_handler(event.message.text)
            if not response:
                return
            with ApiClient(self.configuration) as api_client:
                MessagingApi(api_client).reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=strip_markdown(response)[:5000])],
                    )
                )

    def start(self):
        """Start Flask in a daemon thread so the Qt GUI remains responsive."""
        self._thread = threading.Thread(
            target=self.app.run,
            kwargs={
                "host": self.host,
                "port": self.port,
                "debug": False,
                "use_reloader": False,
            },
            name="line-webhook",
            daemon=True,
        )
        self._thread.start()
        logging.info("LINE webhook listening on %s:%s/webhook/line", self.host, self.port)


def sendLineAlert(groupId, message, channel_access_token=None):
    """Send a LINE Push Message to a user, room, or group ID."""
    if not channel_access_token:
        logging.error("LINE push skipped: LINE_CHANNEL_ACCESS_TOKEN is not configured.")
        return False
    try:
        configuration = Configuration(access_token=channel_access_token)
        with ApiClient(configuration) as api_client:
            MessagingApi(api_client).push_message(
                PushMessageRequest(
                    to=groupId,
                    messages=[TextMessage(text=strip_markdown(message)[:5000])],
                )
            )
        return True
    except Exception:
        logging.exception("LINE push message failed for destination %s", groupId)
        return False
