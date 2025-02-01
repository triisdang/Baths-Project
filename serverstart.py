import os
import subprocess
import time

# Define the repository URL and the directory where the project is located
REPO_URL = "https://github.com/triisdang/Baths-Project.git"
PROJECT_DIR = "Bath-Project"
CHECK_INTERVAL = 300  # Check for updates every 5 minutes

def update_project():
    if not os.path.exists(PROJECT_DIR):
        # Clone the repository if the project directory does not exist
        subprocess.run(["git", "clone", REPO_URL, PROJECT_DIR])
    else:
        # Pull the latest changes if the project directory exists
        result = subprocess.run(["git", "-C", PROJECT_DIR, "pull"], capture_output=True, text=True)
        if "Already up to date." not in result.stdout:
            return True  # Update detected
    return False  # No update detected

def run_bot():
    # Change to the project directory and run the bot
    os.chdir(PROJECT_DIR)
    return subprocess.Popen(["python", "bot.py"])

if __name__ == "__main__":
    bot_process = run_bot()
    try:
        while True:
            time.sleep(CHECK_INTERVAL)
            if update_project():
                print("Update detected, restarting bot...")
                bot_process.terminate()
                bot_process.wait()
                bot_process = run_bot()
    except KeyboardInterrupt:
        print("Shutting down bot...")
        bot_process.terminate()
        bot_process.wait()