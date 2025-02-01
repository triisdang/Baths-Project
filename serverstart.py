import os
import subprocess
#   SERVER ONLY
# Define the repository URL and the directory where the project is located
REPO_URL = "https://github.com/triisdang/Baths-Project.git"
PROJECT_DIR = "Bath-Project"

def update_project():
    if not os.path.exists(PROJECT_DIR):
        # Clone the repository if the project directory does not exist
        subprocess.run(["git", "clone", REPO_URL, PROJECT_DIR])
    else:
        # Pull the latest changes if the project directory exists
        subprocess.run(["git", "-C", PROJECT_DIR, "pull"])

def run_bot():
    # Change to the project directory and run the bot
    os.chdir(PROJECT_DIR)
    subprocess.run(["python", "bot.py"])

if __name__ == "__main__":
    update_project()
    run_bot()