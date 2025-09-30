import socket
import threading
import struct
import sys

# Para leer la MAC del dispositivo
def Obtener_Mac(interface):
    try:
        with open(f'/sys/class/net/{interface}/address', 'r') as f:
            mac = f.read().strip()
            return mac
    except FileNotFoundError:
        return None 

# Trabajo con frame
def MacToBytes(mac):
    return bytes.fromhex(mac.replace(":", ""))

def CreateFrame(mac_dst, mac_src, msg_type, message):
    # Mensaje a bytes:
    if isinstance(message, str):
        message_bytes = message.encode('utf-8')
    else:
        message_bytes = message
    # Longitud
    length = len(message_bytes).to_bytes(2, 'big')
    
    # ETHERTYPE CRUCIAL - Usamos 0x88B5 (protocolo personalizado)
    eth_type = b"\x88\xb5"  # 2 bytes
    # Frame
    print(f"🔧 Frame creado")
    print(f"   EtherType: 0x{eth_type.hex()}")
    return MacToBytes(mac_dst) + MacToBytes(mac_src) + eth_type +  msg_type.to_bytes(1, 'big') + length + message_bytes 

def DecodeFrame(frame):
    return

# Metodos Base De Comunicacion
def CreateSocket(interface):
    raw_socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW,socket.htons(0x88B5))
    raw_socket.bind((interface, 0))
    print(f"socket creado con interface {interface}")
    return raw_socket

def ReciveFrame(raw_socket, buff_size = 1518):
    frame, addr = raw_socket.recvfrom(buff_size) 
    print(f"Frame recibido de {addr}: {frame.hex()}")
    return frame

def SendFrame(raw_socket, interface, frame):
    raw_socket.send(frame)
    print(f"Frame enviado : {frame.hex()}")
    
    
# Trabajo con los hilos de ejecucion
def receive_thread(raw_socket, stop_event):
    try:
        while True:
            ReciveFrame(raw_socket)
            print(f"intento recibir")
    except Exception as e:
        print(f"Error en hilo de recepción: {e}")
    finally:
        print("Cerrando socket desde hilo de recepción")
        raw_socket.close()

def send_thread(raw_socket, interface, mac_dst, mac_src, stop_event):
    try:
        while not stop_event.is_set():
            message = input("Mensaje a enviar ('salir' para terminar): ")
            if message.lower() == "salir":
                stop_event.set()
                break
            frame = CreateFrame(mac_dst, mac_src, 1, message)
            
            SendFrame(raw_socket, interface, frame)
    except Exception as e:
        print(f"Error en hilo de envío: {e}")
    finally:
        print("Cerrando socket desde hilo de envío")
        raw_socket.close()

if __name__ == "__main__":
    interface = "enp0s3"
    raw_socket = CreateSocket(interface)
    mac_src = Obtener_Mac(interface)
    mac_dst = "ff:ff:ff:ff:ff:ff"  # Cambiar por la MAC destino real

    stop_event = threading.Event()

    t1 = threading.Thread(target=receive_thread, args=(raw_socket, stop_event))
    t2 = threading.Thread(target=send_thread, args=(raw_socket, interface, mac_dst, mac_src, stop_event))
    t1.start()
    t2.start()
    t2.join()
    stop_event.set()
    t1.join()
