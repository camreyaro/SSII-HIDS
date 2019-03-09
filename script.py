#! /usr/bin/python3.6
from flask import Flask, request
import hashlib
import os
from apscheduler.schedulers.background import BackgroundScheduler
import json
from conf import conf
import logging
from stat import S_IREAD
import datetime
import sendgrid
from sendgrid.helpers.mail import *

app = Flask(__name__)

checked_files = 0
modified_files = 0
not_modified_files = 0
logfile = "log" + "March" + ".log"
huboIncidencias = False
lastExecution = ""
logger = None
incident_logger = None
last_month = 0
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')


def setup_logger(name, log_file, level=logging.INFO):
    """Function setup as many loggers as you want"""

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


def hash_file(path, file_string, hashes_file):
    hashed_file = str(hashlib.sha256(file_string.encode()).hexdigest())
    hashes_file.write(path + ", " + hashed_file + "\n")


def compare_hash(path, file_string, hashes_file):
    global logfile
    global logger
    global checked_files
    global modified_files
    global not_modified_files

    hashed_file = str(hashlib.sha256(file_string.encode()).hexdigest())
    for line in hashes_file.readlines():
        file_path = line.split(",")[0].strip()
        file_hash = line.split(",")[1].strip()

        if file_path == path:
            checked_files += 1
            if file_hash != hashed_file:
                modified_files += 1
                incident_logger.error(
                    "File " + path + " has been modified")  # añadir totales archivos revisados y cuales han ido bien
            else:
                not_modified_files += 1
                logger.info("File " + path + " has not been modified")
        elif hashes_file.readlines()[-1] == line:
            logger.warning("File " + path + " not founded")


def read_path():
    global logfile
    global logger
    created = True
    mode = "w+"
    logger.info("=========================================")
    if not os.path.isfile("./hashes.txt"):  # comprobar si hay archivos nuevos
        created = False
        logger.info("Hashes file has been created")
    else:
        mode = "r"
        logger.info("Starting execution...")

    with open("./hashes.txt", mode) as hashes_file:
        for path in conf["paths"]:
            try:
                file_string = open(path, "r").read()
                if len(file_string) == 0 or file_string == "":
                    logger.warning("File " + str(path) + " is empty.")
                    continue
            except MemoryError:
                logger.warning("File " + str(path) + " is too big.")
                continue
            except FileNotFoundError:
                logger.warning("File " + str(path) + " does not exists.")
                continue
            if not created:
                hash_file(path, file_string, hashes_file)
            else:
                compare_hash(path, file_string, hashes_file)

    if not created:
        pass
        os.chmod("./hashes.txt", S_IREAD)
    else:
        logger.info("###### Summary ######")
        logger.info("Execution has been finished")
        logger.info("Files to check: " + str(len(conf["paths"])))
        logger.info("Checked files: " + str(checked_files))
        logger.info("Modified files: " + str(modified_files))
        logger.info("Not modified files: " + str(not_modified_files))
        logger.info("==============================================")

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
    global logger
    global last_month
    global incident_logger

    date = datetime.datetime.now()
    if not os.path.isdir('./logs'):
        os.makedirs('./logs')
    if not os.path.isdir('./incidents'):
        os.makedirs('./incidents')

    if last_month != date.month:
        logger = setup_logger('info_logger' + str(date.year) + "-" + str(date.month),
                              "./logs/" + str(date.year) + "-" + str(date.month) + ".log")
        incident_logger = setup_logger('error_logger' + str(date.year) + "-" + str(date.month),
                                       "./incidents/incident-" + str(date.year) + "-" + str(date.month) + ".log",
                                       level=logging.ERROR)
        last_month = date.month
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

        # Email notification
        sg = sendgrid.SendGridAPIClient(apikey="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")
        from_email = Email("insegus@insegus.com")
        to_email = Email(conf["notify_email"])
        subject = "La integridad de su sistema se ha visto comprometido."
        content = Content("text/plain", "Se han detectado incidencias en el sistema.")
        mail = Mail(from_email, subject, to_email, content)
        response = sg.client.mail.send.post(request_body=mail.get())

        return "<h1 style='color:red;'>There were issues, please click <a href='incidencias'>here</a> to see them</h1>" + "<h3> Last Execution1 </h3><p>" + lastExecution + "</p>" + "<br><div><a href='incidencias'><button style='float:left'>Issues</button></a><a href='graficas'><button>Graphs</button></a></div>"


@app.route('/incidencias', methods=['GET'])
def incidencias():
    res = "<ul>"
    for path in os.listdir("./incidents"):
        with open("./incidents/"+path, "r") as incident:
            res += "<li><b>" + path + "</b>:<br> " + str(incident.read()) + "</li><br>"
    return res + "</ul>"


@app.route('/graficas', methods=['GET'])
def graficas():
    return "grafis"


if __name__ == '__main__':
    schedule = BackgroundScheduler(daemon=True)
    schedule.add_job(mainP, "interval", seconds=10)
    schedule.start()
    app.run(host="0.0.0.0", port="9007")
