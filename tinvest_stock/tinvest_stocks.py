import os, socket, time, struct, json



API = "https://invest-public-api.tbank.ru/rest/tinkoff.public.invest.api.contract.v1"

RCON_HOST, RCON_PORT = "127.0.0.1", 25575

RCON_PASSWORD = os.environ.get("RCONS_PASSWORD")

TOKEN = os.environ.get("TINVEST_TOKEN")

def packet(req,type,payload):
    byte = payload.encode("utf-8")
    lenght = 4 + 4 + len(byte) + 2
    header = struct.pack("<iii", lenght, req, type)
    packet = header +  byte + b"\x00\x00"
    return packet
def command(cmd):
    with socket.create_connection((RCON_HOST,RCON_PORT), timeout = 5) as s:

        auth = packet(1, 3, RCON_PASSWORD)
        s.sendall(auth)
        response_auth = s.recv(4096)
        print(response_auth)

        s.sendall(packet(0,2,cmd))
        response_cmd = s.recv(4096)
        print(response_cmd)
 
def main():
    print("wait")

if __name__ == "__main__":
    main()