import os, math, logging, hashlib, threading
from onedrive_offsite.utils import leading_zeros
from cryptography.fernet import Fernet, InvalidToken
from onedrive_offsite.config import Config

# Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(Config.LOG_LEVEL)
logger.addHandler(Config.FILE_HANDLER)
logger.addHandler(Config.STOUT_HANDLER)


class Crypt:
    def __init__(self, key_path):
        self.key_path = key_path

    def gen_key(self):
        try:
            self.key = Fernet.generate_key()
        except Exception as e:
            logger.error("problem generating key from Fernet.generate_key in gen_key()")
            logger.error(e)
            self.key = False
    
    def gen_key_file(self):
        self.gen_key()
        if self.key != False:
            try:
                with open(self.key_path,'wb') as keyfile:
                    keyfile.write(self.key)
                return True
            except Exception as e:
                logger.error("problem writing key file in gen_key_file()")
                logger.error(e)
                return False
        else:
            return False
    
    def fetch_key(self):
        try:
            with open(self.key_path,'rb') as keyfile:
                self.key = keyfile.read()
        except Exception as e:
            logger.error("problem reading key file in fetch_key()")
            logger.error(e)
            return False
    
    def chunk_encrypt(self, file_to_encrypt, dir_for_chunks, chunk_size_mb):
        # get the key
        if self.fetch_key() == False:
            return False

        # convert chunk size from MB to bytes
        chunk_size_bytes = int(chunk_size_mb * 1000000)

        # -- figure out how many chunks we will need --
        # get file size in bytes
        file_size = os.path.getsize(file_to_encrypt)

        # determine max file count number
        max_file_count = int(math.pow(10, math.ceil(math.log10(file_size/chunk_size_bytes + 1))) - 1)

        try:
            with open(file_to_encrypt, 'rb') as backup_file:
                # initialize keep_reading with True to start the while loop, will change over to file contents later
                keep_reading = True
                i = 1
                fernet = Fernet(self.key)
                while keep_reading:
                    # read and encrypt data a chunk at a time
                    keep_reading = backup_file.read(chunk_size_bytes)
                    if keep_reading:
                        encrypted = fernet.encrypt(keep_reading)
                        with open(dir_for_chunks + '/' + leading_zeros(i,max_file_count) + str(i) + '_backup.crypt', 'wb') as chunk_file:
                            chunk_file.write(encrypted)
                            i = i + 1
                return True

        except Exception as e:
            logger.error("problem creating encrypted file chunks in chunk_encrypt()")
            logger.error(e)
            return False

    def chunk_decrypt(self,dir_with_chunks, combined_unencrypted_file_path, removeorig=False):
        # get the key
        if self.fetch_key() == False:
            return False

        fernet = Fernet(self.key)

        try:
            with open(combined_unencrypted_file_path, 'ab') as combined_file:
                for chunk_file in sorted(os.listdir(dir_with_chunks)):
                    with open(os.path.join(dir_with_chunks,chunk_file),'rb') as file:
                        data = file.read()

                    decrypted = fernet.decrypt(data)
                    combined_file.write(decrypted)
                    logger.info("decrypted {0}".format(chunk_file))
                    # if specified, remove encrypted file after its data is decrypted and stored in the combined restored file
                    if removeorig == True:
                        os.remove(os.path.join(dir_with_chunks, chunk_file))
                        logger.info("removed {0}".format(chunk_file))

            return True
        
        except InvalidToken:
            logger.error("invalid decrypt key, cannot decrypt")
            return False

        except Exception as e:
            logger.error("problem decrypting encrypted file chunks in chunk_decrypt()")
            logger.error(e)
            return False

        
class Sha256Calc:
    def __init__(self, file_path: str):
        self.file_path = file_path
    
    def calc(self):
        thread_name = threading.current_thread().getName()

        sha256_hash = hashlib.sha256()
        
        try:
            with open(self.file_path, "rb") as file:
                keep_reading = True
                while keep_reading:
                    file_bytes = file.read(4096)
                    if file_bytes:
                        sha256_hash.update(file_bytes)
                    else:
                        keep_reading = False
        except Exception as e:
            logger.error("thread: {0} - problem reading file to calculate hash - file path: {1}".format(thread_name, self.file_path))
            logger.error(e)
            return None      
        
        try:
            digest = sha256_hash.hexdigest()
        except Exception as e:
            logger.error("thread: {0} - problem fetching hexdigest for sha256 hash".format(thread_name))
            logger.error(e)
            return None
        
        logger.info("thread: {0} - sha256 hash calculated for {1}   digest: {2}".format(thread_name, self.file_path, digest))
        
        return digest





        