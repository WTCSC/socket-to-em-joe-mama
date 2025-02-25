def log_event(message):
    """Log messages for debugging."""
    with open("chat_log.txt", "a") as log_file:
        log_file.write(message + "\n")

def handle_error(error_message):
    """Handle and print errors."""
    print(f"⚠️ Error: {error_message}")
    log_event(f"ERROR: {error_message}")
