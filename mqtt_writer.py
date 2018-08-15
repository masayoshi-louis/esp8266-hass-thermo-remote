# Writer interface over umqtt API.


class MQTTWriter:
    __slots__ = ('topic', 'client')

    def __init__(self, name, client, topic):
        self.topic = topic
        self.client = client

    def on_next(self, x):
        data = bytes(str(x), 'utf-8')
        self.client.publish(bytes(self.topic, 'utf-8'), data)

    def on_completed(self):
        pass

    def on_error(self, e):
        print("upstream error: %s" % e)
