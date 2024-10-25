import os
import readline
import glob
from github import Github # type: ignore
import getpass
import threading
import time

from util.constants import (
    TOKEN, MAIN_BRANCH, LEMONS_FILE, REPO_OWNER, 
    REPO_NAME, branches_lock, seen_branches
)
from util.colors import *
from octo.repo import Repo

banner = '''
            ________          __         _________  ________   __   
            \_____  \   _____/  |_  ____ \_   ___ \ \_____  \_/  |_ 
             /   |   \_/ ___\   __\/  _ \/    \  \/  /  ____/\   __\\
            /    |    \  \___|  | (  <_> )     \____/       \ |  |  
            \_______  /\___  >__|  \____/ \______  /\_______ \|__|  
                    \/     \/                    \/         \/      

'''

# Entry point of the script
if __name__ == "__main__":

    print(f"{BOLD}{MAGENTA}{banner}{RESET}")

    try:
        octo = Repo()

        # List branches at init
        branches_info = octo.list_branches()
        for branch_info in branches_info:
            branch_name, last_modified = branch_info
            print(f"  - {branch_name} (Last checkin: {last_modified})")

        # Enter the pseudo-shell
        octo.run()

    except Exception as e:
        print(f"[-] Error: {str(e)}")
