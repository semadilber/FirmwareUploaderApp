import serial
import time
import threading
from typing import Optional, Callable, List
from .stm32_protocol import STM32Protocol

class UARTCommunication:
    """UART üzerinden STM32 bootloader ile iletişim sağlayan sınıf"""
    
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 1.0):
        """
        UART iletişim nesnesini başlatır
        
        Args:
            port: COM port (örn: 'COM3', '/dev/ttyUSB0')
            baudrate: Baud rate (varsayılan: 115200)
            timeout: Yanıt bekleme süresi (saniye)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn: Optional[serial.Serial] = None
        self.is_connected = False
        self.response_timeout = 10.0  # ACK/NACK bekleme süresi (5 saniyeden 10 saniyeye çıkarıldı)
        
    def connect(self) -> bool:
        """
        UART bağlantısını açar
        
        Returns:
            bool: Bağlantı başarılı ise True
        """
        try:
            # Önce port'u kapatmaya çalış (eğer açıksa)
            try:
                temp_serial = serial.Serial(self.port)
                temp_serial.close()
                time.sleep(0.5)  # Kısa bekleme
            except:
                pass  # Port zaten kapalıysa hata vermez
            
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout
            )
            self.is_connected = True
            print(f"UART bağlantısı başarılı: {self.port} @ {self.baudrate}")
            return True
            
        except serial.SerialException as e:
            print(f"UART bağlantı hatası: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """UART bağlantısını kapatır"""
        if self.serial_conn and self.is_connected:
            self.serial_conn.close()
            self.is_connected = False
            print("UART bağlantısı kapatıldı")
    
    def send_packet_and_wait_ack(self, packet: bytes) -> tuple[bool, str]:
        """
        Paket gönderir ve ACK/NACK yanıtını bekler
        
        Args:
            packet: Gönderilecek paket (21 byte)
            
        Returns:
            tuple: (başarılı_mı, hata_mesajı)
        """
        if not self.is_connected or not self.serial_conn:
            return False, "UART bağlantısı yok"
        
        if len(packet) != STM32Protocol.PACKET_SIZE:
            return False, f"Paket boyutu {STM32Protocol.PACKET_SIZE} byte olmalıdır"
        
        try:
            # Paketi gönder
            print(f"DEBUG: {len(packet)} byte paket gönderiliyor: {packet.hex()}")
            bytes_sent = self.serial_conn.write(packet)
            if bytes_sent != len(packet):
                return False, f"Paket tam gönderilemedi: {bytes_sent}/{len(packet)} byte"
            
            # Paket gönderildikten sonra flush
            self.serial_conn.flush()
            
            # Yanıt bekle
            start_time = time.time()
            print(f"DEBUG: Paket gönderildi, yanıt bekleniyor... (timeout: {self.response_timeout}s)")
            
            # Kısa bir bekleme ekle (STM32'nin işlemesi için)
            time.sleep(0.2)  # Interrupt mode için daha uzun bekleme
            
            while time.time() - start_time < self.response_timeout:
                if self.serial_conn.in_waiting > 0:
                    # Önce 1 byte oku (ACK/NACK)
                    response = self.serial_conn.read(1)
                    if response:
                        first_byte = response[0]
                        time.sleep(0.4)
                        print(f"DEBUG: Yanıt alındı: 0x{first_byte:02X}")
                        
                        if first_byte == 0xAA:  # ACK
                            return True, "ACK alındı"
                        elif first_byte == 0x55:  # NACK
                            # NACK durumunda ek byte'ları da oku (hata kodu)
                            if self.serial_conn.in_waiting > 0:
                                error_code = self.serial_conn.read(1)
                                full_response = response + error_code
                                print(f"DEBUG: NACK + hata kodu: 0x{error_code[0]:02X}")
                            else:
                                full_response = response
                                print("DEBUG: NACK (hata kodu yok)")
                            
                            is_ack, error = STM32Protocol.parse_response(full_response)
                            return False, error
                        else:
                            print(f"DEBUG: Bilinmeyen yanıt kodu: 0x{first_byte:02X}")
                            return False, f"Bilinmeyen yanıt: 0x{first_byte:02X} (Beklenen: ACK=0xAA, NACK=0x55)"
                time.sleep(0.01)  # CPU kullanımını azaltmak için kısa bekleme
            
            print(f"DEBUG: Timeout! {self.response_timeout} saniye içinde yanıt alınamadı")
            return False, "Yanıt timeout"
            
        except serial.SerialException as e:
            return False, f"UART hatası: {str(e)}"
        except Exception as e:
            return False, f"Beklenmeyen hata: {str(e)}"
    
    def clear_buffers(self):
        """Giriş ve çıkış buffer'larını temizler"""
        if self.serial_conn and self.is_connected:
            print("DEBUG: Buffer'lar temizleniyor...")
            self.serial_conn.reset_input_buffer()
            self.serial_conn.reset_output_buffer()
            time.sleep(0.1)  # Buffer temizliği için kısa bekleme
    
    def get_available_ports(self) -> List[str]:
        """Kullanılabilir seri portları listeler"""
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    
    def send_cmd_write_packet(self, sector: int) -> tuple[bool, str]:
        """CMD_WRITE paketi gönderir"""
        try:
            packet = STM32Protocol.create_cmd_write_packet(sector)
            return self.send_packet_and_wait_ack(packet)
        except ValueError as e:
            return False, str(e)
    
    def send_cmd_erase_packet(self, sector: int) -> tuple[bool, str]:
        """CMD_ERASE paketi gönderir"""
        try:
            packet = STM32Protocol.create_cmd_erase_packet(sector)
            return self.send_packet_and_wait_ack(packet)
        except ValueError as e:
            return False, str(e)
    
    def send_data_packet(self, data: bytes) -> tuple[bool, str]:
        """DATA paketi gönderir"""
        try:
            packet = STM32Protocol.create_data_packet(data)
            return self.send_packet_and_wait_ack(packet)
        except ValueError as e:
            return False, str(e)
    
    def send_finish_packet(self) -> tuple[bool, str]:
        """FINISH paketi gönderir"""
        try:
            packet = STM32Protocol.create_finish_packet()
            return self.send_packet_and_wait_ack(packet)
        except ValueError as e:
            return False, str(e)

    # ------------------------------------------------------------------
    # ERASE Akışı
    # ------------------------------------------------------------------
    def erase_sector(self, sector: int, delay_after_cmd: float = 0.5) -> tuple[bool, str]:
        """Belirtilen sektörü siler (CMD_ERASE + gecikme + FINISH)

        Args:
            sector: Silinecek sektör numarası (0-255)
            delay_after_cmd: CMD_ERASE ACK'inden sonra bekleme süresi (saniye)
        Returns:
            (başarılı_mı, mesaj)
        """
        if not self.is_connected:
            return False, "UART bağlantısı yok"

        # Buffer'ları temizle
        self.clear_buffers()

        # CMD_ERASE gönder
        success, message = self.send_cmd_erase_packet(sector)
        if not success:
            return False, f"CMD_ERASE hatası: {message}"

        # Erase işlemi için bekle
        time.sleep(delay_after_cmd)

        # FINISH gönder
        success, message = self.send_finish_packet()
        if not success:
            return False, f"FINISH paketi hatası: {message}"

        return True, f"Sektör {sector} başarıyla silindi"
    
    def send_firmware(self, firmware_data: bytes, sector: int, 
                     progress_callback: Optional[Callable[[int, int], None]] = None) -> tuple[bool, str]:
        """
        Tüm firmware'i gönderir
        
        Args:
            firmware_data: Firmware binary data
            sector: Hedef sektör
            progress_callback: İlerleme callback fonksiyonu (current, total)
            
        Returns:
            tuple: (başarılı_mı, sonuç_mesajı)
        """
        if not self.is_connected:
            return False, "UART bağlantısı yok"
        
        # Buffer'ları temizle
        self.clear_buffers()
        
        # CMD_WRITE paketi gönder (sektörü yazma için hazırla)
        success, message = self.send_cmd_write_packet(sector)
        if not success:
            return False, f"CMD_WRITE paketi hatası: {message}"
        
        # CMD_WRITE ACK'inden sonra gecikme (STM32'nin hazırlanması için)
        time.sleep(1)  # 500 ms bekle

        # DATA paketlerini gönder
        data_size = STM32Protocol.DATA_PAYLOAD_SIZE
        total_packets = (len(firmware_data) + data_size - 1) // data_size
        
        for i in range(total_packets):
            start_idx = i * data_size
            end_idx = min(start_idx + data_size, len(firmware_data))
            chunk = firmware_data[start_idx:end_idx]
            
            success, message = self.send_data_packet(chunk)
            if not success:
                return False, f"DATA paketi {i+1}/{total_packets} hatası: {message}"
            
            if progress_callback:
                progress_callback(i + 1, total_packets)
        
        # FINISH paketi gönder
        success, message = self.send_finish_packet()
        if not success:
            return False, f"FINISH paketi hatası: {message}"
        
        return True, f"Firmware başarıyla gönderildi ({len(firmware_data)} byte, {total_packets} paket)" 