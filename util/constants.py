import threading

# Global variables (replace with your repo details)
TOKEN       = "YOUR_PAT_TOKEN"
REPO_OWNER  = "YOUR_REPO_OWNER_USERNAME"
REPO_NAME   = "OctoC2t"
LEMONS_FILE = "lemons.txt"
MAIN_BRANCH = "main"
CURRENT_BRANCH = "main"
POLLING_INTERVAL = 3        # GitHub rate limits so be careful with this depending on how many octos you have

# Global to store seen branches and threading lock
seen_branches = set()
branches_lock = threading.Lock()
