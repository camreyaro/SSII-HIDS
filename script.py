import hashlib
import os
from apscheduler.schedulers.background import BackgroundScheduler
import json
from conf import conf
import logging
from stat import S_IREAD

def hash_file(path, file_string, hashes_file):
    hashed_file = str(hashlib.sha256(file_string.encode()).hexdigest())
    hashes_file.write(path + ", " + hashed_file + "\n")

def compare_hash(path):
    pass

def read_path():
    with open("./hashes.txt", "w") as hashes_file:
        for path in conf["paths"]:
            file_string = open(path, "r").read()
            hash_file(path, file_string, hashes_file)
    
    os.chmod(path, S_IREAD)

def main():
    path = read_path()

if __name__== "__main__":
    read_path()