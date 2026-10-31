"""Effect registry: /effects <name> → module."""
import importlib

ORDER = ["glass-widgets", "documentary", "orbit", "chart-split", "spotlight", "checklist", "timeline"]


def load(name):
    return importlib.import_module("effects." + name.replace("-", "_"))


def all_effects():
    return [load(n) for n in ORDER]
