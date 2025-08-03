import struct
import zlib
from typing import Tuple, Optional
from enum import IntEnum
import time

class MessageType(IntEnum):
    """Mesaj tiplerini tanımlayan enum"""
    CMD_WRITE = 0x01
    CMD_ERASE = 0x02
    DATA = 0x03
    FINISH = 0x04

class STM32Protocol:
    """STM32 bootloader protokol işlemleri için ana sınıf"""
    
    PACKET_SIZE = 21
    DATA_PAYLOAD_SIZE = 16  # DATA paketinde maksimum 16 byte veri
    
    @staticmethod
    def calculate_crc32(data: bytes) -> int:
        """STM32 bootloader ile uyumlu CRC32 (Polynomial 0xEDB88320, init 0xFFFFFFFF, final XOR)"""
        # STM32 tarafındaki algoritma:
        # uint32_t crc = 0xFFFFFFFF;
        # for (size_t i = 0; i < length; i++) {
        #     crc ^= data[i];
        #     for (int j = 0; j < 8; j++)
        #         crc = (crc >> 1) ^ (0xEDB88320U & -(crc & 1));
        # }
        # return ~crc;
        
        crc = 0xFFFFFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                # STM32'deki -(crc & 1) ifadesi: eğer crc & 1 ise 0xFFFFFFFF, değilse 0
                if crc & 1:
                    crc = (crc >> 1) ^ 0xEDB88320
                else:
                    crc = crc >> 1
        return ~crc & 0xFFFFFFFF
    
    @staticmethod
    def create_cmd_write_packet(sector: int) -> bytes:
        """
        CMD_WRITE paketi oluşturur
        Format: 0x01 + sector(1) + padding(15) + CRC32(4)
        CRC32: İlk 17 byte üzerinden hesaplanır
        """
        if sector < 0 or sector > 255:
            raise ValueError("Sektör numarası 0-255 arasında olmalıdır")
        
        # 21 byte'lık paket oluştur (CRC için 0 ile doldur)
        packet = bytearray(STM32Protocol.PACKET_SIZE)
        packet[0] = MessageType.CMD_WRITE  # 0x01
        packet[1] = sector  # sector
        # packet[2:17] zaten 0 (padding)
        
        # CRC32 hesapla (ilk 17 byte üzerinden)
        crc_offset = STM32Protocol.PACKET_SIZE - 4
        crc32 = STM32Protocol.calculate_crc32(packet[:crc_offset])
        
        # CRC32'yi son 4 byte'a yerleştir
        packet[crc_offset:] = struct.pack('<I', crc32)
        
        return bytes(packet)
    
    @staticmethod
    def create_cmd_erase_packet(sector: int) -> bytes:
        """
        CMD_ERASE paketi oluşturur
        Format: 0x02 + sector(1) + padding(15) + CRC32(4)
        CRC32: İlk 17 byte üzerinden hesaplanır
        """
        if sector < 0 or sector > 255:
            raise ValueError("Sektör numarası 0-255 arasında olmalıdır")
        
        # 21 byte'lık paket oluştur (CRC için 0 ile doldur)
        packet = bytearray(STM32Protocol.PACKET_SIZE)
        packet[0] = MessageType.CMD_ERASE  # 0x02
        packet[1] = sector  # sector
        # packet[2:17] zaten 0 (padding)
        
        # CRC32 hesapla (ilk 17 byte üzerinden)
        crc_offset = STM32Protocol.PACKET_SIZE - 4
        crc32 = STM32Protocol.calculate_crc32(packet[:crc_offset])
        
        # CRC32'yi son 4 byte'a yerleştir
        packet[crc_offset:] = struct.pack('<I', crc32)
        
        return bytes(packet)
    
    @staticmethod
    def create_data_packet(data: bytes) -> bytes:
        """
        DATA paketi oluşturur
        Format: 0x03 + data(16) + CRC32(4)
        CRC32: İlk 17 byte üzerinden hesaplanır
        """
        if len(data) > 16:
            raise ValueError("Data boyutu 16 byte'tan büyük olamaz")
        
        # 21 byte'lık paket oluştur
        packet = bytearray(STM32Protocol.PACKET_SIZE)
        packet[0] = MessageType.DATA  # 0x03
        packet[1:1+len(data)] = data  # data
        # packet[1+len(data):17] zaten 0 (padding)
        
        # CRC32 hesapla (ilk 17 byte üzerinden)
        crc_offset = STM32Protocol.PACKET_SIZE - 4
        crc32 = STM32Protocol.calculate_crc32(packet[:crc_offset])
        
        # CRC32'yi son 4 byte'a yerleştir
        packet[crc_offset:] = struct.pack('<I', crc32)
        
        return bytes(packet)
    
    @staticmethod
    def create_finish_packet() -> bytes:
        """
        FINISH paketi oluşturur
        Format: 0x04 + padding(16) + CRC32(4)
        CRC32: İlk 17 byte üzerinden hesaplanır
        """
        # 21 byte'lık paket oluştur
        packet = bytearray(STM32Protocol.PACKET_SIZE)
        packet[0] = MessageType.FINISH  # 0x04
        # packet[1:17] zaten 0 (padding)
        
        # CRC32 hesapla (ilk 17 byte üzerinden)
        crc_offset = STM32Protocol.PACKET_SIZE - 4
        crc32 = STM32Protocol.calculate_crc32(packet[:crc_offset])
        
        # CRC32'yi son 4 byte'a yerleştir
        packet[crc_offset:] = struct.pack('<I', crc32)
        
        return bytes(packet)
    
    @staticmethod
    def verify_packet_size(packet: bytes) -> bool:
        """Paket boyutunun doğru olduğunu kontrol eder"""
        return len(packet) == STM32Protocol.PACKET_SIZE
    
    @staticmethod
    def parse_response(response: bytes) -> Tuple[bool, Optional[str]]:
        """
        Bootloader'dan gelen yanıtı parse eder
        Returns: (is_ack, error_message)
        """
        if not response:
            return False, "Yanıt alınamadı"
        
        first_byte = response[0]
        if first_byte == 0xAA:      # ACK
            time.sleep(0.2)       # 2 ms STM32'nin RX'i yeniden açması için
            return True, "ACK alındı"
        elif first_byte == 0x55:  # NACK
            # NACK durumunda hata kodu kontrol et
            if len(response) >= 2:
                error_code = response[1]
                error_message = STM32Protocol.get_nack_error_message(error_code)
                return False, f"NACK: {error_message} (Kod: 0x{error_code:02X})"
            else:
                return False, "NACK alındı (Hata kodu yok)"
        else:
            return False, f"Bilinmeyen yanıt: 0x{first_byte:02X}"
    
    @staticmethod
    def get_nack_error_message(error_code: int) -> str:
        """
        NACK hata koduna göre açıklama döner
        """
        error_messages = {
            0x01: "Bilinmeyen mesaj tipi",
            0x02: "CRC kontrolü başarısız", 
            0x03: "Mesaj kuyruğu dolu",
            0x04: "Komut verisi geçersiz (sektör out-of-range)",
            0x05: "Mesaj sıralaması hatalı (CMD gelmeden DATA)"
        }
        
        return error_messages.get(error_code, f"Bilinmeyen hata kodu: 0x{error_code:02X}") 