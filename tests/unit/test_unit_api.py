import unittest, mock, os, json

from onedrive_offsite.api import api as flask_app, _send_error_email


class Testtransferstart(unittest.TestCase):
    test_dir = os.path.abspath(os.path.dirname(__file__))
    test_bfip = os.path.join(test_dir,"./fake_backup_info.json")


    def setUp(self):
        self.flask_app = flask_app
        self.flask_app.testing = True
        self.client = self.flask_app.test_client()

    def tearDown(self):
        if os.path.isfile(Testtransferstart.test_bfip):
            os.remove(Testtransferstart.test_bfip)
    
    @mock.patch("onedrive_offsite.api.Config")
    def test_unit_successful_start_with_upload_name(self, mock_config):
        mock_config.backup_file_info_path = Testtransferstart.test_bfip
        test_req_json = {"file-path":"~/my/backup.vm.zst", "username": "fakeuser", "size-bytes":23, "onedrive-filename":"fake-onedrive-upload.tar.gz", "onedrive-dir":"test_dir"}
        with mock.patch("onedrive_offsite.api.datetime.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2022-01-01-15:30:05"            
            res = self.client.post("/transfer/start", json=test_req_json)
            with open(Testtransferstart.test_bfip, "r") as backup_info_json:
                check_backup_file_info = json.load(backup_info_json)
            
            self.assertEqual(check_backup_file_info.get("backup-file-path"), "/home/fakeuser/my/backup.vm.zst")
            self.assertEqual(check_backup_file_info.get("size-bytes"), 23)
            self.assertEqual(check_backup_file_info.get("start-date-time"), "2022-01-01-15:30:05")
            self.assertEqual(check_backup_file_info.get("onedrive-filename"), "fake-onedrive-upload.tar.gz")
            self.assertEqual(check_backup_file_info.get("onedrive-dir"), "test_dir")
            self.assertEqual(res.status_code, 200)

    @mock.patch("onedrive_offsite.api.Config")
    def test_unit_successful_start_no_upload_name(self, mock_config):
        mock_config.backup_file_info_path = Testtransferstart.test_bfip
        test_req_json = {"file-path":"~/my/backup.vm.zst", "username": "fakeuser", "size-bytes":23, "onedrive-dir":"test_dir"}
        with mock.patch("onedrive_offsite.api.datetime.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2022-01-01-15:30:05"            
            res = self.client.post("/transfer/start", json=test_req_json)
            with open(Testtransferstart.test_bfip, "r") as backup_info_json:
                check_backup_file_info = json.load(backup_info_json)
            
            self.assertEqual(check_backup_file_info.get("backup-file-path"), "/home/fakeuser/my/backup.vm.zst")
            self.assertEqual(check_backup_file_info.get("size-bytes"), 23)
            self.assertEqual(check_backup_file_info.get("start-date-time"), "2022-01-01-15:30:05")
            self.assertEqual(check_backup_file_info.get("onedrive-filename"), None)
            self.assertEqual(check_backup_file_info.get("onedrive-dir"), "test_dir")
            self.assertEqual(res.status_code, 200)

    @mock.patch("onedrive_offsite.api.Config")
    def test_unit_successful_start_with_upload_name_no_tilda(self, mock_config):
        mock_config.backup_file_info_path = Testtransferstart.test_bfip
        test_req_json = {"file-path":"/my/backup.vm.zst", "username": "fakeuser", "size-bytes":23, "onedrive-filename":"fake-onedrive-upload.tar.gz", "onedrive-dir":"test_dir"}
        with mock.patch("onedrive_offsite.api.datetime.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2022-01-01-15:30:05"            
            res = self.client.post("/transfer/start", json=test_req_json)
            with open(Testtransferstart.test_bfip, "r") as backup_info_json:
                check_backup_file_info = json.load(backup_info_json)
            
            self.assertEqual(check_backup_file_info.get("backup-file-path"), "/my/backup.vm.zst")
            self.assertEqual(check_backup_file_info.get("size-bytes"), 23)
            self.assertEqual(check_backup_file_info.get("start-date-time"), "2022-01-01-15:30:05")
            self.assertEqual(check_backup_file_info.get("onedrive-filename"), "fake-onedrive-upload.tar.gz")
            self.assertEqual(check_backup_file_info.get("onedrive-dir"), "test_dir")
            self.assertEqual(res.status_code, 200)

    @mock.patch("onedrive_offsite.api.Config")
    def test_unit_missing_dir(self, mock_config):
        mock_config.backup_file_info_path = Testtransferstart.test_bfip
        test_req_json = {"file-path":"/my/backup.vm.zst", "username": "fakeuser", "size-bytes":23, "onedrive-filename":"fake-onedrive-upload.tar.gz"}
        with mock.patch("onedrive_offsite.api.datetime.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2022-01-01-15:30:05"            
            res = self.client.post("/transfer/start", json=test_req_json)      
            self.assertEqual(res.status_code, 400)

class Testtransferdone(unittest.TestCase):
    test_dir = os.path.abspath(os.path.dirname(__file__))
    test_bfip = os.path.join(test_dir,"./fake_backup_info.json")
    test_backup_file = os.path.join(test_dir, "./fake_backup_file")
    

    def setUp(self):
        self.flask_app = flask_app
        self.flask_app.testing = True
        self.client = self.flask_app.test_client()


    def tearDown(self):
        if os.path.isfile(Testtransferdone.test_bfip):
            os.remove(Testtransferdone.test_bfip)

        if os.path.isfile(Testtransferdone.test_backup_file):
            os.remove(Testtransferdone.test_backup_file)

    @mock.patch("onedrive_offsite.api.Config")
    def test_unit_successful_done_with_upload_name(self, mock_config):
        mock_config.backup_file_info_path = Testtransferdone.test_bfip
        test_info_json = {"backup-file-path": Testtransferdone.test_backup_file , "start-date-time": "2022-01-01-15:30:05", "size-bytes": 23, "onedrive-filename": "fake-onedrive-upload.tar.gz"}
        with open(Testtransferdone.test_bfip, "w") as backup_info_file:
            json.dump(test_info_json, backup_info_file)
        with open(Testtransferdone.test_backup_file, "w") as backup_file:
            backup_file.write("12345678901234567890123")
        with mock.patch("onedrive_offsite.api.datetime.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2022-01-01-15:35:05"
            with mock.patch("onedrive_offsite.api.subprocess.Popen") as mock_popen:
                res = self.client.put("/transfer/done")

                with open(Testtransferdone.test_bfip, "r") as backup_info_json:
                    check_backup_file_info = json.load(backup_info_json)

                self.assertEqual(check_backup_file_info.get("done-date-time"), "2022-01-01-15:35:05")
                self.assertEqual(res.status_code, 201)


    @mock.patch("onedrive_offsite.api.Config")
    def test_unit_fail_done_json_dump_exception(self, mock_config):
        mock_config.backup_file_info_path = Testtransferdone.test_bfip
        test_info_json = {"backup-file-path": Testtransferdone.test_backup_file , "start-date-time": "2022-01-01-15:30:05", "size-bytes": 23, "onedrive-filename": "fake-onedrive-upload.tar.gz"}
        with open(Testtransferdone.test_bfip, "w") as backup_info_file:
            json.dump(test_info_json, backup_info_file)
        with open(Testtransferdone.test_backup_file, "w") as backup_file:
            backup_file.write("12345678901234567890123")
        with mock.patch("onedrive_offsite.api.datetime.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2022-01-01-15:35:05"
            with mock.patch("onedrive_offsite.api.json.dump", side_effect=Exception("exception")) as mock_json_dump:
                with mock.patch("onedrive_offsite.api._send_error_email") as mock_send_err_email:
                    res = self.client.put("/transfer/done")
                    self.assertEqual(res.status_code, 500)

    @mock.patch("onedrive_offsite.api.Config")
    def test_unit_fail_done_backup_file_size_not_match(self, mock_config):
        mock_config.backup_file_info_path = Testtransferdone.test_bfip
        test_info_json = {"backup-file-path": Testtransferdone.test_backup_file , "start-date-time": "2022-01-01-15:30:05", "size-bytes": 15, "onedrive-filename": "fake-onedrive-upload.tar.gz"}
        with open(Testtransferdone.test_bfip, "w") as backup_info_file:
            json.dump(test_info_json, backup_info_file)
        with open(Testtransferdone.test_backup_file, "w") as backup_file:
            backup_file.write("12345678901234567890123")
        with mock.patch("onedrive_offsite.api._send_error_email") as mock_send_err_email:
            res = self.client.put("/transfer/done")
            self.assertEqual(res.status_code, 409)

    @mock.patch("onedrive_offsite.api.Config")
    def test_unit_fail_done_no_backup_file(self, mock_config):
        mock_config.backup_file_info_path = Testtransferdone.test_bfip
        test_info_json = {"backup-file-path": Testtransferdone.test_backup_file , "start-date-time": "2022-01-01-15:30:05", "size-bytes": 23}
        with open(Testtransferdone.test_bfip, "w") as backup_info_file:
            json.dump(test_info_json, backup_info_file)
        with mock.patch("onedrive_offsite.api._send_error_email") as mock_send_err_email:
            res = self.client.put("/transfer/done")
            self.assertEqual(res.status_code, 404)



class Test_senderroremail(unittest.TestCase):

    def test_unit_success_send_email(self):
        with mock.patch("onedrive_offsite.api.get_recent_log_lines", return_value = "fake log lines") as mock_log_lines:
            with mock.patch("onedrive_offsite.api.ses_send_email") as mock_ses_send_email:
                check_value = _send_error_email("fake_onedrive_file_name")
                self.assertEqual(check_value, True)

    def test_unit_fail_send_email_exception(self):
        with mock.patch("onedrive_offsite.api.get_recent_log_lines", return_value = "fake log lines") as mock_log_lines:
            with mock.patch("onedrive_offsite.api.ses_send_email", side_effect=Exception("exception")) as mock_ses_send_email:
                check_value = _send_error_email("fake_onedrive_file_name")
                self.assertEqual(check_value, False)

        
class Testdownloaddecrypt(unittest.TestCase):
    test_dir = os.path.abspath(os.path.dirname(__file__))
    test_download_info_path = os.path.join(test_dir,"./download_info.json")

    

    def setUp(self):
        self.flask_app = flask_app
        self.flask_app.testing = True
        self.client = self.flask_app.test_client()


    def tearDown(self):
        if os.path.isfile(Testdownloaddecrypt.test_download_info_path):
            os.remove(Testdownloaddecrypt.test_download_info_path)


    def test_unit_missing_onedrive_dir(self):
        test_req_json = {"missing-onedrive":"no-dir"}
        with mock.patch("onedrive_offsite.api.datetime.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2022-01-01-15:30:05"            
            res = self.client.post("/download-decrypt", json=test_req_json)
            self.assertEqual(res.status_code, 400)

    @mock.patch("onedrive_offsite.api.Config")
    def test_unit_everything_works(self, mock_config):
        mock_config.download_info_path = Testdownloaddecrypt.test_download_info_path
        test_req_json = {"onedrive-dir":"fake-dir"}
        with mock.patch("onedrive_offsite.api.datetime.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2022-01-01-15:30:05" 
            with mock.patch("onedrive_offsite.api.subprocess.Popen") as mock_popen:
                res = self.client.post("/download-decrypt", json=test_req_json)
                with open(Testdownloaddecrypt.test_download_info_path, "r") as download_info_json:
                    check_download_file_info = json.load(download_info_json)
                
                self.assertEqual(check_download_file_info.get("onedrive-dir"), "fake-dir")
                self.assertEqual(res.status_code, 200)

