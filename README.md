# lpr_print_server.py

**_NOTE: this software is still work in progress and does not work yet as described below_**

Python background utility/daemon that acts as a printing server. Its main purpose is to print various documents directly from different devices, i.e. other computers or smartphones.

With this software you do not need to configure your other devices and connect them to your printer. Just run print server on one host and easily share files (i.e. using Dropbox, Box, Google Drive or any other cloud provider) to transmit them directly to print server which will send it automatically to the printer.

## TODO:

* Test communication with lpr from unprivileged account
* Persist pair (filename,timestamp) to avoid multiple printing of the same file (removal of the file may not be the best idea because cloud providers may re-synchronize the file and/or we may not have write access to remove this file)

## What is the exact usage scenario?

Let's assume that you have multiple computers/devices in your internal network and only one of them (running Linux because this sofware is designed for Linux) is connected to the local printer and has proper drivers installed (let's call it A).

You have lpr_print_server running on A and configured any folder (i.e. /var/clouddata/print) folder as an input folder which will be scanned for files to be printed.

However, you would like to print a PDF document from device B (it could be either a computer or smartphone, it does not matter). All you need to do is to upload this document to your cloud provider to a dedicated folder, let's call it print.

Then your cloud provider automatically synchronizes this document between your machines, also downloading it to your machine A to folder /var/clouddata/print. lpr_print_server recognizes the files and starts printing.

That's it! No more hassle with drivers, various operating systems, printing from smartphone etc.

## Nice! So how to install it?

This software runs on Linux, because it needs lpr printing utility to be installed.

Here are the steps to install and run this print server:

* install [Python 2.7 or newer (but not 3.x!)](https://www.python.org/downloads/)
* install [pip (python software management tool)](https://pypi.python.org/pypi/pip)
* install python package watchdog: `pip install watchdog`
* clone this repository to the directory of your choice: `git clone https://github.com/mwilkowski80/lpr_print_server`
* configure upstart daemon to run this utility on system startup, i.e.:

        # /etc/init/lpr-print-server.conf
        # lpr print server service

        start on (starting network-interface
                  or starting network-manager
                  or starting networking)

        respawn
        setuid mw

        exec /usr/bin/python /home/mw/PyCharmProjects/lpr_print_server/lpr_print_server.py --path ~/Dropbox/print --printer hp_LaserJet_1005 2>&1 >>/var/log/lpr_print_server.log

* run it: sudo service lpr-print-server start
