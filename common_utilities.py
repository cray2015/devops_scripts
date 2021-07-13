from subprocess import check_call, CalledProcessError
import os

check_call(['apt-get', 'install', '-y', 'zip unzip glances htop'], stdout=open(os.devnull,'wb'))