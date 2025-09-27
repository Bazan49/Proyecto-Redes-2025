import socket
import threading
import netifaces

# Para leer la MAC del dispositivo
interfaces = netifaces.interfaces()
print(interfaces)

addrs = netifaces.ifaddresses("enp0s3")
mac = addrs[netifaces.AF_LINK][0]['addr']
print(mac)

# Metodos Base
def MacToBytes(mac):
    return bytes.fromhex(mac.replace(":", ""))

def ReadFrames(interface):
    raw_socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
    raw_socket.bind((interface, 0))

    while(True):
        frame, addr = raw_socket.recvfrom(65535) #valor maximo de bytes permitidos
        print(f"Frame recibido de {addr}: {frame.hex()}")

def SendFrame(interface, frame):
    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
    s.bind((interface,0))
    s.send(frame)
    s.close()

def BuildFrame(DstMAC, SrcMAC, Data):
    return MacToBytes(DstMAC) + MacToBytes(SrcMAC) + Data.encode()