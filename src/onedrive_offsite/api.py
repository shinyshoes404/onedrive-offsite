from flask import Flask, request, make_response
from onedrive_offsite.config import Config
from onedrive_offsite.utils import ses_send_email, get_recent_log_lines
import json, datetime, os, subprocess, logging

# Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(Config.LOG_LEVEL)
logger.addHandler(Config.FILE_HANDLER)
logger.addHandler(Config.STOUT_HANDLER)

api = Flask(__name__)

api.config["DEBUG"] = Config.flask_debug

@api.route("/transfer/start", methods=["POST"])
def transfer_initiate():
    content = request.get_json()
    backup_file_info = {}
    if content.get("file-path")[:1] == "~":
        backup_file_info["backup-file-path"] = "/home/" + content.get("username") + content.get("file-path")[-len(content.get("file-path"))+1:]
    else:
        backup_file_info["backup-file-path"] = content.get("file-path")
    
    backup_file_info["start-date-time"] = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
    backup_file_info["size-bytes"] = content.get("size-bytes")

    # required directory name parameter
    if content.get("onedrive-dir") == None or content.get("onedrive-dir") == "":
        resp = make_response({"error":"missing 'onedrive-dir'"}, 400)
        return resp
    else:
        backup_file_info["onedrive-dir"] = content.get("onedrive-dir")

    # optional file name for naming the file we upload to onedrive
    if content.get("onedrive-filename"):
        backup_file_info["onedrive-filename"] = content.get("onedrive-filename")

    with open(Config.backup_file_info_path, "w") as file:
        json.dump(backup_file_info, file)

    logger.info("Transfer start request received")
    logger.info(backup_file_info)

    return make_response({"msg":"transfer started"}, 200)


@api.route("/transfer/done", methods=["PUT"])
def transfer_done():
    
    with open(Config.backup_file_info_path, "r") as file:
        backup_file_info = json.load(file)
    
    # grab the onedrive base file name to include in the email body and subject
    if backup_file_info.get("onedrive-filename"):
        onedrive_file_name = backup_file_info.get("onedrive-filename")
    else:
        onedrive_file_name = Config.onedrive_upload_default_filename

    if not os.path.isfile(backup_file_info.get("backup-file-path")):
        logger.info("File did not transfer or wrong path was provided - file path provided: " + backup_file_info.get("backup-file-path"))
        _send_error_email(onedrive_file_name)
        return make_response({"Error":"File did not transfer or wrong path was provided", "file-path-provided" : backup_file_info.get("backup-file-path")}, 404)

    if os.path.getsize(backup_file_info.get("backup-file-path")) != backup_file_info.get("size-bytes"):
        logger.info("File size does not match what was provided, file-size-provided: " + str(backup_file_info.get("size-bytes")))
        _send_error_email(onedrive_file_name)
        return make_response({"Error":"File size does not match what was provided", "file-size-provided":backup_file_info.get("size-bytes"), "file-size-actual":os.path.getsize(backup_file_info.get("backup-file-path"))}, 409)
    
    backup_file_info["done-date-time"] = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S")

    try:
        with open(Config.backup_file_info_path, "w") as file:
            json.dump(backup_file_info, file)
    except Exception as e:
        logger.error("problem saving backup_file_info as json file in /transfer/done")
        logger.error(e)
        _send_error_email(onedrive_file_name)
        return make_response({"Error":"Server error."}, 500)

    upload_env = os.environ.copy()

    # check for optional onedrive file name
    if backup_file_info.get("onedrive-filename"):
        upload_env["ONEDRIVE_NAME"] = backup_file_info.get("onedrive-filename")

    subprocess.Popen("onedrive-offsite-build-and-upload", env=upload_env)
    
    logger.info("client indicated file transfer is complete")

    return make_response({"msg":"File transfer complete. Upload process has started"}, 201)


def _send_error_email(onedrive_file_name):
    email_message = "onedrive-offsite failed for " + onedrive_file_name + ".\n\n\n"
    log_text = get_recent_log_lines(20)
    email_message = email_message + log_text
    email_message = email_message.replace("\n","</br>")
    email_subject = "Error - " + onedrive_file_name

    try:            
        ses_send_email(to_email_address=Config.email_to,
                        from_email_address=Config.email_from_addr,
                        email_from_name=Config.email_from_name,
                        email_subject=email_subject,
                        email_message_txt=email_message,
                        ses_aws_region=Config.aws_region)

        logger.info("email sent.")
        return True

    except Exception as e:
        logger.error("problem sending email.")   
        logger.error(e)
        return False

@api.route("/download-decrypt", methods=["POST"])
def download_decrypt():
    content = request.get_json()
    download_info_file = {}
   
    download_info_file["start-date-time"] = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S")

    # required directory name parameter
    if content.get("onedrive-dir") == None or content.get("onedrive-dir") == "":
        resp = make_response({"error":"missing 'onedrive-dir'"}, 400)
        return resp
    else:
        download_info_file["onedrive-dir"] = content.get("onedrive-dir")


    with open(Config.download_info_path, "w") as file:
        json.dump(download_info_file, file)

    logger.info("download decrypt request received for {0}".format(download_info_file["onedrive-dir"]))
    logger.info(download_info_file)

    upload_env = os.environ.copy()
    subprocess.Popen("onedrive-offsite-restore", env=upload_env)

    return make_response({"msg":"download and decrypt process started for {0}".format(download_info_file["onedrive-dir"])}, 200)


    


