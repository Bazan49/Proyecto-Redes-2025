import socket
import threading
import struct
import sys
import binascii
import time
from typing import Dict, List, Optional, Union
from MessageType import MessageType
from enum import Enum

# Offsets de los campos en el frame
# 'dst_mac': 0,      # 6 bytes
# 'src_mac': 6,      # 6 bytes  
# 'ethertype': 12,   # 2 bytes
# 'msg_type': 14,    # 1 byte
# 'fragment_id': 15, # 2 bytes
# 'fragment_num': 17, # 1 byte
# 'more_fragments': 18, # 1 byte
# 'length': 19,      # 2 bytes
# 'payload': 21,     # variable
# CRC está al final, se calcula dinámicamente
       
MTU = 1500
MAX_PAYLOAD_SIZE = MTU - 25

class Frame:
    ETHER_TYPE = b"\x88\xb5"  # EtherType personalizado
    
    def __init__(self, 
                 dst_mac: str = "",
                 src_mac: str = "",
                 msg_type: int = 0,
                 fragment_id: int = 0,
                 fragment_num: int = 0,
                 more_fragments: int = 0,
                 payload: Union[bytes, str] = b""):
        
        self.dst_mac = dst_mac
        self.src_mac = src_mac
        self.msg_type = MessageType.from_value(msg_type)
        self.fragment_id = fragment_id
        self.fragment_num = fragment_num
        self.more_fragments = more_fragments
        self.payload = payload if isinstance(payload, bytes) else payload.encode('utf-8')
        self.length = len(self.payload)
        
    @classmethod
    def from_bytes(cls, frame_data: bytes) -> 'Frame':
        """Crea un Frame a partir de datos bytes recibidos"""
        if len(frame_data) < 25:
            raise ValueError("Frame demasiado corto")
            
        frame = cls()
        
        # Extraer campos del frame
        frame.dst_mac = cls.bytes_to_mac(frame_data[0:6])
        frame.src_mac = cls.bytes_to_mac(frame_data[6:12])
        
        # Verificar EtherType
        ethertype = frame_data[12:14]
        if ethertype != cls.ETHER_TYPE:
            raise ValueError(f"EtherType incorrecto: {ethertype.hex()}")
            
        frame.msg_type = MessageType.from_value(frame_data[14])
        frame.fragment_id = int.from_bytes(frame_data[15:17], 'big')
        frame.fragment_num = frame_data[17]
        frame.more_fragments = frame_data[18]
        frame.length = int.from_bytes(frame_data[19:21], 'big')
        
        # Extraer payload (sin incluir CRC)
        payload_end = 21 + frame.length
        if payload_end > len(frame_data) - 4:
            raise ValueError("Longitud del payload inconsistente")
            
        frame.payload = frame_data[21:payload_end]
        
        return frame
    
    @staticmethod
    def parse_frame_headers(frame):
        if len(frame) < 25:  # validar tamaño mínimo
            raise ValueError("Frame muy corto para los encabezados requeridos")

        mac_dst = frame[0:6].hex()
        mac_src = frame[6:12].hex()
        ethertype = frame[12:14]
        msg_type = frame[14]
        fragment_id = int.from_bytes(frame[15:17], 'big')
        fragment_num = frame[17]
        more_fragments = frame[18]
        length = int.from_bytes(frame[19:21], 'big')
        payload = frame[21:21+length]

        return {
            "mac_dst": mac_dst,
            "mac_src": mac_src,
            "ethertype": ethertype,
            "msg_type": msg_type,
            "fragment_id": fragment_id,
            "fragment_num": fragment_num,
            "more_fragments": more_fragments,
            "length": length,
            "payload": payload,
        }

    def to_bytes(self) -> bytes:
        """Convierte el Frame a bytes listo para enviar"""
        if isinstance(self.payload, str):
            payload_bytes = self.payload.encode('utf-8')
        else:
            payload_bytes = self.payload
            
        length_bytes = len(payload_bytes).to_bytes(2, 'big')
        msg_type_byte = self.msg_type.value if isinstance(self.msg_type, Enum) else int(self.msg_type)
        frame_no_crc = (
            self.mac_to_bytes(self.dst_mac) +
            self.mac_to_bytes(self.src_mac) +
            self.ETHER_TYPE +
            self.msg_type_byte.to_bytes(1, 'big') + #.to_bytes(1, 'big') +
            self.fragment_id.to_bytes(2, 'big') +
            self.fragment_num.to_bytes(1, 'big') +
            self.more_fragments.to_bytes(1, 'big') +
            length_bytes +
            payload_bytes
        )
        
        crc = self.crc32_bytes(frame_no_crc)
        frame = frame_no_crc + crc
        
        print(f"🔧 Frame creado: ID={self.fragment_id}, Num={self.fragment_num}, "
              f"More={self.more_fragments}, Len={len(payload_bytes)}, CRC={crc.hex()}")
        
        return frame
    
    @staticmethod
    def mac_to_bytes(mac: str) -> bytes:
        """Convierte dirección MAC string a bytes"""
        return bytes.fromhex(mac.replace(":", ""))
    
    @staticmethod  
    def bytes_to_mac(mac_bytes: bytes) -> str:
        """Convierte bytes de MAC a string formateado"""
        return ':'.join(f'{b:02x}' for b in mac_bytes)
    
    @staticmethod
    def crc32_bytes(data: bytes) -> bytes:
        """Calcula CRC32 de los datos"""
        crc = binascii.crc32(data) & 0xffffffff
        return crc.to_bytes(4, 'big')
    
    def verify_crc(self, frame_data: bytes) -> bool:
        """Verifica el CRC del frame"""
        if len(frame_data) < 25:
            return False
            
        frame_without_crc = frame_data[:-4]
        crc_received = frame_data[-4:]
        crc_calculated = self.crc32_bytes(frame_without_crc)
        
        return crc_received == crc_calculated
    
    def __str__(self) -> str:
        return (f"Frame(DST={self.dst_mac}, SRC={self.src_mac}, "
                f"Type={self.msg_type}, FragID={self.fragment_id}, "
                f"FragNum={self.fragment_num}, MoreFrags={self.more_fragments}, "
                f"Len={self.length})")


   
    