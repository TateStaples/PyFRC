import socket, threading, pickle  #, jpysocket


class Messenger:
    _key = dict()

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.host("localhost", 1235)
        except Exception as e:
            print("Error:", e)

    def host(self, ip, port):
        self.socket.bind((ip, port))
        self.socket.listen(2)  # the number is the overflow amount of sockets to connect
        connecting_socket, address = self.socket.accept()
        self.connected = connecting_socket
        self.running = True
        threading.Thread(target=self.receive).start()

    def connect(self, ip, port):
        self.socket.connect((ip, port))
        self.connected = self.socket

    def receive(self):
        while self.running:
            try:
                raw = self.connected.recv(2048)  # wait to receive data (up to 2048 bytes at a time)
                if len(raw) == 0: continue  # sometimes java sockets do dumb
                msg = pickle.loads(raw)
                id = msg["id"]  # all messages have a id
                if id in self._key:  # if you have added a listener for this message
                    func, include_args = self._key[id]
                    func(msg) if include_args else func()  #  pass the data from the dict
            except Exception as e:
                print("Connection error:", e)
                self.close()

    def send(self, thing, **kwargs):
        print("sending:", thing)
        # assert "\n" not in thing, "You cant send anything with line breaks"
        # assert "\n" not in id, "Your id cant have line breaks"
        # print("Sending: ", (id, thing))
        # self.connected.send(bytes(id + "\n", self.byte_type))
        # self.connected.send(bytes(thing + "\n", self.byte_type))
        print(kwargs)
        raw = pickle.dumps(thing)
        self.connected.send(raw)  # Send Msg

    def on_receive(self, id, func, pass_data=False):
        self._key[id] = func, pass_data

    def close(self):
        self.running = False
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except: pass
        try:
            self.connected.shutdown(socket.SHUT_RDWR)
            self.connected.close()
        except: pass


if __name__ == "__main__":
    m = Messenger()
    message = ""
    while message != "q":
        message = input("")
        m.send({"msg": message})
    m.close()


'''
Protocol:
All messages be a dictionary / HashMap with an entry being "id"

Controller info: 
-id=Controller{n} (ie Controller1) -> input name, new input value
Dashboard:
-id=DashboardCreate -> unit name, [unit type, unit location info]  # todo: check this
-id=DashboardUpdate -> name, value 
Serial:
-id=msg -> "value", string message

'''

