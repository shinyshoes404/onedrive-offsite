from onedrive_offsite.utils import make_tar_gz, file_cleanup, download_file_email, decrypt_email
from onedrive_offsite.crypt import Crypt, Sha256Calc
from onedrive_offsite.config import Config
from onedrive_offsite.workers import token_refresh_worker, file_upload_worker, upload_manager, dir_manager, DownloadWorker, DownloadManager, DownloadDecrypter

from queue import Queue
from time import sleep
import os, json, logging, math, threading

# Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(Config.LOG_LEVEL)
logger.addHandler(Config.FILE_HANDLER)
logger.addHandler(Config.STOUT_HANDLER)


def crypt_file_build():

    # calculate the max number of encrypted chunks we can include in our tar.gz file
    max_chunks_to_add = math.floor(Config.crypt_tar_gz_max_size_mb/Config.crypt_chunk_size_mb)
    if max_chunks_to_add == 0:
        logger.error("Your max crypt tar gz file size is smaller than your crypt chunk file size. You need to adjust your configuration before combining your crypt chunks into a tar.gz file.")
        # bail out, cleanup files, and send notification email
        file_cleanup(error=True)
        return False

    # instantiate the Crypt object
    crypt = Crypt(Config.key_path)

    try:
        # fetch the backup file descriptive information
        with open(Config.backup_file_info_path, "r") as file:
            backup_file_info = json.load(file)
    except Exception as e:
        logger.error("problem reading backup_file_info_path in crypt_uplod()")
        logger.error(e)
        # bail out, cleanup files, and send notification email
        file_cleanup(error=True)
        return False
    
    # create our backup chunk dir if it doesn't exist
    if os.path.isdir(Config.crypt_chunk_dir) == False:
        try:
            os.mkdir(Config.crypt_chunk_dir)
        except Exception as e:
            logger.error("problem creating crypt_chunk_dir in crypt_upload()")
            logger.error(e)
            # bail out, cleanup files, and send notification email
            file_cleanup(error=True)
            return False

    # capture the sha256 check sum for our backup file before we modify and upload it
    hash_obj = Sha256Calc(backup_file_info.get("backup-file-path"))
    hash_256 = hash_obj.calc()
    if hash_256:
        # store the hash in a file
        try:
            with open(os.path.join(Config.etc_basedir, "sha256hash_" + backup_file_info.get("onedrive-dir")), "w") as hash_file:
                hash_file.write(hash_256)
        except Exception as e:
            logger.error("failed to write 256 hash file for {0}".format(backup_file_info.get("backup-file-path")))
            logger.error(e)
            
    else:
        logger.warning("could not calculate the sha 256 hash for {0}".format(backup_file_info.get("backup-file-path")))
    
    # break our backup file into encrypted chunks
    if crypt.chunk_encrypt(backup_file_info.get("backup-file-path"), Config.crypt_chunk_dir, Config.crypt_chunk_size_mb) == False:
        # bail out, cleanup files, and send notification email
        file_cleanup(error=True)
        return False
    
    # make sure our targz directory exists
    if os.path.isdir(Config.crypt_tar_gz_dir) == False:
        os.mkdir(Config.crypt_tar_gz_dir)

    if os.environ.get("ONEDRIVE_NAME") != None:
        base_file_name = os.environ.get("ONEDRIVE_NAME")
    else:
        base_file_name = Config.onedrive_upload_default_filename
    
    logger.debug("Using base_file_name = {0}".format(base_file_name))

    # combine all of the encrypted chunks into tar.gz files - deleting the encrypted chunks as they are added to the tar.gz file
    if make_tar_gz(Config.crypt_chunk_dir, os.path.join(Config.crypt_tar_gz_dir),max_chunks_to_add, base_file_name, removeorig=True) == False:
        # bail out, cleanup files, and send notification email
        file_cleanup(error=True)
        return False

    return True


def crypt_file_upload():

    to_upload_q = Queue()
    upload_attempted_q = Queue()
    kill_q = Queue()
    error_q = Queue()

    upload_file_list = sorted(os.listdir(Config.crypt_tar_gz_dir))

    credential_thread = threading.Thread(target=token_refresh_worker, name="cred-thread", args=[kill_q, error_q])
    directory_manager = threading.Thread(target=dir_manager, name="dir-manager", args=[kill_q, error_q])
    manager_thread = threading.Thread(target=upload_manager, name="manager-thread", args=[upload_file_list, to_upload_q, upload_attempted_q, kill_q, error_q])
    upload_thread_1 = threading.Thread(target=file_upload_worker, name="worker-thread-1", args=[to_upload_q, upload_attempted_q, kill_q])
    upload_thread_2 = threading.Thread(target=file_upload_worker, name="worker-thread-2", args=[to_upload_q, upload_attempted_q, kill_q])
    upload_thread_3 = threading.Thread(target=file_upload_worker, name="worker-thread-3", args=[to_upload_q, upload_attempted_q, kill_q])
    upload_thread_4 = threading.Thread(target=file_upload_worker, name="worker-thread-4", args=[to_upload_q, upload_attempted_q, kill_q])
    upload_thread_5 = threading.Thread(target=file_upload_worker, name="worker-thread-5", args=[to_upload_q, upload_attempted_q, kill_q])

    credential_thread.start()
    sleep(5)
    directory_manager.start()
    sleep(50)
    manager_thread.start()
    sleep(2)
    upload_thread_1.start()
    upload_thread_2.start()
    upload_thread_3.start()
    upload_thread_4.start()
    upload_thread_5.start()

    credential_thread.join()
    directory_manager.join()
    manager_thread.join()
    upload_thread_1.join()
    upload_thread_2.join()
    upload_thread_3.join()
    upload_thread_4.join()
    upload_thread_5.join()

    if not error_q.empty():
        # bail out, cleanup files, and send notification email
        file_cleanup(error=True)
        return False
    
    # cleanup files and send notification emaisl
    cleanup_status = file_cleanup()
    
    if cleanup_status == False:
        return False
    else:
        return True


# build the encrypted tar.gz file and upload it
def crypt_file_build_and_upload():
    if crypt_file_build() == False:
        return False
    else:
        if crypt_file_upload() == False:
            return False
        else:
            return True


def download():

    to_download_q = Queue()
    download_attempted_q = Queue()
    kill_q = Queue()
    error_q = Queue()

    credential_thread = threading.Thread(target=token_refresh_worker, name="cred-thread-down", args=[kill_q, error_q])
    download_manager = threading.Thread(target=DownloadManager.manage_downloads, name="download-manager", args=[to_download_q, download_attempted_q, kill_q, error_q])
    download_thread_1 = threading.Thread(target=DownloadWorker.download_worker, name="download-1", args=[to_download_q, download_attempted_q, kill_q, error_q])
    download_thread_2 = threading.Thread(target=DownloadWorker.download_worker, name="download-2", args=[to_download_q, download_attempted_q, kill_q, error_q])
    download_thread_3 = threading.Thread(target=DownloadWorker.download_worker, name="download-3", args=[to_download_q, download_attempted_q, kill_q, error_q])
    download_thread_4 = threading.Thread(target=DownloadWorker.download_worker, name="download-4", args=[to_download_q, download_attempted_q, kill_q, error_q])
    download_thread_5 = threading.Thread(target=DownloadWorker.download_worker, name="download-5", args=[to_download_q, download_attempted_q, kill_q, error_q])

    credential_thread.start()
    sleep(5)
    download_manager.start()
    sleep(5)
    download_thread_1.start()
    download_thread_2.start()
    download_thread_3.start()
    download_thread_4.start()
    download_thread_5.start()

    credential_thread.join()
    download_manager.join()
    download_thread_1.join()
    download_thread_2.join()
    download_thread_3.join()
    download_thread_4.join()
    download_thread_5.join()

    if not error_q.empty():
        # bail out send notification email
        download_file_email(error=True)
        return None
    
    # cleanup files and send notification emaisl
    email_status = download_file_email()
    
    if email_status == False:
        return False
    else:
        return True

def restore() -> bool:
    download_result = download()

    if download_result == True or download_result == False:
        if DownloadDecrypter.decrypt_and_combine():
            logger.info("restore complete")
            if decrypt_email():
                return True
            
            return False
            
        else:
            logger.error("problem decrypting and combining")
            decrypt_email(error=True)
            return None
    else:
        logger.error("problem downloading")
        return None