import socket
import struct
import time


class MQTTException(Exception):
    pass


class MQTTClient:
    def __init__(self, client_id, server, port=1883, keepalive=60):
        self.client_id = client_id
        self.server = server
        self.port = port
        self.keepalive = keepalive
        self.sock = None
        self.cb = None

    def set_callback(self, cb):
        self.cb = cb

    def connect(self):
        addr = socket.getaddrinfo(self.server, self.port)[0][-1]
        self.sock = socket.socket()
        self.sock.connect(addr)

        packet = bytearray()
        packet.extend(b"\x10")

        payload = bytearray()
        payload.extend(b"\x00\x04MQTT")
        payload.append(4)
        payload.append(2)
        payload.extend(struct.pack("!H", self.keepalive))
        payload.extend(struct.pack("!H", len(self.client_id)))
        payload.extend(self.client_id)

        packet.extend(struct.pack("!B", len(payload)))
        packet.extend(payload)

        self.sock.send(packet)

    def publish(self, topic, msg):
        pkt = bytearray()
        pkt.extend(b"\x30")

        data = bytearray()
        data.extend(struct.pack("!H", len(topic)))
        data.extend(topic)
        data.extend(msg)

        pkt.append(len(data))
        pkt.extend(data)

        self.sock.send(pkt)

    def subscribe(self, topic):
        pkt = bytearray()
        pkt.extend(b"\x82")

        data = bytearray()
        data.extend(b"\x00\x01")
        data.extend(struct.pack("!H", len(topic)))
        data.extend(topic)

        pkt.append(len(data))
        pkt.extend(data)

        self.sock.send(pkt)

    def check_msg(self):
        if not self.sock:
            return

        self.sock.setblocking(False)
        try:
            data = self.sock.recv(64)
        except:
            return

        if self.cb and data:
            try:
                topic_len = struct.unpack("!H", data[2:4])[0]
                topic = data[4:4+topic_len]
                msg = data[4+topic_len:]
                self.cb(topic, msg)
            except:
                pass

    def disconnect(self):
        if self.sock:
            self.sock.close()
            self.sock = None