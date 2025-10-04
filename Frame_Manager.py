
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
        #self.reassembly_buffers: Dict[tuple, Dict[int, bytes]] = {}
        pass
    
    @staticmethod
    def create_frames(
                        mac_dst: str,
                        mac_src: str, 
                        msg_type: int,
                        message: Union[bytes, str],
                        filename: str = None,
                        max_payload_size: int = MAX_PAYLOAD_SIZE) -> List[bytes]:
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
            frames.append(frame.to_bytes())
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
            frames.append(frame.to_bytes())
            fragment_num += 1

        return frames
    
    @staticmethod
    def decode(frame_data: bytes):# -> Optional[str]:
        
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

        # Si no está fragmentado, devolver directamente
        if frame.more_fragments == 0 and frame.fragment_num == 0:
            return FrameManager._process_complete_frame(frame)
        
        # # Guardar en el buffer y verificar si está completo en caso de ser fragmentado
        # buffer_key = (frame.src_mac, frame.fragment_id)
        
        # if buffer_key not in self.reassembly_buffers:
        #     self.reassembly_buffers[buffer_key] = {}

        # self.reassembly_buffers[buffer_key][frame.fragment_num] = frame

        # # Si es el último fragmento, intentar reensamblar
        # if frame.more_fragments == 0:
        #     return self._reassemble_message(buffer_key, frame)
        
        return None
               
    def _process_complete_frame(frame: Frame) -> Frame:
        """Procesa un frame que ya está completo (no fragmentado)"""
        if frame.msg_type == MessageType.TEXT:    
            try:
                frame.payload = frame.payload.decode('utf-8')
            except Exception:
                print("Error decodificando payload de texto")
        elif frame.msg_type == MessageType.FILE:
            try:
                largo_nombre = int.from_bytes(frame.payload[0:2], 'big')
                nombre = frame.payload[2:2+largo_nombre].decode('utf-8')
                datos_archivo = frame.payload[2+largo_nombre:]
                # Devolvemos el frame con la información procesada
                frame.filename = nombre
                frame.payload = datos_archivo
            except Exception as e:
                print(f"Error procesando archivo: {e}")
        
        return frame
    
    # def _reassemble_message(self,  buffer_key: tuple, last_frame: Frame) -> Optional[Frame]:
    #     """Reensambla mensaje desde los fragmentos"""
    #     if buffer_key not in self.reassembly_buffers:
    #        return None
            
    #     all_fragments = self.reassembly_buffers[fragment_id]
        
    #     # Verificar que tenemos todos los fragmentos consecutivos
    #     max_fragment = max(all_fragments.keys())
    #     for i in range(max_fragment + 1):
    #         if i not in all_fragments:
    #             print(f"⚠️  Fragmento {i} faltante para ID {fragment_id}")
    #             return None
        
    #     # Reensamblar en orden
    #     # message_bytes = b''.join(all_fragments[i] for i in sorted(all_fragments))
        
    #     # Crear frame reensamblado
        # reassembled_frame = Frame(
        #     dst_mac = last_frame.dst_mac,
        #     src_mac = last_frame.src_mac,
        #     msg_type = last_frame.msg_type,
        #     fragment_id = last_frame.fragment_id,
        #     fragment_num = 0,  
        #     more_fragments = 0,
        #     payload = message_bytes
        # )
        
    #     processed_frame = self._process_complete_frame(reassembled_frame)
    #    print(f"✅ Mensaje Reensamblado Completo (Fragment ID {fragment_id}): {message}")

    #     # Limpiar buffer
    #     del self.reassembly_buffers[fragment_id]
        
    #     return processed_frame
    