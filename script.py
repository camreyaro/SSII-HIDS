import hashlib
import os
from apscheduler.schedulers.background import BackgroundScheduler
import json
from conf import conf
import logging
from stat import S_IREAD

checked_files = 0
modified_files = 0
not_modified_files = 0

def hash_file(path, file_string, hashes_file):
    hashed_file = str(hashlib.sha256(file_string.encode()).hexdigest())
    hashes_file.write(path + ", " + hashed_file + "\n")

def compare_hash(path, file_string, hashes_file):
    hashed_file = str(hashlib.sha256(file_string.encode()).hexdigest())
    global checked_files
    global modified_files
    global not_modified_files
    
    for line in hashes_file.readlines():
        file_path = line.split(",")[0].strip()
        file_hash = line.split(",")[1].strip()

        if file_path == path:
            checked_files += 1
            if file_hash != hashed_file:
                modified_files += 1
                logging.error("File " + path + " has been modified") #añadir totales archivos revisados y cuales han ido bien
            else:
                not_modified_files += 1
                logging.info("File " + path + " has not been modified")
		else if hashes_file.readlines()[-1] == line:
			logging.error("File " + path + " not founded")

def read_path():
    created = True
    mode = "w+"
    if not os.path.isfile("./hashes.txt"): #comprobar si hay archivos nuevos
        created = False
        logging.info("Hashes file has been created")
    else:
        mode = "r"
        logging.info("Starting execution...")


    with open("./hashes.txt", mode) as hashes_file:
        for path in conf["paths"]:
            try:
				file_string = open(path, "r").read()
			except:
				logging.error("File "+str(path)+" does not exists.")
				continue
            if not created:
                hash_file(path, file_string, hashes_file)
            else:
                compare_hash(path, file_string, hashes_file)

    if not created:
        os.chmod("./hashes.txt", S_IREAD)
    else:
        logging.info("Execution has been finished")
        logging.info("Files to check: " + str(len(conf["paths"])))
        logging.info("Checked files: " + str(checked_files))
        logging.info("Modified files: " + str(modified_files))
        logging.info("Not modified files: " + str(not_modified_files))

def main():
    path = read_path()

if __name__== "__main__":
    logging.basicConfig(filename="log.log", level=logging.INFO)
	logging.basicConfig(filename="incidents.log", level=logging.ERORR)
    read_path()
    
