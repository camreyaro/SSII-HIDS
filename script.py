#! /usr/bin/python3.6
from flask import Flask, request
import hashlib
import os
from apscheduler.schedulers.background import BackgroundScheduler
import json
from conf import conf
import logging
from stat import S_IREAD, UF_NODUMP

app = Flask(__name__)

checked_files = 0
modified_files = 0
not_modified_files = 0
logfile = "log" + "March" + ".log"
huboIncidencias = False
lastExecution = ""


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
                logging.error(
                    "File " + path + " has been modified")  # añadir totales archivos revisados y cuales han ido bien
            else:
                not_modified_files += 1
                logging.info("File " + path + " has not been modified")


def read_path():
    created = True
    mode = "w+"
    if not os.path.isfile("./hashes.txt"):  # comprobar si hay archivos nuevos
        created = False
        logging.info("Hashes file has been created")
    else:
        mode = "r"
        logging.info("Starting execution...")

    with open("./hashes.txt", mode) as hashes_file:
        for path in conf["paths"]:
            file_string = open(path, "r").read()

            if not created:
                hash_file(path, file_string, hashes_file)
            else:
                compare_hash(path, file_string, hashes_file)

    if not created:
        pass
        os.chmod("./hashes.txt", S_IREAD, UF_NODUMP)
    else:
        logging.info("Execution has been finished")
        logging.info("Files to check: " + str(len(conf["paths"])))
        logging.info("Checked files: " + str(checked_files))
        logging.info("Modified files: " + str(modified_files))
        logging.info("Not modified files: " + str(not_modified_files))

        global lastExecution
        lastExecution = "Files to check: " + str(len(conf["paths"])) + " Checked files: " + str(
            checked_files) + " Modified files: " + str(modified_files) + " Not modified files: " + str(
            not_modified_files)
        if modified_files > 0 or len(conf["paths"]) != checked_files:
            global huboIncidencias
            huboIncidencias = True


def mainP():
    global checked_files
    global modified_files
    global not_modified_files
    global logfile
    checked_files = 0
    modified_files = 0
    not_modified_files = 0
    read_path()


@app.route('/', methods=['GET'])
def index():
    global huboIncidencias
    if not huboIncidencias:
        return "<h3> Last Execution1 </h3><p>" + lastExecution + "</p>" + "<br><div><a href='incidencias'><button style='float:left'>Issues</button></a><a href='graficas'><button>Graphs</button></a></div>"
    else:
        return "<h1 style='color:red;'>There were issues, please click <a href='incidencias'>here</a> to see them</h1>" + "<h3> Last Execution1 </h3><p>" + lastExecution + "</p>" + "<br><div><a href='incidencias'><button style='float:left'>Issues</button></a><a href='graficas'><button>Graphs</button></a></div>"

@app.route('/incidencias', methods=['GET'])
def incidencias():
    return "incidencias"


@app.route('/graficas', methods=['GET'])
def graficas():
    return "grafis"


if __name__ == '__main__':
    logging.basicConfig(filename="./log.log", level=logging.INFO)
    logging.info("Started")
    schedule = BackgroundScheduler(daemon=True)
    schedule.add_job(mainP, "interval", seconds=10)
    schedule.start()
    app.run(host="0.0.0.0", port="9007")
