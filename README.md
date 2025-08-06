# STM32 Bootloader GUI

A UART-based firmware upload application for STM32 bootloaders. Features a modern and user-friendly graphical interface using 21-byte fixed-length packets for secure firmware transfer and sector erasing operations.

## 🚀 Features

- **Modern GUI**: Tkinter-based user-friendly interface
- **Secure Communication**: CRC32 error checking for packet integrity
- **Smart Flow Control**: ACK/NACK-based soft flow control
- **Progress Tracking**: Real-time transfer progress indicator
- **Detailed Logging**: Colored log messages for operation tracking
- **Port Auto-Scan**: Automatic detection of available COM ports
- **Sector Erasing**: Separate interface for sector erasing operations
- **Scrollable Interface**: Vertical scrolling for full content access

## 📋 Protocol Specifications

All packets are **21 bytes fixed length** and support 4 different message types:

### 🟩 CMD_WRITE Packet (Sector Preparation)
```
Format: 0x01 + sector(1 byte) + padding(15 bytes) + CRC32(4 bytes)
Total: 21 bytes
CRC32: Calculated over first 17 bytes
```

### 🟦 CMD_ERASE Packet (Sector Erasing)
```
Format: 0x02 + sector(1 byte) + padding(15 bytes) + CRC32(4 bytes)
Total: 21 bytes
CRC32: Calculated over first 17 bytes
```

### 🟨 DATA Packet (Firmware Data)
```
Format: 0x03 + data(16 bytes) + CRC32(4 bytes)
Total: 21 bytes
CRC32: Calculated over first 17 bytes
```

### 🟥 FINISH Packet (Transfer Completion)
```
Format: 0x04 + padding(16 bytes) + CRC32(4 bytes)
Total: 21 bytes
CRC32: Calculated over first 17 bytes
```

## 🛠️ Installation

### Requirements
- Python 3.7 or higher
- Windows/Linux/macOS support

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Required Packages
- `pyserial>=3.5` - For UART communication
- `tkinter` - GUI (comes with Python)

## 🎯 Usage

### Launch GUI
```bash
python main.py
```

### Step-by-Step Usage

1. **UART Connection**:
   - Select COM port (Refresh button to update ports)
   - Check baud rate (default: 115200)
   - Click "Connect" button

2. **Firmware Upload**:
   - Click "Browse" to select firmware file (.bin, .hex)
   - Set target sector number (0-255)
   - Check firmware information

3. **Transfer Process**:
   - Click "Send Firmware" button
   - Monitor progress bar
   - Watch detailed information in log area

4. **Sector Erasing**:
   - Select target sector number
   - Click "Erase Sector" button
   - Monitor operation status

## 🧪 Testing

Test protocol functions with:
```bash
python tests/test_protocol.py
```

Test output example:
```
🟩 CMD_WRITE Packet Tests:
  Sector 0 packet: 21 bytes - 01008a5b3c3f000000000000000000000000000000
  ✅ CMD_WRITE packet tests successful

🟦 CMD_ERASE Packet Tests:
  Sector 5 packet: 21 bytes - 02058a5b3c3f000000000000000000000000000000
  ✅ CMD_ERASE packet tests successful

🟨 DATA Packet Tests:
  16 byte data packet: 21 bytes - 0348656c6c6f2053544d3332212121211a2c86af
  ✅ DATA packet tests successful
```

## 📁 Project Structure

```
stm32_bootloader_project/
├── src/
│   ├── __init__.py          # Package initialization
│   ├── stm32_protocol.py    # Protocol operations
│   ├── uart_comm.py         # UART communication
│   └── gui.py               # Graphical interface
├── tests/
│   └── test_protocol.py     # Unit tests
├── main.py                  # Main application
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## ⚙️ Technical Details

### CRC32 Calculation
- Uses Python `zlib.crc32()` function
- Little-endian byte ordering
- 32-bit unsigned integer result

### UART Settings
- Baud Rate: 115200 (default)
- Data Bits: 8
- Parity: None
- Stop Bits: 1
- Flow Control: Software (ACK/NACK)

### Thread Safety
- GUI runs in main thread
- Firmware transfer runs in separate thread
- Progress callbacks update in GUI thread

### Communication Flow
1. **CMD_WRITE**: Send sector info → Wait for ACK → 500ms delay
2. **DATA**: Send firmware data → Wait for ACK → Repeat
3. **FINISH**: Send completion signal → Wait for ACK
4. **CMD_ERASE**: Send sector info → Wait for ACK → 500ms delay → FINISH

## 🔧 Troubleshooting

### Common Issues

1. **COM Port Not Found**:
   - Check USB-UART drivers
   - Verify port status in Device Manager
   - Click "Refresh" button

2. **Connection Error**:
   - Ensure port is not used by another application
   - Check baud rate settings
   - Verify USB cables

3. **Transfer Error**:
   - Verify STM32 bootloader is ready
   - Monitor ACK/NACK responses in log
   - Check firmware file validity

4. **Erase Error**:
   - Check sector number validity (0-11)
   - Monitor NACK error codes
   - Verify bootloader erase support

## 📝 License

This project is open source and distributed under the MIT license.

## 🤝 Contributing

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request


<img width="912" height="1013" alt="image" src="https://github.com/user-attachments/assets/c516b8bc-1323-4730-a774-70a462fbe2ea" />



**Note**: This application is designed to work with STM32 bootloaders. Ensure your bootloader firmware sends ACK (0x06) and NACK (0x15) responses.

## 🤖 AI Development Note

This project was developed with the assistance of AI tools for code generation, testing, and documentation. The development process involved iterative refinement based on user feedback and requirements, demonstrating effective human-AI collaboration in embedded systems development. 
