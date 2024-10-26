```
        ________          __         _________  ________   __   
        \_____  \   _____/  |_  ____ \_   ___ \ \_____  \_/  |_ 
         /   |   \_/ ___\   __\/  _ \/    \  \/  /  ____/\   __\
        /    |    \  \___|  | (  <_> )     \____/       \ |  |  
        \_______  /\___  >__|  \____/ \______  /\_______ \|__|  
                \/     \/                    \/         \/      
```
# OctoC2t
Simple C2 using GitHub repository as comms channel. This is just a PoC to show how it is possible to use pretty much any channel you can think of to send & receive commands.

I decided not to release agent code for a few reasons. First, it's great practice to make your own agent. Second, I'm still actively using my agent and don't want it to get signatured too soon :) - However, there are clear instructions on how to code your own below with whatever language you like.

The code is really simple so you should be able to parse through it and craft an agent. It's not meant to be a "serious" C2!

P.S. - If you actually wanna tweak this and use it yourself in an engagement, I recommend using a repo in GitHub Enterprise that's private to your org.

## Installation
- Download & install dependencies
```sh
git clone https://github.com/deletehead/OctoC2t && cd OctoC2t
pip3 install -r requirements.txt
```
- Update `util/constants.py` with your PAT, username, etc.
- Run it!
```sh
python3 octoc2t.py
```

## Agents
Here's how you can build your agents (I call them "octos"):
- Interact with GitHub and handle authentication (e.g., .NET has [OctoKit](https://github.com/octokit))
- Functions:
  - Get task ("tentacle"): Get `lemons.txt` and check if it's a tentacle task/command. If it is, process the command. If not, continue.
  - Send results: Send agent results to `<OCTO-NAME>/file-results.txt`. I name files like: `TIMESTAMP-PID-TentacleNumber.txt`.
    - *IMPORTANT*: The `lemons.txt` file should then be updated to be the new file name. OctoC2t will look for a new file name to print it to the console.
  - Process tentacle command & send results. Here are the functions that the server uses (you can add/remove as needed):
    - `ls`: List CWD
    - `cd`: Change working directory
    - `cmd`: Run command with `cmd.exe`
    - `powershell`: Run command with `powershell.exe`
    - `ex-asm`: Download a file from `srv/NetAssembly.exe` and run it reflectively in memory
    - `download`: Download file from `srv/`
    - `upload`: Upload a file to `<OCTO-NAME>/uploads/` to exfiltrate it
- Initial check-in:
  - Create a new branch (unless one for that agent is created) & set the context to this new branch for future operations
  - Get the initial command (AKA "tentacle") from `lemons.txt` and process/run it (like a `whoami`)
  - Whenever a tentacle command is process, post the results in a new file in `<OCTO-NAME>/`
  - Start a `while true` loop to get the contents of `lemons.txt`.
    - If it's a tentacle command, run it, post results, and update `lemons.txt` with the results file name
    - If `lemons.txt` is a results file name, continue (cause that means the server hasn't sent new commands)

## Usage
- Set up `constants.py` with your username, repo name, and [PAT](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- Craft an agent and run it. You should see it check in.
- Switch to a specific octo agent with: `octo <octo_name>`
- Run commands with `cmd` or `powershell`, host files in `srv/` and download or run reflectively in memory with `ex-asm`

## Limitations
- The shell needs some loving. The shell history, etc. needs addressed but it's not a huge deal imo.
- This works great with only a couple active octos. If you want to use more, adjust the polling interval so you don't get rate limited.
- Remember, this is just a PoC to show how you can easily whip up a C2 using an existing service.

## Why `lemons.txt`?
IDK. I just started tagging random files with `Every. Villain. Is. LEMONS!` and now I use it for like everything.
