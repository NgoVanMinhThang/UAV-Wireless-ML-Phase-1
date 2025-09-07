from __future__ import annotations
class Renderer3DBase:
    def loop(self, world, dt: float, steps: int): raise NotImplementedError
