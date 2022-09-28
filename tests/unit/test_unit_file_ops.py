import unittest, mock, os

from onedrive_offsite.file_ops import crypt_file_build, crypt_file_upload, crypt_file_build_and_upload, download, restore


@mock.patch("onedrive_offsite.file_ops.Config")
class Testcryptfilebuild(unittest.TestCase):

    @mock.patch.dict(os.environ, {"ONEDRIVE_ENV": "dev"}, clear=True) # mocking environment variable, does not need to pass into the test method, clearing everything but ONEDRIVE_ENV
    def test_unit_successful_chunk_dir_exists(self, mock_config):
        mock_config.crypt_tar_gz_max_size_mb = 10
        mock_config.crypt_chunk_size_mb = 1
        mock_config.key_path = "/fake/key/path"
        mock_config.backup_file_info_path = "/fake/backup/file/info/path"
        mock_config.crypt_chunk_dir = "/fake/crypt/chunk/dir"
        mock_config.crypt_tar_gz_dir = "/fake/crypt/targz/dir"
        mock_config.onedrive_upload_default_filename = "fake-onedrive-default-filename.tar.gz"


        with mock.patch("onedrive_offsite.file_ops.Crypt") as mock_crypt:
            mock_crypt.return_value.chunk_encrypt.return_value = True
            with mock.patch("onedrive_offsite.file_ops.open") as mock_open:
                with mock.patch("onedrive_offsite.file_ops.json") as mock_json:
                    backup_info_json = {"backup-file-path":"/fake/backup/path", "start-date-time":"2022-01-10-23:18:18", "size-bytes": 125000000, "onedrive-filename":"fake-onedrive-filename.tar.gz", "done-date-time":"2022-01-10-24:18:18"}
                    mock_json.return_value.load.return_value = backup_info_json
                    with mock.patch("onedrive_offsite.file_ops.os.path.isdir", side_effect=[True, True]) as mock_isdir: # [crypt_chunk_dir, crypt_tar_gz_dir]
                        with mock.patch("onedrive_offsite.file_ops.Sha256Calc") as mock_shacalc:
                            mock_shacalc.return_value.calc.return_value = "fakehash"
                            with mock.patch("onedrive_offsite.file_ops.make_tar_gz", return_value=True) as mock_make_tar_gz:
                                check_value = crypt_file_build()
                                self.assertEqual(check_value, True)

    @mock.patch.dict(os.environ, {"ONEDRIVE_ENV": "dev"}, clear=True) # mocking environment variable, does not need to pass into the test method, clearing everything but ONEDRIVE_ENV
    def test_unit_successful_chunk_dir_exists_fail_hash_calc(self, mock_config):
        mock_config.crypt_tar_gz_max_size_mb = 10
        mock_config.crypt_chunk_size_mb = 1
        mock_config.key_path = "/fake/key/path"
        mock_config.backup_file_info_path = "/fake/backup/file/info/path"
        mock_config.crypt_chunk_dir = "/fake/crypt/chunk/dir"
        mock_config.crypt_tar_gz_dir = "/fake/crypt/targz/dir"
        mock_config.onedrive_upload_default_filename = "fake-onedrive-default-filename.tar.gz"


        with mock.patch("onedrive_offsite.file_ops.Crypt") as mock_crypt:
            mock_crypt.return_value.chunk_encrypt.return_value = True
            with mock.patch("onedrive_offsite.file_ops.open") as mock_open:
                with mock.patch("onedrive_offsite.file_ops.json") as mock_json:
                    backup_info_json = {"backup-file-path":"/fake/backup/path", "start-date-time":"2022-01-10-23:18:18", "size-bytes": 125000000, "onedrive-filename":"fake-onedrive-filename.tar.gz", "done-date-time":"2022-01-10-24:18:18"}
                    mock_json.return_value.load.return_value = backup_info_json
                    with mock.patch("onedrive_offsite.file_ops.os.path.isdir", side_effect=[True, True]) as mock_isdir: # [crypt_chunk_dir, crypt_tar_gz_dir]
                        with mock.patch("onedrive_offsite.file_ops.Sha256Calc") as mock_shacalc:
                            mock_shacalc.return_value.calc.return_value = None
                            with mock.patch("onedrive_offsite.file_ops.make_tar_gz", return_value=True) as mock_make_tar_gz:
                                check_value = crypt_file_build()
                                self.assertEqual(check_value, True)

    def test_unit_max_chunks_0(self, mock_config):
        mock_config.crypt_tar_gz_max_size_mb = 1
        mock_config.crypt_chunk_size_mb = 10
  
        with mock.patch("onedrive_offsite.file_ops.file_cleanup") as mock_file_cleanup:  
            check_value = crypt_file_build()
            self.assertEqual(check_value, False)

    def test_unit_crypt_backup_file_info_read_exception(self, mock_config):
        mock_config.crypt_tar_gz_max_size_mb = 10
        mock_config.crypt_chunk_size_mb = 1
        mock_config.key_path = "/fake/key/path"
        mock_config.backup_file_info_path = "/fake/backup/file/info/path"

        with mock.patch("onedrive_offsite.file_ops.Crypt") as mock_crypt:
            mock_crypt.return_value.chunk_encrypt.return_value = True
            with mock.patch("onedrive_offsite.file_ops.open") as mock_open:
                with mock.patch("onedrive_offsite.file_ops.json.load", side_effect=Exception("fake exception")) as mock_json:
                    with mock.patch("onedrive_offsite.file_ops.file_cleanup") as mock_file_cleanup:  
                        check_value = crypt_file_build()
                        self.assertEqual(check_value, False)
    

    @mock.patch.dict(os.environ, {"ONEDRIVE_ENV": "dev", "ONEDRIVE_NAME": "fake-onedrive-env-name"}, clear=True) # mocking environment variable, does not need to pass into the test method, clearing everything but ONEDRIVE_ENV
    def test_unit_fail_no_chunk_dir_no_crypt_tar_dir_create_successful_make_tar_gz_fail(self, mock_config):
        mock_config.crypt_tar_gz_max_size_mb = 10
        mock_config.crypt_chunk_size_mb = 1
        mock_config.key_path = "/fake/key/path"
        mock_config.backup_file_info_path = "/fake/backup/file/info/path"
        mock_config.crypt_chunk_dir = "/fake/crypt/chunk/dir"
        mock_config.crypt_tar_gz_dir = "/fake/crypt/targz/dir"
        mock_config.onedrive_upload_default_filename = "fake-onedrive-default-filename.tar.gz"


        with mock.patch("onedrive_offsite.file_ops.Crypt") as mock_crypt:
            mock_crypt.return_value.chunk_encrypt.return_value = True
            with mock.patch("onedrive_offsite.file_ops.open") as mock_open:
                with mock.patch("onedrive_offsite.file_ops.json") as mock_json:
                    backup_info_json = {"backup-file-path":"/fake/backup/path", "start-date-time":"2022-01-10-23:18:18", "size-bytes": 125000000, "onedrive-filename":"fake-onedrive-filename.tar.gz", "done-date-time":"2022-01-10-24:18:18"}
                    mock_json.return_value.load.return_value = backup_info_json
                    with mock.patch("onedrive_offsite.file_ops.os.path.isdir", side_effect=[False, False]) as mock_isdir: # [crypt_chunk_dir, crypt_tar_gz_dir]
                        with mock.patch("onedrive_offsite.file_ops.os.mkdir") as mock_mkdir:
                            with mock.patch("onedrive_offsite.file_ops.Sha256Calc") as mock_shacalc:
                                mock_shacalc.return_value.calc.return_value = "fakehash"
                                with mock.patch("onedrive_offsite.file_ops.make_tar_gz", return_value=False) as mock_make_tar_gz:
                                    with mock.patch("onedrive_offsite.file_ops.file_cleanup") as mock_file_cleanup:
                                        check_value = crypt_file_build()
                                        self.assertEqual(check_value, False)


    def test_unit_fail_crypt_chunk_mkdir_exception(self, mock_config):
        mock_config.crypt_tar_gz_max_size_mb = 10
        mock_config.crypt_chunk_size_mb = 1
        mock_config.key_path = "/fake/key/path"
        mock_config.backup_file_info_path = "/fake/backup/file/info/path"
        mock_config.crypt_chunk_dir = "/fake/crypt/chunk/dir"

        with mock.patch("onedrive_offsite.file_ops.Crypt") as mock_crypt:
            mock_crypt.return_value.chunk_encrypt.return_value = True
            with mock.patch("onedrive_offsite.file_ops.open") as mock_open:
                with mock.patch("onedrive_offsite.file_ops.json.load") as mock_json:
                    with mock.patch("onedrive_offsite.file_ops.os.path.isdir", return_value=False) as mock_isdir:
                        with mock.patch("onedrive_offsite.file_ops.os.mkdir", side_effect=Exception("fake exception")) as mock_mkdir:
                            with mock.patch("onedrive_offsite.file_ops.file_cleanup") as mock_file_cleanup:  
                                check_value = crypt_file_build()
                                self.assertEqual(check_value, False)

    def test_unit_fail_chunk_encrypt(self, mock_config):
        mock_config.crypt_tar_gz_max_size_mb = 10
        mock_config.crypt_chunk_size_mb = 1
        mock_config.key_path = "/fake/key/path"
        mock_config.backup_file_info_path = "/fake/backup/file/info/path"
        mock_config.crypt_chunk_dir = "/fake/crypt/chunk/dir"

        with mock.patch("onedrive_offsite.file_ops.Crypt") as mock_crypt:
            mock_crypt.return_value.chunk_encrypt.return_value = False
            with mock.patch("onedrive_offsite.file_ops.open") as mock_open:
                with mock.patch("onedrive_offsite.file_ops.json.load") as mock_json:
                    with mock.patch("onedrive_offsite.file_ops.os.path.isdir", return_value=True) as mock_isdir:
                        with mock.patch("onedrive_offsite.file_ops.Sha256Calc") as mock_shacalc:
                            mock_shacalc.return_value.calc.return_value = "fakehash"
                            with mock.patch("onedrive_offsite.file_ops.file_cleanup") as mock_file_cleanup:  
                                check_value = crypt_file_build()
                                self.assertEqual(check_value, False)



class Testcryptfileupload(unittest.TestCase):

    @mock.patch("onedrive_offsite.file_ops.file_cleanup")
    @mock.patch("onedrive_offsite.file_ops.Config")
    @mock.patch("onedrive_offsite.file_ops.os.listdir", return_value=["file1", "file2", "file3"])
    @mock.patch("onedrive_offsite.file_ops.sleep", return_value=None)
    @mock.patch("onedrive_offsite.file_ops.threading.Thread")
    def test_crypt_file_upload_error_not_empty(self, mock_Thread, mock_sleep, mock_listdir, mock_config, mock_file_clean):
        with mock.patch("onedrive_offsite.file_ops.Queue") as mock_Q:
            mock_to_up_q = mock.Mock()
            mock_attempt_q = mock.Mock()
            mock_kill_q = mock.Mock()
            mock_dir_q = mock.Mock()
            mock_dir_q.empty = mock.PropertyMock(side_effect=[True, False])
            mock_err_q = mock.Mock()
            mock_err_q.empty = mock.PropertyMock(return_value=False)
            mock_Q.side_effect = [mock_to_up_q, mock_attempt_q, mock_kill_q, mock_err_q, mock_err_q]

            check_value = crypt_file_upload()
            self.assertEqual(check_value, False)


    @mock.patch("onedrive_offsite.file_ops.file_cleanup", return_value=False)
    @mock.patch("onedrive_offsite.file_ops.Config")
    @mock.patch("onedrive_offsite.file_ops.os.listdir", return_value=["file1", "file2", "file3"])
    @mock.patch("onedrive_offsite.file_ops.sleep", return_value=None)
    @mock.patch("onedrive_offsite.file_ops.threading.Thread")
    def test_crypt_file_upload_error_empty_cleanup_problem(self, mock_Thread, mock_sleep, mock_listdir, mock_config, mock_file_clean):
        with mock.patch("onedrive_offsite.file_ops.Queue") as mock_Q:
            mock_to_up_q = mock.Mock()
            mock_attempt_q = mock.Mock()
            mock_kill_q = mock.Mock()
            mock_dir_q = mock.Mock()
            mock_dir_q.empty = mock.PropertyMock(side_effect=[True, False])
            mock_err_q = mock.Mock()
            mock_err_q.empty = mock.PropertyMock(return_value=True)
            mock_Q.side_effect = [mock_to_up_q, mock_attempt_q, mock_kill_q, mock_err_q, mock_dir_q]

            check_value = crypt_file_upload()
            self.assertEqual(check_value, False)
    

    @mock.patch("onedrive_offsite.file_ops.file_cleanup", return_value=True)
    @mock.patch("onedrive_offsite.file_ops.Config")
    @mock.patch("onedrive_offsite.file_ops.os.listdir", return_value=["file1", "file2", "file3"])
    @mock.patch("onedrive_offsite.file_ops.sleep", return_value=None)
    @mock.patch("onedrive_offsite.file_ops.threading.Thread")
    def test_crypt_file_upload_error_empty_cleanup_works(self, mock_Thread, mock_sleep, mock_listdir, mock_config, mock_file_clean):
        with mock.patch("onedrive_offsite.file_ops.Queue") as mock_Q:
            mock_to_up_q = mock.Mock()
            mock_attempt_q = mock.Mock()
            mock_kill_q = mock.Mock()
            mock_dir_q = mock.Mock()
            mock_dir_q.empty = mock.PropertyMock(side_effect=[True, False])
            mock_err_q = mock.Mock()
            mock_err_q.empty = mock.PropertyMock(return_value=True)
            mock_Q.side_effect = [mock_to_up_q, mock_attempt_q, mock_kill_q, mock_err_q, mock_dir_q]

            check_value = crypt_file_upload()
            self.assertEqual(check_value, True)


class Testcryptfilebuildandupload(unittest.TestCase):

    def test_unit_successful(self):
        with mock.patch("onedrive_offsite.file_ops.crypt_file_build", return_value=True) as mock_build:
            with mock.patch("onedrive_offsite.file_ops.crypt_file_upload", return_value=True) as mock_upload:
                check_value = crypt_file_build_and_upload()
                self.assertEqual(check_value, True)

    def test_unit_fail_upload(self):
        with mock.patch("onedrive_offsite.file_ops.crypt_file_build", return_value=True) as mock_build:
            with mock.patch("onedrive_offsite.file_ops.crypt_file_upload", return_value=False) as mock_upload:
                check_value = crypt_file_build_and_upload()
                self.assertEqual(check_value, False)

    def test_unit_fail_build(self):
        with mock.patch("onedrive_offsite.file_ops.crypt_file_build", return_value=False) as mock_build:
            check_value = crypt_file_build_and_upload()
            self.assertEqual(check_value, False)


class Testdownload(unittest.TestCase):

    @mock.patch("onedrive_offsite.file_ops.download_file_email", return_value=True)
    @mock.patch("onedrive_offsite.file_ops.sleep", return_value=None)
    @mock.patch("onedrive_offsite.file_ops.threading.Thread")
    def test_unit_download_no_err_email_works(self, mock_Thread, mock_sleep, mock_dl_file_email):
        with mock.patch("onedrive_offsite.file_ops.Queue") as mock_Q:
            mock_to_up_q = mock.Mock()
            mock_attempt_q = mock.Mock()
            mock_kill_q = mock.Mock()
            mock_err_q = mock.Mock()
            mock_err_q.empty = mock.PropertyMock(return_value=True)
            mock_Q.side_effect = [mock_to_up_q, mock_attempt_q, mock_kill_q, mock_err_q]

            check_value = download()
            self.assertEqual(check_value, True)

    @mock.patch("onedrive_offsite.file_ops.download_file_email", return_value=True)
    @mock.patch("onedrive_offsite.file_ops.sleep", return_value=None)
    @mock.patch("onedrive_offsite.file_ops.threading.Thread")
    def test_unit_download_with_err(self, mock_Thread, mock_sleep, mock_dl_file_email):
        with mock.patch("onedrive_offsite.file_ops.Queue") as mock_Q:
            mock_to_up_q = mock.Mock()
            mock_attempt_q = mock.Mock()
            mock_kill_q = mock.Mock()
            mock_err_q = mock.Mock()
            mock_err_q.empty = mock.PropertyMock(return_value=False)
            mock_Q.side_effect = [mock_to_up_q, mock_attempt_q, mock_kill_q, mock_err_q]

            check_value = download()
            self.assertEqual(check_value, None)

    @mock.patch("onedrive_offsite.file_ops.download_file_email", return_value=False)
    @mock.patch("onedrive_offsite.file_ops.sleep", return_value=None)
    @mock.patch("onedrive_offsite.file_ops.threading.Thread")
    def test_unit_download_with_no_err_fail_email(self, mock_Thread, mock_sleep, mock_dl_file_email):
        with mock.patch("onedrive_offsite.file_ops.Queue") as mock_Q:
            mock_to_up_q = mock.Mock()
            mock_attempt_q = mock.Mock()
            mock_kill_q = mock.Mock()
            mock_err_q = mock.Mock()
            mock_err_q.empty = mock.PropertyMock(return_value=True)
            mock_Q.side_effect = [mock_to_up_q, mock_attempt_q, mock_kill_q, mock_err_q]

            check_value = download()
            self.assertEqual(check_value, False)



class Testrestore(unittest.TestCase):


    def test_unit_download_decrypt_email_succeed(self):
        with mock.patch("onedrive_offsite.file_ops.download", return_value=True) as mock_download:
            with mock.patch("onedrive_offsite.file_ops.DownloadDecrypter.decrypt_and_combine", return_value=True) as mock_decrypt:
                with mock.patch("onedrive_offsite.file_ops.decrypt_email", return_value=True) as mock_email:
                    check_val = restore()
                    self.assertIs(check_val, True)


    def test_unit_download_decrypt_email_fail(self):
        with mock.patch("onedrive_offsite.file_ops.download", return_value=True) as mock_download:
            with mock.patch("onedrive_offsite.file_ops.DownloadDecrypter.decrypt_and_combine", return_value=True) as mock_decrypt:
                with mock.patch("onedrive_offsite.file_ops.decrypt_email", return_value=False) as mock_email:
                    check_val = restore()
                    self.assertIs(check_val, False)

    def test_unit_download_decrypt_fail(self):
        with mock.patch("onedrive_offsite.file_ops.download", return_value=True) as mock_download:
            with mock.patch("onedrive_offsite.file_ops.DownloadDecrypter.decrypt_and_combine", return_value=None) as mock_decrypt:
                with mock.patch("onedrive_offsite.file_ops.decrypt_email", return_value=False) as mock_email:
                    check_val = restore()
                    self.assertIs(check_val, None)

    def test_unit_download_fail(self):
        with mock.patch("onedrive_offsite.file_ops.download", return_value=None) as mock_download:
            check_val = restore()
            self.assertIs(check_val, None)