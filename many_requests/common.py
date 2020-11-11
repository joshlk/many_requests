from collections.abc import Iterable

N_WORKERS_DEFAULT = 15
N_CONNECTIONS_DEFAULT = 10


class BadResponse(Exception):
    """BadResponse exception. Contains the `response`, `reason` and `attempt_num` as data if supplied."""
    def __init__(self, description, response=None, reason=None, attempt_num=None):
        self.description = description
        self.response = response
        self.reason = reason
        self.retry_num = attempt_num

    def __repr__(self):
        return f"BadResponse('{self.description}')"


def is_collection(var):
    """Test if iterable but not a string"""
    return isinstance(var, Iterable) and not isinstance(var, str)
