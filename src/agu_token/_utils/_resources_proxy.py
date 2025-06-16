from __future__ import annotations

from typing import Any
from typing_extensions import override

from ._proxy import LazyProxy


class ResourcesProxy(LazyProxy[Any]):
    """A proxy for the `agu_token.resources` module.

    This is used so that we can lazily import `agu_token.resources` only when
    needed *and* so that users can just import `agu_token` and reference `agu_token.resources`
    """

    @override
    def __load__(self) -> Any:
        import importlib

        mod = importlib.import_module("agu_token.resources")
        return mod


resources = ResourcesProxy().__as_proxied__()
