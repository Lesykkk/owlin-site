import json

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from owlin.modules.catalog.constants import MAX_ORDER_REQUEST_BYTES

# Plain JSON requests are tiny. Only order uploads carry files and may be larger.
DEFAULT_LIMIT_BYTES = 64 * 1024
LIMITS_BY_PATH = {"/api/orders": MAX_ORDER_REQUEST_BYTES}


class BodyTooLargeError(Exception):
    pass


class BodyLimitMiddleware:
    """Refuses oversized request bodies before they are read into memory or onto disk.

    A client that announces a too large body is refused at once. One that lies about the size, or
    sends it in chunks, is cut off as soon as it has sent more than the limit.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] not in {"POST", "PUT", "PATCH"}:
            await self.app(scope, receive, send)
            return

        limit = LIMITS_BY_PATH.get(scope["path"], DEFAULT_LIMIT_BYTES)
        announced = dict(scope["headers"]).get(b"content-length")
        if announced is not None and announced.isdigit() and int(announced) > limit:
            await self._refuse(send)
            return

        received = 0
        response_started = False

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    raise BodyTooLargeError
            return message

        async def tracking_send(message: Message) -> None:
            nonlocal response_started
            response_started = response_started or message["type"] == "http.response.start"
            await send(message)

        try:
            await self.app(scope, limited_receive, tracking_send)
        except BodyTooLargeError:
            if not response_started:
                await self._refuse(send)

    @staticmethod
    async def _refuse(send: Send) -> None:
        body = json.dumps({"detail": "The request is too large"}).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())],
            }
        )
        await send({"type": "http.response.body", "body": body})
