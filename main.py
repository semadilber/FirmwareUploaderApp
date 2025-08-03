#!/usr/bin/env python3
"""
STM32 Bootloader GUI - Ana Uygulama
===================================

STM32 tabanlı bootloader için UART üzerinden firmware gönderim uygulaması.

Protokol özellikleri:
- 20 byte sabit uzunlukta paketler
- CMD, DATA, FINISH mesaj tipleri  
- CRC32 hata kontrolü
- ACK/NACK soft flow control
- 115200 baud rate

Kullanım:
    python main.py

Requirements:
    - Python 3.7+
    - pyserial
    - tkinter (Python ile birlikte gelir)
"""

import sys
import os

# src klasörünü Python path'ine ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.gui import STM32BootloaderGUI

def main():
    """Ana fonksiyon"""
    try:
        print("STM32 Bootloader GUI başlatılıyor...")
        app = STM32BootloaderGUI()
        app.run()
    except KeyboardInterrupt:
        print("\nUygulama kullanıcı tarafından sonlandırıldı.")
    except Exception as e:
        print(f"Hata: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 