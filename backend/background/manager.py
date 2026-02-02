"""
Background runner manager: centralno mesto za registraciju i dohvatanje singleton Runner instance.
"""

_runner = None


def set_runner(runner):
    global _runner
    _runner = runner


def get_runner():
    return _runner
