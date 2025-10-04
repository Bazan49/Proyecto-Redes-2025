import socket
import queue
from Frame_Manager import FrameManager

class LinkLayer:
    
    def __init__(self, interface, ethertype=0x88B5):
        self.interface = interface
        self.raw_socket = None
        self.ethertype = ethertype
        self.local_mac = self.get_Mac(interface)
        self.CreateSocket()
        self.incoming_queue = queue.Queue()
        
    def CreateSocket(self):
        try:
            self.raw_socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(self.ethertype))
            self.raw_socket.bind((self.interface, 0))
            print(f"Socket creado en interfaz {self.interface}")
        except Exception as e:
            print(f"Error creando socket en {self.interface}: {e}")
            raise
        
    def send_frame(self, frame_list):
        for i, frame in enumerate(frame_list):
            try:
                bytes_sent = self.raw_socket.send(frame)
                print(f"frame enviado: {frame.hex()}")
                print(f"Frame {i+1}/{len(frame_list)} enviado ({bytes_sent} bytes)")
            except Exception as e:
                print(f"Error enviando frame {i+1}: {e}")
                raise

    def receive_frame(self, buff_size=65535):
        try:
            frame, addr = self.raw_socket.recvfrom(buff_size)
            print(f"recibi el frame :{frame.hex()}")
            print(f"Frame recibido de {addr}: {len(frame)} bytes")
            return frame
        except socket.timeout:
            return None
        except Exception as e:
            print(f"Error en receive_frame: {e}")
            return None

    def receive_thread(self, stop_event):
        try:
            # Configurar timeout para verificar stop_event periódicamente
            self.raw_socket.settimeout(1.0)
            
            while not stop_event.is_set():
                frame = self.receive_frame()
                if frame:
                    decoded_frame = FrameManager.decode(frame)
                    if decoded_frame:
                        self.incoming_queue.put(decoded_frame)
        except Exception as e:
            print(f"Error en hilo de recepción: {e}")
        finally:
            self.close()

    def close(self):
        if self.raw_socket:
            try:
                self.raw_socket.close()
            except Exception as e:
                print(f"Error cerrando socket: {e}")
            finally:
                self.raw_socket = None
                print("Socket cerrado")

    def get_Mac(self, interface):
        try:
            with open(f'/sys/class/net/{interface}/address', 'r') as f:
                mac = f.read().strip()
                print(f"mac obtenida: {mac}")
                if not mac or mac == "00:00:00:00:00:00":
                    raise ValueError(f"MAC address inválida para {interface}")
                return mac
        except FileNotFoundError:
            raise ValueError(f"Interfaz {interface} no encontrada")
        except Exception as e:
            raise ValueError(f"Error leyendo MAC de {interface}: {e}")