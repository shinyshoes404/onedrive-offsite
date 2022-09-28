from onedrive_offsite.onedrive import OneDriveLargeUpload, MSGraphCredMgr, OneDriveDirMgr, OneDriveGetItemDetails, OneDriveFileDownloadMgr, OneDriveItemGetter
from onedrive_offsite.utils import FilePartialRead, extract_tar_gz
from onedrive_offsite.config import Config
from onedrive_offsite.crypt import Crypt, Sha256Calc
from time import sleep
from datetime import datetime, timedelta
import os, logging, queue, threading, json

# Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(Config.LOG_LEVEL)
logger.addHandler(Config.FILE_HANDLER)
logger.addHandler(Config.STOUT_HANDLER)

##################################################################################################################
##### ------------------------------------------ HELPER FUNCTIONS -------------------------------------------------

def write_to_error_q(error_q):
    thread_name = threading.current_thread().getName()
    msg = "error"
    try:
        error_q.put(msg)
        logger.info("thread: {0} - put this message on the error queue msg: {1}".format(thread_name, str(msg)))
        return True
    except Exception as e:
        logger.error("thread: {0} - problem putting msg on attempted queue".format(thread_name))
        logger.error(e)
        return False

def _check_token_read(msgcm, targz_file, upload_attempted_q, kill_q):
    thread_name = threading.current_thread().getName()
    if msgcm.read_tokens() == False:
        logger.warning("thread: {0} - problem reading credentials file".format(thread_name))
        q_msg = upload_status_gen(targz_file, "error", "problem reading credentials file")        
        publish_to_attempted_q(q_msg, upload_attempted_q, kill_q)
        return False
    return True        


def flood_kill_queue(kill_q):
    for i in range(0,20):
        kill_q.put("kill")


def upload_status_gen(targz_filename, status, msg=""):
    q_message = {"filename": targz_filename, "status": status, "msg": msg }
    return q_message


def publish_to_attempted_q(q_msg, upload_attempted_q, kill_q):
    thread_name = threading.current_thread().getName()
    try:
        upload_attempted_q.put(q_msg)
        logger.info("thread: {0} - put this message on the attempted upload queue msg: {1}".format(thread_name, str(q_msg)))
        return True
    except Exception as e:
        logger.error("thread: {0} - problem putting msg on upload attempted queue, flooding kill queue".format(thread_name))
        logger.error(e)
        flood_kill_queue(kill_q)
        return False


#######################################################################################################################
##### ---------------------------- TOKEN REFRESH WORKER AND HELPER FUNCTIONS ------------------------------------------

def token_refresh_cycle():
    # instatiate the MSGraphCredMgr object to manage access and refresh tokens from Microsoft's Graph API
    # Note: You have to have setup the app for this to work by running: onedrive-offsite-create-key, onedrive-offsite-setup-app, and onedrive-offsite-signin in that order
    msgcm = MSGraphCredMgr()
    if msgcm.read_tokens() == False:                                                # have to read in the existing tokens before we can attempt to refresh
        return False
    if msgcm.refresh_tokens() == False:                                             # refresh the tokens and check for an issue at the same time
        return False    
    return msgcm                                                                    # pass the object back so we can use it to check the expires property

def _token_refresh_get_offset(retry):
    if retry == 0:
        return 1200   # 20 min before expiration
    if retry == 1:
        return 600    # 10 min before expiration
    else:
        return 300    # 5 min before expiration

def _lock_file_check():
    thread_name = threading.current_thread().getName()

    if not os.path.isfile(Config.cred_mgr_lock_path):
        return False
    
    try:
        with open(Config.cred_mgr_lock_path, "r") as lock_file:
            lock_val = lock_file.read()
    except Exception as e:
        logger.error("thread: {0} - problem readng lock file".format(thread_name))
        logger.error(e)
        return None
    
    if lock_val == "locked":
        return True
    if lock_val == "not locked":
        return False
    
    logger.error("thread: {0} - unexpected value in lock file".format(thread_name))
    return None

def _write_to_lock_file(lock_status: str):
    thread_name = threading.current_thread().getName()

    try:
        with open(Config.cred_mgr_lock_path, "w") as lock_file:
            lock_file.write(lock_status)
    except Exception as e:
        logger.error("thread: {0} - problem writing to lock file".format(thread_name))
        logger.error(e)
        return None
    
    return True


def token_refresh_worker(kill_q, error_q):

    thread_name = threading.current_thread().getName()
    logger.info("thread: {0} - token refresh worker thread starting".format(thread_name)) 

    while _lock_file_check() == True:
        logger.info("thread: {0} - in lock file loop".format(thread_name)) 
        if not kill_q.empty():
            return None
        sleep(300)
    
    # update lock file to locked since we are going to refresh credentials
    if not _write_to_lock_file("locked"):
        logger.error("thread: {0} - could not write to lock file, flooding kill queue".format(thread_name))
        flood_kill_queue(kill_q)
        write_to_error_q(error_q)
        _write_to_lock_file("not locked")
        return None

    logger.info("thread: {0} - initial refresh".format(thread_name))
    msgcm_obj = token_refresh_cycle()                         # initial token refresh
    if msgcm_obj == False:
        logger.error("thread: {0} - token refresh worker failed to refresh tokens".format(thread_name))
        flood_kill_queue(kill_q)                                                    # make sure the rest of the threads know to stop
        write_to_error_q(error_q)
        _write_to_lock_file("not locked")
        return False

    retry = 0    
    while kill_q.empty():                                                           # keep looping to make sure the token is refreshed during the upload process
        msgcm_obj.read_tokens()                                                     # read the current info from the oauth2_creds.json file

        offset = _token_refresh_get_offset(retry)
        current_datetime = datetime.now()
        logger.debug("thread: {0} - check time left".format(thread_name))
        if current_datetime > msgcm_obj.expires - timedelta(seconds=offset):        # if the token expires within offset seconds, refresh the token
            check_refresh = token_refresh_cycle()                                   # read and refresh the tokens and get back the MSGRaphCredMgr object
            if check_refresh != False:
                msgcm_obj = check_refresh

            if check_refresh == False and retry > 1:
                logger.error("thread: {0} - token refresh worker failed to refresh tokens".format(thread_name))
                flood_kill_queue(kill_q)                                            # make sure the rest of the threads know to stop
                write_to_error_q(error_q)
                _write_to_lock_file("not locked")
                return False

            if check_refresh == False:
                logger.warning("thread: {0} - token refresh worker failed to refresh tokens, need to retry, current retry: {1}".format(thread_name, retry))
                retry = retry + 1
            else:
                retry = 0
        sleep(60)                                                                   # wait for one minute to check the token expiration again
    
    if not _write_to_lock_file("not locked"):
        logger.error("thread: {0} - could not write to lock file to unlock".format(thread_name))
        write_to_error_q(error_q)

    logger.info("thread: {0} - token refresh worker thread is exiting".format(thread_name))

    return True



###############################################################################################################
##### ---------------------------- UPLOAD WORKER AND HELPER FUNCTIONS ------------------------------------------

def _worker_upload(bytes_to_send, targz_file, chunks, fpr, upload_attempted_q, kill_q, odlu):

    thread_name = threading.current_thread().getName()

    if bytes_to_send == None:
        logger.error("thread: {0} - no bytes read in with read_file_bytes()".format(thread_name))
        q_msg = upload_status_gen(targz_file, "error", "no bytes read in with read_file_bytes()" )
        publish_to_attempted_q(q_msg, upload_attempted_q, kill_q)
        return "error-empty-bytes"

    else:
        try:
            upload_response = odlu.upload_file_part(str(fpr.file_size), str(chunks[0]), chunks[2], bytes_to_send)

            if upload_response == "move-next" or upload_response == "upload-complete":
                return "upload-succeeded"

            # if we run into an issue while uploading, cancel the upload and stop looping through the file chunks
            if upload_response == False or (upload_response.status_code !=200 and upload_response.status_code != 201 and upload_response.status_code != 202):
                logger.error("thread: {0} - {1} upload not successful - attempt to cancel the upload".format(thread_name, targz_file))
                odlu.cancel_upload_session()
                q_msg = upload_status_gen(targz_file, "error", "upload not completed successfully")
                publish_to_attempted_q(q_msg, upload_attempted_q, kill_q)
                return "upload-failed"
        except Exception as e:
            logger.error("thread: {0} - problem with _worker_upload".format(thread_name))
            logger.error(e)
            return "upload-failed"
        
        return "upload-succeeded"


def _worker_chunk_loop(fpr, targz_file, upload_attempted_q, kill_q, odlu):

    # loop through the calculated chunks and upload them
    for chunks in fpr.upload_array:
        if kill_q.empty():  # make sure the kill queue is still empty between each upload attempt
            bytes_to_send = fpr.read_file_bytes(chunks[1], fpr.file_range_size_bytes)

            upload_result = _worker_upload(bytes_to_send, targz_file, chunks, fpr, upload_attempted_q, kill_q, odlu)
            
            if upload_result == "error-empty-bytes" or upload_result == "upload-failed":
                return "upload-failed"

        else:
            return "kill-q"
    
    return "upload-success"


def _worker_start_upload_session(odlu,msgcm, targz_file, upload_attempted_q, kill_q):

    thread_name = threading.current_thread().getName()    

    # initialize the upload session to retrieve the upload URL
    if odlu.initiate_upload_session(msgcm.access_token) == False:
        q_msg = upload_status_gen(targz_file, "error", "unable to initiate upload session")
        logger.info("thread: {0} - queue msg: {1}".format(thread_name, str(q_msg)))
        publish_to_attempted_q(q_msg, upload_attempted_q, kill_q)
        return False

    return True


def file_upload_worker(to_upload_q, upload_attempted_q, kill_q):
    
    thread_name = threading.current_thread().getName()
    logger.info("starting thread {0}".format(thread_name))
    start_time = datetime.now() # initialize start time variable so that we can prevent this while loop from running forever
    
    file_upload_status = None

    while kill_q.empty():
        try:
            start_time = datetime.now() # reset the start_time variable, since we had a message on the queue   
            targz_file = to_upload_q.get_nowait()         
            odlu = OneDriveLargeUpload(targz_file) # instantiate the OneDriveLargUpload object, using the same file name as the encrypted tar.gz files
            msgcm = MSGraphCredMgr()

            if _check_token_read(msgcm, targz_file, upload_attempted_q, kill_q): # if we can read the tokens, move forward

                if _worker_start_upload_session(odlu, msgcm, targz_file, upload_attempted_q, kill_q): # if we can successfully initiate an upload session, move forward                    
                    fpr = FilePartialRead(os.path.join(Config.crypt_tar_gz_dir, targz_file), Config.onedrive_upload_chunk_size_kb) # instantiate the FilePartialRead object which will calculate how to break up the backup file during the upload
                    upload_chunks_result = _worker_chunk_loop(fpr, targz_file, upload_attempted_q, kill_q, odlu)

                    if upload_chunks_result == "upload-success":
                        upload_failed = False
                        file_upload_status = "upload-success"
                    else:
                        upload_failed = True
                        file_upload_status = "upload-fail"
                    
                    if upload_failed == False:
                        if kill_q.empty():    
                            logger.info("thread: {0} - finished uploading {1} successfully".format(thread_name, targz_file))
                            q_msg = upload_status_gen(targz_file, "complete", "successfully uploaded")
                            publish_to_attempted_q(q_msg, upload_attempted_q, kill_q)
                
                else: # when upload fails to start
                    file_upload_status = "upload-start-fail"
            else: # when check token read fails
                file_upload_status = "token-read-fail"

        except queue.Empty:
            logger.debug("thread: {0} - to upload queue is empty".format(thread_name))
            if (datetime.now() - start_time).total_seconds()/60/60 > 2:    # if the to upload queue has been empty for too long, exit this thread
                logger.info("thread: {0} - the to upload queue has been empty for more than 2 hrs, exiting this thread".format(thread_name))
                file_upload_status = "to-upload-empty-too-long"
                break
            sleep(5) # if the to upload queue is empty, wait a bit for it to get some more data
        
    try:
        kill_data = kill_q.get_nowait()

        if kill_data == "kill":
            logger.info("thread: {0} - exiting because of kill msg".format(thread_name))
            flood_kill_queue(kill_q)

    except queue.Empty:
        logger.error("thread: {0} - exited while loop, but kill queue is empty".format(thread_name))
    
    return file_upload_status


###############################################################################################################
##### ---------------------------- UPLOAD MANAGER AND HELPER FUNCTIONS ------------------------------------------

def _prime_to_upload_q(upload_file_list: list, to_upload_q, kill_q, error_q):
    thread_name = threading.current_thread().getName()

    upload_mgmt = {}

    for targz_file in upload_file_list:
        upload_mgmt[targz_file] = {"status": "not started", "retry_attempts": 0}
        try:
            to_upload_q.put(targz_file)
        except Exception as e:
            logger.error("thread: {0} - error putting targz files on the to upload queue".format(thread_name))
            logger.error(e)
            logger.error("thread: {0} - flooding kill queue".format(thread_name))
            flood_kill_queue(kill_q)
            write_to_error_q(error_q)
            return False
    return upload_mgmt

def _put_file_back_on_q(file_name: str, to_upload_q, kill_q, error_q):
    thread_name = threading.current_thread().getName()

    try:
        to_upload_q.put(file_name)
        logger.info("thread {0} - put file: {1} back on the to upload queue".format(thread_name, file_name))
    except:
        logger.error("thread {0} - problem putting file: {1} back on the to upload queue, flooding the kill queue".format(thread_name, file_name))
        write_to_error_q(error_q)
        flood_kill_queue(kill_q)
        return False
    
    return True

def _evaluate_upload_mgmt(upload_mgmt: dict, kill_q, error_q):
    thread_name = threading.current_thread().getName()
    complete_status = True
    exceed_retry = False

    for file in upload_mgmt:
        if upload_mgmt[file]["status"] != "complete":
            complete_status = False
        if upload_mgmt[file]["retry_attempts"] > 5:
            exceed_retry = True

    if complete_status == True:
        logger.info("thread: {0} - uploads are complete, putting kill on kill queue".format(thread_name))
        flood_kill_queue(kill_q)
        return True
    
    if exceed_retry == True:
        logger.error("thread {0} - too many upload attempts, putting kill on kill queue".format(thread_name))
        flood_kill_queue(kill_q)
        write_to_error_q(error_q)
        return False    
    return None

def _empty_check(start_time, kill_q, error_q):
    thread_name = threading.current_thread().getName()
    if (datetime.now() - start_time).total_seconds()/60/60 > 4: # if no messages have been posted to the upload attempted queue for four hrs, flood the kill queue
        logger.error("thread: {0} - the attempted queue has been empty for more than 4 hours, something is wrong, flooding the kill queue".format(thread_name))
        flood_kill_queue(kill_q)
        write_to_error_q(error_q)
        return False
    sleep(5) # wait for a bit before checking the queue again
    return None

def upload_manager(upload_file_list, to_upload_q, upload_attempted_q, kill_q, error_q):
    thread_name = threading.current_thread().getName()
    logger.info("starting thread {0}".format(thread_name))

    upload_mgmt = _prime_to_upload_q(upload_file_list, to_upload_q, kill_q, error_q)
    if upload_mgmt == False:
        return False

    start_time = datetime.now()    # initialize the start time variable so that we can prevent this thread from running forever
    while kill_q.empty():
        try:
            upload_info = upload_attempted_q.get_nowait()
            start_time = datetime.now() # reset the start_time variable
            logger.info("thread: {0} - upload status msg: {1}".format(thread_name, upload_info))
            logger.info("thread: {0} - current upload_mgmt: {1}".format(thread_name, upload_mgmt))
            upload_mgmt[upload_info["filename"]]["status"] = upload_info["status"]
            if upload_info["status"] == "error":
                logger.info("thread {0} - error uploading file: {1}".format(thread_name, upload_info["filename"]))
                upload_mgmt[upload_info["filename"]]["retry_attempts"] = upload_mgmt[upload_info["filename"]]["retry_attempts"] + 1

                if not _put_file_back_on_q(upload_info["filename"], to_upload_q, kill_q, error_q):  # attempt to put the file name back on the to upload queue
                    return False
            
            logger.info("thread: {0} - new upload_mgmt: {1}".format(thread_name, upload_mgmt))

            upload_mgmt_eval = _evaluate_upload_mgmt(upload_mgmt, kill_q, error_q)  # check the recently updated upload_mgmt dict to determine if uploads have completed, we have exceeded our retries, or we just need to keep going
            if upload_mgmt_eval == True or upload_mgmt_eval == False:
                return upload_mgmt_eval

        except queue.Empty:
            logger.debug("thread: {0} - upload attempted queue is empty".format(thread_name))
            if _empty_check(start_time, kill_q, error_q) == False:  # if the to upload queue has been empty for too long, break out by returning False
                return False
    
    logger.error("thread: {0} - kill queue not empty, manager thread exiting".format(thread_name))
    write_to_error_q(error_q)
    return False

#######################################################################################################################
##### ----------------------------------------------- DIR MANAGER -----------------------------------------------------

def _write_to_dir_complete_q(dir_complete_q):
    thread_name = threading.current_thread().getName()
    msg = "done"
    try:
        dir_complete_q.put(msg)
        logger.info("thread: {0} - put this message on the dir complete queue - msg: {1}".format(thread_name, str(msg)))
        return True            
    except Exception as e:
        logger.error("thread: {0} - problem putting msg on dir complete queue".format(thread_name))
        logger.error(e)
        return False

def dir_manager(kill_q, error_q, dir_complete_q):
    thread_name = threading.current_thread().getName()
    msgcm = MSGraphCredMgr()
    oddm = OneDriveDirMgr(msgcm)

    if oddm.dir_name == None:
        logger.error("thread: {0} - problem retrieving dir_name, flooding kill queue".format(thread_name))
        flood_kill_queue(kill_q)
        write_to_error_q(error_q)
        _write_to_dir_complete_q(dir_complete_q)
        return None
    
    if not oddm.create_dir():
        logger.error("thread: {0} - unable to verify or create onedrive directory, flooding kill queue".format(thread_name))
        flood_kill_queue(kill_q)
        write_to_error_q(error_q)
        _write_to_dir_complete_q(dir_complete_q)
        return None
    else:
        _write_to_dir_complete_q(dir_complete_q)
        return True



#######################################################################################################################
##### ------------------------------------------------ DOWNLOADS ------------------------------------------------------

class DownloadManager:

    @staticmethod
    def _get_download_info() -> dict:
        thread_name = threading.current_thread().getName()

        try:
            with open(Config.download_info_path) as dl_info:
                dl_json = json.load(dl_info)
        except Exception as e:
            logger.error("thread: {0} - problem reading download info file".format(thread_name))
            logger.error(e)
            return None
        
        if not DownloadManager._verify_dl_json(dl_json):
            return None
        
        return dl_json
        
    @staticmethod
    def _verify_dl_json(dl_json):
        thread_name = threading.current_thread().getName()

        if not dl_json.get("onedrive-dir"):
            logger.error("thread {0} - 'onedrive-dir' missing from download info file".format(thread_name))
            return None
        
        return True
    
    @staticmethod
    def _prime_to_download_q(to_download_q, items_to_download: list ) -> dict:
        thread_name = threading.current_thread().getName()

        download_mgr = {}

        for item in items_to_download:
            download_mgr[item.get("id")] = {"name": item.get("name"), "retry": 0, "status": "not started"}
            try:
                to_download_q.put(item)
            except Exception as e:
                logger.error("thead: {0} - error priming to_download_q".format(thread_name))
                return None
        
        return download_mgr
    

    @staticmethod
    def _get_download_list() -> list:
        thread_name = threading.current_thread().getName()

        dl_info_json = DownloadManager._get_download_info()
        if not dl_info_json:
            logger.error("thread: {0} - problem getting dir name".format(thread_name))
            return None

        dir_name = dl_info_json.get("onedrive-dir")
        if not dir_name:
            logger.error("thread: {0} - problem getting dir name".format(thread_name))
            return None
        
        msgcm = MSGraphCredMgr()

        if msgcm.read_tokens() == False:
            logger.error("thread: {0} - problem reading tokens".format(thread_name))
            return None
        
        odig = OneDriveItemGetter(msgcm.access_token, dir_name)
        file_list = odig.get_dir_items()

        if not file_list:
            logger.error("thread: {0} - problem getting file list".format(thread_name))
            return None
        
        return file_list

    @staticmethod
    def _put_file_back_on_q(id: str, name: str, to_download_q, kill_q, error_q) -> bool:
        thread_name = threading.current_thread().getName()

        try:
            to_download_q.put({"id": id, "name": name})
            logger.info("thread {0} - put file: {1} back on the to download queue".format(thread_name, name))
        except:
            logger.error("thread {0} - problem putting file: {1} back on the to download queue, flooding the kill queue".format(thread_name, name))
            write_to_error_q(error_q)
            flood_kill_queue(kill_q)
            return None
        
        return True

    @staticmethod
    def _evaluate_download_mgr(download_mgr: dict, kill_q, error_q) -> bool:
        thread_name = threading.current_thread().getName()
        complete_status = True
        exceed_retry = False

        for file in download_mgr:
            if download_mgr[file]["status"] != "complete":
                complete_status = False
            if download_mgr[file]["retry"] > 2:
                exceed_retry = True

        if complete_status == True:
            logger.info("thread: {0} - downloads are complete, putting kill on kill queue".format(thread_name))
            flood_kill_queue(kill_q)
            return True
        
        if exceed_retry == True:
            logger.error("thread {0} - too many download attempts, putting kill on kill queue".format(thread_name))
            flood_kill_queue(kill_q)
            write_to_error_q(error_q)
            return False    
        return None
    
    @staticmethod
    def _create_download_dir(kill_q, error_q) -> bool:
        thread_name = threading.current_thread().getName()

        if not os.path.isdir(Config.download_dir):
            try:
                os.mkdir(Config.download_dir)
                logger.info("thread: {0} - created download directory {1}".format(thread_name, Config.download_dir))
                return True

            except Exception as e:
                logger.error("thread: {0} - problem creating download directory".format(thread_name))
                logger.error(e)
                flood_kill_queue(kill_q)
                write_to_error_q(error_q)
                return None
        
        return False
    
    @staticmethod
    def manage_downloads(to_download_q, download_attempted_q, kill_q, error_q):
        thread_name = threading.current_thread().getName()

        DownloadManager._create_download_dir(kill_q, error_q)

        file_list = DownloadManager._get_download_list()
        if not file_list:
            flood_kill_queue(kill_q)
            write_to_error_q(error_q)
            return None

        logger.info("thread: {0} - file list retrieved  list: {1}".format(thread_name, file_list))

        download_mgr = DownloadManager._prime_to_download_q(to_download_q, file_list)
        if not download_mgr:
            flood_kill_queue(kill_q)
            write_to_error_q(error_q)
            return None
        
        logger.info("thread: {0} - to_upload_q primed".format(thread_name))


        start_time = datetime.now()    # initialize the start time variable so that we can prevent this thread from running forever
        while kill_q.empty():
            try:
                download_info = download_attempted_q.get_nowait()
                start_time = datetime.now() # reset the start_time variable
                logger.info("thread: {0} - downlaod status msg: {1}".format(thread_name, download_info))
                logger.info("thread: {0} - current download_mgr: {1}".format(thread_name, download_mgr))
                download_mgr[download_info["id"]]["status"] = download_info["status"]
                if download_info["status"] == "error":
                    logger.info("thread {0} - error downloading file: {1}".format(thread_name, download_info["name"]))
                    download_mgr[download_info["id"]]["retry"] = download_mgr[download_info["id"]]["retry"] + 1

                    if not DownloadManager._put_file_back_on_q(download_info["id"], download_info["name"], to_download_q, kill_q, error_q):  # attempt to put the file name back on the to download queue
                        return None
                
                logger.info("thread: {0} - new download_mgr: {1}".format(thread_name, download_mgr))

                download_mgr_eval = DownloadManager._evaluate_download_mgr(download_mgr, kill_q, error_q)  # check the recently updated download_mgr dict to determine if uploads have completed, we have exceeded our retries, or we just need to keep going
                if download_mgr_eval == True or download_mgr_eval == False:
                    return download_mgr_eval

            except queue.Empty:
                logger.debug("thread: {0} - download attempted queue is empty".format(thread_name))
                if _empty_check(start_time, kill_q, error_q) == False:  # if the to download queue has been empty for too long, break out by returning False
                    return False
        
        logger.error("thread: {0} - kill queue not empty, download manager thread exiting".format(thread_name))
        write_to_error_q(error_q)
        return False


class DownloadWorker:
    @staticmethod
    def _publish_to_attempted_q(q_msg, download_attempted_q, kill_q):
        thread_name = threading.current_thread().getName()
        try:
            download_attempted_q.put(q_msg)
            logger.info("thread: {0} - put this message on the attempted download queue msg: {1}".format(thread_name, str(q_msg)))
            return True
        except Exception as e:
            logger.error("thread: {0} - problem putting msg on download attempted queue, flooding kill queue".format(thread_name))
            logger.error(e)
            flood_kill_queue(kill_q)
            return False


    @staticmethod
    def _check_token_read(msgcm, download_attempted_q, kill_q, name: str, id: str):
        thread_name = threading.current_thread().getName()
        if msgcm.read_tokens() == False:
            logger.error("thread: {0} - problem reading credentials file".format(thread_name))
            q_msg = {"id": id, "name": name, "status": "error"}
            DownloadWorker._publish_to_attempted_q(q_msg, download_attempted_q, kill_q)
            return False
        return True

    @staticmethod
    def _remove_failed_download(file_name: str, kill_q, error_q) -> bool:
        thread_name = threading.current_thread().getName()

        file_path = os.path.join(Config.download_dir, file_name)

        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                logger.info("thread: {0} - failed download file {1} removed".format(thread_name, file_path))
                return True
            except Exception as e:
                logger.error("thread: {0} - failed to remove failed download file, flood kill queue".format(thread_name))
                logger.error(e)
                flood_kill_queue(kill_q)
                write_to_error_q(error_q)
                return None
        else:
            logger.warning("thread: {0} - no failed file found to delete, checked {1}".format(thread_name, file_path))
            return True
                

    @staticmethod
    def download_worker(to_download_q, download_attempted_q, kill_q, error_q):

        thread_name = threading.current_thread().getName()
        logger.info("starting thread {0}".format(thread_name))
        start_time = datetime.now() # initialize start time variable so that we can prevent this while loop from running forever
        
        # this variable is not being used again, commenting out
        #file_download_status = None

        while kill_q.empty():
            try:
                start_time = datetime.now() # reset the start_time variable, since we had a message on the queue   
                download_file = to_download_q.get_nowait()         
                msgcm = MSGraphCredMgr()

                if DownloadWorker._check_token_read(msgcm, download_attempted_q, kill_q, download_file.get("name"), download_file.get("id")): # if we can read the tokens, move forward
                    
                    file_download_info = OneDriveGetItemDetails.get_details(download_file.get("id"), msgcm.access_token)
                    if file_download_info:
                        odfdm = OneDriveFileDownloadMgr(file_download_info.get("download_url"), file_download_info.get("size_bytes"), Config.download_chunk_size_b, os.path.join(Config.download_dir,download_file.get("name")) , file_download_info.get("sha256hash"))
                        download_result = odfdm.download_file()

                        if download_result == True:
                            q_msg = {"id": download_file.get("id"), "name": download_file.get("name"), "status": "complete"}
                            DownloadWorker._publish_to_attempted_q(q_msg, download_attempted_q, kill_q)
                        
                        else:
                            q_msg = {"id": download_file.get("id"), "name": download_file.get("name"), "status": "error"}
                            DownloadWorker._remove_failed_download(download_file.get("name"), kill_q, error_q)
                            DownloadWorker._publish_to_attempted_q(q_msg, download_attempted_q, kill_q)

                    
            except queue.Empty:
                logger.debug("thread: {0} - to download queue is empty".format(thread_name))
                if (datetime.now() - start_time).total_seconds()/60/60 > 2:    # if the to download queue has been empty for too long, exit this thread
                    logger.info("thread: {0} - the to download queue has been empty for more than 2 hrs, exiting this thread".format(thread_name))
                    break
                sleep(5) # if the to upload queue is empty, wait a bit for it to get some more data
            
        try:
            kill_data = kill_q.get_nowait()

            if kill_data == "kill":
                logger.info("thread: {0} - exiting because of kill msg".format(thread_name))
                flood_kill_queue(kill_q)

        except queue.Empty:
            logger.error("thread: {0} - exited while loop, but kill queue is empty".format(thread_name))
        
        return None



class DownloadDecrypter:
    
    @staticmethod
    def _get_downloaded_gz_files() -> list:
        try:
            file_list = sorted(os.listdir(Config.download_dir))
        except Exception as e:
            logger.error("Problem getting list of downloaded tar.gz files from {0}".format(Config.download_dir))
            return None
        
        if not file_list:
            logger.error("No files are currently in {0}".format(Config.download_dir))
            return None
        
        return file_list
    

    @staticmethod
    def _extract_tar_gzs(file_list: list) -> bool:

        for targz in file_list:
            full_path = os.path.join(Config.download_dir, targz)
            if not extract_tar_gz(full_path, Config.extract_dir, keep_targz=False):
                return None        
        return True
   
    
    @staticmethod
    def _decrypt() -> bool:

        download_json = DownloadManager._get_download_info() # reusing this method to get the json out of the download info json file
        if not download_json:
            logger.error("problem getting download info")
            return None
        
        restore_file_name = download_json.get("onedrive-dir")
        if not restore_file_name:
            logger.error("no onedrive-dir in download info json")
            return None
        
        crypt = Crypt(Config.key_path)

        restore_file_path = os.path.join(Config.var_basedir, restore_file_name + ".vma.zst")

        if crypt.chunk_decrypt(Config.extract_dir, restore_file_path, removeorig=True) == True:
            logger.info("finished decrypting and reassembling {0}".format(restore_file_path))
            return True

        logger.error("problem decrypting and reassembling file")
        return None

    @staticmethod
    def _fetch_hash(onedrive_dir: str) -> str:
        try:
            with open(Config.etc_basedir + "sha256hash_" + onedrive_dir, "r") as hash_file:
                hash_256 = hash_file.read()
            return hash_256

        except Exception as e:
            logger.error("failed to fetch sha256 hash")
            return None

    
    @staticmethod
    def _verify_hash() -> bool:
        try:
            with open(Config.download_info_path, "r") as download_info_file:
                download_info = json.load(download_info_file)
        
        except Exception as e:
            logger.error("failed to read download info file")
            return None

        original_hash_256 = DownloadDecrypter._fetch_hash(download_info.get("onedrive-dir"))

        if original_hash_256:
            download_hash_obj = Sha256Calc(os.path.join(Config.var_basedir, download_info.get("onedrive-dir") + ".vma.zst"))
            download_hash = download_hash_obj.calc()
            if download_hash:
                if original_hash_256 == download_hash:
                    logger.info("original sha 256 hash and downloaded and combined sha 256 hash match!")
                    return True
                logger.error("original sha 256 hash and downloaded and combined sha 256 hash do not match")
                return None
            logger.error("problem getting sha256 for downloaded and combined file")
            return None
        logger.error("problem getting original sha 256 hash")
        return None
            

    
    @staticmethod
    def decrypt_and_combine() -> bool:
        
        file_list = DownloadDecrypter._get_downloaded_gz_files()
        if not file_list:
            return None
        
        extract_result = DownloadDecrypter._extract_tar_gzs(file_list)
        if not extract_result:
            return None
        
        if DownloadDecrypter._decrypt() == True:
            logger.info("decrypt and combine complete")
            if DownloadDecrypter._verify_hash() == True:
                logger.info("sha256 hash verified, backup file is intact")
                return True
            else:
                logger.error("sha256 hash for decrypted and combined file does not match the hash before upload")
        
        logger.error("problem with decrypt and combine")
        return None


    
    