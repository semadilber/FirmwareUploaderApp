import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
from typing import Optional
from .uart_comm import UARTCommunication

class STM32BootloaderGUI:
    """STM32 Bootloader GUI ana sınıfı"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("STM32 Bootloader GUI")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        self.root.minsize(800, 600)
        
        # Windows DPI scaling düzeltmesi
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
        
        # UART iletişim nesnesi
        self.uart_comm: Optional[UARTCommunication] = None
        self.firmware_data: Optional[bytes] = None
        self.firmware_path: str = ""
        
        # GUI bileşenlerini oluştur
        self.create_widgets()
        self.refresh_ports()
        
        # Uygulama kapatılırken temizlik yap
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """GUI bileşenlerini oluşturur"""
        
        # Modern stil konfigürasyonu
        style = ttk.Style()
        style.theme_use('clam')
        
        # Modern renk paleti
        bg_primary = "#2c3e50"      # Koyu mavi-gri
        bg_secondary = "#34495e"    # Orta mavi-gri  
        bg_surface = "#ecf0f1"      # Açık gri
        accent_blue = "#3498db"     # Mavi
        accent_green = "#27ae60"    # Yeşil
        accent_red = "#e74c3c"      # Kırmızı
        accent_orange = "#f39c12"   # Turuncu
        text_primary = "#2c3e50"    # Koyu metin
        text_secondary = "#7f8c8d"  # Açık metin
        
        # Ana pencere stilini ayarla
        self.root.configure(bg=bg_surface)
        
        # Modern stil yapılandırması - Daha net fontlar
        style.configure('Title.TLabel', 
                       font=('Microsoft YaHei UI', 16, 'bold'),
                       foreground=bg_primary,
                       background=bg_surface)
        
        style.configure('Header.TLabel',
                       font=('Microsoft YaHei UI', 10, 'bold'),
                       foreground=bg_primary,
                       background=bg_surface)
        
        style.configure('Modern.TLabelframe',
                       background=bg_surface,
                       relief='flat',
                       borderwidth=1)
        
        style.configure('Modern.TLabelframe.Label',
                       font=('Microsoft YaHei UI', 9, 'bold'),
                       foreground=bg_primary,
                       background=bg_surface)
        
        style.configure('Modern.TButton',
                       font=('Microsoft YaHei UI', 8),
                       padding=(10, 8))
        
        style.configure('Connect.TButton',
                       font=('Microsoft YaHei UI', 8, 'bold'))
        
        style.configure('Send.TButton',
                       font=('Microsoft YaHei UI', 9, 'bold'),
                       padding=(15, 10))
        
        style.map('Connect.TButton',
                 background=[('active', accent_blue)])
        
        style.map('Send.TButton',
                 background=[('active', accent_green)])
        
        style.configure('Modern.TEntry',
                       fieldbackground='white',
                       borderwidth=1,
                       relief='solid')
        
        style.configure('Modern.TCombobox',
                       fieldbackground='white',
                       borderwidth=1,
                       relief='solid')
        
        # Ana başlık
        title_label = ttk.Label(self.root, text="🚀 STM32 Bootloader GUI", style='Title.TLabel')
        title_label.grid(row=0, column=0, pady=(20, 10))
        
        # -- Kaydırılabilir ana alan --
        container = ttk.Frame(self.root)
        container.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        canvas = tk.Canvas(container, bg=bg_surface, highlightthickness=0)
        vsb = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        # Ana çerçeve canvas içinde
        main_frame = ttk.Frame(canvas, padding="20", style='Modern.TFrame')
        frame_id = canvas.create_window((0, 0), window=main_frame, anchor="nw")

        # Scroll bölgesini otomatik ayarla
        def _on_frame_config(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # iç çerçeveyi canvas genişliğine uydur
            canvas.itemconfig(frame_id, width=canvas.winfo_width())
        main_frame.bind("<Configure>", _on_frame_config)

        # İlk kurulumdan sonra scroll bölgesini ayarla
        self.root.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox('all'))
        canvas.itemconfig(frame_id, width=canvas.winfo_width())

        # Mouse wheel (Windows/Linux)
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # MacOS için farklı
        def _on_mousewheel_mac(event):
            canvas.yview_scroll(int(event.delta), "units")
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, 'units'))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, 'units'))
        
        # Grid yapılandırması
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Bağlantı ayarları grubu
        connection_group = ttk.LabelFrame(main_frame, text="📡 UART Bağlantısı", padding="15", style='Modern.TLabelframe')
        connection_group.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        connection_group.columnconfigure(1, weight=1)
        
        # COM Port seçimi
        ttk.Label(connection_group, text="🔌 COM Port:", style='Header.TLabel').grid(row=0, column=0, sticky=tk.W, padx=(0, 10), pady=(0, 5))
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(connection_group, textvariable=self.port_var, state="readonly", style='Modern.TCombobox', width=15)
        self.port_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(0, 5))
        
        # Yenile butonu
        self.refresh_btn = ttk.Button(connection_group, text="🔄 Yenile", command=self.refresh_ports, style='Modern.TButton')
        self.refresh_btn.grid(row=0, column=2, padx=(5, 0), pady=(0, 5))
        
        # Baud rate
        ttk.Label(connection_group, text="⚡ Baud Rate:", style='Header.TLabel').grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 5))
        self.baudrate_var = tk.StringVar(value="115200")
        
        # Yaygın baud rate seçenekleri
        baudrate_options = [
            "9600",      # Eski cihazlar
            "19200",     # Eski cihazlar
            "38400",     # Orta hız
            "57600",     # Orta hız
            "115200",    # STM32 için standart
            "230400",    # Yüksek hız
            "460800",    # Yüksek hız
            "921600",    # Çok yüksek hız
            "1000000",   # 1Mbps
            "2000000",   # 2Mbps
            "3000000",   # 3Mbps
            "4000000"    # 4Mbps
        ]
        
        self.baudrate_combo = ttk.Combobox(connection_group, textvariable=self.baudrate_var, 
                                          values=baudrate_options, state="readonly", 
                                          style='Modern.TCombobox', width=12)
        self.baudrate_combo.grid(row=1, column=1, sticky=tk.W, padx=(0, 10), pady=(5, 5))
        
        # Bağlan/Bağlantıyı kes butonu
        self.connect_btn = ttk.Button(connection_group, text="🔗 Bağlan", command=self.toggle_connection, style='Connect.TButton')
        self.connect_btn.grid(row=1, column=2, padx=(5, 0), pady=(5, 5))
        
        # Bağlantı durumu
        status_frame = ttk.Frame(connection_group)
        status_frame.grid(row=2, column=0, columnspan=3, pady=(10, 0))
        
        # ----------------------------
        # 🧹 Sektör Silme Grubu
        # ----------------------------
        erase_group = ttk.LabelFrame(main_frame, text="🧹 Sektör Silme", padding="15", style='Modern.TLabelframe')
        erase_group.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        erase_group.columnconfigure(1, weight=1)
        
        ttk.Label(erase_group, text="🎯 Sektör:", style='Header.TLabel').grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.erase_sector_var = tk.StringVar(value="0")
        self.erase_sector_spinbox = ttk.Spinbox(erase_group, from_=0, to=255, textvariable=self.erase_sector_var, width=12, style='Modern.TEntry')
        self.erase_sector_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(0,10))
        
        self.erase_btn = ttk.Button(erase_group, text="🧹 Sektör Sil", command=self.erase_sector_thread, style='Send.TButton')
        self.erase_btn.grid(row=0, column=2, padx=(5,0))
        self.erase_btn.config(state="disabled")

        # Silme durum metni
        self.erase_status = ttk.Label(erase_group, text="", font=('Microsoft YaHei UI', 8), foreground="#7f8c8d")
        self.erase_status.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5,0))
        
        ttk.Label(status_frame, text="📊 Durum:", style='Header.TLabel').pack(side=tk.LEFT, padx=(0, 5))
        self.connection_status = ttk.Label(status_frame, text="❌ Bağlantı yok", foreground="#e74c3c", font=('Microsoft YaHei UI', 8, 'bold'))
        self.connection_status.pack(side=tk.LEFT)
        
        # Firmware ayarları grubu
        firmware_group = ttk.LabelFrame(main_frame, text="💾 Firmware Yükleme", padding="15", style='Modern.TLabelframe')
        firmware_group.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        firmware_group.columnconfigure(1, weight=1)
        
        # Firmware dosyası seçimi
        ttk.Label(firmware_group, text="📁 Dosya:", style='Header.TLabel').grid(row=0, column=0, sticky=tk.W, padx=(0, 10), pady=(0, 5))
        self.firmware_path_var = tk.StringVar()
        self.firmware_entry = ttk.Entry(firmware_group, textvariable=self.firmware_path_var, state="readonly", style='Modern.TEntry')
        self.firmware_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(0, 5))
        
        self.browse_btn = ttk.Button(firmware_group, text="📂 Gözat", command=self.browse_firmware, style='Modern.TButton')
        self.browse_btn.grid(row=0, column=2, padx=(5, 0), pady=(0, 5))
        
        # Sektör numarası
        ttk.Label(firmware_group, text="🎯 Hedef Sektör:", style='Header.TLabel').grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 5))
        self.sector_var = tk.StringVar(value="0")
        self.sector_spinbox = ttk.Spinbox(firmware_group, from_=0, to=255, textvariable=self.sector_var, width=12, style='Modern.TEntry')
        self.sector_spinbox.grid(row=1, column=1, sticky=tk.W, padx=(0, 10), pady=(5, 5))
        
        # Firmware bilgisi
        info_frame = ttk.Frame(firmware_group)
        info_frame.grid(row=2, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Label(info_frame, text="ℹ️ Bilgi:", style='Header.TLabel').pack(side=tk.LEFT, padx=(0, 5))
        self.firmware_info = ttk.Label(info_frame, text="Firmware yüklenmedi", foreground="#7f8c8d", font=('Microsoft YaHei UI', 8))
        self.firmware_info.pack(side=tk.LEFT)
        
        # İlerleme alanı (Firmware grubunda)
        progress_header = ttk.Label(firmware_group, text="📊 İlerleme Durumu", style='Header.TLabel')
        progress_header.grid(row=3, column=0, columnspan=3, pady=(10, 5), sticky=tk.W)

        # İlerleme çubuğu
        self.progress = ttk.Progressbar(firmware_group, mode='determinate', length=400)
        self.progress.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 8))
        firmware_group.columnconfigure(0, weight=1)

        # İlerleme metni
        self.progress_text = ttk.Label(firmware_group, text="⏳ Hazır", font=('Microsoft YaHei UI', 8), foreground="#7f8c8d")
        self.progress_text.grid(row=5, column=0, columnspan=3, pady=(0, 10), sticky=tk.W)

        # Gönder butonu
        self.send_btn = ttk.Button(firmware_group, text="🚀 Firmware Gönder", command=self.send_firmware_thread, style='Send.TButton')
        self.send_btn.grid(row=6, column=0, columnspan=3, pady=(5, 0))
        self.send_btn.config(state="disabled")
        
        # Log alanı
        log_group = ttk.LabelFrame(main_frame, text="📜 Sistem Günlüğü", padding="15", style='Modern.TLabelframe')
        log_group.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 0))
        log_group.columnconfigure(0, weight=1)
        log_group.rowconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Log başlığı ve temizle butonu
        log_header_frame = ttk.Frame(log_group)
        log_header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        log_header_frame.columnconfigure(0, weight=1)
        
        ttk.Label(log_header_frame, text="📋 İşlem Detayları", style='Header.TLabel').pack(side=tk.LEFT)
        clear_log_btn = ttk.Button(log_header_frame, text="🗑️ Temizle", command=self.clear_log, style='Modern.TButton')
        clear_log_btn.pack(side=tk.RIGHT)
        
        # Log metin alanı
        self.log_text = scrolledtext.ScrolledText(
            log_group, 
            height=12, 
            wrap=tk.WORD,
            font=('Courier New', 9),
            bg='#f8f9fa',
            fg='#2c3e50',
            relief='flat',
            borderwidth=1
        )
        self.log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def log_message(self, message: str, level: str = "INFO"):
        """Log alanına mesaj ekler"""
        timestamp = tk.StringVar()
        import datetime
        timestamp.set(datetime.datetime.now().strftime("%H:%M:%S"))
        
        log_entry = f"[{timestamp.get()}] {level}: {message}\n"
        
        # Debug: Konsola da yazdır
        print(f"LOG [{level}]: {message}")
        
        # GUI thread'inden çalıştır
        self.root.after(0, lambda: self._append_log(log_entry, level))
    
    def _append_log(self, text: str, level: str):
        """Log metnini ekler (GUI thread'inde çalışır)"""
        self.log_text.insert(tk.END, text)
        
        # Log seviyesine göre renklendirme
        if level == "ERROR":
            start_line = float(self.log_text.index(tk.END)) - 1.0
            self.log_text.tag_add("error", f"{start_line:.1f}", tk.END)
            self.log_text.tag_config("error", foreground="red")
        elif level == "SUCCESS":
            start_line = float(self.log_text.index(tk.END)) - 1.0
            self.log_text.tag_add("success", f"{start_line:.1f}", tk.END)
            self.log_text.tag_config("success", foreground="green")
        
        self.log_text.see(tk.END)
    
    def clear_log(self):
        """Log alanını temizler"""
        self.log_text.delete(1.0, tk.END)
    
    def refresh_ports(self):
        """Kullanılabilir COM portlarını yeniler"""
        # Geçici UART nesnesi oluştur
        temp_uart = UARTCommunication("dummy")
        ports = temp_uart.get_available_ports()
        
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.set(ports[0])
            self.log_message(f"{len(ports)} COM port bulundu")
        else:
            self.log_message("Hiç COM port bulunamadı", "ERROR")
        
        # Eğer bağlıysa bağlantıyı kes
        if self.uart_comm and self.uart_comm.is_connected:
            self.uart_comm.disconnect()
            self.uart_comm = None
            self.connect_btn.config(text="🔗 Bağlan")
            self.connection_status.config(text="❌ Bağlantı yok", foreground="#e74c3c")
            self.send_btn.config(state="disabled")
            self.erase_btn.config(state="disabled")
            self.log_message("Port yenilendi, bağlantı kapatıldı")
    
    def toggle_connection(self):
        """UART bağlantısını açar/kapatır"""
        if self.uart_comm and self.uart_comm.is_connected:
            # Bağlantıyı kes
            self.uart_comm.disconnect()
            self.uart_comm = None
            self.connect_btn.config(text="🔗 Bağlan")
            self.connection_status.config(text="❌ Bağlantı yok", foreground="#e74c3c")
            self.send_btn.config(state="disabled")
            self.erase_btn.config(state="disabled")
            self.log_message("UART bağlantısı kapatıldı")
        else:
            # Bağlan
            port = self.port_var.get()
            if not port:
                messagebox.showerror("Hata", "Lütfen bir COM port seçin")
                return
            
            try:
                baudrate = int(self.baudrate_var.get())
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz baud rate")
                return
            
            self.uart_comm = UARTCommunication(port, baudrate)
            if self.uart_comm.connect():
                self.connect_btn.config(text="🔌 Bağlantıyı Kes")
                self.connection_status.config(text=f"✅ Bağlı: {port} @ {baudrate}", foreground="#27ae60")
                self.update_action_buttons()
                self.log_message(f"UART bağlantısı kuruldu: {port} @ {baudrate}", "SUCCESS")
            else:
                self.uart_comm = None
                messagebox.showerror("Hata", f"UART bağlantısı kurulamadı: {port}")
    
    def browse_firmware(self):
        """Firmware dosyası seçer"""
        file_path = filedialog.askopenfilename(
            title="Firmware Dosyası Seç",
            filetypes=[
                ("Binary files", "*.bin"),
                ("Hex files", "*.hex"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                with open(file_path, 'rb') as f:
                    self.firmware_data = f.read()
                
                self.firmware_path = file_path
                self.firmware_path_var.set(os.path.basename(file_path))
                
                # Firmware bilgisini güncelle
                size_kb = len(self.firmware_data) / 1024
                self.firmware_info.config(text=f"✅ Yüklendi: {len(self.firmware_data)} byte ({size_kb:.1f} KB)", foreground="#27ae60")
                
                self.update_action_buttons()
                self.log_message(f"Firmware yüklendi: {os.path.basename(file_path)} ({len(self.firmware_data)} byte)")
                
            except Exception as e:
                error_msg = f"Firmware dosyası okunamadı: {e}"
                messagebox.showerror("Hata", error_msg)
                self.log_message(f"Firmware okuma hatası: {str(e)}", "ERROR")
    
    def update_action_buttons(self):
        """Gönder / Sil butonlarının durumunu günceller"""
        if self.uart_comm and self.uart_comm.is_connected:
            # Bağlı ise ERASE her zaman kullanılabilir
            self.erase_btn.config(state="normal")
            # SEND için firmware gerekiyor
            if self.firmware_data is not None:
                self.send_btn.config(state="normal")
            else:
                self.send_btn.config(state="disabled")
        else:
            # Bağlı değilse ikisi de pasif
            self.send_btn.config(state="disabled")
            self.erase_btn.config(state="disabled")
    
    def update_progress(self, current: int, total: int):
        """İlerleme çubuğunu günceller"""
        percentage = (current / total) * 100
        self.root.after(0, lambda: self.progress.config(value=percentage))
        self.root.after(0, lambda: self.progress_text.config(text=f"📦 Paket {current}/{total} ({percentage:.1f}%)"))
    
    def send_firmware_thread(self):
        """Firmware gönderimini ayrı thread'de çalıştırır"""
        def send_worker():
            try:
                sector = int(self.sector_var.get())
            except ValueError:
                error_msg = "Geçersiz sektör numarası"
                self.log_message(error_msg, "ERROR")
                return
            
            # UI'yi disable et
            self.root.after(0, lambda: self.send_btn.config(state="disabled"))
            self.root.after(0, lambda: self.progress.config(value=0))
            self.root.after(0, lambda: self.progress_text.config(text="🚀 Firmware gönderiliyor..."))
            
            self.log_message(f"Firmware gönderimi başlıyor (Sektör: {sector})")
            
            # Firmware gönder
            success, message = self.uart_comm.send_firmware(
                self.firmware_data, sector, self.update_progress
            )
            
            # Sonucu logla
            if success:
                self.log_message(message, "SUCCESS")
                self.root.after(0, lambda: self.progress_text.config(text="✅ Tamamlandı!", foreground="#27ae60"))
            else:
                self.log_message(f"Firmware gönderim hatası: {message}", "ERROR")
                self.root.after(0, lambda: self.progress_text.config(text="❌ Hata!", foreground="#e74c3c"))
            
            # UI'yi tekrar enable et
            self.root.after(0, self.update_action_buttons)
        
        # Worker thread'i başlat
        thread = threading.Thread(target=send_worker, daemon=True)
        thread.start()
    
    def erase_sector_thread(self):
        """Sektör silme işlemini ayrı thread'de yapar"""
        def erase_worker():
            try:
                sector = int(self.erase_sector_var.get())
            except ValueError:
                self.log_message("Geçersiz sektör numarası", "ERROR")
                return

            # UI kilitle
            self.root.after(0, lambda: self.erase_btn.config(state="disabled"))
            self.root.after(0, lambda: self.progress.config(value=0))
            self.root.after(0, lambda: self.erase_status.config(text="🧹 Sektör siliniyor...", foreground="#7f8c8d"))

            self.log_message(f"Sektör silme başlıyor (Sektör: {sector})")

            success, message = self.uart_comm.erase_sector(sector)

            if success:
                self.log_message(message, "SUCCESS")
                self.root.after(0, lambda: self.erase_status.config(text="✅ Silme tamamlandı", foreground="#27ae60"))
            else:
                self.log_message(f"Sektör silme hatası: {message}", "ERROR")
                self.root.after(0, lambda: self.erase_status.config(text="❌ Hata!", foreground="#e74c3c"))

            # UI butonlarını güncelle
            self.root.after(0, self.update_action_buttons)

        threading.Thread(target=erase_worker, daemon=True).start()

    def on_closing(self):
        """Uygulama kapatılırken çağrılır"""
        if self.uart_comm and self.uart_comm.is_connected:
            self.uart_comm.disconnect()
        self.root.destroy()
    
    def run(self):
        """GUI'yi başlatır"""
        self.root.mainloop()

def main():
    """Ana fonksiyon"""
    app = STM32BootloaderGUI()
    app.run()

if __name__ == "__main__":
    main() 