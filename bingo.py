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

def print_normalized_device_status(left_stick_x, left_stick_y, right_stick_x, right_stick_y, l2, r2, last_post_time, sent_data):
    # Move cursor up 8 lines
    sys.stdout.write('\x1b[8A')
    
    sys.stdout.write('\rLeftstick X: {:>6}\n'.format(left_stick_x))
    sys.stdout.write('\rLeftstick Y: {:>6}\n'.format(left_stick_y))
    sys.stdout.write('\rRightstick X: {:>6}\n'.format(right_stick_x))
    sys.stdout.write('\rRightstick Y: {:>6}\n'.format(right_stick_y))
    sys.stdout.write('\rL2: {:>6}\n'.format(l2))
    sys.stdout.write('\rR2: {:>6}\n'.format(r2))
    sys.stdout.write('\rLast post: {:>6}\n'.format(last_post_time))
    sys.stdout.write('\rSent data: {:>6}\n'.format(sent_data))

    sys.stdout.flush()  # Ensure it prints before the next loop

def print_device_status(left_stick_x, left_stick_y, right_stick_x, right_stick_y, l2, r2):
    # Move cursor up 6 lines
    sys.stdout.write('\x1b[6A')
    
    sys.stdout.write('\rLeftstick X: {:>6}\n'.format(left_stick_x))
    sys.stdout.write('\rLeftstick Y: {:>6}\n'.format(left_stick_y))
    sys.stdout.write('\rRightstick X: {:>6}\n'.format(right_stick_x))
    sys.stdout.write('\rRightstick Y: {:>6}\n'.format(right_stick_y))
    sys.stdout.write('\rL2: {:>6}\n'.format(l2))
    sys.stdout.write('\rR2: {:>6}\n'.format(r2))
    
    sys.stdout.flush()  # Ensure it prints before the next loop
    
class SenderThread(threading.Thread):
    def __init__(self, sender_url, shared_data, lock, stop_event):
        super().__init__()
        self.sender_url = sender_url
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
            
            requests.post(f"{self.sender_url}/update", json=payload)
            
            with self.lock:
                self.shared_data['formatted_time'] = datetime.datetime.now().strftime("%H:%M:%S:%f")
                
            
            time.sleep(0.5)  # Delay to reduce CPU usage

class ReceiverThread(threading.Thread):
    def __init__(self, receiver_url, shared_data, lock, stop_event):
        super().__init__()
        self.arduino_url = receiver_url
        self.shared_data = shared_data
        self.lock = lock
        self.stop_event = stop_event

    def run(self):
        while not self.stop_event.is_set():
            with self.lock:
                self.shared_data['sent_data'] = requests.get(f"{self.arduino_url}/data").json()
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
                print_normalized_device_status(
                    self.shared_data['left_stick_x'],
                    self.shared_data['left_stick_y'],
                    self.shared_data['right_stick_x'],
                    self.shared_data['right_stick_y'],
                    self.shared_data['l2'],
                    self.shared_data['r2'],
                    self.shared_data['formatted_time'],
                    self.shared_data['sent_data']
                )
            time.sleep(0.1)  # Update the print every 100ms

# Main function
if __name__ == "__main__":
    dualsense = pydualsense()
    dualsense.init()

    # Url for robot arm
    sender_url = "http://172.20.10.13:6942"
    
    # Url for receiving data from sensors (endpoint)
    receiver_url = "http://172.20.10.13:6969"

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
        'sent_data': ""
    }
    
    lock = threading.Lock()
    stop_event = threading.Event()

    sender_thread = SenderThread(sender_url, shared_data, lock, stop_event)
    printer_thread = PrinterThread(shared_data, lock, stop_event)
    receiver_thread = ReceiverThread(receiver_url, shared_data, lock, stop_event)

    receiver_thread.start()
    sender_thread.start()
    printer_thread.start()

    receiver_thread.join()
    stop_event.set() # Signals all threads to stop once receiver thread is done
    
    sender_thread.join()
    printer_thread.join()
    
    dualsense.close()
