import time
import schedule
import pyautogui
import os
from urllib.parse import quote
import threading
import sys
import shlex

def send_whatsapp_message(phone, message):
    print(f"\n[Scheduler] Sending message to {phone}...")
    try:
        # Launching the WhatsApp application with pre-filled phone and text
        os.startfile(f"whatsapp://send?phone={phone}&text={quote(message)}")
        
        # We need to wait for the app to come to the foreground and load the chat
        time.sleep(10)
        
        # Press Enter to send the message
        pyautogui.press('enter')
        print(f"[Scheduler] Message to {phone} successfully executed.")
    except Exception as e:
        print(f"\n[Scheduler] Failed to send message to {phone}. Error: {e}")
    
    # We return CancelJob so this specific job doesn't repeat every day at this time
    return schedule.CancelJob

def job_runner():
    # Background thread loop to run any scheduled tasks
    while True:
        schedule.run_pending()
        time.sleep(1)

def main():
    print("=" * 50)
    print("   WhatsApp CLI Scheduler Started")
    print("=" * 50)
    print("Available Commands:")
    print("  add [phone] [\"message\"] [HH:MM]   - Schedule a message (24-hour format)")
    print("  list                            - List all pending scheduled messages")
    print("  exit                            - Exit the program")
    print("Example: add +919876543210 \"Hello!\" 14:30\n")
    
    # Start the background scheduler thread
    t = threading.Thread(target=job_runner, daemon=True)
    t.start()
    
    while True:
        try:
            cmd_input = input("wp-scheduler> ").strip()
            if not cmd_input:
                continue
                
            parts = cmd_input.split(" ", 1)
            cmd = parts[0].lower()
            
            if cmd == "exit":
                print("Exiting scheduler...")
                break
            elif cmd == "list":
                jobs = schedule.get_jobs()
                if not jobs:
                    print("No pending scheduled messages.")
                else:
                    print("Pending messages:")
                    for i, job in enumerate(jobs, 1):
                        print(f"  {i}. {job}")
            elif cmd == "add":
                if len(parts) < 2:
                    print("Usage: add [phone] [\"message\"] [HH:MM]")
                    continue
                
                try:
                    args = shlex.split(parts[1])
                    if len(args) != 3:
                        print("Error: Provide exactly three arguments.")
                        print("Example: add +919876543210 \"Hello my friend\" 14:30")
                        continue
                    
                    phone = args[0]
                    message = args[1]
                    send_time = args[2]
                    
                    # Schedule it securely
                    schedule.every().day.at(send_time).do(send_whatsapp_message, phone, message)
                    print(f"Success: Message to {phone} scheduled for {send_time}.")
                except Exception as e:
                    print(f"Error parsing arguments: {e}. Check your quotes around the message.")
            else:
                print("Unknown command. Available commands: add, list, exit")
        except KeyboardInterrupt:
            print("\nExiting scheduler. Goodbye.")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
