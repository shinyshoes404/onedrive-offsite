import unittest, mock, os, shutil
from onedrive_offsite.config import Config

from onedrive_offsite.utils import leading_zeros, make_tar_gz, FilePartialRead, get_file_groups, ses_send_email, file_cleanup, get_recent_log_lines, download_file_email, extract_tar_gz, decrypt_email, read_backup_file_info


class TestUtilsleadingzeros(unittest.TestCase):
    def test_unit_no_zeros_small(self):
        check_value = leading_zeros(1,9)
        self.assertEqual(check_value, "", "Expecting empty string")

    def test_unit_one_zero(self):
        check_value = leading_zeros(57,100)
        self.assertEqual(check_value, "0", "Expecting one leading zero")

    def test_unit_two_zeros(self):
        check_value = leading_zeros(1,100)
        self.assertEqual(check_value, "00", "Expecting two leading zeros")

    def test_unit_no_zeros_large(self):
        check_value = leading_zeros(99998, 99999)
        self.assertEqual(check_value, "", "Expecting empty string")

class TestUtilsextracttargz(unittest.TestCase):
    
    def test_unit_tarfile_open_except(self):
        with mock.patch("onedrive_offsite.utils.tarfile.open", side_effect=Exception("fake exception")) as mock_tarfile:
            targz_path = "fake/targz/path"
            extract_dir = "fake/extract/path"
            check_val = extract_tar_gz(targz_path, extract_dir)
            self.assertIs(check_val, None)

    def test_unit_tarfile_extract_keep_targz(self):
        with mock.patch("onedrive_offsite.utils.tarfile.open") as mock_tarfile:
            targz_path = "fake/targz/path"
            extract_dir = "fake/extract/path"
            check_val = extract_tar_gz(targz_path, extract_dir)
            self.assertIs(check_val, True)

    def test_unit_tarfile_extract_dont_keep_targz(self):
        with mock.patch("onedrive_offsite.utils.tarfile.open") as mock_tarfile:
            with mock.patch("onedrive_offsite.utils.os.remove") as mock_rm:
                targz_path = "fake/targz/path"
                extract_dir = "fake/extract/path"
                check_val = extract_tar_gz(targz_path, extract_dir, keep_targz=False)
                self.assertIs(check_val, True)
                self.assertEqual(mock_rm.call_count, 1)

    def test_unit_tarfile_extract_dont_keep_targz_remove_except(self):
        with mock.patch("onedrive_offsite.utils.tarfile.open") as mock_tarfile:
            with mock.patch("onedrive_offsite.utils.os.remove", side_effect=Exception("fake exception")) as mock_rm:
                targz_path = "fake/targz/path"
                extract_dir = "fake/extract/path"
                check_val = extract_tar_gz(targz_path, extract_dir, keep_targz=False)
                self.assertIs(check_val, None)
                self.assertEqual(mock_rm.call_count, 1)

class TestUtilsmaketargz(unittest.TestCase):
    test_dir = os.path.abspath(os.path.dirname(__file__))
    test_chunk_dir = os.path.join(test_dir,"./test_chunk_dir")
    test_targz_dir = os.path.join(test_dir, "./test_targz")

    def setUp(self):        
        os.mkdir(TestUtilsmaketargz.test_targz_dir)
        os.mkdir(TestUtilsmaketargz.test_chunk_dir)
        for i in range(0, 24):
            with open(TestUtilsmaketargz.test_chunk_dir + "/test_file_" + str(i), "w") as test_file:
                test_file.write("my test file data " + str(i))
    
    def tearDown(self):
        shutil.rmtree(TestUtilsmaketargz.test_chunk_dir)
        shutil.rmtree(TestUtilsmaketargz.test_targz_dir)

    def test_unit_create_tar_keep_orig(self):
        make_tar_gz(TestUtilsmaketargz.test_chunk_dir, TestUtilsmaketargz.test_targz_dir, 2, Config.onedrive_upload_default_filename)
        self.assertTrue(os.path.isfile(os.path.join(TestUtilsmaketargz.test_targz_dir, "0012_" + Config.onedrive_upload_default_filename)), "0012 tar.gz file should exist")
        self.assertTrue(os.path.isfile(TestUtilsmaketargz.test_chunk_dir + "/test_file_1"), "Original files should still be there")

    
    def test_unit_create_tar_remove_orig(self):
        make_tar_gz(TestUtilsmaketargz.test_chunk_dir, TestUtilsmaketargz.test_targz_dir, 2, Config.onedrive_upload_default_filename, removeorig=True)
        self.assertTrue(os.path.isfile(os.path.join(TestUtilsmaketargz.test_targz_dir, "0003_" + Config.onedrive_upload_default_filename)), "0003 tar.gz file should exist")
        self.assertFalse(os.path.isfile(TestUtilsmaketargz.test_chunk_dir + "/test_file_1"), "Original files should NOT be there")

    def test_unit_exception(self):
        with mock.patch('onedrive_offsite.utils.tarfile.open', side_effect=Exception("fake tarfile.open exception")):
            check_value = make_tar_gz(TestUtilsmaketargz.test_chunk_dir, TestUtilsmaketargz.test_targz_dir, 2, Config.onedrive_upload_default_filename, removeorig=True)
            self.assertFalse(check_value)


class TestUtilsgetfilegroups(unittest.TestCase):
    test_dir = os.path.abspath(os.path.dirname(__file__))
    test_chunk_dir = os.path.join(test_dir,"./test_chunk_dir")
    test_targz_dir = os.path.join(test_dir, "./test_targz")

    def setUp(self):        
        os.mkdir(TestUtilsmaketargz.test_targz_dir)
        os.mkdir(TestUtilsmaketargz.test_chunk_dir)
        for i in range(0, 20):
            with open(TestUtilsmaketargz.test_chunk_dir + "/test_file_" + str(i), "w") as test_file:
                test_file.write("my test file data " + str(i))
    
    def tearDown(self):
        shutil.rmtree(TestUtilsmaketargz.test_chunk_dir)
        shutil.rmtree(TestUtilsmaketargz.test_targz_dir)

    def test_unit_maxgrp_6_list_count(self):
        check_value = get_file_groups(self.test_chunk_dir, 6)
        self.assertEqual(len(check_value), 4, "Expecting 4 lists in our list.")
   
    def test_unit_maxgrp_6_last_list_count(self):
        check_value = get_file_groups(self.test_chunk_dir, 6)
        self.assertEqual(len(check_value[3]), 2, "Expecting 2 elements in the 4th list.")


class TestUtilFPR(unittest.TestCase):
    test_dir = os.path.abspath(os.path.dirname(__file__))
    test_file_path_10kb = os.path.join(test_dir, "testfile10000")
    test_file_path_10_5kb = os.path.join(test_dir, "testfile10500")
    

    def setUp(self):
        # make a test file that is 10,000 bytes
        for i in range(0, 1000):
            with open(TestUtilFPR.test_file_path_10kb, "a") as file:
                file.write("1234567890") # 10 bytes
        
        # make a test file that is 10,500 bytes
        for i in range(0, 1050):
            with open(TestUtilFPR.test_file_path_10_5kb, "a") as file:
                file.write("1234567890")
    
    def tearDown(self):
        if os.path.isfile(TestUtilFPR.test_file_path_10kb):
            os.remove(TestUtilFPR.test_file_path_10kb)

        if os.path.isfile(TestUtilFPR.test_file_path_10_5kb):
            os.remove(TestUtilFPR.test_file_path_10_5kb)

    def test_unit_chunk_count_no_remainder(self):
        fpr = FilePartialRead(TestUtilFPR.test_file_path_10kb, 1, 1000)
        test_value = len(fpr.upload_array)
        self.assertEqual(test_value, 10, "Expecting 10 chunks")

    def test_unit_final_chunk_range_no_remainder(self):
        fpr = FilePartialRead(TestUtilFPR.test_file_path_10kb, 1, 1000)
        test_value = fpr.upload_array[len(fpr.upload_array)-1][2]
        self.assertEqual(test_value, "9000-9999", "Expecting '9000-9999' range")
    
    def test_unit_chunk_count_with_remainder(self):
        fpr = FilePartialRead(TestUtilFPR.test_file_path_10_5kb, 1, 1000)
        test_value = len(fpr.upload_array)
        self.assertEqual(test_value, 11, "Expecting 11 chunks")

    def test_unit_final_chunk_range_with_remainder(self):
        fpr = FilePartialRead(TestUtilFPR.test_file_path_10_5kb, 1, 1000)
        test_value = fpr.upload_array[len(fpr.upload_array)-1][2]
        self.assertEqual(test_value, "10000-10499", "Expecting '10000-10499' range")

    def test_unit_chunk_count_with_small_max(self):
        fpr = FilePartialRead(TestUtilFPR.test_file_path_10kb, 1, 1500)
        test_value = len(fpr.upload_array)
        self.assertEqual(test_value, 10, "Expecting 10 chunks")

    def test_unit_final_chunk_range_with_small_max(self):
        fpr = FilePartialRead(TestUtilFPR.test_file_path_10kb, 1, 1500)
        test_value = fpr.upload_array[len(fpr.upload_array)-1][2]
        self.assertEqual(test_value, "9000-9999", "Expecting '9000-9999' range")

    def test_unit_chunk_count_with_small_file(self):
        fpr = FilePartialRead(TestUtilFPR.test_file_path_10kb, 20, 30000)
        test_value = len(fpr.upload_array)
        self.assertEqual(test_value, 1, "Expecting 1 chunk")

    def test_unit_final_chunk_range_with_small_file(self):
        fpr = FilePartialRead(TestUtilFPR.test_file_path_10kb, 20, 30000)
        test_value = fpr.upload_array[len(fpr.upload_array)-1][2]
        self.assertEqual(test_value, "0-9999", "Expecting '0-9999' range")
    
    def test_unit_read_data(self):
        fpr = FilePartialRead(TestUtilFPR.test_file_path_10_5kb, 1, 1000)
        test_value = fpr.read_file_bytes(5, 10)
        self.assertEqual(test_value, b'6789012345', "Expecting b'6789012345")

    def test_unit_read_data_except(self):
        with mock.patch('onedrive_offsite.utils.open', side_effect=Exception):
            fpr = FilePartialRead(TestUtilFPR.test_file_path_10_5kb, 1, 1000)
            test_value = fpr.read_file_bytes(5, 10)
            self.assertEqual(test_value, None, "Expecting None")


class TestUtilsessendemail(unittest.TestCase):

    @mock.patch('onedrive_offsite.utils.SESSender')
    def test_unit_fail_validate(self, mock_sessender):
        mock_sessender.return_value.ses_validate.return_value = False
        check_value = ses_send_email("to@email.com", "from@email.com", "fromname", "my email msg","email subject", "aws region" )
        self.assertFalse(check_value, "Expecting failed validation")
    
    @mock.patch('onedrive_offsite.utils.SESSender')
    def test_unit_send_email_success(self, mock_sessender):
        mock_sessender.return_value.ses_validate.return_value = True
        mock_sessender.return_value.send_email.return_value = "fakemsgID"
        check_value = ses_send_email("to@email.com", "from@email.com", "fromname", "my email msg","email subject", "aws region" )
        self.assertTrue(check_value, "Expecting successful send")

    @mock.patch('onedrive_offsite.utils.SESSender')
    def test_unit_send_email_except(self, mock_sessender):
        mock_sessender.return_value.ses_validate.return_value = True
        mock_sessender.return_value.send_email.side_effect = Exception("fake send_email exception")
        check_value = ses_send_email("to@email.com", "from@email.com", "fromname", "my email msg","email subject", "aws region" )
        self.assertFalse(check_value, "Expecting exception")


class TestUtilsfilecleanup(unittest.TestCase):
    @mock.patch('onedrive_offsite.utils.ses_send_email', return_value=True)
    @mock.patch('onedrive_offsite.utils.shutil.rmtree')
    @mock.patch('onedrive_offsite.utils.os.path.isdir', return_value=True)
    @mock.patch('onedrive_offsite.utils.os.remove')
    @mock.patch('onedrive_offsite.utils.os.path.isfile', return_value=True)
    @mock.patch('onedrive_offsite.utils.open')
    @mock.patch('onedrive_offsite.utils.json.load', return_value={"onedrive-filename":"cool_onedrive_filename","backup-file-path":"cool_backup_file_path"})
    def test_unit_everything_exists_and_works_email_sends(self, mock_json_load, mock_open, mock_isfile, mock_os_rem, mock_isdir, mock_shutil_rmtree, mock_ses_email):
        check_value = file_cleanup()
        self.assertTrue(check_value)

    @mock.patch('onedrive_offsite.utils.ses_send_email', return_value=False)
    @mock.patch('onedrive_offsite.utils.shutil.rmtree')
    @mock.patch('onedrive_offsite.utils.os.path.isdir', return_value=True)
    @mock.patch('onedrive_offsite.utils.os.remove')
    @mock.patch('onedrive_offsite.utils.os.path.isfile', return_value=True)
    @mock.patch('onedrive_offsite.utils.open')
    @mock.patch('onedrive_offsite.utils.json.load', return_value={"onedrive-filename":"cool_onedrive_filename","backup-file-path":"cool_backup_file_path"})
    def test_unit_everything_exists_and_works_email_does_not_send(self, mock_json_load, mock_open, mock_isfile, mock_os_rem, mock_isdir, mock_shutil_rmtree, mock_ses_email):
        check_value = file_cleanup()
        self.assertFalse(check_value)
    
    @mock.patch('onedrive_offsite.utils.get_recent_log_lines', return_value="------ RECENT LOG -------\n\nlog line 1\nlog line 2\nlog line 3\n")
    @mock.patch('onedrive_offsite.utils.ses_send_email', return_value=True)
    @mock.patch('onedrive_offsite.utils.shutil.rmtree')
    @mock.patch('onedrive_offsite.utils.os.path.isdir', return_value=True)
    @mock.patch('onedrive_offsite.utils.open')
    @mock.patch('onedrive_offsite.utils.json.load', side_effect=Exception("fake open exception"))
    def test_unit_backup_file_info_json_load_except(self, mock_json_load, mock_open, mock_isdir, mock_shutil_rmtree, mock_ses_email, mock_log_lines):
        check_value = file_cleanup()
        self.assertFalse(check_value)

    @mock.patch('onedrive_offsite.utils.ses_send_email', return_value=True)
    @mock.patch('onedrive_offsite.utils.shutil.rmtree')
    @mock.patch('onedrive_offsite.utils.os.path.isdir', return_value=True)
    @mock.patch('onedrive_offsite.utils.os.remove')
    @mock.patch('onedrive_offsite.utils.os.path.isfile', return_value=True)
    @mock.patch('onedrive_offsite.utils.open')
    @mock.patch('onedrive_offsite.utils.json.load', return_value={"backup-file-path":"cool_backup_file_path"})
    def test_unit_no_onedrivefilename_files_dirs_exist_email_sends(self, mock_json_load, mock_open, mock_isfile, mock_os_rem, mock_isdir, mock_shutil_rmtree, mock_ses_email):
        check_value = file_cleanup()
        self.assertTrue(check_value)

    @mock.patch('onedrive_offsite.utils.get_recent_log_lines', return_value="------ RECENT LOG -------\n\nlog line 1\nlog line 2\nlog line 3\n")
    @mock.patch('onedrive_offsite.utils.ses_send_email', return_value=True)
    @mock.patch('onedrive_offsite.utils.shutil.rmtree')
    @mock.patch('onedrive_offsite.utils.os.path.isdir', return_value=True)
    @mock.patch('onedrive_offsite.utils.os.remove', side_effect=Exception("fake os.remove exception"))
    @mock.patch('onedrive_offsite.utils.os.path.isfile', return_value=True)
    @mock.patch('onedrive_offsite.utils.open')
    @mock.patch('onedrive_offsite.utils.json.load', return_value={"onedrive-filename":"cool_onedrive_filename","backup-file-path":"cool_backup_file_path"})
    def test_unit_cant_rm_backup_file_email_sends(self, mock_json_load, mock_open, mock_isfile, mock_os_rem, mock_isdir, mock_shutil_rmtree, mock_ses_email, mock_log_lines):
        check_value = file_cleanup()
        self.assertFalse(check_value)

    @mock.patch('onedrive_offsite.utils.get_recent_log_lines', return_value="------ RECENT LOG -------\n\nlog line 1\nlog line 2\nlog line 3\n")
    @mock.patch('onedrive_offsite.utils.ses_send_email', return_value=True)
    @mock.patch('onedrive_offsite.utils.shutil.rmtree', side_effect=Exception("fake shutil.rmtree exception"))
    @mock.patch('onedrive_offsite.utils.os.path.isdir', return_value=True)
    @mock.patch('onedrive_offsite.utils.os.remove')
    @mock.patch('onedrive_offsite.utils.os.path.isfile', return_value=True)
    @mock.patch('onedrive_offsite.utils.open')
    @mock.patch('onedrive_offsite.utils.json.load', return_value={"onedrive-filename":"cool_onedrive_filename","backup-file-path":"cool_backup_file_path"})
    def test_unit_cant_rm_dirs_email_sends(self, mock_json_load, mock_open, mock_isfile, mock_os_rem, mock_isdir, mock_shutil_rmtree, mock_ses_email, mock_log_lines):
        check_value = file_cleanup()
        self.assertFalse(check_value)

    @mock.patch('onedrive_offsite.utils.get_recent_log_lines', return_value="------ RECENT LOG -------\n\nlog line 1\nlog line 2\nlog line 3\n")
    @mock.patch('onedrive_offsite.utils.ses_send_email', return_value=False)
    @mock.patch('onedrive_offsite.utils.shutil.rmtree', side_effect=Exception("fake shutil.rmtree exception"))
    @mock.patch('onedrive_offsite.utils.os.path.isdir', return_value=True)
    @mock.patch('onedrive_offsite.utils.os.remove')
    @mock.patch('onedrive_offsite.utils.os.path.isfile', return_value=True)
    @mock.patch('onedrive_offsite.utils.open')
    @mock.patch('onedrive_offsite.utils.json.load', return_value={"onedrive-filename":"cool_onedrive_filename","backup-file-path":"cool_backup_file_path"})
    def test_unit_cant_rm_dirs_email_does_not_send(self, mock_json_load, mock_open, mock_isfile, mock_os_rem, mock_isdir, mock_shutil_rmtree, mock_ses_email, mock_log_lines):
        check_value = file_cleanup()
        self.assertFalse(check_value)


class TestUtilsdownloadfileemail(unittest.TestCase):
    
    @mock.patch('onedrive_offsite.utils.shutil.rmtree')
    @mock.patch('onedrive_offsite.utils.get_recent_log_lines', return_value="------ RECENT LOG -------\n\nlog line 1\nlog line 2\nlog line 3\n")
    @mock.patch('onedrive_offsite.utils.ses_send_email', return_value=False)
    @mock.patch('onedrive_offsite.utils.open', side_effect=Exception("fake exception"))
    def test_unit_download_file_email_info_read_fail_shutil_rm_success_email_fail(self, mock_open, mock_send_email, mock_get_log, mock_shutil):
        check_val = download_file_email()
        self.assertIs(check_val, False)

    @mock.patch('onedrive_offsite.utils.shutil.rmtree', side_effect=Exception("fake exception"))
    @mock.patch('onedrive_offsite.utils.get_recent_log_lines', return_value="------ RECENT LOG -------\n\nlog line 1\nlog line 2\nlog line 3\n")
    @mock.patch('onedrive_offsite.utils.ses_send_email', return_value=True)
    @mock.patch('onedrive_offsite.utils.open', side_effect=Exception("fake exception"))
    def test_unit_download_file_email_info_read_fail_shutil_rm_except_email_success(self, mock_open, mock_send_email, mock_get_log, mock_shutil):
        check_val = download_file_email()
        self.assertIs(check_val, False)

    @mock.patch("onedrive_offsite.utils.json.load", return_value={"onedrive-dir": "fake-dir"})
    @mock.patch('onedrive_offsite.utils.ses_send_email', return_value=True)
    @mock.patch('onedrive_offsite.utils.open')
    def test_unit_download_file_email_info_read_success_email_success(self, mock_open, mock_send_email, mock_json_load):
        check_val = download_file_email()
        self.assertIs(check_val, True)

    @mock.patch("onedrive_offsite.utils.json.load", return_value={"onedrive-dir": "fake-dir"})
    @mock.patch('onedrive_offsite.utils.ses_send_email', return_value=False)
    @mock.patch('onedrive_offsite.utils.open')
    def test_unit_download_file_email_info_read_success_email_fail(self, mock_open, mock_send_email, mock_json_load):
        check_val = download_file_email()
        self.assertIs(check_val, False)


class TestUtilsgetrecentloglines(unittest.TestCase):
    test_dir = os.path.abspath(os.path.dirname(__file__))
    test_log_dir = os.path.join(test_dir,"./test_log_dir")
    test_log_path = os.path.join(test_log_dir, "./test_log")

    def setUp(self):        
        os.mkdir(TestUtilsgetrecentloglines.test_log_dir)
        for i in range(0, 10):
            with open(TestUtilsgetrecentloglines.test_log_path, "a") as test_file:
                test_file.write("log line " + str(i+1) + "\n")
    
    def tearDown(self):
        shutil.rmtree(TestUtilsgetrecentloglines.test_log_dir)
    
    def test_unit_read_last_3_lines(self):
        check_value = get_recent_log_lines(3,TestUtilsgetrecentloglines.test_log_path)
        self.assertEqual(check_value, "--------------------------- RECENT LOGS -----------------------------\n\nlog line 8\nlog line 9\nlog line 10\n\n")





class TestUtilsdecryptemail(unittest.TestCase):
    
    @mock.patch('onedrive_offsite.utils.get_recent_log_lines', return_value="------ RECENT LOG -------\n\nlog line 1\nlog line 2\nlog line 3\n")
    @mock.patch('onedrive_offsite.utils.ses_send_email', return_value=False)
    @mock.patch('onedrive_offsite.utils.open', side_effect=Exception("fake exception"))
    def test_unit_decrypt_email_info_read_fail_email_fail(self, mock_open, mock_send_email, mock_get_log):
        check_val = decrypt_email()
        self.assertIs(check_val, False)

    @mock.patch('onedrive_offsite.utils.get_recent_log_lines', return_value="------ RECENT LOG -------\n\nlog line 1\nlog line 2\nlog line 3\n")
    @mock.patch('onedrive_offsite.utils.ses_send_email', return_value=True)
    @mock.patch('onedrive_offsite.utils.open', side_effect=Exception("fake exception"))
    def test_unit_decrypt_email_info_read_fail_email_succeed(self, mock_open, mock_send_email, mock_get_log):
        check_val = decrypt_email()
        self.assertIs(check_val, False)

    @mock.patch("onedrive_offsite.utils.json.load", return_value={"onedrive-dir": "fake-dir"})
    @mock.patch('onedrive_offsite.utils.ses_send_email', return_value=True)
    @mock.patch('onedrive_offsite.utils.open')
    def test_unit_decrypt_email_info_read_succeed_email_succeed(self, mock_open, mock_send_email, mock_load_json):
        check_val = decrypt_email()
        self.assertIs(check_val, True)

    @mock.patch("onedrive_offsite.utils.json.load", return_value={"onedrive-dir": "fake-dir"})
    @mock.patch('onedrive_offsite.utils.ses_send_email', return_value=False)
    @mock.patch('onedrive_offsite.utils.open')
    def test_unit_decrypt_email_info_read_succeed_email_fail(self, mock_open, mock_send_email, mock_load_json):
        check_val = decrypt_email()
        self.assertIs(check_val, False)


class TestUtilsread_backup_file(unittest.TestCase):

    @mock.patch("onedrive_offsite.utils.Config")
    def test_unit_read_backup_file_exception(self, mock_config):
        mock_config.backup_file_info_path = "fake-path"
        with mock.patch("onedrive_offsite.utils.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.utils.open") as mock_open:
                with mock.patch("onedrive_offsite.utils.json.load", side_effect=Exception("fake-exception")) as mock_json_load:
                    check_val = read_backup_file_info()
                    self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.utils.Config")
    def test_unit_read_backup_file_successfully_return_info(self, mock_config):
        mock_config.backup_file_info_path = "fake-path"
        with mock.patch("onedrive_offsite.utils.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.utils.open") as mock_open:
                test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                                "start-date-time": "2022-04-14-21:37:09",
                                "size-bytes": 170403564,
                                "onedrive-dir": "backup_test_2",
                                "onedrive-filename": "backup_test_local.tar.gz",
                                "done-date-time": "2022-04-14-21:37:15", 
                                "onedrive-dir-id": "D23D09990A1D5FC9!161"}
                with mock.patch("onedrive_offsite.utils.json.load", return_value=test_info_json) as mock_json_load:
                    check_val = read_backup_file_info()
                    self.assertEqual(check_val, test_info_json)
