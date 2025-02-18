import serial
import time
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime

class PT100TempLogger:
    def __init__(self, port, baudrate=9600):
        """Initialize the serial connection with Arduino"""
        try:
            self.ser = serial.Serial(port=port, baudrate=baudrate, timeout=1)
            time.sleep(2)
        except serial.SerialException as e:
            print(f"Error opening serial port: {e}")
            raise

    def read_temperature(self):
        """Read temperature data from Arduino"""
        try:
            self.ser.write(b'r')
            if self.ser.in_waiting:
                line = self.ser.readline().decode('utf-8').strip()
                try:
                    return float(line)
                except ValueError:
                    print(f"Invalid data received: {line}")
                    return None
        except serial.SerialException as e:
            print(f"Error reading from serial port: {e}")
            return None

    def __del__(self):
        """Cleanup: Close serial connection"""
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()

def create_plots(df, output_folder):
    """Create and save plots from the measurement data"""
    df['Seconds'] = (df['Timestamp'] - df['Timestamp'].iloc[0]).dt.total_seconds()
    plt.figure(figsize=(15, 10))

    plt.subplot(2, 2, 1)
    plt.plot(df['Seconds'], df['Temperature'], 'b-')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Temperature (°C)')
    plt.title('Temperature vs Time')
    plt.grid(True)

    plt.subplot(2, 2, 2)
    plt.plot(df['Set_Voltage'], df['Temperature'], 'r-')
    plt.xlabel('Set Voltage (V)')
    plt.ylabel('Temperature (°C)')
    plt.title('Temperature vs Set Voltage')
    plt.grid(True)

    plt.subplot(2, 2, 3)
    plt.plot(df['Measured_Voltage'], df['Temperature'], 'g-')
    plt.xlabel('Measured Voltage (V)')
    plt.ylabel('Temperature (°C)')
    plt.title('Temperature vs Measured Voltage')
    plt.grid(True)

    plt.subplot(2, 2, 4)
    plt.plot(df['Measured_Current'], df['Temperature'], 'm-')
    plt.xlabel('Current (A)')
    plt.ylabel('Temperature (°C)')
    plt.title('Temperature vs Current')
    plt.grid(True)

    plt.tight_layout()
    plot_file = os.path.join(output_folder, 'measurement_plots.png')
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    plt.close()

    return plot_file

def save_data(data, output_folder, error=False):
    """Save measurement data to Excel and create plots"""
    if data:
        df = pd.DataFrame(data)
        suffix = '_ERROR' if error else ''
        excel_file = os.path.join(output_folder, f'power_supply_temp_log{suffix}.xlsx')
        df.to_excel(excel_file, index=False)
        plot_file = create_plots(df, output_folder)
        return excel_file, plot_file
    return None, None

def pid_control(target_temp, current_temp, Kp, Ki, Kd, integral, prev_error):
    """Calculate the voltage adjustment using PID control."""
    error = target_temp - current_temp
    integral += error
    derivative = error - prev_error
    output = Kp * error + Ki * integral + Kd * derivative

    output = max(0, min(output, 12))  # Constrain output to 0-12V range

    if output == 0 or output == 12:
        integral -= error  # Prevent integral windup

    prev_error = error
    return output, integral, prev_error