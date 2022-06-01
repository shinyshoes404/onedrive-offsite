import requests, json, logging, time, threading, os, mock, math
from onedrive_offsite.config import Config
from onedrive_offsite.crypt import Sha256Calc
from onedrive_offsite.utils import read_backup_file_info
from datetime import datetime, timedelta

if os.environ.get("TESTING_ENV") == "test":
    sleep = mock.Mock()
    sleep.return_value = None
else:
    from time import sleep

# Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(Config.LOG_LEVEL)
logger.addHandler(Config.FILE_HANDLER)
logger.addHandler(Config.STOUT_HANDLER)

class OneDriveLargeUpload:
    def __init__(self, upload_file_name: str):
        # initialize some properties
        self.file_name = upload_file_name
        self.onedrive_upload_url = None
        self.onedrive_upload_exp = None
        self.thread_name = threading.current_thread().getName()

        try:
            with open(Config.backup_file_info_path, "r") as info_file:
                info_json = json.load(info_file)

            if info_json.get("onedrive-dir") == None or info_json.get("onedrive-dir") == "":
                logger.error("thread: {0} - no onedrive-dir in backup file info".format(self.thread_name))
                self.dir_name = None
            else:
                self.dir_name = info_json.get("onedrive-dir")
            
            if info_json.get("onedrive-dir-id") == None or info_json.get("onedrive-dir-id") == "":
                logger.error("thread: {0} - no onedrive-dir-id in backup file info".format(self.thread_name))
                self.dir_id = None
            else:
                self.dir_id = info_json.get("onedrive-dir-id")

        except Exception as e:
            logger.error("thread: {0} - problem reading backup file info to get directory info".format(self.thread_name))
            logger.error(e)
            self.dir_name = None
            self.dir_id = None     


    @staticmethod
    def _upload_initiate_retry(retry_count: int, file_name: str) -> bool:
        thread_name = threading.current_thread().getName()
        if retry_count == 1:
            time.sleep(10)
            logger.warning("thread: {0} - Retry 1 to initiate upload session for file: {1}".format(thread_name, file_name))
            return True
        elif retry_count == 2:
            time.sleep(60)
            logger.warning("thread: {0} - Retry 2 to initiate upload session for file: {1}".format(thread_name, file_name))
            return True
        elif retry_count == 3:
            time.sleep(300)
            logger.warning("thead: {0} - Retry 3 to initiate upload session for file: {1}".format(thread_name, file_name))
            return True
        if retry_count > 3:
            return False

    def initiate_upload_session(self, access_token):
         
        api_url = Config.api_url + '/v1.0/me/drive/items/' + self.dir_id + '/children/' + self.file_name +'/createUploadSession'
        headers = {'Content-type': 'application/json'}
        headers['Authorization'] = "Bearer " + access_token
        body = { "item" : {"name" : self.file_name}}      
        
        retry_flag = True
        retry_count = 0

        logger.info("thread: {0} - attempt to create uplodad session for file: {1}".format(self.thread_name, self.file_name))
        while retry_flag == True:
            timeout = False
            ssl_err = False
            conn_err = False
            
            try:
                # send our post request to the microsoft graph api to get an upload session url to use for uploading our large file a piece at a time
                upload_session_response = requests.post(url=api_url, headers=headers, json=body, timeout=Config.api_timeout)
                upload_session_response.close()

            except requests.exceptions.Timeout:
                logger.warning("thread: {0} - Session create request timeout".format(self.thread_name))
                retry_count = retry_count + 1
                timeout = True
                retry_flag = self._upload_initiate_retry(retry_count, self.file_name)
                       
            except requests.exceptions.SSLError:
                logger.warning("thread: {0} - SSL error - upload initiation".format(self.thread_name))
                ssl_err = True
                retry_count = retry_count + 1
                retry_flag = self._upload_initiate_retry(retry_count, self.file_name)

            except requests.exceptions.ConnectionError:
                logger.warning("thread: {0} - Connection error".format(self.thread_name))
                conn_err = True
                retry_count = retry_count + 1
                retry_flag = self._upload_initiate_retry(retry_count, self.file_name)

            except Exception as e:
                logger.error("thread: {0} - issue with post request in initiate_upload_session()".format(self.thread_name))
                logger.error(e)
                return False

            if timeout == True or ssl_err == True or conn_err == True:
                if retry_flag == False:
                    return False
            
            elif upload_session_response.status_code == 200:
                response_body = upload_session_response.json()
                self.onedrive_upload_url = response_body.get("uploadUrl")
                self.onedrive_upload_exp = response_body.get("expirationDateTime")
                logger.info("thread: {0} - Upload session created".format(self.thread_name))
                logger.info("thread: {0} ------ upload URL -------".format(self.thread_name))
                logger.info("thread: {0} - {1}".format(self.thread_name, self.onedrive_upload_url))
                logger.info("thread: {0} ---------------------------".format(self.thread_name))
                return True

            elif upload_session_response.status_code == 500 or upload_session_response.status_code == 502 or upload_session_response.status_code == 503 or upload_session_response.status_code == 504:
                logger.info("thread: {0} - Service problem".format(self.thread_name))
                logger.info("thread: {0} - Status code: {1}".format(self.thread_name, upload_session_response.status_code))
                logger.info("thread: {0} - Body: {1}".format(self.thread_name, upload_session_response.content))
                retry_count = retry_count + 1
                retry_flag = self._upload_initiate_retry(retry_count, self.file_name)
                if retry_flag == False:
                    return False

            else:
                logger.error("thread: {0} - Problem creating upload session.\n status code: {1}\n response body: {2}".format(self.thread_name, upload_session_response.status_code, upload_session_response.json()))
                return False



    @staticmethod
    def _retry_logic(content_range_bytes: str, retry_count: int) -> bool:
        
        thread_name = threading.current_thread().getName()

        if retry_count == 1:
            time.sleep(15)
            logger.info("thread: {0} - Retry 1 for range {1}".format(thread_name, content_range_bytes))
            return True
        elif retry_count == 2:
            time.sleep(600)
            logger.info("thread: {0} - Retry 2 for range {1}".format(thread_name, content_range_bytes))
            return True
        elif retry_count == 3:
            time.sleep(1800)
            logger.info("thread: {0} - Retry 3 for range {1}".format(thread_name, content_range_bytes))
            return True
        if retry_count > 3:
            return False

    def upload_file_part(self, file_size_bytes: str, content_length_bytes: str, content_range_bytes: str, bytes_to_upload: bytes, flag_416=False):
        headers = {"Content-Length": content_length_bytes, "Content-Range": "bytes " + content_range_bytes + "/" + file_size_bytes}
        logger.debug("thread: {0} - Content-Length ".format(self.thread_name) + str(headers.get("Content-Length")))
        logger.info("thread: {0} - Content-Range ".format(self.thread_name) + headers.get("Content-Range"))

        retry_flag = True
        retry_count = 0
        
        while retry_flag == True:
            timeout = False
            ssl_err = False
            conn_err = False
            try:
                upload_response = requests.put(url=self.onedrive_upload_url, headers=headers, data=bytes_to_upload, timeout=Config.api_timeout)
                upload_response.close()
            except requests.exceptions.Timeout:
                logger.warning("thread: {0} - Upload request timeout.".format(self.thread_name))
                retry_count = retry_count + 1
                timeout = True
                retry_flag = self._retry_logic(content_range_bytes, retry_count)
            
            except requests.exceptions.SSLError:
                logger.warning("thread: {0} - SSL error".format(self.thread_name))
                ssl_err = True
                retry_count = retry_count + 1
                retry_flag = self._retry_logic(content_range_bytes, retry_count)

            except requests.exceptions.ConnectionError:
                logger.warning("thread: {0} - Connection error".format(self.thread_name))
                conn_err = True
                retry_count = retry_count + 1
                retry_flag = self._retry_logic(content_range_bytes, retry_count)

            except Exception as e:
                logger.error("thread: {0} - problem with file part upload in upload_file_part()".format(self.thread_name))
                logger.error(e)
                return False

            if timeout == True or ssl_err == True or conn_err == True:
                if retry_flag == False:
                    return False
            
            elif upload_response.status_code == 202:
                logger.info("thread: {0} - Upload accepted for range {1}".format(self.thread_name, content_range_bytes))
                retry_flag = False

            elif upload_response.status_code == 200 or upload_response.status_code == 201:                
                resp_json = upload_response.json()
                logger.info("thread: {0} - Upload complete".format(self.thread_name))
                logger.info("thread: {0} - File name: {1} size (bytes): {2}".format(self.thread_name, resp_json.get("name"), resp_json.get("size")))
                retry_flag = False

            elif upload_response.status_code == 500 or upload_response.status_code == 502 or upload_response.status_code == 503 or upload_response.status_code == 504:
                logger.info("thread: {0} - Service problem".format(self.thread_name))
                logger.info("thread: {0} - Status code: {1}".format(self.thread_name, upload_response.status_code))
                logger.info("thread: {0} - Body: {1}".format(self.thread_name, upload_response.content))
                retry_count = retry_count + 1
                retry_flag = self._retry_logic(content_range_bytes, retry_count)

            elif upload_response.status_code == 416 and flag_416 == False:
                logger.info("thread: {0} - attempting partial fragment retry".format(self.thread_name))
                partial_retry_result = self._retry_partial_fragment(file_size_bytes, content_range_bytes, bytes_to_upload)
                if partial_retry_result == False:
                    logger.error("thread: {0} - partial fragment retry failed".format(self.thread_name))
                elif partial_retry_result == "move-next":
                    logger.info("thread: {0} - partial retry - returning 'move-next'".format(self.thread_name))
                    return "move-next"
                elif partial_retry_result == "upload-complete":
                    logger.info("thread: {0} - partial retry - returning 'upload-complete'".format(self.thread_name))
                    return "upload-complete"
                else:
                    upload_response = partial_retry_result
                    logger.info("thread: {0} - partial fragment retry succeeded".format(self.thread_name))
                retry_flag = False

            elif upload_response.status_code == 416 and flag_416 == True:
                logger.info("thread: {0} - Problem with specific byte range after retry. Stopping retries.".format(self.thread_name))
                logger.info("thread: {0} - status code: {1} body: {2}".format(self.thread_name, upload_response.status_code, upload_response.content))
                retry_flag = False

            else:
                logger.info("thread: {0} - Problem uploading data".format(self.thread_name))
                logger.info("thread: {0} - status code: {1} body: {2}".format(self.thread_name, upload_response.status_code, upload_response.content))
                retry_count = retry_count + 1
                retry_flag = self._retry_logic(content_range_bytes, retry_count)
                
        return upload_response

    def _partial_retry_upload(self, file_size_bytes, remaining_len, remaining_range, remaining_bytes, flag_416):

        partial_retry_resp = self.upload_file_part(file_size_bytes, remaining_len, remaining_range, remaining_bytes, flag_416=flag_416)

        if partial_retry_resp.status_code != 200 and partial_retry_resp.status_code != 201 and partial_retry_resp.status_code != 202:
            logger.warning("thread: {0} - partial fragment retry failed".format(self.thread_name))
            logger.warning("thread: {0} - status code: {1}, content: {2}".format(self.thread_name, partial_retry_resp.status_code, partial_retry_resp.content))
            return False

        return partial_retry_resp
    
    def _retry_partial_fragment(self,file_size_bytes: str, byte_range: str, bytes_fragment: bytes):
        logger.info("thread: {0} - checking upload status".format(self.thread_name))
        # get the current status of the upload session
        try:
            status_resp = requests.get(self.onedrive_upload_url, timeout=Config.api_timeout)
            status_json = status_resp.json()
            logger.info("thread: {0} - current upload status {1}".format(self.thread_name, status_json))
        except Exception as e:
            logger.error("thread: {0} - failed to fetch upload status".format(self.thread_name))
            return False
        
        # if we get a 400 status because upload session isn't found, check to see if the file was updated recently
        # if so, we probably just completed our last chunk
        if status_resp.status_code == 400:
            if status_json.get("error"):
                if status_json["error"].get("innererror"):
                    if status_json["error"]["innererror"].get("code") == "uploadSessionNotFound":
                        logger.info("thread: {0} - the upload session does not exist, checking to see if the file was modified recently".format(self.thread_name))
                        if self._check_file_update_recent():
                            logger.info("thread: {0} - assuming {1} uploaded successfully".format(self.thread_name, self.file_name))
                            return "upload-complete"
                        else:
                            return False
                        
        
        # get the next byte expected by onedrive
        next_expected_byte = int(status_json.get("nextExpectedRanges")[0][:status_json.get("nextExpectedRanges")[0].find("-")])

        # what was the end of the fragment that we were uploading
        fragment_end = int(byte_range[-byte_range.find("-"):])

        # what was the start of the fragment that we were uploading
        fragment_start = int(byte_range[:byte_range.find("-")])

        # check to see if the next expected byte is the top of our current range + 1, if yes, then the MS api must have actually received our last upload
        if next_expected_byte == fragment_end + 1:
            logger.info("thread: {0} - it looks like our last upload was actually accepted, move on to the next chunk".format(self.thread_name))
            return "move-next"

        # check if the expected next byte is not in our current range
        if next_expected_byte < fragment_start or next_expected_byte > fragment_end:
            logger.error("thread: {0} - next expected byte is outside of our fragment range".format(self.thread_name))
            return False
        
        remaining_bytes = bytes_fragment[-(fragment_end-next_expected_byte+1):]
        remaining_range = str(next_expected_byte) + "-" + str(fragment_end)
        remaining_len = str(len(remaining_bytes))

        logger.info("thread: {0} - partial retry - waiting for 5 min before attempting upload of partial fragment".format(self.thread_name))
        sleep(300)

        logger.info("thread: {0} - partial retry info - file_size_bytes: {1} remaining_len: {2} remaining_range: {3}".format(self.thread_name, file_size_bytes, remaining_len, remaining_range))
        
        partial_retry_resp = self._partial_retry_upload(file_size_bytes, remaining_len, remaining_range, remaining_bytes, flag_416=True)

        if partial_retry_resp == False:
            logger.warning("thread: {0} - first partial retry failed, waiting for 20 min".format(self.thread_name))
            sleep(1200)
            logger.info("thread: {0} - partial retry info - file_size_bytes: {1} remaining_len: {2} remaining_range: {3}".format(self.thread_name, file_size_bytes, remaining_len, remaining_range))
            partial_retry_resp = self._partial_retry_upload(file_size_bytes, remaining_len, remaining_range, remaining_bytes, flag_416=True)
            if partial_retry_resp == False:
                logger.error("thread: {0} - first partial retry failed retry, stop retrying".format(self.thread_name))
                return False

        return partial_retry_resp

  
    def cancel_upload_session(self):
        try:
            cancel_resp = requests.delete(url=self.onedrive_upload_url, timeout=Config.api_timeout)
            cancel_resp.close()
        except Exception as e:
            logger.error("thread: {0} - problem with cancel upload session delete request in cancel_upload_session()".format(self.thread_name))
            logger.error(e)
            return False

        if cancel_resp.status_code == 204:
            logger.info("thread: {0} - Upload successfully canceled".format(self.thread_name))
            return True
        else:
            logger.info("thread: {0} - Problem cancelling upload status code: {1}   response body: {2}".format(self.thread_name, cancel_resp.status_code, cancel_resp.content))
            return False
    
    def _check_file_update_recent(self) -> bool:
        msgcm = MSGraphCredMgr()
        if not msgcm.read_tokens():
            logger.error("thread: {0} - problem reading tokens while seeing if upload finished".format(self.thread_name))
            return None
        
        odig = OneDriveItemGetter(msgcm.access_token, self.dir_name)
        item_info = odig.find_item(self.file_name)
        if not item_info:
            logger.error("thread: {0} - unable to find item {1}".format(self.thread_name, self.file_name))
            return None
        
        last_mod_datetime = datetime.strptime(item_info.get("last-mod"), "%Y-%m-%dT%H:%M:%S.%fZ" )
        if last_mod_datetime >= datetime.utcnow() - timedelta(minutes=15):
            logger.info("thread: {0} - file {1} was updated in the last 15 min".format(self.thread_name, self.file_name))
            return True
        else:
            logger.warning("thread: {0} - file {1} has not been updated in the last 15 min. Last updated {2}".format(self.thread_name, self.file_name, item_info.get("last-mod")))
            return False





class MSGraphCredMgr:
    def __init__(self, oauth2_file_path=None, app_file_path=None):

        # If no oauth2 file path was provided, set a default path based on Config
        if oauth2_file_path == None:
            self.oauth2_file_path = Config.oauth2_json_path
        else:
            self.oauth2_file_path = oauth2_file_path
        
        # if no app file path was provided, set a default path based on Config
        if app_file_path == None:
            self.app_file_path = Config.app_json_path
        else:
            self.app_file_path = app_file_path
        
        self.thread_name = threading.current_thread().getName()


    def read_tokens(self):
        try:
            with open(self.oauth2_file_path, 'r') as json_file:
                creds_json = json.load(json_file)
                self.access_token = creds_json.get("access_token")
                self.refresh_token = creds_json.get("refresh_token")
                self.expires = datetime.strptime(creds_json.get("expires"),'%Y-%m-%d %H:%M:%S')
            
        except Exception as e:
            logger.error("thread: {0} - problem reading tokens in read_tokens".format(self.thread_name))
            logger.error(e)
            return False
        
        return True

    
    def refresh_tokens(self):
        body_data = {"grant_type":"refresh_token"}
        body_data["refresh_token"] = self.refresh_token
        headers = {"Content-type":"application/x-www-form-urlencoded"}
        headers["Authorization"] = "bearer " + self.access_token

        try:
            with open(self.app_file_path, 'r') as json_file:
                app_json = json.load(json_file)
                body_data["client_id"] = app_json.get("client_id")
                body_data["client_secret"] = app_json.get("client_secret")
                body_data["redirect_uri"] = app_json.get("redirect_uri")
        
        except Exception as e:
            logger.error("thread: {0} - problem reading app information from app_file_path in refresh_tokens()".format(self.thread_name))
            logger.error(e)
            return False
        
        token_url = Config.token_url + "/consumers/oauth2/v2.0/token"

        try:
            # body_data dict will be form url encoded automatically when we pass it in as the data= argument
            refresh_token_resp = requests.post(url=token_url, data=body_data, headers=headers, timeout=Config.api_timeout)
        
        except Exception as e:
            logger.error("thread: {0} - problem with post request to refresh access token in refresh_tokens()".format(self.thread_name))
            logger.error(e)
            return False

        if refresh_token_resp.status_code == 200:
            resp_json = refresh_token_resp.json()
            self.access_token = resp_json.get("access_token")
            self.refresh_token = resp_json.get("refresh_token")
            
            try:
                with open(self.oauth2_file_path, 'w') as json_file:
                    json_data = {}
                    json_data["access_token"] = resp_json.get("access_token")
                    json_data["refresh_token"] = resp_json.get("refresh_token")
                    expires = (datetime.now() + timedelta(seconds=resp_json.get("expires_in"))).strftime('%Y-%m-%d %H:%M:%S')
                    json_data["expires"] = expires
                    json.dump(json_data, json_file)
                    logger.info("thread: {0} - tokens refreshed".format(self.thread_name))
                    return True
            except Exception as e:
                logger.error("thread: {0} - problem writing to oauth2_file_path in refresh_tokens()".format(self.thread_name))
                logger.error(e)
                return False
        
        else:
            logger.info("thread: {0} - Problem with token refresh".format(self.thread_name))
            logger.info("thread: {0} - status code: {1} \n response body: {2}".format(self.thread_name, refresh_token_resp.status_code, refresh_token_resp.json()))
            return False


class OneDriveDirMgr:
    def __init__(self, access_token):
        thread_name = threading.current_thread().getName()
        self.access_token = access_token
        self.api_url = Config.api_url + '/v1.0/me/drive/special/approot/children'
        self.headers = {"Authorization": "Bearer " + access_token}

        info_json = read_backup_file_info()
        if not info_json:
            logger.error("thread: {0} - problem reading backup file info to get directory info".format(thread_name))
            self.dir_name = None

        elif info_json.get("onedrive-dir") == None or info_json.get("onedrive-dir") == "":
            logger.error("thread: {0} - no onedrive-dir in backup file info".format(thread_name))
            self.dir_name = None
        else:
            self.dir_name = info_json.get("onedrive-dir")

        
    def _write_dir_id(self, dir_id):
        thread_name = threading.current_thread().getName()
        try:
            with open(Config.backup_file_info_path, "r") as info_file:
                info_json = json.load(info_file)
                info_json["onedrive-dir-id"] = dir_id
            
            with open(Config.backup_file_info_path, "w") as info_file:
                json.dump(info_json, info_file)
            logger.info("thread: {0} - wrote dir id: {1}  to backup info json file".format(thread_name, dir_id))
            return True

        except Exception as e:
            logger.error("thread: {0} - problem writing onedrive-dir-id to backup file info".format(thread_name))
            logger.error(e)
            return False
    
    def _check_dir_exists(self):
        thread_name = threading.current_thread().getName()
        try:
            status_resp = requests.get(url=self.api_url + '/' + self.dir_name, timeout=Config.api_timeout, headers=self.headers)    # see if directory already exits
        except Exception as e:
            logger.warning("thread: {0} - exception while checking status of directory: {1}".format(thread_name, self.dir_name))
            logger.warning(e)
            return "error - exception"
        
        if status_resp.status_code == 404:
            return False    # directory doesn't exist
        elif status_resp.status_code == 200:
            resp_json = status_resp.json()
            dir_id = resp_json.get("id")
            if self._write_dir_id(dir_id):
                logger.info("thread: {0} - directory: {1} already exists".format(thread_name ,self.dir_name))
                return True     # directory does exist and we recoreded its id
            else:
                return "error - write"
        else:
            return "error - unknown"     # something unexpected happened
    
    def _create_onedrive_dir(self):
        thread_name = threading.current_thread().getName()

        body = {"name": self.dir_name, "folder": {}}

        try:
            create_resp = requests.post(url=self.api_url, timeout=Config.api_timeout, headers=self.headers, json=body)
        except Exception as e:
            logger.error("thread: {0} - exception while creating directory: {1}".format(thread_name, self.dir_name))
            logger.error(e)
            return None
        
        if create_resp.status_code == 201:
            logger.info("thread: {0} - directory: {1} created".format(thread_name, self.dir_name))
            resp_json = create_resp.json()
            dir_id = resp_json.get("id")
            if self._write_dir_id(dir_id):
                return True
            else:
                return None
        else:
            logger.error("thread: {0} - directory: {1} was not successfully created".format(thread_name, self.dir_name))
            logger.error("thread: {0} - status code: {1}  content: {2}".format(thread_name, create_resp.status_code, create_resp.content))
            return False
    
    def create_dir(self):
        thread_name = threading.current_thread().getName()

        dir_check_status = self._check_dir_exists()
        if dir_check_status != True and dir_check_status != False:
            logger.warning("thread: {0} - problem checking directory status, wait 20 seconds and try again".format(thread_name))
            sleep(20)
            dir_check_status = self._check_dir_exists()
            if dir_check_status != True and dir_check_status != False:
                logger.error("thread: {0} - could not check directory status")
                return None
        
        if dir_check_status == False:
            logger.info("thread: {0} - directory: {1} does not exist, let's make it".format(thread_name, self.dir_name))
            dir_create_status = self._create_onedrive_dir()
            if dir_create_status != True:
                logger.warning("thread: {0} - problem creating directory: {1}, wait 20 seconds and try again.".format(thread_name, self.dir_name))
                sleep(20)
                dir_create_status = self._create_onedrive_dir()
                if dir_create_status != True:
                    logger.error("thread: {0} - failed to create directory: {1}".format(thread_name, self.dir_name))
                    return None
        
        return True
    
      
            

class OneDriveFileDownloadMgr:
    def __init__(self, download_url: str, file_size_bytes: int, download_chunk_size_bytes: int, download_file_path: str, sha256_hash: str):
        self.download_url = download_url
        self.file_size_bytes = file_size_bytes
        self.download_chunk_size_bytes = download_chunk_size_bytes
        self.download_file_path = download_file_path
        self.sha256_hash = sha256_hash
        self.thread_name = threading.current_thread().getName()
    
    def _download_chunk(self, start_byte: int, end_byte: int) -> bytes: 

        byte_range = "bytes=" + str(start_byte) + "-" + str(end_byte)
        headers = {"Range": byte_range}

        try:
            resp = requests.get(url=self.download_url, headers=headers, timeout=Config.api_timeout)
        except Exception as e:
            logger.warning("thread: {0} - exception while downloading chunk".format(self.thread_name))
            logger.warning(e)
            return None

        if resp.status_code == 206:
            logger.info("thread: {0} - chunk download successful for byte range: {1}".format(self.thread_name, byte_range))
            logger.debug("thread: {0} - download headers: {1}".format(self.thread_name, resp.headers))
            return resp.content
        
        logger.warning("thread: {0} - unexpected response while downloading chunk  status: {1}  content: {2}".format(self.thread_name, resp.status_code, resp.content))
        return None
    
    def _retry_delay(self, retry_count: int, start_byte: int, end_byte: int) -> bool:
        if retry_count == 1:
            sleep(15)
            logger.warning("thread: {0} - Retry 1 for download start_byte: {1}  end_byte: {2}".format(self.thread_name, start_byte, end_byte))
            return True
        elif retry_count == 2:
            sleep(600)
            logger.warning("thread: {0} - Retry 2 for download start_byte: {1}  end_byte: {2}".format(self.thread_name, start_byte, end_byte))
            return True
        elif retry_count == 3:
            sleep(1800)
            logger.warning("thread: {0} - Retry 3 for download start_byte: {1}  end_byte: {2}".format(self.thread_name, start_byte, end_byte))
            return True
        else:
            logger.warning("thread: {0} - Retry greater than 3, sleeping 20 seconds, download start_byte: {1}  end_byte: {1}".format(self.thread_name, start_byte, end_byte))
            sleep(20)
            return False
        
    def _download_with_retry(self, start_byte: int, end_byte: int) -> bytes:
        exit_loop = False
        retry_count = 0
        loop_counter = 0

        while not exit_loop:            
            bytes_to_write = self._download_chunk(start_byte, end_byte)
            if not bytes_to_write:
                retry_count = retry_count + 1
                if not self._retry_delay(retry_count, start_byte, end_byte):
                    logger.error("thread: {0} - exceeded retries for download".format(self.thread_name))
                    return False
            else:
                return bytes_to_write
            
            loop_counter = loop_counter + 1
            if loop_counter > 10:
                logger.error("thead: {0} - problem in _download_with_retry, runaway while loop, force exiting loop".format(self.thread_name))
                exit_loop = True
        
        return None

    def _verify_download(self) -> bool:
        # verify the file is actually done downloading
        if os.path.getsize(self.download_file_path) == self.file_size_bytes:
            logger.info("thread: {0} - downloaded file {1} matches expected size of {2} bytes".format(self.thread_name, self.download_file_path, self.file_size_bytes))
            ## now check the hash before returning True
            sha_calc = Sha256Calc(self.download_file_path)
            sha_hash = sha_calc.calc()
            if not sha_hash:
                logger.error("thread: {0} - problem getting sha256 hash of download file".format(self.thread_name))
                return False

            if sha_hash.upper() == self.sha256_hash:
                logger.info("thread: {0} - sha256 hash of downloaded file matches MS graph hash, file download confirmed".format(self.thread_name))
                return True
        else:
            logger.error("thread: {0} - download should be done, but the download file size is not correct for {1}, expected size: {2} bytes".format(self.thread_name, self.download_file_path, self.file_size_bytes))
            return False

    def download_file(self):

        bytes_remaining = self.file_size_bytes
        start_byte = 0
        if self.file_size_bytes >= self.download_chunk_size_bytes:
            end_byte = self.download_chunk_size_bytes - 1
        else:
            end_byte = self.file_size_bytes - 1
        
        download_count = math.ceil(self.file_size_bytes/self.download_chunk_size_bytes)

        for i in range(0, download_count):

            bytes_to_write = self._download_with_retry(start_byte, end_byte)
            if not bytes_to_write:
                logger.error("thread: {0} - problem downloading file, exiting download loop".format(self.thread_name))
                return False
            try:
                with open(self.download_file_path, "ab") as download_file:
                    download_file.write(bytes_to_write)
                logger.debug("thread: {0} - successfully wrote bytes to download file start_byte: {1}  end_byte: {2}".format(self.thread_name, start_byte, end_byte))
            except Exception as e:
                logger.error("thread: {0} - problem writing bytes to file, exiting download attempt".format(self.thread_name))
                logger.error(e)
                return False
            
            bytes_remaining = bytes_remaining - self.download_chunk_size_bytes
            start_byte = self.file_size_bytes - bytes_remaining

            if bytes_remaining > self.download_chunk_size_bytes:
                end_byte = start_byte + self.download_chunk_size_bytes - 1
            else:
                end_byte = self.file_size_bytes - 1
            
                
        if self._verify_download():
            return True
        else:
            logger.error("thread: {0} - downloaded file could not be verified".format(self.thread_name))
            return False
        

class OneDriveItemGetter:

    def __init__(self, access_token, dir_name):
        self.access_token = access_token
        self.dir_name = dir_name
        self.headers = {"Authorization": "Bearer " + self.access_token}
        self.thread_name = threading.current_thread().getName()

    def _get_dir_details(self) -> str:

        dir_url = Config.api_url + "/v1.0/me/drive/special/approot/children/" + self.dir_name

        try:
            resp = requests.get(url=dir_url, headers=self.headers, timeout=Config.api_timeout)        
        except Exception as e:
            logger.warning("thread: {0} - exception encountered while fetching directory details for {1}".format(self.thread_name, self.dir_name))
            logger.warning(e)
            return None
        
        if resp.status_code == 200:
            try:
                resp_json = resp.json()
            except Exception as e:
                logger.error("thread: {0} - problem getting json from get dir details response".format(self.thread_name))
                logger.error(e)
                return None
            dir_id = resp_json.get("id")

            return dir_id
        
        logger.error("thread: {0} - unexpected status code for get dir details request, status code: {1}  content: {2}".format(self.thread_name, resp.status_code, resp.content))
        return None
    
    def _process_json(self, resp_json: dict) -> list:
        if not resp_json.get("value"):
            logger.error("thread: {0} - no 'value' key in directory listing response".format(self.thread_name))
            return None

        item_list = []

        for item in resp_json.get("value"):
            if not item.get("id"):
                logger.error("thread: {0} - one of the items is missing an 'id' key".format(self.thread_name))
                return None
            
            if not item.get("name"):
                logger.error("thread: {0} - one of the items is missing the 'name' key".format(self.thread_name))
                return None
            
            if not item.get("lastModifiedDateTime"):
                logger.error("thread: {0} - one of the items is missing the 'lastModifiedDateTime' key".format(self.thread_name))
                return None

            item_list.append({"id": item.get("id"), "name": item.get("name"), "last-mod": item.get("lastModifiedDateTime")})
        
        return item_list

    def get_dir_items(self) -> list:

        dir_item = self._get_dir_details()
        if not dir_item:
            logger.error("thread: {0} - problem getting directory details from One Drive".format(self.thread_name))
            return None

        dir_url = Config.api_url + "/v1.0/me/drive/items/" + dir_item + "/children"
        
        try:
            resp = requests.get(url=dir_url, headers=self.headers, timeout=Config.api_timeout)
        except Exception as e:
            logger.error("thread: {0} - exception encountered while trying to get list of item in dir: {1}".format(self.thread_name, self.dir_name))
            logger.error(e)
            return None
        
        if resp.status_code == 200:        
            try:
                resp_json = resp.json()
            except Exception as e:
                logger.error("thread: {0} - problem getting json from response for list of items in the dir".format(self.thread_name))
                logger.error(e)
                return None           

            item_list = self._process_json(resp_json)

            if not item_list:
                logger.error("thead: {0} - response json could not be processed".format(self.thread_name))
            
            return item_list
        
        logger.error("thread: {0} - unexpected status code in response to get list of items in dir, status code: {1}  content: {2}".format(self.thread_name, resp.status_code, resp.content))
        return None

    def find_item(self, item_name: str) -> dict:
        item_list = self.get_dir_items()
        if item_list:
            for item in item_list:
                if item.get("name") == item_name:
                    return item
        
        logger.warning("thread: {0} - item {1} not found in dir {2}".format(self.thread_name, item_name, self.dir_name))
        return None


class OneDriveGetItemDetails:

    @staticmethod
    def get_details(item_id: str, access_token: str) -> str:
        thread_name = threading.current_thread().getName()
        item_url = Config.api_url + "/v1.0/me/drive/items/" + item_id
        headers = {"Authorization": "Bearer " + access_token}

        try:
            resp = requests.get(url=item_url, headers=headers, timeout=Config.api_timeout)
        except Exception as e:
            logger.error("thread: {0} - problem getting item detail".format(thread_name))
            logger.error(e)
            return None
        
        if resp.status_code == 200:
            try:
                resp_json = resp.json()
            except Exception as e:
                logger.error("thread: {0} - proglem getting json from item detail response".format(thread_name))
                logger.error(e)
                return None
            
            download_url = resp_json.get("@microsoft.graph.downloadUrl")
            if not download_url:            
                logger.error("thread: {0} - download url is missing".format(thread_name))
                return None
            
            size = resp_json.get("size")
            if not size:
                logger.error("thread: {0} - file size is missing".format(thread_name))
                return None
                      
            file_detail = resp_json.get("file")
            if not file_detail:
                logger.error("thread: {0} - missing file detail".format(thread_name))
                return None
            
            hashes = file_detail.get("hashes")
            if not hashes:
                logger.error("thread: {0} - missing hashes".format(thread_name))
                return None 

            sha256hash = hashes.get("sha256Hash")
            if not sha256hash:
                logger.error("thread: {0} - missing sha256 hash".format(thread_name))
                return None
            
            file_download_info = {"download_url": download_url, "size_bytes": size, "sha256hash": sha256hash}
            return file_download_info                
        
        logger.error("thread: {0} - unexpected status code while fetching download item info".format(thread_name))
        logger.error("thread: {0} - status code: {1}  content: {2} ".format(thread_name, resp.status_code, resp.content))
        return None

        


        



        
            

            

        
        
     