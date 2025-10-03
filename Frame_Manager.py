import socket
import threading
import struct
import sys
import binascii
import time
from typing import Dict, List, Optional, Union
from MessageType import MessageType
from enum import Enum
from Frame_Class import Frame

MTU = 1500
MAX_PAYLOAD_SIZE = MTU - 25

class FrameManager:
    def __init__(self):
        #self.reassembly_buffers: Dict[int, Dict[int, bytes]] = {}
        pass
    
    def create_frames(self, 
                        mac_dst: str,
                        mac_src: str, 
                        msg_type: int,
                        message: Union[bytes, str],
                        filename: str = None,
                        max_payload_size: int = MAX_PAYLOAD_SIZE) -> List[Frame]:
        """Fragmenta un mensaje en múltiples frames"""
        
        if filename is not None:  ##verificar que sea de tipo archivo ademas
            nombre_bytes = filename.encode('utf-8')
            largo_nombre = len(nombre_bytes)
            # La secuencia completa: largo (2 bytes) + nombre + mensaje (bytes) 
            message_bytes = (largo_nombre.to_bytes(2, 'big') + nombre_bytes + message_bytes)
        else:
                if isinstance(message, str):
                    message_bytes = message.encode('utf-8')
                else:
                    message_bytes = message

        total_length = len(message_bytes)
        fragment_id = int(time.time() * 1000) % 65536
        offset = 0
        fragment_num = 0
        frames = []

        # Si no necesita fragmentación
        if total_length <= max_payload_size:
            frame = Frame(
                dst_mac=mac_dst,
                src_mac=mac_src,
                msg_type=msg_type,
                fragment_id=fragment_id,
                fragment_num=0,
                more_fragments=0,
                payload=message_bytes
            )
            frames.append(frame.to_bytes)
            return frames

        # Fragmentar el mensaje
        while offset < total_length:
            chunk = message_bytes[offset:offset + max_payload_size]
            offset += max_payload_size
            more_fragments = 1 if offset < total_length else 0

            frame = Frame(
                dst_mac=mac_dst,
                src_mac=mac_src,
                msg_type=msg_type,
                fragment_id=fragment_id,
                fragment_num=fragment_num,
                more_fragments=more_fragments,
                payload=chunk
            )
            frames.append(frame.to_bytes)
            fragment_num += 1

        return frames
    
    def decode(self, frame_data: bytes):# -> Optional[str]:
        
        try:
            frame = Frame.from_bytes(frame_data)
        except ValueError as e:
            print(f"Error parsing frame: {e}")
            return None
        
        # Verificar CRC
        if not frame.verify_crc(frame_data):
            print("Error: CRC no coincide, descartando frame")  
            return None

        print(f"📦 Frame recibido: {frame}")

        # Decodificar el payload si es necesario
        if frame.msg_type == MessageType.TEXT:    
            try:
                frame.payload = frame.payload.decode('utf-8')
            except Exception:
                print(f"hubo un error")
            return frame 
        elif frame.msg_type == MessageType.FILE:
            largo_nombre = int.from_bytes(frame.payload[0:2], 'big')
            nombre = frame.payload[2:2+largo_nombre].decode('utf-8')
            datos_archivo = frame.payload[2+largo_nombre:]
            return nombre  #VERIFICAR BIEN COMO ENVIAR ESTO
            
        
    
        #POR AHORA NO
        
        # Guardar fragmento en buffer de reensamblaje
        # if frame.fragment_id not in self.reassembly_buffers:
        #     self.reassembly_buffers[frame.fragment_id] = {}

        # self.reassembly_buffers[frame.fragment_id][frame.fragment_num] = frame.payload

        # # Si es el último fragmento, intentar reensamblar
        # if frame.more_fragments == 0:
        #     return self._reassemble_message(frame.fragment_id)
        
        # return None
    
    # def _reassemble_message(self, fragment_id: int) -> Optional[str]:
    #     """Reensambla mensaje desde los fragmentos"""
    #     if fragment_id not in self.reassembly_buffers:
    #         return None
            
    #     all_fragments = self.reassembly_buffers[fragment_id]
        
    #     # Verificar que tenemos todos los fragmentos consecutivos
    #     max_fragment = max(all_fragments.keys())
    #     for i in range(max_fragment + 1):
    #         if i not in all_fragments:
    #             print(f"⚠️  Fragmento {i} faltante para ID {fragment_id}")
    #             return None
        
    #     # Reensamblar en orden
    #     # message_bytes = b''.join(all_fragments[i] for i in sorted(all_fragments))
        
    #     #provisional
    #     try:
    #         message = message_bytes.decode('utf-8')
    #     except UnicodeDecodeError:
    #         message = f"<Datos binarios: {len(message_bytes)} bytes>"
        
    #    print(f"✅ Mensaje Reensamblado Completo (Fragment ID {fragment_id}): {message}")

    #     # Limpiar buffer
    #     del self.reassembly_buffers[fragment_id]
        
    #     return message
    