"""Minimal fallbacks for the dependency-free focused runtime check.

The normal project install provides httpx and pydantic.  The runtime checker
installs only pytest, so keep these small test-only shims available for that
environment without changing the application package's production imports.
"""

import sys
import types
import asyncio
import inspect


def _install_httpx_fallback() -> None:
    if "httpx" in sys.modules:
        return
    try:
        __import__("httpx")
        return
    except ModuleNotFoundError:
        pass

    class Request:
        def __init__(self, method: str, url: str, **kwargs):
            self.method = method
            self.url = url
            self.headers = kwargs.get("headers", {})
            self.content = kwargs.get("content")

    class Response:
        def __init__(self, status_code: int, json=None, headers=None):
            self.status_code = status_code
            self._json = json
            self.headers = headers or {}

        def json(self):
            if self._json is Exception:
                raise ValueError("invalid JSON")
            return self._json

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError(f"HTTP {self.status_code}")

    class MockTransport:
        def __init__(self, handler):
            self.handler = handler

    class AsyncClient:
        def __init__(self, base_url="", headers=None, transport=None):
            self.base_url = base_url
            self.headers = headers or {}
            self.transport = transport

        async def request(self, method, url, json=None):
            request = Request(method, url, headers=self.headers, content=json)
            return await self.transport.handler(request)

        async def aclose(self):
            return None

    module = types.ModuleType("httpx")
    module.Request = Request
    module.Response = Response
    module.MockTransport = MockTransport
    module.AsyncClient = AsyncClient
    module.AsyncBaseTransport = object
    sys.modules["httpx"] = module


def _install_pydantic_fallback() -> None:
    if "pydantic" in sys.modules:
        return
    try:
        __import__("pydantic")
        return
    except ModuleNotFoundError:
        pass

    class BaseModel:
        def __init__(self, **values):
            annotations = getattr(type(self), "__annotations__", {})
            for name in annotations:
                if name in values:
                    setattr(self, name, values[name])

    def Field(default=None, **kwargs):
        return default

    module = types.ModuleType("pydantic")
    module.BaseModel = BaseModel
    module.Field = Field
    sys.modules["pydantic"] = module


_install_httpx_fallback()
_install_pydantic_fallback()


def pytest_pyfunc_call(pyfuncitem):
    """Run coroutine tests when pytest-asyncio is not installed."""
    test = pyfuncitem.obj
    if inspect.iscoroutinefunction(test):
        asyncio.run(test(**pyfuncitem.funcargs))
        return True
    return None
