import os, platform, logging, sys
from logging.handlers import RotatingFileHandler


class Config:

    ### ENCRYPTION KEY ###
    key_name = "onedrive-offsite"
    key_extension = ".key"
    
    ### DEFAULT UPLOAD FILE NAME ###
    if os.environ.get("ONEDRIVE_DEFAULT_FILE_NAME") != None:
        onedrive_upload_default_filename = os.environ.get("ONEDRIVE_DEFAULT_FILE_NAME")
    else:
        onedrive_upload_default_filename = "onedrive_offsite_backup.tar.gz"

    ### UPLOAD THEADING ###
    upload_threads = 3

    ### WHERE TO FIND FILES AND FLASK DEBUG ###
    if os.environ.get("ONEDRIVE_ENV") == "dev":
        etc_basedir = os.path.abspath(os.path.dirname(__file__))
        etc_basedir = os.path.join(etc_basedir, '../../')
        var_basedir = etc_basedir
        flask_debug = True

    
    else:
        if platform.system() == "Linux":
            etc_basedir = '/etc/onedrive-offsite'
            var_basedir = '/var/onedrive-offsite'
        elif platform.system() == "Windows":
            etc_basedir = "C:\\Users\\" + os.getlogin() + "\\.onedrive-offsite"
            var_basedir = etc_basedir
        flask_debug = False

    app_json_path = os.path.join(etc_basedir, "app_info.json")
    oauth2_json_path = os.path.join(etc_basedir, "oauth2_creds.json")
    key_path = os.path.join(etc_basedir, key_name + key_extension)
    backup_file_info_path = os.path.join(etc_basedir, "backup_file_info.json")
    crypt_chunk_dir = os.path.join(var_basedir, "backup_crypt_chunks/")
    crypt_tar_gz_dir = os.path.join(var_basedir, "crypt_tar_gz/")
    crypt_tar_gz_path = os.path.join(var_basedir, onedrive_upload_default_filename)
    crypt_chunk_size_mb = 30

    cred_mgr_lock_path = os.path.join(etc_basedir, "cred_mgr_lock")

    ### DOWNLOAD CONFIG
    download_info_path = os.path.join(etc_basedir, "download_info.json")
    download_dir = os.path.join(var_basedir, "download/")
    download_chunk_size_b = 10485760
    extract_dir = os.path.join(var_basedir, "extracted_crypt")

    ### FILE SIZES ###
    if os.environ.get("TESTING_ENV") == "test" or os.environ.get("TESTING_ENV") == "test-dev" or os.environ.get("TESTING_ENV") == "test-live":
        crypt_tar_gz_max_size_mb = 90     
        onedrive_upload_chunk_size_kb = 10485.76
    
    else:    
        crypt_tar_gz_max_size_mb = 10000     # note: microsoft will only allow you upload a max file size of 268 GB.
        onedrive_upload_chunk_size_kb = 10485.76 # per microsoft's documentation, the optimal fragment size for high speed internet connections is 10,485,760 bytes

    ### --- API PARAMETERS --- ###
    # some of these are used for automated testing with a test api not included with this repo

    # -- URLs
    if os.environ.get("TESTING_ENV") == "test":
        token_url = "http://msgraphonedrive-testapi:8000"
        api_url = "http://msgraphonedrive-testapi:8000"

    elif os.environ.get("TESTING_ENV") == "test-dev":
        token_url = "http://localhost:5000"
        api_url = "http://localhost:5000"
    
    else: # test-live will also use these
        token_url = "https://login.microsoftonline.com"
        api_url = "https://graph.microsoft.com"

    api_timeout = (10, 60)        # This will be used for our API requests. The requests library does not timeout by defualt
                                    # which could cause our app to hang forever. The tuple represents (connect_timeout_seconds, read_data_seconds)
                                    # So, if this config value is (10, 60), the request will timeout if connecting takes longer than
                                    # 10 seconds or reading/sending data takes longer than 60 seconds. The typical upload request pushes
                                    # 10 MB to the onedrive api at a time. 60 seconds should be plenty for that to complete.

    
    ### --- LOG PARAMETERS --- ###
    LOG_PATH = os.path.join(etc_basedir, "onedrive-offsite.log")
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = logging.Formatter(" %(asctime)s - [%(levelname)s] - %(name)s - %(message)s", "%Y-%m-%d %H:%M:%S %z")
    LOG_MAXBYTES = 20000000
    LOG_BACKUP_COUNT = 1
 
    FILE_HANDLER = RotatingFileHandler(LOG_PATH, maxBytes=LOG_MAXBYTES, backupCount=LOG_BACKUP_COUNT) 
    FILE_HANDLER.setLevel(LOG_LEVEL)
    FILE_HANDLER.setFormatter(LOG_FORMAT)

    STOUT_HANDLER = logging.StreamHandler(sys.stdout)
    STOUT_HANDLER.setLevel(LOG_LEVEL)
    STOUT_HANDLER.setFormatter(LOG_FORMAT)


    #### --- EMAIL CONFIG --- ###
    email_to = "shinyshoes404@protonmail.com"
    email_from_addr = "onedrive-backup@cloud.alden.swilsycloud.com"
    email_from_name = "onedrive-offsite"
    aws_region = "us-west-2"

