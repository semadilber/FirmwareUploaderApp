#!/usr/bin/env python3
"""
STM32 Protokol Test Dosyası
===========================

STM32Protocol sınıfının temel fonksiyonlarını test eder.
"""

import sys
import os

# src klasörünü Python path'ine ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from stm32_protocol import STM32Protocol, MessageType

def test_cmd_packets():
    """CMD paketi oluşturma testleri"""
    print("🟩 CMD Paketi Testleri:")
    
    # CMD_WRITE testi
    packet = STM32Protocol.create_cmd_write_packet(5)
    print(f"  CMD_WRITE Sektör 5 paketi: {len(packet)} byte - {packet.hex()}")
    assert len(packet) == 21, "Paket boyutu 21 byte olmalı"
    assert packet[0] == MessageType.CMD_WRITE, "İlk byte CMD_WRITE tipi olmalı"
    assert packet[1] == 5, "İkinci byte sektör numarası olmalı"
    assert packet[2:17] == b'\x00' * 15, "Padding sıfır olmalı"
    
    print("  ✅ CMD paket testleri başarılı\n")

def test_data_packet():
    """DATA paketi oluşturma testleri"""
    print("🟦 DATA Paketi Testleri:")
    
    # 15 byte veri testi
    test_data = b"Hello STM32!!!!!"  # 16 byte
    packet = STM32Protocol.create_data_packet(test_data)
    print(f"  15 byte veri paketi: {len(packet)} byte - {packet.hex()}")
    assert len(packet) == 21, "Paket boyutu 21 byte olmalı"
    assert packet[0] == MessageType.DATA, "İlk byte DATA tipi olmalı"
    assert packet[1:17] == test_data, "Veri kısmı doğru olmalı"
    
    # Kısa veri testi (padding)
    short_data = b"Test"  # 4 byte
    packet = STM32Protocol.create_data_packet(short_data)
    print(f"  4 byte veri paketi: {len(packet)} byte - {packet.hex()}")
    assert packet[1:5] == short_data, "Veri kısmı doğru olmalı"
    assert packet[5:17] == b'\x00' * 12, "Padding doğru olmalı"
    
    print("  ✅ DATA paket testleri başarılı\n")

def test_finish_packet():
    """FINISH paketi oluşturma testleri"""
    print("🟥 FINISH Paketi Testleri:")
    
    packet = STM32Protocol.create_finish_packet()
    print(f"  FINISH paketi: {len(packet)} byte - {packet.hex()}")
    assert len(packet) == 21, "Paket boyutu 21 byte olmalı"
    assert packet[0] == MessageType.FINISH, "İlk byte FINISH tipi olmalı"
    assert packet[1:17] == b'\x00' * 16, "Padding sıfır olmalı"
    
    print("  ✅ FINISH paket testleri başarılı\n")

def test_crc32_calculation():
    """CRC32 hesaplama testleri"""
    print("🔧 CRC32 Hesaplama Testleri:")
    
    # Bilinen veri için CRC32 testi
    test_data = b"Hello"
    crc = STM32Protocol.calculate_crc32(test_data)
    print(f"  'Hello' CRC32: 0x{crc:08X}")
    assert isinstance(crc, int), "CRC32 integer olmalı"
    assert 0 <= crc <= 0xFFFFFFFF, "CRC32 32-bit range'de olmalı"
    
    # Aynı veri için aynı CRC32
    crc2 = STM32Protocol.calculate_crc32(test_data)
    assert crc == crc2, "Aynı veri için aynı CRC32 üretilmeli"
    
    print("  ✅ CRC32 testleri başarılı\n")

def test_packet_verification():
    """Paket boyut kontrolü testleri"""
    print("📏 Paket Boyut Kontrol Testleri:")
    
    # Doğru boyut
    valid_packet = b'\x00' * 21
    assert STM32Protocol.verify_packet_size(valid_packet), "21 byte paket geçerli olmalı"
    
    # Yanlış boyut
    invalid_packet = b'\x00' * 19
    assert not STM32Protocol.verify_packet_size(invalid_packet), "19 byte paket geçersiz olmalı"
    
    print("  ✅ Paket boyut testleri başarılı\n")

def test_nack_error_parsing():
    """NACK hata kodu parse etme testleri"""
    print("🚨 NACK Hata Kodu Testleri:")
    
    # Test cases
    test_cases = [
        (b'\x55\x01', "Bilinmeyen mesaj tipi"),
        (b'\x55\x02', "CRC kontrolü başarısız"),
        (b'\x55\x03', "Mesaj kuyruğu dolu"),
        (b'\x55\x04', "Komut verisi geçersiz (sektör out-of-range)"),
        (b'\x55\x05', "Mesaj sıralaması hatalı (CMD gelmeden DATA)"),
        (b'\x55\xFF', "Bilinmeyen hata kodu: 0xFF"),
    ]
    
    for response, expected_error in test_cases:
        is_ack, error = STM32Protocol.parse_response(response)
        assert not is_ack, "NACK durumunda is_ack False olmalı"
        assert expected_error in error, f"Beklenen hata: {expected_error}, Alınan: {error}"
        print(f"  {response.hex()}: {error}")
    
    print("  ✅ NACK hata kodu testleri başarılı\n")

def main():
    """Ana test fonksiyonu"""
    print("STM32 Protokol Testleri Başlatılıyor...\n")
    
    try:
        test_crc32_calculation()
        test_cmd_packets()
        test_data_packet()
        test_finish_packet()
        test_packet_verification()
        test_nack_error_parsing()
        
        print("🎉 Tüm testler başarıyla tamamlandı!")
        
    except AssertionError as e:
        print(f"❌ Test hatası: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 