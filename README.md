# Thermocouple Logger (Python + PyQt5 + MCP9600 + Arduino)

This project contains two major components:
- **Arduino Firmware**  
- **Python GUI Application**

Use the navigation links below to jump directly to each section:

## 📌 Jump To:
- [Arduino Firmware Guide](#arduino)
- [Python GUI Guide](#python-gui)

---

# ARDUINO

## 🔧 Uploading the Firmware to the Arduino

The Arduino firmware is located in:

```
ArduinoCode/main/
    ├── config.h
    └── main.ino
```

---

## 📥 1. Install the Required Arduino Library

The firmware depends on the official Adafruit thermocouple amplifier driver.

### Install via Library Manager:
1. Open **Arduino IDE**
2. Go to **Sketch → Include Library → Manage Libraries**
3. Search for:
```
Adafruit MCP9600
```
4. Install:
- **Adafruit MCP9600**
- **Adafruit BusIO** (dependency) [should automatically ask if you want to install it]

---

## 📂 2. Open the Firmware Folder

Inside Arduino IDE:

**File → Open Folder**  
Select:
```
MDILab_ThermoCoupleArduino/ArduinoCode/main/
```

This ensures `main.ino` and `config.h` are loaded correctly.

---

## 🛠️ 3. Configure Board & Port

### Board:
```
Tools → Board → Arduino AVR Boards → Arduino Uno
```

### Port:
```
Tools → Port → COM4
```
(or whichever COM port appears when plugging in the board)

---

## 📤 4. Upload the Firmware

Click **Upload**.

Expected output:
```
Upload complete.
READY
```

The Arduino will begin streaming CSV temperature data.

---

## 🧪 5. Confirm Serial Output (Optional)

1. Open **Tools → Serial Monitor**
2. Set baud rate:
```
115200
```

You should see:
```
READY
23.5,21.8,24.1,22.0,...
```

---

# 🚨 IMPORTANT WARNING  
# **IF YOU DO STEP 5 AND OPEN THE SERIAL MONITOR, YOU MUST CLOSE IT BEFORE RUNNING THE PYTHON GUI.**  
Only one program can use the COM port at a time.

Leaving Serial Monitor open will cause:
- Python connection failures  
- “Port Busy / Access Denied” errors  
- No temperature data  

Close Serial Monitor before starting the GUI.

---

# PYTHON GUI

## 📂 Folder Structure

```
MDILab_ThermoCoupleArduino/
│
├── ArduinoCode/                    # Arduino firmware
│   └── main/                       # Main Arduino sketch folder
│       ├── config.h                # Sensor/channel configuration
│       └── main.ino                # Arduino thermocouple reader
│
├── PythonCode/                     # Python GUI application
│   ├── config.py                   # User config (COM port, sensor names, etc.)
│   ├── main.py                     # Real GUI communicating with Arduino
│   ├── test_config.py              # Config for fake sensor mode
│   └── test_main.py                # GUI for simulated sensor data
│
├── Wiring/                         # Hardware reference documents
│   └── Wiring.pdf                  # Wiring diagram for MCP9600 + TCA9548A + Arduino
│
├── venv/                           # Virtual environment
│
├── .gitignore                      # Ensures DataLog/, venv/, etc. are not tracked
├── README.md                       # Documentation
└── requirements.txt                # Python dependencies
```

---

## 🐍 Python Version

This project is tested with **Python 3.13**.

---

# 🖥️ Opening the Terminal in Visual Studio Code (Windows)

Before running the GUI, you must open the VS Code terminal.

## First: Open the Project Folder

1. Open **Visual Studio Code**  
2. Go to:
```
File → Open Folder
```
3. Select the **MDILab_ThermoCoupleArduino** folder.

---

## Then: Open the VS Code Terminal

### Method 1 — Menu
```
Terminal → New Terminal
```

### or

### Method 2 — Keyboard Shortcut
(Symbol right above TAB)
```
Ctrl + `
```

Your terminal should now look like:
```
PS C:\Users\You\MDILab_ThermoCoupleArduino>
```

---

## 🧪 Creating and Activating a Virtual Environment

### 1. Create venv
```
py -3.13 -m venv venv
```

### 2. Activate venv
```
venv\Scripts\activate
```

You should now see:
```
(venv) PS C:\Users\You\MDILab_ThermoCoupleArduino>
```

---

## 📥 Install Dependencies


```
pip install pyqt5 pyqtgraph pyserial
```

---

## 🚀 Running the GUI

### Real Arduino-connected mode:
```
cd PythonCode
python main.py
```

Or one line:
```
python PythonCode/main.py
```

The GUI waits for the Arduino to print:
```
READY
```

---

## 🧪 Running Test Mode (Fake Sensor Data)

```
cd PythonCode
python test_main.py
```

---

## 🔄 Updating via ZIP Download

### First Time Install: Steps 1–2  
### Updating: Steps 1–3

### 1. Download the ZIP
GitHub → **Code → Download ZIP**

### 2. Extract ZIP
Example:
```
Downloads/MDILab_ThermoCoupleArduino/
```

### 3. Copy updated folders into your working directory:
- PythonCode/
- ArduinoCode/
- Wiring/

Choose **Replace** when prompted.

Your DataLog folders remain untouched.

---

## 📚 Troubleshooting

### GUI opens but no data  
- Wrong COM port in `config.py`  
- Arduino not printing `READY`  
- Serial Monitor still open  

### Empty plot  
- Arduino must send **16 CSV values** (hot/cold for 8 sensors)

### Missing modules  
```
pip install -r requirements.txt
```

---

