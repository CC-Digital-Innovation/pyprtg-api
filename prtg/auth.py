from requests.auth import AuthBase

class BasicAuth(AuthBase):
    """Basic authentication using username and password"""
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __call__(self, r):
        r.prepare_url(r.url, {'username': self.username, 'password': self.password})
        return r

class BasicPasshash(AuthBase):
    """Like BasicAuth, this basic authentication uses
    username but uses passhash in place of password."""
    def __init__(self, username, passhash):
        self.username = username
        self.passhash = passhash

    def __call__(self, r):
        r.prepare_url(r.url, {'username': self.username, 'passhash': self.passhash})
        return r

class BasicToken(AuthBase):
    """Basic authentication using only API token."""
    def __init__(self, api_token):
        self.api_token = api_token

    def __call__(self, r):
        r.prepare_url(r.url, {'apitoken': self.api_token})
        return r