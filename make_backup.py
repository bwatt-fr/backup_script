#! venv/bin/python

import json
import os
import shutil
import datetime
import glob

from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient


def create_backup_archive(backup_name, config):
    """ Creation of the backup archive
    """
    os.makedirs(backup_name)
    for f in config['files']:
        if "file" in f:
            shutil.copyfile(f["file"], backup_name + f["file"])
        elif "dir" in f and "ignore" in f:
            shutil.copytree(f["dir"], backup_name + f["dir"],
                            ignore=shutil.ignore_patterns(*f["ignore"]))
        elif "dir" in f:
            shutil.copytree(f["dir"], backup_name + f["dir"])

    shutil.make_archive(backup_name, 'gztar', base_dir=backup_name)


def remove_backup_archive(backup_name):
    """ Remove the backup on local computer
    """
    shutil.rmtree(backup_name)
    os.remove(backup_name + '.tar.gz')


def retrieve_date_from_file(file_name):
    """ Create a date from a file_name of the form year_month_day.tar.gz
    """
    year, month, day = file_name.split('.')[0].split('_')[1:]
    file_date = datetime.datetime(int(year), int(month), int(day))
    return file_date

# Load of the config
with open('config.json') as my_json:
    config = json.load(my_json)

# We test if the last backup is deleted. If not, the transfer was not good, and
# we have to remove the backup on the backup server
to_delete = glob.glob('*.tar.gz')
if to_delete:
    os.remove(to_delete[0])
    shutil.rmtree(to_delete[0].split('.')[0])

# The backups are named with the date
now = datetime.datetime.now()
backup_name = ('backup_{year}_{month}_{day}'
               .format(year=now.year, month=format(now.month, '02'),
                       day=format(now.day, '02')))

# Initialization of the connection
ssh = SSHClient()
ssh.set_missing_host_key_policy(AutoAddPolicy())
ssh.connect(config['host'], username=config['user'],
            password=config['password'], key_filename=config['key_filename'])

# If there is a backup to delete, we do it before searching the other backups
# (because as she is corrupt, we have to replace it)
if to_delete:
    command_rm_to_delete = 'rm Backup/' + to_delete[0]
    ssh.exec_command(command_rm_to_delete)

# We search the number of backup
command = 'ls ' + config['dir_dest']
(stdin, stdout, stderr) = ssh.exec_command(command)
backups = [line.replace('\n', '') for line in stdout.readlines()]

if len(backups) == 0:
    # If there is no backup, we put one
    scp = SCPClient(ssh.get_transport())
    create_backup_archive(backup_name, config)
    scp.put(backup_name + '.tar.gz', config['dir_dest'])
    scp.close()
    remove_backup_archive(now)

elif len(backups) in range(1, 5):
    newer_file_date = retrieve_date_from_file(backups[-1])
    if (now - newer_file_date).days >= config['days_between_backup']:
        # Copy of the file
        scp = SCPClient(ssh.get_transport())
        create_backup_archive(backup_name, config)
        scp.put(backup_name + '.tar.gz', config['dir_dest'])
        scp.close()
        remove_backup_archive(now)

        # Remove of the old backups
        if len(backups) == 4:
            older_file_date = retrieve_date_from_file(backups[0])
            second_older_file_date = retrieve_date_from_file(backups[1])

            # We always keep an old backup (30 days before the second oldest by
            # default)
            if ((second_older_file_date - older_file_date).days >
                    config['days_between_old_backup']):
                command_rm = 'rm {dir_dest}/{file}'.format(
                                dir_dest=config['dir_dest'],
                                file=older_file)
            else:
                command_rm = 'rm {dir_dest}/{file}'.format(
                                dir_dest=config['dir_dest'],
                                file=second_older_file)
            ssh.exec_command(command_rm)

# We close the connection
ssh.close()
