import sys
import os
import csv
import time
import serial
from datetime import datetime
from collections import deque

from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg


# ---------------- USER CONFIG ------------------

PORT = "COM4"
BAUD = 115200

EXPERIMENT_TYPE = "HotWater"
SENSOR_COUNT = 8
ROOT_LOG_DIR = "DataLog"

HISTORY_SECONDS = 60
POLL_INTERVAL_MS = 100
VIEW_MODE_DEFAULT = "merged"

TEMP_UNIT = "C"

PLOT_LAYOUT = {
    "split2": {
        "left":  [0, 1, 2, 3],
        "right": [4, 5, 6, 7],
    }
}

CURVE_COLORS = {
    "hot0":  (255, 0, 0),       "cold0": (150, 0, 0),
    "hot1":  (0, 200, 0),       "cold1": (0, 100, 0),
    "hot2":  (0, 0, 255),       "cold2": (0, 0, 150),
    "hot3":  (255, 165, 0),     "cold3": (180, 110, 0),
    "hot4":  (128, 0, 128),     "cold4": (90, 0, 90),
    "hot5":  (0, 128, 128),     "cold5": (0, 90, 90),
    "hot6":  (128, 128, 0),     "cold6": (90, 90, 0),
    "hot7":  (255, 20, 147),    "cold7": (180, 10, 100),
}


def wait_for_ready(ser):
    print("Waiting for Arduino READY signal...")
    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if line == "READY":
            print("Arduino is ready!\n")
            return


def parse_csv(line):
    try:
        return [float(x) if x != "nan" else float("nan") for x in line.split(",")]
    except ValueError:
        return None


def build_output_path():
    now = datetime.now()
    date_folder = now.strftime("%Y-%m-%d")
    time_folder = now.strftime("%H-%M-%S")

    full_path = os.path.join(ROOT_LOG_DIR, date_folder, time_folder)
    os.makedirs(full_path, exist_ok=True)

    filename = f"{EXPERIMENT_TYPE}_{SENSOR_COUNT}ch.csv"
    file_path = os.path.join(full_path, filename)

    print(f"Saving logs to: {file_path}")
    return file_path


# ---------------- MAIN GUI CLASS ------------------

class SerialPlotter(QtWidgets.QMainWindow):
    def __init__(self, port, baud, parent=None):
        super().__init__(parent)

        self.port = port
        self.baud = baud

        self.view_mode = VIEW_MODE_DEFAULT
        self.start_time = time.time()

        # Serial connection
        self.ser = serial.Serial(self.port, self.baud, timeout=1)
        wait_for_ready(self.ser)

        # Data storage
        self.time_data = deque(maxlen=20000)
        self.curves_data = {
            f"hot{i}": deque(maxlen=20000) for i in range(SENSOR_COUNT)
        }
        self.curves_data.update({
            f"cold{i}": deque(maxlen=20000) for i in range(SENSOR_COUNT)
        })

        # Set up CSV logging
        self.output_file = build_output_path()
        self.csvfile = open(self.output_file, "w", newline="")
        self.csvwriter = csv.writer(self.csvfile)
        self.write_header()

        # Build UI (now matches test_main.py)
        self.init_ui()

        # Serial polling timer
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.poll_serial)
        self.timer.start(POLL_INTERVAL_MS)

    # ---------- Conversion ----------

    def convert_temp(self, celsius):
        if TEMP_UNIT == "F":
            return celsius * 9/5 + 32
        return celsius

    def unit_suffix(self):
        return "°F" if TEMP_UNIT == "F" else "°C"

    # ---------- CSV Header ----------

    def write_header(self):
        header = ["time_since_start", "datetime"]
        for i in range(SENSOR_COUNT):
            header.extend((f"hot{i}", f"cold{i}"))
        self.csvwriter.writerow(header)
        self.csvfile.flush()

    # ---------- UI Setup----------

    def init_ui(self):
        self.setWindowTitle("Thermocouple Logger (Arduino)")

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QHBoxLayout(central)

        # ---------------- PLOTS ----------------
        self.plot_container = QtWidgets.QWidget()
        self.plot_layout = QtWidgets.QGridLayout(self.plot_container)
        main_layout.addWidget(self.plot_container, stretch=3)

        # ---------------- CONTROL PANEL ----------------
        control_panel = QtWidgets.QWidget()
        control_layout = QtWidgets.QVBoxLayout(control_panel)

        # -------- UNIT TOGGLE ----------
        unit_box = QtWidgets.QGroupBox("Temperature Units")
        ul = QtWidgets.QHBoxLayout(unit_box)

        self.btn_unit_c = QtWidgets.QPushButton("°C")
        self.btn_unit_f = QtWidgets.QPushButton("°F")

        self.btn_unit_c.setCheckable(True)
        self.btn_unit_f.setCheckable(True)
        self.btn_unit_c.setChecked(True)

        self.btn_unit_c.clicked.connect(lambda: self.change_units("C"))
        self.btn_unit_f.clicked.connect(lambda: self.change_units("F"))

        ul.addWidget(self.btn_unit_c)
        ul.addWidget(self.btn_unit_f)
        control_layout.addWidget(unit_box)

        # -------- LIVE READOUT PANEL ----------
        live_box = QtWidgets.QGroupBox("Live Values")
        live_layout = QtWidgets.QVBoxLayout(live_box)

        self.live_labels = {}

        for i in range(SENSOR_COUNT):
            label = QtWidgets.QLabel(
                f"Sensor {i}:  HOT 0000.00 °C   COLD 0000.00 °C"
            )
            label.setStyleSheet("font-family: Consolas; font-size: 12pt;")
            label.setMinimumWidth(380)
            label.setFixedHeight(22)

            live_layout.addWidget(label)
            self.live_labels[f"row{i}"] = label

        control_layout.addWidget(live_box)

        # -------- GLOBAL HOT/COLD TOGGLES ----------
        global_box = QtWidgets.QGroupBox("Global Visibility")
        gl = QtWidgets.QHBoxLayout(global_box)

        self.cb_global_hot = QtWidgets.QCheckBox("Show All HOT")
        self.cb_global_hot.setChecked(True)
        self.cb_global_hot.stateChanged.connect(self.toggle_all_hot)

        self.cb_global_cold = QtWidgets.QCheckBox("Show All COLD")
        self.cb_global_cold.setChecked(True)
        self.cb_global_cold.stateChanged.connect(self.toggle_all_cold)

        gl.addWidget(self.cb_global_hot)
        gl.addWidget(self.cb_global_cold)
        control_layout.addWidget(global_box)

        # -------- VIEW MODE BUTTONS ----------
        btn_box = QtWidgets.QHBoxLayout()
        self.btn_merged = QtWidgets.QPushButton("Merged View")
        self.btn_split2 = QtWidgets.QPushButton("2-Column View")

        self.btn_merged.clicked.connect(self.switch_to_merged)
        self.btn_split2.clicked.connect(self.switch_to_split2)

        btn_box.addWidget(self.btn_merged)
        btn_box.addWidget(self.btn_split2)

        control_layout.addLayout(btn_box)

        # -------- SENSOR CHECKBOXES ----------
        self.checkboxes = {}

        for i in range(SENSOR_COUNT):
            group = QtWidgets.QGroupBox(f"Sensor {i}")
            hl = QtWidgets.QHBoxLayout(group)

            key_hot = f"hot{i}"
            key_cold = f"cold{i}"

            cb_hot = QtWidgets.QCheckBox("Hot")
            cb_hot.setChecked(True)
            cb_hot.toggled.connect(lambda chk, k=key_hot: self.on_curve_toggled(k, chk))
            self.checkboxes[key_hot] = cb_hot

            cb_cold = QtWidgets.QCheckBox("Cold")
            cb_cold.setChecked(True)
            cb_cold.toggled.connect(lambda chk, k=key_cold: self.on_curve_toggled(k, chk))
            self.checkboxes[key_cold] = cb_cold

            hl.addWidget(cb_hot)
            hl.addWidget(cb_cold)
            control_layout.addWidget(group)

        control_layout.addStretch()
        main_layout.addWidget(control_panel, stretch=1)

        # Build initial plots
        self.curves_plot = {}
        self.plot_widgets = []
        self.build_plots()

    # ---------- UNIT SWITCH ----------

    def change_units(self, unit):
        global TEMP_UNIT
        TEMP_UNIT = unit

        self.btn_unit_c.setChecked(unit == "C")
        self.btn_unit_f.setChecked(unit == "F")

        self.update_live_labels()
        self.update_plot()

    def update_live_labels(self):
        for i in range(SENSOR_COUNT):
            if len(self.curves_data[f"hot{i}"]) == 0:
                continue

            hot = self.convert_temp(self.curves_data[f"hot{i}"][-1])
            cold = self.convert_temp(self.curves_data[f"cold{i}"][-1])

            self.live_labels[f"row{i}"].setText(
                f"Sensor {i}:  HOT {hot:7.2f} {self.unit_suffix()}   "
                f"COLD {cold:7.2f} {self.unit_suffix()}"
            )

    # ---------- Plot Building ----------

    def clear_plots(self):
        for w in self.plot_widgets:
            self.plot_layout.removeWidget(w)
            w.deleteLater()
        self.plot_widgets.clear()
        self.curves_plot.clear()

    def build_plots(self):
        self.clear_plots()

        if self.view_mode == "merged":
            self.build_merged()
        else:
            self.build_split2()

    def build_merged(self):
        p = pg.PlotWidget()
        p.addLegend()
        p.setLabel("left", f"Temperature ({self.unit_suffix()})")
        p.setLabel("bottom", "Time (s)")

        self.plot_layout.addWidget(p, 0, 0)
        self.plot_widgets.append(p)

        for i in range(SENSOR_COUNT):
            for kind in ("hot", "cold"):
                key = f"{kind}{i}"
                color = CURVE_COLORS[key]
                curve = p.plot([], [], pen=pg.mkPen(color=color, width=2), name=key)
                curve.setVisible(self.checkboxes[key].isChecked())
                self.curves_plot[key] = curve

    def build_split2(self):
        cfg = PLOT_LAYOUT["split2"]

        for col_idx, side in enumerate(cfg.keys()):
            for row_idx, sensor in enumerate(cfg[side]):
                p = pg.PlotWidget()
                p.addLegend()
                p.setLabel("left", f"S{sensor} Temp ({self.unit_suffix()})")
                p.setLabel("bottom", "Time (s)")

                self.plot_layout.addWidget(p, row_idx, col_idx)
                self.plot_widgets.append(p)

                for kind in ("hot", "cold"):
                    key = f"{kind}{sensor}"
                    color = CURVE_COLORS[key]
                    curve = p.plot([], [], pen=pg.mkPen(color=color, width=2), name=key)
                    curve.setVisible(self.checkboxes[key].isChecked())
                    self.curves_plot[key] = curve

    # ---------- View Toggles ----------

    def switch_to_merged(self):
        self.view_mode = "merged"
        self.build_plots()

    def switch_to_split2(self):
        self.view_mode = "split2"
        self.build_plots()

    def on_curve_toggled(self, key, checked):
        if key in self.curves_plot:
            self.curves_plot[key].setVisible(checked)

    def toggle_all_hot(self, state):
        show = (state == QtCore.Qt.Checked)
        for i in range(SENSOR_COUNT):
            key = f"hot{i}"
            self.checkboxes[key].setChecked(show)

    def toggle_all_cold(self, state):
        show = (state == QtCore.Qt.Checked)
        for i in range(SENSOR_COUNT):
            key = f"cold{i}"
            self.checkboxes[key].setChecked(show)

    # ---------- Serial Polling ----------

    def poll_serial(self):
        try:
            while self.ser.in_waiting:
                line = self.ser.readline().decode(errors="ignore").strip()

                if not line or "," not in line:
                    continue

                values = parse_csv(line)
                if values is None or len(values) != 2 * SENSOR_COUNT:
                    continue

                now = time.time()
                elapsed = round(now - self.start_time, 3)
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Log to CSV
                self.csvwriter.writerow([elapsed, now_str] + values)
                self.csvfile.flush()

                # Store time & values
                self.time_data.append(elapsed)

                for i in range(SENSOR_COUNT):
                    self.curves_data[f"hot{i}"].append(values[2 * i])
                    self.curves_data[f"cold{i}"].append(values[2 * i + 1])

                self.update_live_labels()

            self.update_plot()

        except serial.SerialException as e:
            print("Serial error:", e)
            self.timer.stop()

    # ---------- Plot Updating ----------

    def update_plot(self):
        if not self.time_data:
            return

        # Trim old data
        while self.time_data and (self.time_data[-1] - self.time_data[0] > HISTORY_SECONDS):
            self.time_data.popleft()
            for dq in self.curves_data.values():
                if dq:
                    dq.popleft()

        t = list(self.time_data)

        for key, curve in self.curves_plot.items():
            y = [self.convert_temp(v) for v in self.curves_data[key]]
            if len(y) == len(t):
                curve.setData(t, y)

    # ---------- Cleanup ----------

    def closeEvent(self, event):
        self.timer.stop()
        try:
            if self.ser.is_open:
                self.ser.close()
        except:
            pass

        try:
            self.csvfile.close()
        except:
            pass

        event.accept()


def main():
    app = QtWidgets.QApplication(sys.argv)
    win = SerialPlotter(PORT, BAUD)
    win.resize(1500, 900)
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
