from concurrent.futures import Executor
from datetime import datetime, timedelta
from dotenv import load_dotenv, set_key
from pathlib import Path
import os

# HELPER: Checks if env file exists, if not, prompts user for required variables
def ensure_env_file():
    # Check if .env file exists
    if Path(".env").exists():
        return
    
    print("No .env file found. Let's set up your configuration:")
    
    config = {}
    
    print("\nLogin Credentials:")
    config["EMAIL"]             = input("Email address: ").strip()
    config["APP_PASSWORD"]      = input("App-Specific Password: ").strip()
    config["FOLDER"]            = input("Folder to scan for TLDR emails: ").strip()

    print("\nSend/Recieve Email Settings:")
    config["FROM_ALIAS"]        = input(f"Email that will send the TLDR Pro newsletter(default: {config['EMAIL']}): ").strip() or config["EMAIL"]
    config["TO_ALIAS"]          = input("Email address to receive the TLDR Pro newsletter: ").strip() or config["EMAIL"]
        
    print("\nIMAP/SMTP Settings:")
    config["IMAP_HOST"]         = input("IMAP host: ").strip()
    config["IMAP_PORT"]         = input("IMAP port (default: 993): ").strip() or "993"
    config["SMTP_HOST"]         = input("SMTP host: ").strip()
    config["SMTP_PORT"]         = input("SMTP port (default: 587): ").strip() or "587"

    print("\nAdditional Settings:")
    config["EXECUTION_HOUR"]    = input("Hour to run the executor(24-hour format): ").strip()
    
    # Write to .env
    print(f"\nCreating .env file...")
    for key, value in config.items():
        set_key(".env", key, value)
    
    print(f".env file created successfully!\n")

# GETTER: Grabs settings and returns a simple object
def get_settings():
    # Grabbing environment variables or if none exist, prompts user for required variables
    ensure_env_file()
    load_dotenv()
    
    EMAIL           = os.getenv("EMAIL")                    # Email address to login with
    APP_PASSWORD    = os.getenv("APP_PASSWORD")             # Email app-specific password
    FOLDER          = os.getenv("FOLDER")                   # Folder to scan for TLDR emails
    FROM_ALIAS      = os.getenv("FROM_ALIAS")               # Email address that will send the TLDR Pro newsletter
    TO_ALIAS        = os.getenv("TO_ALIAS")                 # Email address to receive the TLDR Pro newsletter
    IMAP_HOST       = os.getenv("IMAP_HOST")                # IMAP host
    IMAP_PORT       = int(os.getenv("IMAP_PORT", "993"))    # IMAP port
    SMTP_HOST       = os.getenv("SMTP_HOST")                # SMTP host
    SMTP_PORT       = int(os.getenv("SMTP_PORT", "587"))    # SMTP port
    EXECUTION_HOUR  = os.getenv("EXECUTION_HOUR")           # Hour to run the program


    if not all([EMAIL, APP_PASSWORD, FOLDER, FROM_ALIAS, TO_ALIAS, IMAP_HOST, SMTP_HOST, EXECUTION_HOUR]):
        raise ValueError("Missing required environment variables. Required variables: EMAIL\nAPP_PASSWORD\nFOLDER\nFROM_ALIAS\nTO_ALIAS\nIMAP_HOST\nSMTP_HOST\nEXECUTION_HOUR")
    
    # Settings object to hold everythign and return
    class Settings:
        email           = EMAIL
        app_password    = APP_PASSWORD
        folder          = FOLDER
        from_alias      = FROM_ALIAS
        to_alias        = TO_ALIAS
        imap_host       = IMAP_HOST
        imap_port       = IMAP_PORT
        smtp_host       = SMTP_HOST
        smtp_port       = SMTP_PORT
        execution_hour  = EXECUTION_HOUR
    
    return Settings() # By John Michael