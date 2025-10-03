import socket
import queue
from Frame_Manager import FrameManager

# Clase encargada de la comunicacion a nivel capa de enlace
class LinkLayer:
    def __init__(self, interface, ethertype=0x88B5):
        self.interface = interface
        self.raw_socket = None
        self.ethertype = ethertype
        self.local_mac = self.get_Mac()
        self.CreateSocket()

        # Cola de mensajes recibidos
        self.incoming_queue = queue.Queue()
        
    def CreateSocket(self):
        self.raw_socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(self.ethertype))
        self.raw_socket.bind((self.interface, 0))

    def send_frame(self, frame_list):
        for frame in frame_list:
            self.raw_socket.send(frame)
        print(f"Frame enviado: {frame.hex()}")

    def receive_frame(self, buff_size=65535):
        frame, addr = self.raw_socket.recvfrom(buff_size)
        print(f"Frame recibido de {addr}: {frame.hex()}")
        return frame

    # Metodo para la recepcion continua de mensajes
    def receive_thread(self, stop_event):
        try:
            while not stop_event.is_set():
                frame = self.receive_frame()
                decoded_frame = FrameManager.decode(frame)
                if decoded_frame:
                    self.incoming_queue.put(decoded_frame)
        except Exception as e:
            print(f"Error en hilo de recepción: {e}")
        finally:
            self.close()

    def close(self):
        if self.raw_socket:
            self.raw_socket.close()
            self.raw_socket = None
            print("Socket cerrado")

    # Metodo para leer la MAC del dispositivo
    def get_Mac(self, interface):
        try:
            with open(f'/sys/class/net/{interface}/address', 'r') as f:
                mac = f.read().strip()
                return mac
        except FileNotFoundError:
            return None 