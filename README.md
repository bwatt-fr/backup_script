# Goal

This script is used to make my personnal backups. Feel free to use it, or to inspire yourself.

# Usage

You must first initialize a virtual environment with the requirements.txt. You have then to complete the config.json file, with all the informations connections. You also have to say what directories and files you want to backup. It's possible to ignore some files or directories inside a directory with the flag exchange. You can also configure the frequancy of backups: I make it all three days, with another 30 days before. Finally, you have to launch your script with a cron one time a day (or more often if you want).

# Error

If the there is a problem during the transfer (no internet, computer closed), the backup is corrupted. It will be deleted at the launch of the script the day after.
