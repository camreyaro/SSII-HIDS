#! /usr/bin/python3.6
from flask import Flask, request, render_template
import hashlib
import os
from apscheduler.schedulers.background import BackgroundScheduler
import json
import logging
from stat import S_IREAD, S_IWRITE
import datetime
import sendgrid
from sendgrid.helpers.mail import *
import importlib
import configuration
import base64
from importlib import reload

app = Flask(__name__)

checked_files = 0
modified_files = 0
not_modified_files = 0
logfile = "log" + "March" + ".log"
huboIncidencias = False
first_time = True
lastExecution = ""
logger = None
incident_logger = None
last_month = 0
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
last_paths = 0
incidents_data = []
modified_files_data = []
not_modified_files_data = []
files_to_check_data = []
checked_files_data = []


def setup_logger(name, log_file, level=logging.INFO):
    """Function setup as many loggers as you want"""

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


def hash_file(path, file_string, hashes_file):
    hashed_file = str(hashlib.sha256(file_string).hexdigest())
    hashes_file.write(path + ", " + hashed_file + "\n")


def compare_hash(hashes_file):
    global logfile
    global logger
    global checked_files
    global modified_files
    global not_modified_files
    conf = configuration.conf
    
    i = -1
    for line in hashes_file.readlines():
        i += 1

        file_path = line.split(",")[0].strip()
        file_hash = line.split(",")[1].strip()

        if file_path == conf["paths"][i]:
            checked_files += 1
            with open(file_path, "rb") as file_string:
                hashed_file = str(hashlib.sha256(file_string.read()).hexdigest())
            if file_hash != hashed_file:
                modified_files += 1
                incident_logger.error("File " + conf["paths"][
                    i] + " has been modified")  # añadir totales archivos revisados y cuales han ido bien
            else:
                not_modified_files += 1
                logger.info("File " + conf["paths"][i] + " has not been modified")
        else:
            logger.warning("File " + conf["paths"][i] + " not founded")


def read_path():
    global logfile
    global logger
    global checked_files_data
    global modified_files_data
    global not_modified_files_data
    global files_to_check_data
    conf = configuration.conf
    created = True
    mode = "w+"
    logger.info("=========================================")
    if not os.path.isfile(conf['workDirectory']+"/hashes.txt"):  # comprobar si hay archivos nuevos
        created = False
        logger.info("Hashes file has been created")
    else:
        mode = "r"
        logger.info("Starting execution...")

    with open(conf['workDirectory']+"/hashes.txt", mode) as hashes_file:
        for path in conf["paths"]:
            try:
                file_string = open(path, "rb").read()
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
                compare_hash(hashes_file)

    if not created:
        os.chmod(conf['workDirectory']+"/hashes.txt", S_IREAD)
    else:
        logger.info("###### Summary ######")
        logger.info("Execution has been finished")
        logger.info("Files to check: " + str(len(conf["paths"])))
        logger.info("Checked files: " + str(checked_files))
        logger.info("Modified files: " + str(modified_files))
        logger.info("Not modified files: " + str(not_modified_files))
        logger.info("==============================================")
        checked_files_data = [checked_files]
        modified_files_data = [modified_files]
        not_modified_files_data = [not_modified_files]
        files_to_check_data = [len(conf["paths"])]
        global lastExecution
        global last_paths
        last_paths = len(conf["paths"])
        lastExecution = "Files to check: " + str(len(conf["paths"])) + " Checked files: " + str(
            checked_files) + " Modified files: " + str(modified_files) + " Not modified files: " + str(
            not_modified_files)
        if modified_files > 0:
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
    global last_paths
    global huboIncidencias
    global first_time
    reload(configuration)
    from configuration import conf
    print("paths de antes " + str(last_paths))
    print("paths de ahora " + str(len(conf["paths"])))
    # reload(conf.conf)
    if last_paths != len(conf["paths"]) and not huboIncidencias and not first_time:

        old_hashes = Attachment()
        with open("hashes.txt", "r") as file_to_attach:
            # encoded_string = base64.b64encode(file_to_attach.read()).decode()
            # old_hashes.content = file_to_attach
            # old_hashes.type = "text/plain"
            # old_hashes.filename = os.path.basename("old_hashes.txt")
            # old_hashes.disposition = "attachment"
            data = file_to_attach.read()

        content_string = "El archivo de configuración ha sido modificado, compruebe que ha sido el administrador del sistema.\n Hashes antiguos:\n" + str(
            data) + "\n"
        # Email notification
        sg = sendgrid.SendGridAPIClient(apikey="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")
        from_email = Email("insegus@insegus.com")
        to_email = Email(conf["notify_email"])
        subject = "Se ha modificado la configuracion."

        logger.warning("Paths change detected, hashing files...")
        os.chmod(conf['workDirectory']+"/hashes.txt", S_IWRITE)
        with open(conf['workDirectory']+"/hashes.txt", 'w') as hashes_file:
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

                hash_file(path, file_string, hashes_file)

        new_hashes = Attachment()
        with open(conf['workDirectory']+"/hashes.txt", "rb") as file_to_attach:
            content_string += "Hashes nuevos\n" + str(file_to_attach.read())
        content = Content("text/plain", content_string)
        mail = Mail(from_email, subject, to_email, content)
        response = sg.client.mail.send.post(request_body=mail.get())

        logger.warning("Hashfile updated")
        os.chmod(conf['workDirectory']+"/hashes.txt", S_IREAD)

    first_time = False
    last_paths = len(conf["paths"])
    date = datetime.datetime.now()
    if not os.path.isdir(conf['workDirectory']+'/logs'):
        os.makedirs(conf['workDirectory']+'/logs')
    if not os.path.isdir(conf['workDirectory']+'/incidents'):
        os.makedirs(conf['workDirectory']+'/incidents')

    if last_month != date.month:
        logger = setup_logger('info_logger' + str(date.year) + "-" + str(date.month),
                              conf['workDirectory']+"/logs/" + str(date.year) + "-" + str(date.month) + ".log")
        logger.addHandler(logging.StreamHandler())
        incident_logger = setup_logger('error_logger' + str(date.year) + "-" + str(date.month),
                                       conf['workDirectory']+"/incidents/incident-" + str(date.year) + "-" + str(date.month) + ".log",
                                       level=logging.ERROR)
        last_month = date.month
    checked_files = 0
    modified_files = 0
    not_modified_files = 0
    read_path()


@app.route('/', methods=['GET'])
def index():
    conf = configuration.conf
    global huboIncidencias
    if not huboIncidencias:
        return "<h3> Last Execution1 </h3><p>" + lastExecution + "</p>" + "<br><div><a href='incidencias'><button style='float:left'>Issues</button></a><a href='graficas'><button>Graphs</button></a></div>"
    else:
        # Email notification
        sg = sendgrid.SendGridAPIClient(apikey="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")
        from_email = Email("insegus@insegus.com")
        to_email = Email(conf["notify_email"])
        subject = "La integridad de su sistema se ha visto comprometido."
        content = Content("text/plain",
                          "Se han detectado incidencias en el sistema, compruebe su archivo de incidencias.")
        mail = Mail(from_email, subject, to_email, content)
        response = sg.client.mail.send.post(request_body=mail.get())

        return "<h1 style='color:red;'>There were issues, please click <a href='incidencias'>here</a> to see them</h1>" + "<h3> Last Execution1 </h3><p>" + lastExecution + "</p>" + "<br><div><a href='incidencias'><button style='float:left'>Issues</button></a><a href='graficas'><button>Graphs</button></a></div>"


@app.route('/incidencias', methods=['GET'])
def incidencias():
    conf = configuration.conf
    res = "<ul>"
    for path in os.listdir("./incidents"):
        with open("./incidents/" + path, "r") as incident:
            res += "<li><b>" + path + "</b>:<br> " + str(incident.read()) + "</li><br>"
    return res + "</ul>"


@app.route('/graficas', methods=['GET'])
def graficas():
    return render_template('graph.html', modified_files_data=modified_files_data, checked_files_data=checked_files_data,
                           not_modified_files_data=not_modified_files_data, files_to_check_data=files_to_check_data)


if __name__ == '__main__':
    schedule = BackgroundScheduler(daemon=True)
    schedule.add_job(mainP, "interval", seconds=configuration.conf['frequency'])
    schedule.start()
    app.run(host="localhost", port="9007")


