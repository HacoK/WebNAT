class ConnectionDAO(object):
    def __init__(self):
        self.counter = 0
        self.conections = {}

    def get(self, connection_id):
        return self.conections[connection_id]

    def add(self, telnet_client):
        self.counter += 1
        self.conections[self.counter] = telnet_client
        return self.counter

    def update(self, connection_id, telnet_client):
        self.conections[connection_id] = telnet_client

    def delete(self, connection_id):
        self.conections[connection_id].logout()
        del self.conections[connection_id]