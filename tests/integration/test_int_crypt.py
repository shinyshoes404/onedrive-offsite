import unittest, os, shutil

from onedrive_offsite.crypt import Crypt


### ------------------------------ chunk encryption and chunk decrypt with key gen -----------------------------------

class TestCryptEncryptDecrypt(unittest.TestCase):
    test_dir = os.path.abspath(os.path.dirname(__file__))
    test_chunk_dir = os.path.join(test_dir, "test_chunks/")

    test_backup_path = os.path.join(test_dir, "test_backup")
    test_backup_data = "1234567890abcdefghijABCDEFGHIJ!#$" # 3 x 10 bytes + 3 more bytes
    test_restored_backup_path = os.path.join(test_dir, "test_restored")

    test_key_path = os.path.join(test_dir, "test_key.key")


    def setUp(self):
        if os.path.isdir(TestCryptEncryptDecrypt.test_chunk_dir) == False:
            os.mkdir(TestCryptEncryptDecrypt.test_chunk_dir)
        
        with open(TestCryptEncryptDecrypt.test_backup_path, "w") as test_backup_file:
            test_backup_file.write(TestCryptEncryptDecrypt.test_backup_data)

    def tearDown(self):
        if os.path.isdir(TestCryptEncryptDecrypt.test_chunk_dir):
            shutil.rmtree(TestCryptEncryptDecrypt.test_chunk_dir)

        if os.path.isfile(TestCryptEncryptDecrypt.test_backup_path):
            os.remove(TestCryptEncryptDecrypt.test_backup_path)

        if os.path.isfile(TestCryptEncryptDecrypt.test_restored_backup_path):
            os.remove(TestCryptEncryptDecrypt.test_restored_backup_path)

        if os.path.isfile(TestCryptEncryptDecrypt.test_key_path):
            os.remove(TestCryptEncryptDecrypt.test_key_path)     
        

    def test_int_chunk_encrypt_create_files_successfully(self):
        crypt = Crypt(TestCryptEncryptDecrypt.test_key_path)
        crypt.gen_key_file()
        check_value = crypt.chunk_encrypt(TestCryptEncryptDecrypt.test_backup_path, TestCryptEncryptDecrypt.test_chunk_dir, .000010)
        self.assertEqual(check_value, True)

    def test_int_chunk_encrypt_create_files_confirm_count(self):
        crypt = Crypt(TestCryptEncryptDecrypt.test_key_path)
        crypt.gen_key_file()
        crypt.chunk_encrypt(TestCryptEncryptDecrypt.test_backup_path, TestCryptEncryptDecrypt.test_chunk_dir, .000010) # setting chunk size to 10 bytes, expecting 4 encrypted files to be made
        check_value = len(os.listdir(TestCryptEncryptDecrypt.test_chunk_dir))
        self.assertEqual(check_value, 4)
    
    def test_int_chunk_encrypt_chunk_decrypt_verify_restored_backup_keep_orig(self):
        crypt = Crypt(TestCryptEncryptDecrypt.test_key_path)
        crypt.gen_key_file()
        crypt.chunk_encrypt(TestCryptEncryptDecrypt.test_backup_path, TestCryptEncryptDecrypt.test_chunk_dir, .000010)
        crypt.chunk_decrypt(TestCryptEncryptDecrypt.test_chunk_dir, TestCryptEncryptDecrypt.test_restored_backup_path, removeorig=False)
        # check to see if the restored backup matches the original file
        with open(TestCryptEncryptDecrypt.test_restored_backup_path, "r") as restored_file:
            restored_data = restored_file.read()
        
        with open(TestCryptEncryptDecrypt.test_backup_path, "r") as orig_file:
            orig_data = orig_file.read()
        
        self.assertEqual(restored_data, orig_data)

    def test_int_chunk_encrypt_chunk_decrypt_verify_restored_backup_remove_orig(self):
        crypt = Crypt(TestCryptEncryptDecrypt.test_key_path)
        crypt.gen_key_file()
        crypt.chunk_encrypt(TestCryptEncryptDecrypt.test_backup_path, TestCryptEncryptDecrypt.test_chunk_dir, .000010)
        crypt.chunk_decrypt(TestCryptEncryptDecrypt.test_chunk_dir, TestCryptEncryptDecrypt.test_restored_backup_path, removeorig=True)
        # check to see if the restored backup matches the original file
        with open(TestCryptEncryptDecrypt.test_restored_backup_path, "r") as restored_file:
            restored_data = restored_file.read()
        
        with open(TestCryptEncryptDecrypt.test_backup_path, "r") as orig_file:
            orig_data = orig_file.read()
        
        self.assertEqual(restored_data, orig_data)

    def test_int_chunk_encrypt_chunk_decrypt_remove_orig_verify_removed(self):
        crypt = Crypt(TestCryptEncryptDecrypt.test_key_path)
        crypt.gen_key_file()
        crypt.chunk_encrypt(TestCryptEncryptDecrypt.test_backup_path, TestCryptEncryptDecrypt.test_chunk_dir, .000010)
        crypt.chunk_decrypt(TestCryptEncryptDecrypt.test_chunk_dir, TestCryptEncryptDecrypt.test_restored_backup_path, removeorig=True)
        # check to see if the restored backup matches the original file
        with open(TestCryptEncryptDecrypt.test_restored_backup_path, "r") as restored_file:
            restored_data = restored_file.read()
        
        with open(TestCryptEncryptDecrypt.test_backup_path, "r") as orig_file:
            orig_data = orig_file.read()
        
        check_value = len(os.listdir(TestCryptEncryptDecrypt.test_chunk_dir))
        self.assertEqual(check_value, 0)