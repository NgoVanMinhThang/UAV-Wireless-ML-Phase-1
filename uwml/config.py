from __future__ import annotations
import yaml, types
class DotDict(types.SimpleNamespace):
    @classmethod
    def from_dict(cls, d):
        ns = cls()
        for k, v in d.items():
            setattr(ns, k, cls.from_dict(v) if isinstance(v, dict) else v)
        return ns
def load_config(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return DotDict.from_dict(data)
