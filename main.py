import pyvisa
import time
import os
from datetime import datetime
import signal
import sys
from pid_utils import PT100TempLogger, save_data, pid_control
import serial.tools.list_ports

def signal_handler(signum, frame):
    """Handle keyboard interrupts and system signals"""
    print("\nSignal received. Saving data and shutting down...")
    raise KeyboardInterrupt

def control_power_supply_with_temp_monitoring():
    # Initialize signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder = f'measurements_{timestamp}'
    os.makedirs(output_folder, exist_ok=True)
    
    temp_logger = None
    ps = None
    rm = None
    data = []
    
    TARGET_TEMPERATURE = 20.0
    reading_counter = 0
    target_reached = False
    
    # PID parameters
    Kp, Ki, Kd = 0.65, 0.01, 0.05
    integral = 0
    prev_error = 0
    
    try:
        port = next((port.device for port in serial.tools.list_ports.comports() if 'ch340' in port.description.lower()), None)   # write the name of your arduino device name
        print(f"Arduino device port: {port}" if port else "No CH340 device found")
        temp_logger = PT100TempLogger(port)

        port2 = next((p.device for p in serial.tools.list_ports.comports() if 'PL2303GT' in str(p.description)), None)   # write the name of your power supply device name
        print(f"Power supply port: {port2}" if port2 else "No power supply device found")
        rm = pyvisa.ResourceManager()
        ps = rm.open_resource(port2)
        
        ps.write('*RST')
        ps.write('SYST:REM')
        
        target_voltage = 6.0  # To limit power supply
        rate = 0.05
        duration = 120
        
        voltage_step = rate
        current_voltage = 0
        start_time = time.time()
        elapsed_time = 0
        
        while elapsed_time < duration:
            temperature = temp_logger.read_temperature()

            if not target_reached:
                if current_voltage < target_voltage:
                    current_voltage = min(current_voltage + voltage_step, target_voltage)
            else:
                current_voltage, integral, prev_error = pid_control(
                    TARGET_TEMPERATURE, temperature, Kp, Ki, Kd, integral, prev_error
                )

            ps.write(f'VOLT {current_voltage:.3f}')
            ps.write('OUTP ON')
            
            actual_voltage = float(ps.query('MEAS:VOLT?'))
            actual_current = float(ps.query('MEAS:CURR?'))
            timestamp = datetime.now()
            
            data.append({
                'Timestamp': timestamp,
                'Set_Voltage': current_voltage,
                'Measured_Voltage': actual_voltage,
                'Measured_Current': actual_current,
                'Temperature': temperature
            })
            
            print(f'\nElapsed time: {elapsed_time:.1f}s')
            print(f'Time: {timestamp.strftime("%H:%M:%S")}')
            print(f'Set Voltage: {current_voltage:.3f}V')
            print(f'Measured Voltage: {actual_voltage:.3f}V')
            print(f'Measured Current: {actual_current:.3f}A')
            print(f'Temperature: {temperature:.2f}°C' if temperature is not None else 'Temperature: Reading Error')
            print('-' * 50)
            
            reading_counter += 1
            if reading_counter > 3 and temperature is not None:
                if abs(temperature - TARGET_TEMPERATURE) <= 0.1:
                    if not target_reached:
                        print(f"\nTarget temperature {TARGET_TEMPERATURE}°C reached! Switching to PID control.")
                        target_reached = True
            
            time.sleep(1)
            elapsed_time = time.time() - start_time

        # Normal completion - save data and create plots
        excel_file, plot_file = save_data(data, output_folder)
        print(f"\nMeasurement complete!")
        print(f"Data saved to: {excel_file}")
        print(f"Plots saved to: {plot_file}")
        
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
        excel_file, plot_file = save_data(data, output_folder, error=True)
        print(f"Partial data saved to: {excel_file}")
        print(f"Partial plots saved to: {plot_file}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        excel_file, plot_file = save_data(data, output_folder, error=True)
        print(f"Partial data saved to: {excel_file}")
        print(f"Partial plots saved to: {plot_file}")
    
    finally:
        # Cleanup resources
        if ps:
            try:
                ps.write('OUTP OFF')
                ps.close()
            except:
                pass
        
        if rm:
            try:
                rm.close()
            except:
                pass
            
        if temp_logger:
            try:
                del temp_logger
            except:
                pass

if __name__ == "__main__":
    control_power_supply_with_temp_monitoring()