class Unauthorized(Exception):
    """Raised when access to API failed from lacking or
    having incorrect credentials
    """

class ObjectNotFound(Exception):
    """Raised when an object is expected but none are found.
    """

class DuplicateObject(Exception):
    """Raised when a single object is expected but multiple
    objects are returned.
    """
