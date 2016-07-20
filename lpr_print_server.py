from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import time
import threading
import subprocess
import argparse
import logging

parser = argparse.ArgumentParser()
parser.add_argument('--path', required=True)
parser.add_argument('--printer', required=True)
parser.add_argument('--lpr', required=False)
parser.add_argument('--min_interval_seconds', required=False)
args = parser.parse_args()

config = {}
config['path'] = os.path.expanduser(args.path)
config['printer'] = args.printer
config['lpr'] = args.lpr or 'lpr'
config['extensions'] = set(('pdf','doc'))
config['min_interval_seconds'] = args.min_interval_seconds or 5

def intercept_error(fn):
    from functools import wraps
    @wraps(fn)
    def error_interceptor(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except BaseException as e:
            logging.exception("error intercepted")
    return error_interceptor

class PrintServerFileEventHandler(FileSystemEventHandler):
    def __init__(self, config):
        self.config = config
        self.monitor = {}
        self.monitorLock = threading.Lock()
        self.thread = threading.Thread(target=PrintServerFileEventHandler.thread_worker, args=(self,))
        self.thread.start()
        self.log = logging.getLogger('PrintServerFileEventHandler')

    @staticmethod
    def thread_worker(a_self):
        a_self.self_thread_worker()

    def self_thread_worker(self):
        # worker thread started
        while True:
            # iterating all items in monitor map
            self.monitorLock.acquire()
            try:
                # filtering items and print items that were changed
                items_to_print = filter(lambda (k,v): v + self.config['min_interval_seconds'] < time.time() , self.monitor.iteritems())
            finally:
                self.monitorLock.release()
            for item_to_print, _ in items_to_print:
                self.print_item(item_to_print)
                del self.monitor[item_to_print]
            time.sleep(3)

    @intercept_error
    def print_item(self, item_to_print):
        cmd_line_args = [self.config['lpr'], '-P', self.config['printer'], item_to_print]
        self.log.info('Printing %s. Command line: %s' % (item_to_print, cmd_line_args))
        subprocess.call(cmd_line_args)

    def add_to_filemap(self, path):
        # checking if this filename has supported extension
        extensions = self.config['extensions']
        _, extension = os.path.splitext(path)
        if not extension or len(extension) == 0 or extension[1:] not in extensions:
            # extension is empty or was not found in supported extension set. Skipping
            return
        # extension is supported. Adding file to the map
        self.monitorLock.acquire()
        try:
            self.monitor[path] = time.time()
        finally:
            self.monitorLock.release()

    def remove_from_filemap(self, path):
        if path in self.monitor:
            self.monitorLock.acquire()
            try:
                del self.monitor[path]
            finally:
                self.monitorLock.release()

    @intercept_error
    def on_created(self, event):
        # registered event that a file is created. Adding this file to the map
        # of files that should be polled/checked
        if not event.is_directory:
            self.add_to_filemap(event.src_path)

    @intercept_error
    def on_modified(self, event):
        # behave the same as if the file was created
        self.on_created(event)

    @intercept_error
    def on_moved(self, event):
        if not event.is_directory:
            self.add_to_filemap(event.src_path)
            self.add_to_filemap(event.dest_path)

    @intercept_error
    def on_deleted(self, event):
        self.remove_from_filemap(event.src_path)

if __name__ == '__main__':
    logging.basicConfig(level='INFO')

    # creating observer object that listens for any changes in the given folder
    event_handler = PrintServerFileEventHandler(config)
    observer = Observer()
    observer.schedule(event_handler, config['path'], recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

