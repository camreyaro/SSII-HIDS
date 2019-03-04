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

def compare_hash(path, file_string, hashes_file):
    hashed_file = str(hashlib.sha256(file_string.encode()).hexdigest())
    for line in hashes_file.readlines():
        file_path = line.split(",")[0].trim()
        file_hash = line.split(",")[1].trim()

        if file_hash != hashed_file:
            logging.info("File " + path + " has been modified") #añadir totales archivos revisados y cuales han ido bien
        else:
            logging.info("File " + path + " has not been modified")

def read_path():
    created = True
    if not os.path.isfile("./hashes.txt"): #comprobar si hay archivos nuevos
        created = False

    with open("./hashes.txt", "w+") as hashes_file:
        print(hashes_file.read())
        for path in conf["paths"]:
            file_string = open(path, "r").read()

            if not created:
                hash_file(path, file_string, hashes_file)
            else:
                compare_hash(path, file_string, hashes_file)

    os.chmod(path, S_IREAD)

def main():
    path = read_path()

if __name__== "__main__":
    read_path()