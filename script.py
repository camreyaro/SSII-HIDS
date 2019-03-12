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
integrity_radio_data = []

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
        # mail = Mail(from_email, subject, to_email, content)
        # response = sg.client.mail.send.post(request_body=mail.get())

def compare_hashes(old_hash, new_hash):

	result_hashes = ""
	old_hashes = old_hash.split("\n")
	new_hashes = new_hash.split("\n")

	for o_hash in old_hashes:
		is_in_file = False
		for n_hash in new_hashes:
			if o_hash.strip() in n_hash.strip():
				is_in_file = True
				break
		if not is_in_file:
			result_hashes += "OLD:"+ o_hash+"\n"

	for n_hash in new_hashes:
		is_in_file = False
		for o_hash in old_hashes:
			if o_hash.strip() in n_hash.strip():
				is_in_file = True
				break
		if not is_in_file:
			result_hashes += "NEW:"+ o_hash+"\n"
	
	return result_hashes

def sendChangeHashesMail(newHashes):
    """This function will recieve the new hases and will send an email with the news and the old hashes
    sou you will be able to see the differences between them."""
    from configuration import conf
    global oldHashes

    sg = sendgrid.SendGridAPIClient(apikey="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")
    from_email = Email("insegus@insegus.com")
    to_email = Email(conf["notify_email"])
    subject = "El fichero de hashes ha cambiado"
    changes = compare_hashes(oldHashes, newHashes)
    print(changes)
    content = Content("text/plain",
                      "El fichero de hashes ha cambiado puede deberse a un cambio en la configuración o a un atacante. Por favor, revise que los hashes que no han sido añadidos nuevamente estan correctos \n Hashes antiguos: \n" + oldHashes + "\n \n Hashes nuevos: \n" + newHashes+"\n Changes:\n"+changes)
    # mail = Mail(from_email, subject, to_email, content)
    # response = sg.client.mail.send.post(request_body=mail.get())

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
    """This function will compare the hashing of the files in the hashes files received with their current hash"""
    global logger
    global checked_files
    global modified_files
    global not_modified_files
    global incidentMail
    conf = configuration.conf

    i = -1
    for line in hashes_file.readlines():  # For every line of the hashes file
        i += 1

        file_path = line.split(",")[0].strip()  # file to check their integrity
        file_hash = line.split(",")[1].strip()  # its previous hashing

        if file_path == conf["paths"][i]:  # if it's the file I have to check now
            checked_files += 1
            with open(file_path, "rb") as file_string:
                hashed_file = str(hashlib.sha256(file_string.read()).hexdigest())  # Calculating its current hashing
            if file_hash != hashed_file:  # if it has changed
                modified_files += 1
                incident_logger.error("File " + conf["paths"][i] + " has been modified")  # Incident log
                incidentMail += "File " + conf["paths"][i] + " has been modified \n"  # Incident mail
            else:  # OK
                not_modified_files += 1

                logger.info("File " + conf["paths"][i] + " has not been modified")
        else:  # The file its not founded or hashes file is corrupted
            logger.warning("File " + conf["paths"][i] + " not founded")
            incidentMail += "File " + conf["paths"][
                i] + " not founded or hashes file is corrupted. Maybe the hashes file has not the files in the same order than the configuration, please check it. If the error persists you can remove the hashes file and it will be created again"


def read_path():
    """This function will execute the algorithm to check the integrity calling the previous functions"""
    global logger
    global checked_files_data
    global modified_files_data
    global not_modified_files_data
    global files_to_check_data
    global integrity_radio_data
    date = datetime.datetime.now()
    conf = configuration.conf
    created = True
    mode = "w+"

    logger.info("=========================================")
    if not os.path.isfile(conf['workDirectory'] + "/hashes.txt"):  # if the hashes file does not exist we create it
        created = False

        logger.info("Creating hashes file...")
        with open(conf['workDirectory'] + "/hashes.txt", mode) as hashes_file:
            for path in conf["paths"]:
                try:
                    file_string = open(path, "rb").read()  # we read the file to hash in binary
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
        os.chmod(conf['workDirectory'] + "/hashes.txt", S_IREAD)  # we change the hashes file to read only file

    else:  # If it's created we will compare hashes and will show information

        logger.info("Starting execution...")

        with open(conf['workDirectory'] + "/hashes.txt", "r") as hashes_file:
            compare_hash(hashes_file)
        logger.info("###### Summary ######")
        logger.info("Files to check: " + str(len(conf["paths"])))
        logger.info("Checked files: " + str(checked_files))
        logger.info("Modified files: " + str(modified_files))
        logger.info("Not modified files: " + str(not_modified_files))
        logger.info("Integrity ratio: " + str((not_modified_files/checked_files)*100)+"%")
        integrity_radio_data.append({"x":str(date.second), "y":(not_modified_files/checked_files)*100})
        logger.info("Execution has been finished")
        logger.info("==============================================")
        checked_files_data = [checked_files]
        modified_files_data = [modified_files]
        not_modified_files_data = [not_modified_files]
        files_to_check_data = [len(conf["paths"])]

        global lastExecution
        global huboIncidencias

        lastExecution = "Files to check: " + str(len(conf["paths"])) + " Checked files: " + str(
            checked_files) + " Modified files: " + str(modified_files) + " Not modified files: " + str(
            not_modified_files)
        huboIncidencias = modified_files > 0 or checked_files != len(conf['paths'])

        sendIncidentMail()  # We will notify the e-mail in configuration if there were some incidents

    # HASHES FILE INTEGRITY
    with open(conf['workDirectory'] + "/hashes.txt", "r") as hashes_file:
        global oldHashes
        if not created and oldHashes != "":  # It's not created but it was not the first execution, we send an e-mail becuase it was deleted
            sendChangeHashesMail("Se ha borrado el fichero")
        elif not created:  # It's not created but it's the first execution, we created it and update the old hashes
            oldHashes = hashes_file.read()
        elif oldHashes == "":  # It's created but it's the first execution, we update the old hashes
            oldHashes = hashes_file.read()
        elif oldHashes != hashes_file.read():  # If the hashes file is different from the previous execution we notify
            sendChangeHashesMail(hashes_file.read())


def mainP():
    """This function will initialize every needed variable for the execution, loggers and some directories"""
    global checked_files
    global modified_files
    global not_modified_files
    global logger
    global last_month
    global incident_logger
    global huboIncidencias
    global incidentMail
    global integrity_radio_data
    reload(configuration)
    from configuration import conf

    date = datetime.datetime.now()

    if not os.path.isdir(conf['workDirectory'] + '/logs'):
        os.makedirs(conf['workDirectory'] + '/logs')
    if not os.path.isdir(conf['workDirectory'] + '/incidents'):
        os.makedirs(conf['workDirectory'] + '/incidents')

    if last_month != date.month:
        integrity_radio_data = []
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

# VIEWS
@app.route('/', methods=['GET'])
def index():
    global huboIncidencias
    if not huboIncidencias:
        return "<h3> Last Execution1 </h3><p>" + lastExecution + "</p>" + "<br><div><a href='incidencias'><button style='float:left'>Issues</button></a><a href='graficas'><button>Graphs</button></a></div>"
    else:
        return "<h1 style='color:red;'>There were issues, please click <a href='incidencias'>here</a> to see them</h1>" + "<h3> Last Execution1 </h3><p>" + lastExecution + "</p>" + "<br><div><a href='incidencias'><button style='float:left'>Issues</button></a><a href='graficas'><button>Graphs</button></a></div>"


@app.route('/incidencias', methods=['GET'])
def incidencias():
    from configuration import conf
    res = "<ul>"
    for path in os.listdir(conf['workDirectory'] + "/incidents"):
        with open(conf['workDirectory'] + "//incidents/" + path, "r") as incident:
            res += "<li><b>" + path + "</b>:<br> " + str(incident.read()) + "</li><br>"
    return res + "</ul>"


@app.route('/graficas', methods=['GET'])
def graficas():
    return render_template('graph.html', modified_files_data=modified_files_data, checked_files_data=checked_files_data,
                           not_modified_files_data=not_modified_files_data, files_to_check_data=files_to_check_data, integrity_radio_data=integrity_radio_data)


if __name__ == '__main__':
    # creating a ubuntu daemon
    schedule = BackgroundScheduler(daemon=True)
    schedule.add_job(mainP, "interval", seconds=configuration.conf['frequency'])
    schedule.start()
    # running the app
    app.run(host="localhost", port="9007")
