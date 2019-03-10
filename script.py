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

checked_files = 0  # How many files have been checked in this execution
modified_files = 0  # How many files have been modified in this execution
not_modified_files = 0  # How many files have not been modified in this execution
huboIncidencias = False  # Variable to control if there were incidents and show a link in the index
lastExecution = ""  # Variable to show in the view how it went the previous execution
logger = None  # Logger
incident_logger = None  # Logger of incidents
last_month = 0  # Variable to control the month of the previous execution, it will help us to change of main log file
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')  # Format of the logger
incidents_data = []  # Variable to create graphs
modified_files_data = []  # Variable to create graphs
not_modified_files_data = []  # Variable to create graphs
files_to_check_data = []  # Variable to create graphs
checked_files_data = []  # Variable to create graphs

incidentMail = ""  # This variable will be the content of the incident mail
oldHashes = ""  # This variable will storage the last version of hashes file to see if it was changed


def setup_logger(name, log_file, level=logging.INFO):
    """Function setup as many loggers as you want"""

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


def sendIncidentMail():
    """This function will send an email if there are some incidents"""
    global incidentMail
    conf = configuration.conf

    if incidentMail != "":
        sg = sendgrid.SendGridAPIClient(apikey="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")
        from_email = Email("insegus@insegus.com")
        to_email = Email(conf["notify_email"])
        subject = "La integridad de su sistema se ha visto comprometido."
        content = Content("text/plain",
                          incidentMail)
        mail = Mail(from_email, subject, to_email, content)
        response = sg.client.mail.send.post(request_body=mail.get())


def sendChangeHashesMail(newHashes):
    """This function will recieve the new hases and will send an email with the news and the old hashes
    sou you will be able to see the differences between them."""
    from configuration import conf
    global oldHashes

    sg = sendgrid.SendGridAPIClient(apikey="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")
    from_email = Email("insegus@insegus.com")
    to_email = Email(conf["notify_email"])
    subject = "El fichero de hashes ha cambiado"
    content = Content("text/plain",
                      "El fichero de hashes ha cambiado puede deberse a un cambio en la configuración o a un atacante. Por favor, revise que los hashes que no han sido añadidos nuevamente estan correctos \n Hashes antiguos: \n" + oldHashes + "\n \n Hashes nuevos: \n" + newHashes)
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())

    # if last_paths != len(conf["paths"]) and not huboIncidencias and not first_time:
    #     with open("hashes.txt", "r") as file_to_attach:
    #         data = file_to_attach.read()
    #
    #     content_string = "El archivo de configuración ha sido modificado, compruebe que ha sido el administrador del sistema.\n Hashes antiguos:\n" + str(
    #         data) + "\n"
    #     # Email notification
    #
    #     subject = "Se ha modificado la configuracion."
    #
    #     logger.warning("Paths change detected, hashing files...")
    #     os.chmod(conf['workDirectory'] + "/hashes.txt", S_IWRITE)
    #     with open(conf['workDirectory'] + "/hashes.txt", 'w') as hashes_file:
    #         for path in conf["paths"]:
    #             try:
    #                 file_string = open(path, "rb").read()
    #                 if len(file_string) == 0 or file_string == "":
    #                     logger.warning("File " + str(path) + " is empty.")
    #                     continue
    #             except MemoryError:
    #                 logger.warning("File " + str(path) + " is too big.")
    #                 continue
    #             except FileNotFoundError:
    #                 logger.warning("File " + str(path) + " does not exists.")
    #                 continue
    #
    #             hash_file(path, file_string, hashes_file)
    #
    #     new_hashes = Attachment()
    #     with open(conf['workDirectory'] + "/hashes.txt", "rb") as file_to_attach:
    #         content_string += "Hashes nuevos\n" + str(file_to_attach.read())
    #     content = Content("text/plain", repr(content_string))
    #     mail = Mail(from_email, subject, to_email, content)
    #     response = sg.client.mail.send.post(request_body=mail.get())
    #
    #     logger.warning("Hashfile updated")
    #     os.chmod(conf['workDirectory'] + "/hashes.txt", S_IREAD)


def hash_file(path, file_string, hashes_file):
    """hashing the file in the path, both are recieved as the file where they have to be written"""
    hashed_file = str(hashlib.sha256(file_string).hexdigest())
    hashes_file.write(path + ", " + hashed_file + "\n")


def compare_hash(hashes_file):
    """This function will compare """
    global logger
    global checked_files
    global modified_files
    global not_modified_files
    global incidentMail
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
                incident_logger.error("File " + conf["paths"][i] + " has been modified")
                incidentMail += "File " + conf["paths"][i] + " has been modified \n"
            else:
                not_modified_files += 1

                logger.info("File " + conf["paths"][i] + " has not been modified")
        else:
            logger.warning("File " + conf["paths"][i] + " not founded")
            incidentMail += "File " + conf["paths"][i] + " not founded"


def read_path():
    global logger
    global checked_files_data
    global modified_files_data
    global not_modified_files_data
    global files_to_check_data
    conf = configuration.conf
    created = True
    mode = "w+"
    logger.info("=========================================")
    if not os.path.isfile(conf['workDirectory'] + "/hashes.txt"):  # comprobar si hay archivos nuevos
        created = False
        logger.info("Hashes file has been created")
    else:
        mode = "r"
        logger.info("Starting execution...")

    with open(conf['workDirectory'] + "/hashes.txt", mode) as hashes_file:
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
        os.chmod(conf['workDirectory'] + "/hashes.txt", S_IREAD)
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

        # sendIncidentMail()

    ##### INTEGRIDAD EN EL FICHERO DE HASHES ####
    with open(conf['workDirectory'] + "/hashes.txt", "r") as hashes_file:
        global oldHashes
        if not created and oldHashes != "":
            sendChangeHashesMail("Se ha borrado el fichero")
        elif not created:
            oldHashes = hashes_file.read()
        elif oldHashes == "":
            oldHashes = hashes_file.read()
        elif oldHashes != hashes_file.read():
            sendChangeHashesMail(hashes_file.read())


def mainP():
    global checked_files
    global modified_files
    global not_modified_files
    global logger
    global last_month
    global incident_logger
    global huboIncidencias
    global incidentMail
    reload(configuration)
    from configuration import conf

    date = datetime.datetime.now()

    if not os.path.isdir(conf['workDirectory'] + '/logs'):
        os.makedirs(conf['workDirectory'] + '/logs')
    if not os.path.isdir(conf['workDirectory'] + '/incidents'):
        os.makedirs(conf['workDirectory'] + '/incidents')

    if last_month != date.month:
        logger = setup_logger('info_logger' + str(date.year) + "-" + str(date.month),
                              conf['workDirectory'] + "/logs/" + str(date.year) + "-" + str(date.month) + ".log")
        logger.addHandler(logging.StreamHandler())
        incident_logger = setup_logger('error_logger' + str(date.year) + "-" + str(date.month),
                                       conf['workDirectory'] + "/incidents/incident-" + str(date.year) + "-" + str(
                                           date.month) + ".log",
                                       level=logging.ERROR)
        last_month = date.month
    checked_files = 0
    modified_files = 0
    not_modified_files = 0
    incidentMail = ""
    read_path()


@app.route('/', methods=['GET'])
def index():
    conf = configuration.conf
    global huboIncidencias
    if not huboIncidencias:
        return "<h3> Last Execution1 </h3><p>" + lastExecution + "</p>" + "<br><div><a href='incidencias'><button style='float:left'>Issues</button></a><a href='graficas'><button>Graphs</button></a></div>"
    else:
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
