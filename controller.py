import threading
import sys
import requests
import time
import datetime
import flask
from pydualsense import *

# Function to map values
def _map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def print_normalized_controller_status(left_stick_x, left_stick_y, right_stick_x, right_stick_y, l2, r2, last_post_time):
    # Move cursor up 8 lines
    sys.stdout.write('\x1b[8A')
    
    sys.stdout.write('\rLeftstick X: {:>6}\n'.format(left_stick_x))
    sys.stdout.write('\rLeftstick Y: {:>6}\n'.format(left_stick_y))
    sys.stdout.write('\rRightstick X: {:>6}\n'.format(right_stick_x))
    sys.stdout.write('\rRightstick Y: {:>6}\n'.format(right_stick_y))
    sys.stdout.write('\rL2: {:>6}\n'.format(l2))
    sys.stdout.write('\rR2: {:>6}\n'.format(r2))
    sys.stdout.write('\rLast post: {:>6}\n'.format(last_post_time))

    sys.stdout.flush()  # Ensure it prints before the next loop

def print_controller_status(left_stick_x, left_stick_y, right_stick_x, right_stick_y, l2, r2):
    # Move cursor up 6 lines
    sys.stdout.write('\x1b[6A')
    
    sys.stdout.write('\rLeftstick X: {:>6}\n'.format(left_stick_x))
    sys.stdout.write('\rLeftstick Y: {:>6}\n'.format(left_stick_y))
    sys.stdout.write('\rRightstick X: {:>6}\n'.format(right_stick_x))
    sys.stdout.write('\rRightstick Y: {:>6}\n'.format(right_stick_y))
    sys.stdout.write('\rL2: {:>6}\n'.format(l2))
    sys.stdout.write('\rR2: {:>6}\n'.format(r2))
    
    sys.stdout.flush()  # Ensure it prints before the next loop

class ControllerThread(threading.Thread):
    def __init__(self, dualsense, shared_data, lock, stop_event):
        super().__init__()
        self.dualsense = dualsense
        self.shared_data = shared_data
        self.lock = lock
        self.stop_event = stop_event

    def run(self):
        while not self.stop_event.is_set() and not self.dualsense.state.circle:
            with self.lock:
                # Map controller values to servo angles
                self.shared_data['left_stick_x'] = _map(self.dualsense.state.LX, -128, 127, 0, 180)  # Rotate base
                self.shared_data['left_stick_y'] = _map(self.dualsense.state.LY, -128, 127, 15, 165)  # Move shoulder up and down
                self.shared_data['right_stick_x'] = _map(self.dualsense.state.RX, -128, 127, 0, 180)  # Rotate wrist
                self.shared_data['right_stick_y'] = _map(self.dualsense.state.RY, -128, 127, 0, 180)  # Move elbow up and down
                self.shared_data['l2'] = _map(self.dualsense.state.L2, 0, 255, 0, 180)  # Rotate gripper
                self.shared_data['r2'] = _map(self.dualsense.state.R2, 0, 255, 10, 73)  # Close / Open gripper
            time.sleep(0.01)  # Small delay to reduce CPU usage
        self.stop_event.set()  # Signal other threads to stop

class SenderThread(threading.Thread):
    def __init__(self, arduino_url, shared_data, lock, stop_event):
        super().__init__()
        self.arduino_url = arduino_url
        self.shared_data = shared_data
        self.lock = lock
        self.stop_event = stop_event
        self.last_post_time = time.time()

    def run(self):
        while not self.stop_event.is_set():
            with self.lock:
                payload = {
                    "base": int(self.shared_data['left_stick_x']),
                    "shoulder": int(self.shared_data['left_stick_y']),
                    "wrist": int(self.shared_data['right_stick_x']),
                    "elbow": int(self.shared_data['right_stick_y']),
                    "wristRot": int(self.shared_data['l2']),
                    "gripper": int(self.shared_data['r2'])
                }
            
            requests.post(f"{self.arduino_url}/update", json=payload)
            
            with self.lock:
                self.shared_data['formatted_time'] = datetime.datetime.now().strftime("%H:%M:%S:%f")
                
            
            time.sleep(0.5)  # Delay to reduce CPU usage

class PrinterThread(threading.Thread):
    def __init__(self, shared_data, lock, stop_event):
        super().__init__()
        self.shared_data = shared_data
        self.lock = lock
        self.stop_event = stop_event

    def run(self):
        while not self.stop_event.is_set():
            with self.lock:
                print_normalized_controller_status(
                    self.shared_data['left_stick_x'],
                    self.shared_data['left_stick_y'],
                    self.shared_data['right_stick_x'],
                    self.shared_data['right_stick_y'],
                    self.shared_data['l2'],
                    self.shared_data['r2'],
                    self.shared_data['formatted_time']
                )
            time.sleep(0.1)  # Update the print every 100ms

# Main function
if __name__ == "__main__":
    dualsense = pydualsense()
    dualsense.init()

    arduino_url = "http://192.168.1.19:6942"

    # Clears the terminal
    print("\033c")


    shared_data = {
        'left_stick_x': 0,
        'left_stick_y': 0,
        'right_stick_x': 0,
        'right_stick_y': 0,
        'l2': 0,
        'r2': 0,
        'formatted_time': datetime.datetime.fromtimestamp(time.time()).strftime("%H:%M:%S:%f"),
    }
    
    lock = threading.Lock()
    stop_event = threading.Event()

    controller_thread = ControllerThread(dualsense, shared_data, lock, stop_event)
    sender_thread = SenderThread(arduino_url, shared_data, lock, stop_event)
    printer_thread = PrinterThread(shared_data, lock, stop_event)

    controller_thread.start()
    sender_thread.start()
    #printer_thread.start()

    controller_thread.join()
    stop_event.set()  # Signals all threads to stop (stops onced circle is pressed)
    
    sender_thread.join()
    #printer_thread.join()
    
    dualsense.close()
