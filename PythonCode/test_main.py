import sys
import os
import csv
import time
import random
from datetime import datetime
from collections import deque
from test_config import *
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg

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
            header.extend((
                f"{SENSOR_NAMES[i]}_{HOT_LABEL}",
                f"{SENSOR_NAMES[i]}_{COLD_LABEL}",
            ))
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
                f"{SENSOR_NAMES[i]}:  {HOT_LABEL} 0000.00 °C   {COLD_LABEL} 0000.00 °C"
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

        self.cb_global_hot = QtWidgets.QCheckBox(f"Show All {HOT_LABEL}")
        self.cb_global_hot.setChecked(True)
        self.cb_global_hot.stateChanged.connect(self.toggle_all_hot)

        self.cb_global_cold = QtWidgets.QCheckBox(f"Show All {COLD_LABEL}")
        self.cb_global_cold.setChecked(True)
        self.cb_global_cold.stateChanged.connect(self.toggle_all_cold)

        gl.addWidget(self.cb_global_hot)
        gl.addWidget(self.cb_global_cold)
        control_layout.addWidget(global_box)

        # --------- AXIS SCALING PANEL ---------
        axis_box = QtWidgets.QGroupBox("Manual Axis Scaling")
        axis_layout = QtWidgets.QGridLayout(axis_box)

        # X min/max
        axis_layout.addWidget(QtWidgets.QLabel("X Min:"), 0, 0)
        self.xmin_edit = QtWidgets.QLineEdit()
        if AXIS_X_MIN is not None:
            self.xmin_edit.setText(str(AXIS_X_MIN))
        self.xmin_edit.setPlaceholderText("auto")
        axis_layout.addWidget(self.xmin_edit, 0, 1)

        axis_layout.addWidget(QtWidgets.QLabel("X Max:"), 0, 2)
        self.xmax_edit = QtWidgets.QLineEdit()
        if AXIS_X_MAX is not None:
            self.xmax_edit.setText(str(AXIS_X_MAX))
        self.xmax_edit.setPlaceholderText("auto")
        axis_layout.addWidget(self.xmax_edit, 0, 3)

        # Y min/max
        axis_layout.addWidget(QtWidgets.QLabel("Y Min:"), 1, 0)
        self.ymin_edit = QtWidgets.QLineEdit()
        if AXIS_Y_MIN is not None:
            self.ymin_edit.setText(str(AXIS_Y_MIN))
        self.ymin_edit.setPlaceholderText("auto")
        axis_layout.addWidget(self.ymin_edit, 1, 1)

        axis_layout.addWidget(QtWidgets.QLabel("Y Max:"), 1, 2)
        self.ymax_edit = QtWidgets.QLineEdit()
        if AXIS_Y_MAX is not None:
            self.ymax_edit.setText(str(AXIS_Y_MAX))
        self.ymax_edit.setPlaceholderText("auto")
        axis_layout.addWidget(self.ymax_edit, 1, 3)

        # Buttons
        apply_btn = QtWidgets.QPushButton("Apply Scaling")
        apply_btn.clicked.connect(self.apply_manual_scaling)

        auto_btn = QtWidgets.QPushButton("Auto Scale")
        auto_btn.clicked.connect(self.reset_auto_scaling)

        axis_layout.addWidget(apply_btn, 2, 0, 1, 2)
        axis_layout.addWidget(auto_btn, 2, 2, 1, 2)

        control_layout.addWidget(axis_box)

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
            group = QtWidgets.QGroupBox(f"{SENSOR_NAMES[i]}")
            hl = QtWidgets.QHBoxLayout(group)

            key_hot = f"hot{i}"
            key_cold = f"cold{i}"

            cb_hot = QtWidgets.QCheckBox(HOT_LABEL)
            cb_hot.setChecked(True)
            cb_hot.toggled.connect(lambda chk, k=key_hot: self.on_curve_toggled(k, chk))
            self.checkboxes[key_hot] = cb_hot

            cb_cold = QtWidgets.QCheckBox(COLD_LABEL)
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
                f"{SENSOR_NAMES[i]}:  {HOT_LABEL} {hot:7.2f} {self.unit_suffix()}   "
                f"{COLD_LABEL} {cold:7.2f} {self.unit_suffix()}"
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

        # After rebuilding plots, redraw any existing data
        self.update_plot()

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
                display_name = f"{SENSOR_NAMES[i]} {HOT_LABEL if kind == 'hot' else COLD_LABEL}"
                item = p.plot([], [], pen=pen, name=display_name)
                item.setVisible(self.checkboxes[key].isChecked())
                self.curves_plot[key] = item

    def build_split2(self):
        cfg = PLOT_LAYOUT["split2"]

        for col_idx, side in enumerate(cfg.keys()):
            for row_idx, sensor in enumerate(cfg[side]):
                p = pg.PlotWidget()
                p.addLegend()
                p.setLabel("left", f"{SENSOR_NAMES[sensor]} Temp ({self.unit_suffix()})")
                p.setLabel("bottom", "Time (s)")

                self.plot_layout.addWidget(p, row_idx, col_idx)
                self.plot_widgets.append(p)

                for kind in ("hot", "cold"):
                    key = f"{kind}{sensor}"
                    pen = pg.mkPen(color=CURVE_COLORS[key], width=2)
                    display_name = f"{SENSOR_NAMES[sensor]} {HOT_LABEL if kind == 'hot' else COLD_LABEL}"
                    item = p.plot([], [], pen=pen, name=display_name)
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

    # ---------- MANUAL AXIS CONTROL ----------

    def apply_manual_scaling(self):
        global AXIS_X_MIN, AXIS_X_MAX, AXIS_Y_MIN, AXIS_Y_MAX

        def parse_value(text):
            text = text.strip()
            if not text:
                return None
            try:
                return float(text)
            except ValueError:
                # Invalid input -> treat as auto
                return None

        AXIS_X_MIN = parse_value(self.xmin_edit.text())
        AXIS_X_MAX = parse_value(self.xmax_edit.text())
        AXIS_Y_MIN = parse_value(self.ymin_edit.text())
        AXIS_Y_MAX = parse_value(self.ymax_edit.text())

        self.update_plot()

    def reset_auto_scaling(self):
        global AXIS_X_MIN, AXIS_X_MAX, AXIS_Y_MIN, AXIS_Y_MAX
        AXIS_X_MIN = AXIS_X_MAX = AXIS_Y_MIN = AXIS_Y_MAX = None

        # Clear text fields back to empty (auto)
        self.xmin_edit.clear()
        self.xmax_edit.clear()
        self.ymin_edit.clear()
        self.ymax_edit.clear()

        # Re-enable auto range on all plots
        for p in self.plot_widgets:
            p.enableAutoRange()

        self.update_plot()

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
                f"{SENSOR_NAMES[i]}:  {HOT_LABEL} {hot_conv:7.2f} {self.unit_suffix()}   "
                f"{COLD_LABEL} {cold_conv:7.2f} {self.unit_suffix()}"
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

        # Apply manual axis scaling globally (if configured)
        for p in self.plot_widgets:
            if AXIS_X_MIN is not None and AXIS_X_MAX is not None:
                p.setXRange(AXIS_X_MIN, AXIS_X_MAX)
            if AXIS_Y_MIN is not None and AXIS_Y_MAX is not None:
                p.setYRange(AXIS_Y_MIN, AXIS_Y_MAX)

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
