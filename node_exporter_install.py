import os
import sys
import stat
import requests
import subprocess
import tarfile
import shutil
import grp
from pwd import getpwnam

# This program can be modified to be a selector for selecting the arch version of the exporter
# default port to open for node_exporter - 9100

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


RELEASE_NAME = ''
RELEASE_URL = ''
DIR_NAME = ''
USR_GRP_NAME = 'node_exporter'
python_version = sys.version
IS_PYTHON2 = python_version.startswith('2')


def print_error_msg(msg):
    print(bcolors.FAIL + msg + bcolors.ENDC)


def print_ok_msg(msg):
    print(bcolors.OKBLUE + msg + bcolors.ENDC)


def call_subprocess(call_args):
    if IS_PYTHON2:
        subprocess.check_call(call_args)
    else:
        subprocess.run(call_args)


def download_node_exporter_tarball():
    print_ok_msg('Downloading the latest release')
    call_args = ['curl', '-LO', RELEASE_URL]
    print(RELEASE_URL)

    try:
        response = requests.get(
            url=RELEASE_URL)
        open(RELEASE_NAME, 'wb').write(response.content)
    except Exception as e:
        print(e.args)
        print_error_msg(
            '---Failed to download the latest release---' + bcolors.ENDC)
        sys.exit(1)


def set_latest_release_info():
    print_ok_msg('Getting latest release info')
    global RELEASE_NAME
    global RELEASE_URL
    global DIR_NAME

    response = requests.get(
        url="https://api.github.com/repos/prometheus/node_exporter/releases/latest")
    latest_releases = response.json()

    for item in latest_releases['assets']:
        if item['name'].find("linux-amd64.tar.gz") > -1:
            RELEASE_NAME = item['name']
            RELEASE_URL = item['browser_download_url']
            DIR_NAME = RELEASE_NAME.replace('.tar.gz', '')
        if RELEASE_NAME != '':
            break

    print("------------Latest node_exporter release:----------")
    print(RELEASE_NAME)


def deflate_tarball():
    # extracting all the files
    print_ok_msg('Extracting all the files now...')
    tar = tarfile.open(RELEASE_NAME, "r:gz")
    tar.extractall()
    tar.close()


def create_user():
    call_args = ['useradd', '--no-create-home',
                 '--shell', '/bin/false', 'node_exporter']
    try:
        call_subprocess(call_args)
    except Exception as ex:
        print_error_msg('Failed to add user')
        print(ex.args)
        sys.exit(1)


def check_and_create_node_exporter_user():
    print_ok_msg('Creating node_exporter user')
    try:
        user_info = getpwnam('node_exporter')
        print_ok_msg('node_exporter user already exists')
        # executing useradd command using subprocess module
    except Exception as e:
        x = e.args
        if x[0].find('name not found') > -1:
            create_user()
        else:
            print_ok_msg('node_exporter user already exists')


def copy_node_exporter_to_usr_bin_dir():
    print_ok_msg('Copying node_exporter bin to /usr/local/bin')
    try:
        shutil.copyfile(DIR_NAME+'/node_exporter',
                        '/usr/local/bin/node_exporter')
        # copyfile(DIR_NAME+'/node_exporter', os.curdir+'/node_exporter')
    except Exception as e:
        # print(e.args)
        print_error_msg('Failed to copy node_exporter')
        print_error_msg('Reason:')
        print(e.args)
        sys.exit(1)


def change_ownership_of_node_exporter():
    print_ok_msg(
        'Changing ownership of node_exporter in /usr/local/bin to node_exporter user')
    BIN_LOCATION = '/usr/local/bin/node_exporter'
    try:
        os.chown(BIN_LOCATION, getpwnam(USR_GRP_NAME)
                 [2], grp.getgrnam(USR_GRP_NAME)[2])
        perms = os.stat(BIN_LOCATION)
        os.chmod(BIN_LOCATION, perms.st_mode |
                 stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except Exception as e:
        print_error_msg('Failed to change ownership of node_exporter')
        print_error_msg('Reason:')
        print(e.args)
        sys.exit(1)


def create_node_exporter_service():
    print_ok_msg('Creating Node exporter service')
    textList = ['[Unit]',
                'Description=Node Exporter',
                'Wants=network-online.target',
                'After=network-online.target',
                '\n',
                '[Service]',
                'User=node_exporter',
                'Group=node_exporter',
                'Type=simple',
                'ExecStart=/usr/local/bin/node_exporter',
                '\n',
                '[Install]',
                'WantedBy=multi-user.target'
                ]
    outF = open("/etc/systemd/system/node_exporter.service", "w")
    for line in textList:
        outF.write(line)
        outF.write("\n")
    outF.close()


def setup_and_enable_systemctl():
    print_ok_msg('Setting up systemctl')
    call_subprocess(['systemctl', 'daemon-reload'])
    call_subprocess(['systemctl', 'start',  'node_exporter'])
    call_subprocess(['systemctl', 'enable', 'node_exporter'])
    call_subprocess(['systemctl', 'status', 'node_exporter'])
    # os.system('systemctl daemon-reload')
    # os.system('systemctl start node_exporter')
    # os.system('systemctl enable node_exporter')
    # os.system('systemctl status node_exporter')


def cleanup():
    os.remove(RELEASE_NAME)
    shutil.rmtree(DIR_NAME)


def main():
    # We will work in HOME dir
    print_ok_msg('Switching to HOME dir')
    os.chdir(os.getenv("HOME"))
    check_and_create_node_exporter_user()
    set_latest_release_info()
    download_node_exporter_tarball()
    deflate_tarball()
    copy_node_exporter_to_usr_bin_dir()
    change_ownership_of_node_exporter()
    create_node_exporter_service()
    setup_and_enable_systemctl()
    cleanup()


main()
