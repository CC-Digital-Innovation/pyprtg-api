class BasicPassword:
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def authenticate(self, session):
        session.params.update({'username': self.username, 'password': self.password})

class BasicPasshash:
    def __init__(self, username, passhash):
        self.username = username
        self.passhash = passhash

    def authenticate(self, session):
        session.params.update({'username': self.username, 'passhash': self.passhash})

class BasicToken:
    def __init__(self, api_token):
        self.api_token = api_token

    def authenticate(self, session):
        session.params.update({'apitoken': self.api_token})