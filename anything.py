import time
from plyer import notification

def send_alert(title, message):
    """Sends a native desktop notification."""
    notification.notify(
        title=title,
        message=message,
        app_name="Focus Buddy",
        timeout=10  # Seconds the toast stays on screen
    )

def start_pomodoro(work_mins, break_mins):
    print(f"🚀 Focus session started for {work_mins} minutes.")
    
    # Work Loop
    time.sleep(work_mins * 60)
    send_alert("Time's Up!", "Take a break! You've worked hard.")
    
    print(f"☕ Break started for {break_mins} minutes.")
    
    # Break Loop
    time.sleep(break_mins * 60)
    send_alert("Break Over", "Back to work! Let's get it done.")

if __name__ == "__main__":
    # Standard Pomodoro: 25 mins work, 5 mins break
    # (Set to 0.1 for a 6-second test run!)
    try:
        start_pomodoro(work_mins=25, break_mins=5)
    except KeyboardInterrupt:
        print("\nSession stopped by user.")