import unittest, mock, os, shutil

from onedrive_offsite.crypt import Crypt, Sha256Calc


### ------------------------------ Crypt.gen_key() -----------------------------------
class TestCryptgenkey(unittest.TestCase):

    def test_unit_gen_key_success(self):
        crypt = Crypt("fake/key/path")
        crypt.gen_key()
        self.assertIsNot(crypt.key, False)
    
    def test_unit_gen_key_exception(self):
        with mock.patch("onedrive_offsite.crypt.Fernet.generate_key", side_effect=Exception("fake exception")) as mock_fernet:
            crypt = Crypt("fake/key/path")
            crypt.gen_key()
            self.assertEqual(crypt.key, False)

### ------------------------------ Crypt.gen_key_file() -----------------------------------
class TestCryptgenkeyfile(unittest.TestCase):
    test_dir = os.path.abspath(os.path.dirname(__file__))
    test_file_path = os.path.join(test_dir, "testkey.key")

    def tearDown(self):
        if os.path.isfile(TestCryptgenkeyfile.test_file_path):
            os.remove(TestCryptgenkeyfile.test_file_path)
    
    def test_unit_gen_key_file_works_return_true(self):
        with mock.patch("onedrive_offsite.crypt.Crypt.gen_key") as mock_gen_key:
            crypt = Crypt(TestCryptgenkeyfile.test_file_path)
            crypt.key = b'big-long-fake-encryption-key' # writes key in bytes to file
            check_value = crypt.gen_key_file()
            self.assertEqual(check_value, True)

    def test_unit_gen_key_file_works_verify_file(self):
        with mock.patch("onedrive_offsite.crypt.Crypt.gen_key") as mock_gen_key:
            crypt = Crypt(TestCryptgenkeyfile.test_file_path)
            crypt.key = b'big-long-fake-encryption-key' # writes key in bytes to file
            crypt.gen_key_file()
            check_value = os.path.isfile(TestCryptgenkeyfile.test_file_path)
            self.assertEqual(check_value, True)

    def test_unit_gen_key_file_works_verify_file_contents(self):
        with mock.patch("onedrive_offsite.crypt.Crypt.gen_key") as mock_gen_key:
            crypt = Crypt(TestCryptgenkeyfile.test_file_path)
            crypt.key = b'big-long-fake-encryption-key' # writes key in bytes to file
            crypt.gen_key_file()
            with open(TestCryptgenkeyfile.test_file_path, 'br') as test_key_file:
                check_value = test_key_file.read()
                self.assertEqual(check_value, crypt.key)

    def test_unit_gen_key_file_gen_key_fail(self):
        with mock.patch("onedrive_offsite.crypt.Crypt.gen_key") as mock_gen_key:
            crypt = Crypt(TestCryptgenkeyfile.test_file_path)
            crypt.key = False 
            check_value = crypt.gen_key_file()
            self.assertEqual(check_value, False)

    def test_unit_gen_key_fail_to_write_file(self):
        with mock.patch("onedrive_offsite.crypt.Crypt.gen_key") as mock_gen_key:
            with mock.patch("onedrive_offsite.crypt.open", side_effect = Exception("fake write exception")) as mock_open:
                crypt = Crypt(TestCryptgenkeyfile.test_file_path)
                crypt.key = b'big-long-fake-encryption-key' # writes key in bytes to file
                check_value = crypt.gen_key_file()
                self.assertEqual(check_value, False)

        
### ------------------------------ Crypt.fetch_key() -----------------------------------
class TestCryptfetchkey(unittest.TestCase):
    test_dir = os.path.abspath(os.path.dirname(__file__))
    test_file_path = os.path.join(test_dir, "testkey.key")
    key = b'big-long-fake-encryption-key'

    def setUp(self):
        with open(TestCryptfetchkey.test_file_path, 'wb') as keyfile:
            keyfile.write(TestCryptfetchkey.key)
    
    def tearDown(self):
        if os.path.isfile(TestCryptfetchkey.test_file_path):
            os.remove(TestCryptfetchkey.test_file_path)
    
    def test_unit_fetch_key_from_file(self):
        crypt = Crypt(TestCryptgenkeyfile.test_file_path)
        crypt.fetch_key()
        self.assertEqual(crypt.key, TestCryptfetchkey.key)

    def test_unit_fetch_key_from_file_exception(self):
        with mock.patch("onedrive_offsite.crypt.open", side_effect=Exception("fake exception")) as mock_open:
            crypt = Crypt(TestCryptgenkeyfile.test_file_path)
            check_value = crypt.fetch_key()
            self.assertEqual(check_value, False)


### ------------------------------ Crypt.chunk_encrypt() -----------------------------------
class TestCryptchunkencrypt(unittest.TestCase):
    
    def test_unit_chunk_encrypt_unable_to_fetch_key(self):
        with mock.patch("onedrive_offsite.crypt.Crypt.fetch_key", return_value=False) as mock_fetch_key:
            crypt = Crypt("fake/key/path")
            check_value = crypt.chunk_encrypt("fake/file/to/encrypt", "fake/chunk/dir", 1)
            self.assertEqual(check_value, False)

    def test_unit_chunk_encrypt_exception(self):
        with mock.patch("onedrive_offsite.crypt.Crypt.fetch_key", return_value=True) as mock_fetch_key:
            with mock.patch("onedrive_offsite.crypt.os.path.getsize", return_value=10) as mock_getsize:
                with mock.patch("onedrive_offsite.crypt.open", side_effect=Exception("fake exception")) as mock_open:
                    crypt = Crypt("fake/key/path")
                    check_value = crypt.chunk_encrypt("fake/file/to/encrypt", "fake/chunk/dir", 1)
                    self.assertEqual(check_value, False)
    
### ------------------------------ Crypt.chunk_decrypt() -----------------------------------
class TestCryptchunkdecrypt(unittest.TestCase):

    def test_unit_chunk_decrypt_unable_to_fetch_key(self):
        with mock.patch("onedrive_offsite.crypt.Crypt.fetch_key", return_value=False) as mock_fetch_key:
            crypt = Crypt("fake/key/path")
            check_value = crypt.chunk_decrypt("fake/chunk/dir","fake/combined/file", removeorig=False)
            self.assertEqual(check_value, False)

    def test_unit_chunk_decrypt_exception(self):
        with mock.patch("onedrive_offsite.crypt.Crypt.fetch_key", return_value=True) as mock_fetch_key:
            with mock.patch("onedrive_offsite.crypt.Fernet") as mock_fernet:
                with mock.patch("onedrive_offsite.crypt.open", side_effect=Exception("fake exception")) as mock_open:
                    crypt = Crypt("fake/key/path")
                    crypt.key = "fakekey"
                    check_value = crypt.chunk_decrypt("fake/chunk/dir","fake/combined/file", removeorig=False)
                    self.assertEqual(check_value, False)


### ------------------------------ Sha256Calc -----------------------------------
class TestSha256Calc(unittest.TestCase):

    ### ------------ fixtures ----------------
    test_dir = os.path.abspath(os.path.dirname(__file__))
    test_dir = os.path.join(test_dir,"./test_files")
    test_file = os.path.join(test_dir, "./test_file")

    def setUp(self):        
        os.mkdir(TestSha256Calc.test_dir)
        with open(TestSha256Calc.test_file, "w") as test_file:
            test_file.write("fakefilecontent")
    
    def tearDown(self):
        shutil.rmtree(TestSha256Calc.test_dir)

    ### -------------- tests -------------------
    @mock.patch("onedrive_offsite.crypt.hashlib")
    @mock.patch("onedrive_offsite.crypt.threading.current_thread")
    def test_unit_sha256calc_calc_open_exception(self, mock_curr_thread, mock_hash_lib):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.crypt.open", side_effect=Exception("fake exception")) as mock_open:

            sha_calc = Sha256Calc("fakefilepath")
            check_val = sha_calc.calc()
            self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.crypt.hashlib")
    @mock.patch("onedrive_offsite.crypt.threading.current_thread")
    def test_unit_sha256calc_calc_read_file_digest_exception(self, mock_curr_thread, mock_hash_lib):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"

        mock_hash_obj = mock.Mock()
        mock_hash_obj.update = mock.PropertyMock(return_value=True)
        mock_hash_obj.hexdigest = mock.PropertyMock(side_effect=Exception("fake exception"))

        mock_hash_lib.sha256.return_value = mock_hash_obj

        sha_calc = Sha256Calc(TestSha256Calc.test_file)
        check_val = sha_calc.calc()
        self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.crypt.hashlib")
    @mock.patch("onedrive_offsite.crypt.threading.current_thread")
    def test_unit_sha256calc_calc_read_file_digest_success(self, mock_curr_thread, mock_hash_lib):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"

        mock_hash_obj = mock.Mock()
        mock_hash_obj.update = mock.PropertyMock(return_value=True)
        mock_hash_obj.hexdigest = mock.PropertyMock(return_value="0123456789abcdef")

        mock_hash_lib.sha256.return_value = mock_hash_obj

        sha_calc = Sha256Calc(TestSha256Calc.test_file)
        check_val = sha_calc.calc()
        self.assertEqual(check_val, "0123456789abcdef")


