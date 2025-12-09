import sys
import os
import csv
import time
import random
from datetime import datetime
from collections import deque

from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg


# ---------------- USER CONFIG ------------------

EXPERIMENT_TYPE = "thermalTest"
SENSOR_COUNT = 8
ROOT_LOG_DIR = "DataLog_Test"

HISTORY_SECONDS = 60
FAKE_INTERVAL_MS = 1000
VIEW_MODE_DEFAULT = "merged"

# Default GUI temperature units: "C" or "F"
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


# ---------------- FAKE CSV GENERATOR ------------------

def generate_fake_csv():
    """Simulates Arduino CSV output."""
    values = []
    for i in range(SENSOR_COUNT):
        hot = round(random.uniform(20, 300), 2)
        cold = round(random.uniform(20, 40), 2)
        values.extend([hot, cold])
    return ",".join(str(v) for v in values)


# ---------------- LOGGING HELPERS ------------------

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

class FakeSerialPlotter(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.view_mode = VIEW_MODE_DEFAULT
        self.start_time = time.time()

        # Time + sensor data storage
        self.time_data = deque(maxlen=20000)
        self.curves_data = {
            f"hot{i}": deque(maxlen=20000) for i in range(SENSOR_COUNT)
        }
        self.curves_data.update({
            f"cold{i}": deque(maxlen=20000) for i in range(SENSOR_COUNT)
        })

        # CSV logging
        self.output_file = build_output_path()
        self.csvfile = open(self.output_file, "w", newline="")
        self.csvwriter = csv.writer(self.csvfile)
        self.write_header()

        # Build UI
        self.init_ui()

        # Timer for fake serial data
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.inject_fake_data)
        self.timer.start(FAKE_INTERVAL_MS)

    # ---------- CSV Header ----------

    def write_header(self):
        header = ["time_since_start", "datetime"]
        for i in range(SENSOR_COUNT):
            header.extend((f"hot{i}", f"cold{i}"))
        self.csvwriter.writerow(header)
        self.csvfile.flush()

    # ---------- Temperature Conversion ----------

    def convert_temp(self, celsius):
        if TEMP_UNIT == "F":
            return (celsius * 9/5) + 32
        return celsius

    def unit_suffix(self):
        return "°F" if TEMP_UNIT == "F" else "°C"

    # ---------- UI SETUP ----------

    def init_ui(self):
        self.setWindowTitle("Thermocouple Logger (TEST MODE)")

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QHBoxLayout(central)

        # ---------- Plot container ----------
        self.plot_container = QtWidgets.QWidget()
        self.plot_layout = QtWidgets.QGridLayout(self.plot_container)
        main_layout.addWidget(self.plot_container, stretch=3)

        # ---------- Control panel ----------
        control_panel = QtWidgets.QWidget()
        control_layout = QtWidgets.QVBoxLayout(control_panel)

        # --------- UNIT TOGGLE ---------
        unit_box = QtWidgets.QGroupBox("Temperature Units")
        unit_layout = QtWidgets.QHBoxLayout(unit_box)

        self.btn_unit_c = QtWidgets.QPushButton("°C")
        self.btn_unit_f = QtWidgets.QPushButton("°F")

        self.btn_unit_c.setCheckable(True)
        self.btn_unit_f.setCheckable(True)

        self.btn_unit_c.setChecked(True)

        self.btn_unit_c.clicked.connect(lambda: self.change_units("C"))
        self.btn_unit_f.clicked.connect(lambda: self.change_units("F"))

        unit_layout.addWidget(self.btn_unit_c)
        unit_layout.addWidget(self.btn_unit_f)
        control_layout.addWidget(unit_box)

        # --------- LIVE VALUE PANEL ---------
        live_box = QtWidgets.QGroupBox("Live Values")
        live_layout = QtWidgets.QVBoxLayout(live_box)

        self.live_labels = {}
        for i in range(SENSOR_COUNT):
            # Allocate fixed-width placeholder to prevent jitter
            label = QtWidgets.QLabel(
                f"Sensor {i}:  HOT 0000.00 °C   COLD 0000.00 °C"
            )
            label.setStyleSheet("font-family: Consolas; font-size: 12pt;")
            label.setMinimumWidth(380)
            label.setFixedHeight(22)

            live_layout.addWidget(label)
            self.live_labels[f"row{i}"] = label

        control_layout.addWidget(live_box)

        # --------- GLOBAL TOGGLES ---------
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

        # --------- VIEW MODE BUTTONS ---------
        btns = QtWidgets.QHBoxLayout()
        self.btn_merged = QtWidgets.QPushButton("Merged View")
        self.btn_split2 = QtWidgets.QPushButton("2-Column View")

        self.btn_merged.clicked.connect(self.switch_to_merged)
        self.btn_split2.clicked.connect(self.switch_to_split2)

        btns.addWidget(self.btn_merged)
        btns.addWidget(self.btn_split2)
        control_layout.addLayout(btns)

        # --------- Per-sensor toggles ---------
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

        # Initialize plots
        self.curves_plot = {}
        self.plot_widgets = []
        self.build_plots()

    # ---------- UNIT SWITCH -----------

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

    # ---------- PLOT BUILDING ----------

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
                pen = pg.mkPen(color=CURVE_COLORS[key], width=2)
                item = p.plot([], [], pen=pen, name=key)
                item.setVisible(self.checkboxes[key].isChecked())
                self.curves_plot[key] = item

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
                    pen = pg.mkPen(color=CURVE_COLORS[key], width=2)
                    item = p.plot([], [], pen=pen, name=key)
                    item.setVisible(self.checkboxes[key].isChecked())
                    self.curves_plot[key] = item

    # ---------- VIEW MODE BUTTONS ----------

    def switch_to_merged(self):
        self.view_mode = "merged"
        self.build_plots()

    def switch_to_split2(self):
        self.view_mode = "split2"
        self.build_plots()

    # ---------- VISIBILITY ----------

    def on_curve_toggled(self, key, checked):
        if key in self.curves_plot:
            self.curves_plot[key].setVisible(checked)

    def toggle_all_hot(self, state):
        show = (state == QtCore.Qt.Checked)
        for i in range(SENSOR_COUNT):
            key = f"hot{i}"
            self.checkboxes[key].setChecked(show)
            if key in self.curves_plot:
                self.curves_plot[key].setVisible(show)

    def toggle_all_cold(self, state):
        show = (state == QtCore.Qt.Checked)
        for i in range(SENSOR_COUNT):
            key = f"cold{i}"
            self.checkboxes[key].setChecked(show)
            if key in self.curves_plot:
                self.curves_plot[key].setVisible(show)

    # ---------- FAKE DATA LOOP ----------

    def inject_fake_data(self):
        csv_line = generate_fake_csv()
        values = [float(x) for x in csv_line.split(",")]

        now = time.time()
        elapsed = round(now - self.start_time, 3)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Save CSV
        self.csvwriter.writerow([elapsed, now_str] + values)
        self.csvfile.flush()

        # Save time
        self.time_data.append(elapsed)

        # Update curves and live readout
        for i in range(SENSOR_COUNT):
            hot = values[2 * i]
            cold = values[2 * i + 1]

            self.curves_data[f"hot{i}"].append(hot)
            self.curves_data[f"cold{i}"].append(cold)

            hot_conv = self.convert_temp(hot)
            cold_conv = self.convert_temp(cold)

            self.live_labels[f"row{i}"].setText(
                f"Sensor {i}:  HOT {hot_conv:7.2f} {self.unit_suffix()}   "
                f"COLD {cold_conv:7.2f} {self.unit_suffix()}"
            )

        self.update_plot()

    # ---------- PLOTTING ----------

    def update_plot(self):
        if not self.time_data:
            return

        # Trim history
        while self.time_data and (self.time_data[-1] - self.time_data[0] > HISTORY_SECONDS):
            self.time_data.popleft()
            for v in self.curves_data.values():
                if v:
                    v.popleft()

        t = list(self.time_data)

        # Update curves
        for key, curve in self.curves_plot.items():
            y = [self.convert_temp(v) for v in self.curves_data[key]]
            if len(y) == len(t):
                curve.setData(t, y)

    # ---------- CLEANUP ----------

    def closeEvent(self, event):
        self.csvfile.close()
        event.accept()


# ---------------- ENTRY POINT ------------------

def main():
    app = QtWidgets.QApplication(sys.argv)
    win = FakeSerialPlotter()
    win.resize(1500, 900)
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
