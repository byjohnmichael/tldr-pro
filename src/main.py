from settings import get_settings
import time
import os

# Main Function
def main():
    os.system("clear")
    print("TLDR Pro")
    print("=" * 50)
    time.sleep(1)

    print("\nLoading settings...")
    time.sleep(0.5)
    settings = get_settings()
    if settings:
        print("Settings loaded successfully!")
    else:
        print("Failed to load settings!")
        return
    
    # TODO: Implement workflow steps
    # 1. Connect to IMAP and fetch newsletters
    # 2. Parse newsletters
    # 3. Merge and deduplicate
    # 4. Select best items
    # 5. Render email
    # 6. Send via SMTP
    # 7. Cleanup (delete/archive)

# Entry Point
if __name__ == "__main__":
    main() # By John Michael