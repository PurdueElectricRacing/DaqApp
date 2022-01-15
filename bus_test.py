from communication.client import TCPBus

bus = TCPBus('169.254.48.90', 8080)

try:
    while True:
        print(bus.recv(2))

except KeyboardInterrupt:
    bus.shutdown()