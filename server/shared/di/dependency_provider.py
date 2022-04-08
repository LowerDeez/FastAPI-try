import inspect
from textwrap import dedent
from typing import Callable, Dict, Type

from .exceptions import DependencyInjectionError, DependencyNotFound


class DependencyProvider:
    def __init__(self):
        self.provider_map: Dict[Type, Callable] = {}

    def get(self, protocol):
        try:
            return self.provider_map[protocol]()
        except KeyError:
            raise DependencyNotFound(protocol)

    def register_as_singleton(self, protocol, cls):
        instance = cls()
        self.provider_map[protocol] = lambda: instance

    def register_as_factory(self, protocol, cls):
        self.provider_map[protocol] = cls

    def register(self, protocol, cls, as_singleton: bool = True):
        self.check_implements_protocol(protocol, cls)

        if as_singleton:
            self.register_as_singleton(protocol, cls)
        else:
            self.register_as_factory(protocol, cls)

    def check_implements_protocol(self, protocol, cls):
        protocol_funcs = self.get_functions_with_signatures(protocol)
        cls_funcs = self.get_functions_with_signatures(cls)
        for name, sig in protocol_funcs.items():
            if name not in cls_funcs or cls_funcs[name] != sig:
                raise DependencyInjectionError(
                    dedent(
                        f"""
                        Class {cls} does not implement function '{name}' of protocol\
                        {protocol} correctly.
                        Protocol implementation: {sig}
                        Class implementation: {cls_funcs.get(name)}
                        """
                    )
                )

    def get_functions_with_signatures(self, cls):
        # ignore all functions which start with an underscore
        return {
            t[0]: inspect.signature(t[1])
            for t in inspect.getmembers(cls)
            if t[0][0] != "_" and inspect.isfunction(t[1])
        }


injector = DependencyProvider()
