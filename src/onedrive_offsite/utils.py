import math, tarfile, os, logging, json, shutil, mock, threading
from onedrive_offsite.config import Config


if os.environ.get("TESTING_ENV") == "test" or os.environ.get("TESTING_ENV") == "test-dev":
    SESSender = mock.Mock()
    SESSender.return_value.ses_validate.return_value = True
    SESSender.return_value.send_email.return_value = True
else:
    # import the SESSender class
    from py_basic_ses.emailing import SESSender


# Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(Config.LOG_LEVEL)
logger.addHandler(Config.FILE_HANDLER)
logger.addHandler(Config.STOUT_HANDLER)


# this function takes in a number and a max number as integers and determines if any leading zeros are required
# if no leading zeros are required, an empty string is returned, otherwise the required zeros are returned as
# a string
def leading_zeros(number: int, max_number: int):
    # rounding up log10 of max_number will tell us the total number of places to the left of the decimal to expect
    # rounding up log10 of the number provided will tell us the the number of places to the left of the decimal that number occupies
    # This function assumes that number will start at 1, not 0. 
    # You will notice that we are adding .1 to the number provided. This is to deal with transition numbers like 1, 10, 100, 1000.
    #   Example:
    #       max_number = 999, number = 1
    #       ceil(log10(999)) = 3    ceil(log10(1)) = 0 
    #       resulting in "000" returning from the function
    #       If you are using this function to name a file, you would name your file 0001_file instead of 001_file, as you probably intended
    zero_count = math.ceil(math.log10(max_number+.1)) - math.ceil(math.log10(number+.1))
    zero_str = ""

    for i in range(zero_count):
        zero_str = zero_str + "0"

    return zero_str


def extract_tar_gz(targz_path: str, extract_dir: str, keep_targz=True) -> bool:
    try:
        with tarfile.open(targz_path) as targz_file:
            targz_file.extractall(extract_dir)
    except Exception as e:
        logger.error("problem extracting {0} to {1}".format(targz_path, extract_dir))
        return None
    
    if keep_targz == False:
        try:
            os.remove(targz_path)
        except Exception as e:
            logger.error("problem removing {0}".format(targz_path))
            return None
    
    return True


# function to create a tar.gz archive file from a collection of files located in a directory provided as a positional argument
def make_tar_gz(dir_with_files: str, tar_gz_dir_path: str, max_chunks_to_add: int, base_file_name, removeorig=False):

    file_counter = 1  
    chunk_groups = get_file_groups(dir_with_files, max_chunks_to_add)    

    try:
        for files in chunk_groups:  
            # set leading zeros assuming we will never have more than 1000 tar.gz files to upload
            lead_zeros = leading_zeros(file_counter, 1000)          
            # create a tar file and compress with gunzip
            logger.info("creating tar.gz file {0}{1}".format(lead_zeros, file_counter))
            with tarfile.open(os.path.join(tar_gz_dir_path, lead_zeros + str(file_counter) + "_" + base_file_name), "x:gz") as tar:                               
               for file in files:
                    # add the specified file to the tar.gz file
                    # using path.join to build the full file path
                    # using arcname kwarg to prevent leading subdirectoring from being created in the archive
                    tar.add(os.path.join(dir_with_files,file),arcname=file)
                    # if specified, remove the original file once it is archived
                    if removeorig==True:
                        os.remove(os.path.join(dir_with_files,file))

            logger.info("done creating tar.gz file {0}{1}".format(lead_zeros, file_counter))
            file_counter = file_counter + 1

    except Exception as e:
        logger.error("problem in make_tar_gz()")
        logger.error(e)
        return False
    
    return True

def get_file_groups(dir: str, max_group_size: int) -> list:
    sub_group = []
    file_groups = []
    j = 1
    i = 0
    for file in sorted(os.listdir(dir)):
        sub_group.append(file)
        i = i + 1
        if i == max_group_size * j:
            file_groups.append(sub_group)
            sub_group = []
            j = j + 1

    if len(sub_group) > 0:
        file_groups.append(sub_group)
    
    return file_groups



class FilePartialRead:
    
    def __init__(self, file_path, max_size_kb, range_factor_bytes=327680):
        self.file_path = file_path
        self.max_size_bytes = int(max_size_kb * 1000)
        self.file_size = os.path.getsize(file_path)

        # --- Tryig to accomdoate this note from the Microsoft documentation with a default value of 327,680 bytes ---
        # Note: If your app splits a file into multiple byte ranges, the size of each byte range MUST be a multiple of 320 KiB (327,680 bytes).
        # Using a fragment size that does not divide evenly by 320 KiB will result in errors committing some files.
        self.range_factor_bytes = range_factor_bytes

        self._calc_sizes_and_ranges()
    
    def _calc_sizes_and_ranges(self):
        byte_range_multiple = math.floor(self.max_size_bytes/self.range_factor_bytes)      
        if byte_range_multiple == 0:
            self.file_range_size_bytes = self.max_size_bytes
            if self.file_size < self.max_size_bytes:
                self.file_range_size_bytes = self.file_size
                self.count_of_full_ranges = 0
            else:
                self.count_of_full_ranges = math.floor(self.file_size/self.file_range_size_bytes)
        else:
            self.file_range_size_bytes = byte_range_multiple * self.range_factor_bytes
            self.count_of_full_ranges = math.floor(self.file_size/self.file_range_size_bytes)
        
        # build an array listing the byte ranges and content length sizes
        self.upload_array = []
        
        # start with the chunks that will be the chunk size of the set range
        for i in range(0, self.count_of_full_ranges):
            self.upload_array.append([ 
                    # content length in bytes
                    self.file_range_size_bytes,
                    # starting byte for this chunk
                    i * self.file_range_size_bytes,
                    # content range, following the format '0-25' as a string
                    str(i * self.file_range_size_bytes) + "-" + str((i+1) * self.file_range_size_bytes - 1)
                 ])

        # now, create an array element for the remainder
        # if there are no entries in our array so far, then we will only have a remainder range
        if len(self.upload_array) == 0:
            i = 0
        else:
            # otherwise increment our counter so the math works
            i = i + 1

        start_byte = i * self.file_range_size_bytes
        remaining_bytes_size = self.file_size - start_byte
        if remaining_bytes_size == 0:
            pass
        else:
            self.upload_array.append([
                # content length in bytes
                remaining_bytes_size,
                # starting byte for this chunk
                start_byte,
                # content range, following the format '26-40'
                str(start_byte) + "-" + str(self.file_size -1)
            ])  


    # function to return a subset of data from a file in the form of bytes  
    def read_file_bytes(self, start_byte: int, read_bytes: int) -> bytes:
        try:
            with open(self.file_path, 'rb') as file:
                # the 0 indicates to start from the beginning of the file before offsetting
                file.seek(start_byte, 0)
                file_data = file.read(read_bytes)
        except Exception as e:
            logger.error("problem reading file in read_file_bytes")
            logger.error(e)
            return None

        return file_data


def ses_send_email(to_email_address: str, from_email_address: str, email_from_name: str, email_message_txt: str, email_subject: str, ses_aws_region: str ) -> bool:

    # instantiate the SESSender object
    ses_send_obj = SESSender(sendto=to_email_address,           # Required
                            fromaddr=from_email_address,        # Required
                            fromname=email_from_name,           # Optional
                            message_txt=email_message_txt,      # Required
                            msgsubject=email_subject,           # Optional
                            aws_region=ses_aws_region)          # Required

    # validate the arguments and credentials before trying to send our email using the ses_validate method
    check_validation = ses_send_obj.ses_validate()
    if check_validation == False:
        return False

    # if everything validated, try to send the email
    logger.info("Attempting to send an email To: {0}   From: {1}".format(to_email_address, from_email_address))
    try:
        ses_send_obj.send_email()
        return True
    except Exception as e:
        logger.error("Problem sending email")
        logger.error(e)
        return False


def file_cleanup(error: bool=False) -> bool:
    logger.info("Attempting file cleanup.")
    
    # initializing in case of json.load() exception
    backup_file_info = {}

    # get the backup file descriptive info from the json file
    try:
        with open(Config.backup_file_info_path, "r") as file:
            backup_file_info = json.load(file)
            backup_info_file_present = True
    except Exception as e:
        logger.error("Problem reading backup_file_info_path in file_cleanup()")
        logger.error(e)
        error = True
        backup_info_file_present = False
        
    
    # grab the onedrive base file name to include in the email body and subject
    if backup_file_info.get("onedrive-filename"):
        onedrive_file_name = backup_file_info.get("onedrive-filename")
    else:
        onedrive_file_name = Config.onedrive_upload_default_filename
    
    # if we were able to read the json file and it included backup-file-path
    if backup_file_info.get("backup-file-path"):
        # remove the original backup file that was sent from the remote machine
        if os.path.isfile(backup_file_info.get("backup-file-path")):
            try:
                os.remove(backup_file_info.get("backup-file-path"))
                logger.info("{0} removed".format(backup_file_info.get("backup-file-path")))
            except Exception as e:
                logger.error("Problem removing {0}".format(backup_file_info.get("backup-file-path")))
                logger.error(e)
                error = True    

    # remove the encrypted chunks directory and contents
    if os.path.isdir(Config.crypt_chunk_dir):
        try:
            shutil.rmtree(Config.crypt_chunk_dir)
            logger.info("Removed {0} and its contents.".format(Config.crypt_chunk_dir))
        except Exception as e:
            logger.error("Problem removing {0}".format(Config.crypt_chunk_dir))
            logger.error(e)
            error = True
    
    # remove encrypted tar.gz directory and contents
    if os.path.isdir(Config.crypt_tar_gz_dir):
        try:
            shutil.rmtree(Config.crypt_tar_gz_dir)
            logger.info("Removed {0} and its contents.".format(Config.crypt_tar_gz_dir))
        except Exception as e:
            logger.error("Problem removing {0}".format(Config.crypt_tar_gz_dir))
            logger.error(e)
            error = True
    
    if backup_info_file_present == True:
        try:
            os.remove(Config.backup_file_info_path)
            logger.info("Removed: {0}".format(Config.backup_file_info_path))
        except Exception as e:
            logger.error("Problem removing {0}".format(Config.backup_file_info_path))
            logger.error(e)
            error = True
    
    if error == False:
        logger.info("File cleanup successful")
        email_subject = "Successful Offsite Backup - " + onedrive_file_name
        email_text = "onedrive-offsite backup successfully completed without errors for " + onedrive_file_name + "."
        email_status = ses_send_email(to_email_address=Config.email_to,
                                         from_email_address=Config.email_from_addr,
                                         email_from_name=Config.email_from_name,
                                         email_subject=email_subject,
                                         email_message_txt=email_text,
                                         ses_aws_region=Config.aws_region)

        if email_status == True:
            logger.info("Success! Email sent.")
            return True
        else:
            logger.error("Problem sending email.")
            return False
    
    else:
        # grab the last 30 lines of the log file to include in our email
        log_lines = get_recent_log_lines(30, Config.LOG_PATH)
        email_subject = "Error - " + onedrive_file_name
        email_text = "onedrive-offsite encountered an error for " + onedrive_file_name + ".\n\n\n"
        email_text = email_text + log_lines
        email_text = email_text.replace("\n","</br>")

        email_status = ses_send_email(to_email_address=Config.email_to,
                                    from_email_address=Config.email_from_addr,
                                    email_from_name=Config.email_from_name,
                                    email_subject=email_subject,
                                    email_message_txt=email_text,
                                    ses_aws_region=Config.aws_region)

        if email_status == True:
            logger.info("email sent.")
            return False
        else:
            logger.error("problem sending email.")
            return False


def get_recent_log_lines(num_lines: int, log_path: str=Config.LOG_PATH) -> str:
    with open(log_path, "r") as log_file:
        last_lines = ""
        for lines in (log_file.readlines() [-num_lines:]):
            last_lines = last_lines + lines
    
    # add a new line character before we return the string
    last_lines = last_lines + "\n"

    email_text = "--------------------------- RECENT LOGS -----------------------------\n\n"
    email_text = email_text + last_lines
    
    return email_text


def download_file_email(error: bool=False) -> bool:
    logger.info("Attempting download file email.")
    
    download_file_info = {} # initialize empty json in case reading the file fails

    # get the download file descriptive info from the json file
    try:
        with open(Config.download_info_path, "r") as file:
            download_file_info = json.load(file)
            download_info_file_present = True
    except Exception as e:
        logger.error("Problem reading download info file in download_file_cleanup()")
        logger.error(e)
        error = True
        download_info_file_present = False
            
    
    if error == False:
        email_subject = "Successful Download - " + str(download_file_info.get("onedrive-dir"))
        email_text = "onedrive-offsite download successfully completed without errors for " + str(download_file_info.get("onedrive-dir")) + "."
        email_status = ses_send_email(to_email_address=Config.email_to,
                                         from_email_address=Config.email_from_addr,
                                         email_from_name=Config.email_from_name,
                                         email_subject=email_subject,
                                         email_message_txt=email_text,
                                         ses_aws_region=Config.aws_region)

        if email_status == True:
            logger.info("Success! Email sent.")
            return True
        else:
            logger.error("Problem sending email.")
            return False
    
    else:
        try:
            shutil.rmtree(Config.download_dir)
            logger.info("removed dir and contents {0}".format(Config.download_dir))
        except Exception as e:
            logger.error("problem removing {0}".format(Config.download_dir))

        # grab the last 30 lines of the log file to include in our email
        log_lines = get_recent_log_lines(30, Config.LOG_PATH)
        email_subject = "Download Error - " + str(download_file_info.get("onedrive-dir"))
        email_text = "onedrive-offsite encountered an error for " + str(download_file_info.get("onedrive-dir")) + ".\n\n\n"
        email_text = email_text + log_lines
        email_text = email_text.replace("\n","</br>")

        email_status = ses_send_email(to_email_address=Config.email_to,
                                    from_email_address=Config.email_from_addr,
                                    email_from_name=Config.email_from_name,
                                    email_subject=email_subject,
                                    email_message_txt=email_text,
                                    ses_aws_region=Config.aws_region)

        if email_status == True:
            logger.info("email sent.")
            return False
        else:
            logger.error("problem sending email.")
            return False


def decrypt_email(error: bool=False) -> bool:
    logger.info("Attempting decrypt email.")
    
    download_file_info = {} # initialize empty json in case reading the file fails

    # get the download file descriptive info from the json file
    try:
        with open(Config.download_info_path, "r") as file:
            download_file_info = json.load(file)
            download_info_file_present = True
    except Exception as e:
        logger.error("Problem reading download info file in decrypt_email()")
        logger.error(e)
        error = True
        download_info_file_present = False
            
    
    if error == False:
        email_subject = "Successful Decrypt - " + str(download_file_info.get("onedrive-dir"))
        email_text = "onedrive-offsite decrypt and combine successfully completed without errors for " + str(download_file_info.get("onedrive-dir")) + "."
        email_status = ses_send_email(to_email_address=Config.email_to,
                                         from_email_address=Config.email_from_addr,
                                         email_from_name=Config.email_from_name,
                                         email_subject=email_subject,
                                         email_message_txt=email_text,
                                         ses_aws_region=Config.aws_region)

        if email_status == True:
            logger.info("Success! Email sent.")
            return True
        else:
            logger.error("Problem sending email.")
            return False
    
    else:
        
        # grab the last 30 lines of the log file to include in our email
        log_lines = get_recent_log_lines(30, Config.LOG_PATH)
        email_subject = "Decrypt Error - " + str(download_file_info.get("onedrive-dir"))
        email_text = "onedrive-offsite encountered an error while decrypting and combining " + str(download_file_info.get("onedrive-dir")) + ".\n\n\n"
        email_text = email_text + log_lines
        email_text = email_text.replace("\n","</br>")

        email_status = ses_send_email(to_email_address=Config.email_to,
                                    from_email_address=Config.email_from_addr,
                                    email_from_name=Config.email_from_name,
                                    email_subject=email_subject,
                                    email_message_txt=email_text,
                                    ses_aws_region=Config.aws_region)

        if email_status == True:
            logger.info("email sent.")
            return False
        else:
            logger.error("problem sending email.")
            return False


def read_backup_file_info() -> dict:
    thread_name = threading.current_thread().getName()
    
    try:
        with open(Config.backup_file_info_path, "r") as info_file:
            info_json = json.load(info_file)

    except Exception as e:
        logger.error("thread: {0} - problem reading backup file info to get directory info".format(thread_name))
        logger.error(e)
        return None

    return info_json

