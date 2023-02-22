class ObjectNotFound(Exception):
    """Raised when an object is expected but none are found.
    """

class DuplicateObject(Exception):
    """Raised when a single object is expected but multiple
    objects are returned.
    """
