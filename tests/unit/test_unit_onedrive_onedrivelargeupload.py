import unittest, mock, requests

from onedrive_offsite.onedrive import OneDriveLargeUpload

@mock.patch("onedrive_offsite.onedrive.threading.current_thread")
class TestOneDriveLargeUpload(unittest.TestCase):

### -------------- OneDriveLargeUpload.__init__() ------------------------
    def test_unit_init_except(self, mock_thread_getname):  
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            with mock.patch("onedrive_offsite.onedrive.json.load", side_effect=Exception("fake exception")) as mock_json_load:    
                odlu = OneDriveLargeUpload("fakeuploadfilename")
                self.assertEqual(odlu.dir_name, None)
                self.assertEqual(odlu.dir_id, None)

    def test_unit_init_no_dir(self, mock_thread_getname):  
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                             "start-date-time": "2022-04-14-21:37:09",
                             "size-bytes": 170403564,
                             "onedrive-filename": "backup_test_local.tar.gz",
                             "done-date-time": "2022-04-14-21:37:15", 
                             "onedrive-dir-id": "D23D09990A1D5FC9!161"}
            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:   
                odlu = OneDriveLargeUpload("fakeuploadfilename")
                self.assertEqual(odlu.dir_name, None)
                self.assertEqual(odlu.dir_id, "D23D09990A1D5FC9!161")

    def test_unit_init_no_dir_id(self, mock_thread_getname):  
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                             "start-date-time": "2022-04-14-21:37:09",
                             "size-bytes": 170403564,
                             "onedrive-dir": "backup_test_2",
                             "onedrive-filename": "backup_test_local.tar.gz",
                             "done-date-time": "2022-04-14-21:37:15",}
            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:   
                odlu = OneDriveLargeUpload("fakeuploadfilename")
                self.assertEqual(odlu.dir_name, "backup_test_2")
                self.assertEqual(odlu.dir_id, None)
 


#### ------------ OneDriveLargeUpload._upload_initiate_retry() -------------------------
    def test_unit_upload_initiate_retry_retry_1(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.time.sleep", return_value=None) as mock_sleep:
            check_value = OneDriveLargeUpload._upload_initiate_retry(1, "fakefilename")
            self.assertEqual(check_value, True)
    
    def test_unit_upload_initiate_retry_retry_2(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.time.sleep", return_value=None) as mock_sleep:
            check_value = OneDriveLargeUpload._upload_initiate_retry(2, "fakefilename")
            self.assertEqual(check_value, True)
    
    def test_unit_upload_initiate_retry_retry_3(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.time.sleep", return_value=None) as mock_sleep:
            check_value = OneDriveLargeUpload._upload_initiate_retry(3, "fakefilename")
            self.assertEqual(check_value, True)

    def test_unit_upload_initiate_retry_retry_4(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.time.sleep", return_value=None) as mock_sleep:
            check_value = OneDriveLargeUpload._upload_initiate_retry(4, "fakefilename")
            self.assertEqual(check_value, False)

### -------------- OneDriveLargeUpload.initiate_upload_session() ------------------------
    def test_unit_initiate_upload_session_success(self, mock_thread_getname):  
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                             "start-date-time": "2022-04-14-21:37:09",
                             "size-bytes": 170403564,
                             "onedrive-dir": "backup_test_2",
                             "onedrive-filename": "backup_test_local.tar.gz",
                             "done-date-time": "2022-04-14-21:37:15", 
                             "onedrive-dir-id": "D23D09990A1D5FC9!161"}
            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:      
                with mock.patch("onedrive_offsite.onedrive.requests.post") as mock_requests_post:
                    mock_requests_post.return_value.status_code =200
                    mock_requests_post.return_value.json.return_value = {"uploadUrl":"fake-url", "expirationDateTime":"2015-01-29T09:21:55.523Z"}
                    odlu = OneDriveLargeUpload("fakeuploadfilename")
                    check_value = odlu.initiate_upload_session("fakeaccesstoken")
                    self.assertEqual(check_value, True)

    def test_unit_initiate_upload_session_fail_timeout(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                             "start-date-time": "2022-04-14-21:37:09",
                             "size-bytes": 170403564,
                             "onedrive-dir": "backup_test_2",
                             "onedrive-filename": "backup_test_local.tar.gz",
                             "done-date-time": "2022-04-14-21:37:15", 
                             "onedrive-dir-id": "D23D09990A1D5FC9!161"}
            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                with mock.patch("onedrive_offsite.onedrive.requests.post", side_effect=requests.exceptions.Timeout) as mock_requests_post:
                    with mock.patch("onedrive_offsite.onedrive.OneDriveLargeUpload._upload_initiate_retry", return_value=False) as mock_retry:
                        odlu = OneDriveLargeUpload("fakeuploadfilename")
                        check_value = odlu.initiate_upload_session("fakeaccesstoken")
                        self.assertEqual(check_value, False)

    def test_unit_initiate_upload_session_fail_sslerror(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                             "start-date-time": "2022-04-14-21:37:09",
                             "size-bytes": 170403564,
                             "onedrive-dir": "backup_test_2",
                             "onedrive-filename": "backup_test_local.tar.gz",
                             "done-date-time": "2022-04-14-21:37:15", 
                             "onedrive-dir-id": "D23D09990A1D5FC9!161"}
            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                with mock.patch("onedrive_offsite.onedrive.requests.post", side_effect=requests.exceptions.SSLError) as mock_requests_post:
                    with mock.patch("onedrive_offsite.onedrive.OneDriveLargeUpload._upload_initiate_retry", return_value=False) as mock_retry:
                        odlu = OneDriveLargeUpload("fakeuploadfilename")
                        check_value = odlu.initiate_upload_session("fakeaccesstoken")
                        self.assertEqual(check_value, False)
    
    def test_unit_initiate_upload_session_fail_connection_error(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                             "start-date-time": "2022-04-14-21:37:09",
                             "size-bytes": 170403564,
                             "onedrive-dir": "backup_test_2",
                             "onedrive-filename": "backup_test_local.tar.gz",
                             "done-date-time": "2022-04-14-21:37:15", 
                             "onedrive-dir-id": "D23D09990A1D5FC9!161"}
            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                with mock.patch("onedrive_offsite.onedrive.requests.post", side_effect=requests.exceptions.ConnectionError) as mock_requests_post:
                    with mock.patch("onedrive_offsite.onedrive.OneDriveLargeUpload._upload_initiate_retry", return_value=False) as mock_retry:
                        odlu = OneDriveLargeUpload("fakeuploadfilename")
                        check_value = odlu.initiate_upload_session("fakeaccesstoken")
                        self.assertEqual(check_value, False)

    def test_unit_initiate_upload_session_fail_unhandled_exception(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                             "start-date-time": "2022-04-14-21:37:09",
                             "size-bytes": 170403564,
                             "onedrive-dir": "backup_test_2",
                             "onedrive-filename": "backup_test_local.tar.gz",
                             "done-date-time": "2022-04-14-21:37:15", 
                             "onedrive-dir-id": "D23D09990A1D5FC9!161"}
            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                with mock.patch("onedrive_offsite.onedrive.requests.post", side_effect=Exception("fake exception")) as mock_requests_post:
                    odlu = OneDriveLargeUpload("fakeuploadfilename")
                    check_value = odlu.initiate_upload_session("fakeaccesstoken")
                    self.assertEqual(check_value, False)
    
    def test_unit_initiate_upload_session_fail_5xx(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                             "start-date-time": "2022-04-14-21:37:09",
                             "size-bytes": 170403564,
                             "onedrive-dir": "backup_test_2",
                             "onedrive-filename": "backup_test_local.tar.gz",
                             "done-date-time": "2022-04-14-21:37:15", 
                             "onedrive-dir-id": "D23D09990A1D5FC9!161"}
            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                with mock.patch("onedrive_offsite.onedrive.requests.post") as mock_requests_post:
                    mock_requests_post.return_value.status_code = 503
                    mock_requests_post.return_value.json.return_value = {"Error":"fake error"}
                    with mock.patch("onedrive_offsite.onedrive.OneDriveLargeUpload._upload_initiate_retry", return_value=False) as mock_retry:
                        odlu = OneDriveLargeUpload("fakeuploadfilename")
                        check_value = odlu.initiate_upload_session("fakeaccesstoken")
                        self.assertEqual(check_value, False)

    def test_unit_initiate_upload_session_fail_4xx(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                             "start-date-time": "2022-04-14-21:37:09",
                             "size-bytes": 170403564,
                             "onedrive-dir": "backup_test_2",
                             "onedrive-filename": "backup_test_local.tar.gz",
                             "done-date-time": "2022-04-14-21:37:15", 
                             "onedrive-dir-id": "D23D09990A1D5FC9!161"}
            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                with mock.patch("onedrive_offsite.onedrive.requests.post") as mock_requests_post:
                    mock_requests_post.return_value.status_code = 416
                    mock_requests_post.return_value.json.return_value = {"Error":"fake error"}
                    odlu = OneDriveLargeUpload("fakeuploadfilename")
                    check_value = odlu.initiate_upload_session("fakeaccesstoken")
                    self.assertEqual(check_value, False)


### ---------------------- OneDriveLargeUpload._retry_logic() ---------------------------------------------

    def test_unit_retry_logic_1(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.time.sleep", return_value=None) as mock_sleep:
            check_value = OneDriveLargeUpload._retry_logic("0-100001", 1)
            self.assertEqual(check_value, True)
    
    def test_unit_retry_logic_2(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.time.sleep", return_value=None) as mock_sleep:
            check_value = OneDriveLargeUpload._retry_logic("0-100001", 2)
            self.assertEqual(check_value, True)

    def test_unit_retry_logic_3(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.time.sleep", return_value=None) as mock_sleep:    
            check_value = OneDriveLargeUpload._retry_logic("0-100001", 3)
            self.assertEqual(check_value, True)

    def test_unit_retry_logic_4(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.time.sleep", return_value=None) as mock_sleep:
            check_value = OneDriveLargeUpload._retry_logic("0-100001", 4)
            self.assertEqual(check_value, False)



### ----------------------- OneDriveLargeUpload.upload_file_part() ----------------------------------------

    def test_unit_upload_file_part_upload_accepted(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                             "start-date-time": "2022-04-14-21:37:09",
                             "size-bytes": 170403564,
                             "onedrive-dir": "backup_test_2",
                             "onedrive-filename": "backup_test_local.tar.gz",
                             "done-date-time": "2022-04-14-21:37:15", 
                             "onedrive-dir-id": "D23D09990A1D5FC9!161"}
            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                test_json = {'expirationDateTime': '2022-01-22T22:49:43.2Z', 'nextExpectedRanges': ['500-999']}
                with mock.patch("onedrive_offsite.onedrive.requests.put") as mock_requests_put:
                    mock_requests_put.return_value.status_code = 202
                    mock_requests_put.return_value.json.return_value = test_json
                    odlu = OneDriveLargeUpload("fakefilename")
                    check_value = odlu.upload_file_part("1000", "500", "0-499", b'my fake bytes, definitely not 500 bytes')
                    self.assertEqual(check_value.status_code, 202)
                    self.assertEqual(check_value.json(), test_json)

    def test_unit_upload_file_part_upload_complete(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                             "start-date-time": "2022-04-14-21:37:09",
                             "size-bytes": 170403564,
                             "onedrive-dir": "backup_test_2",
                             "onedrive-filename": "backup_test_local.tar.gz",
                             "done-date-time": "2022-04-14-21:37:15", 
                             "onedrive-dir-id": "D23D09990A1D5FC9!161"}
            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                test_json = {"id": "912310013A123","name": "fakefilename","size": 500, "file": { }}
                with mock.patch("onedrive_offsite.onedrive.requests.put") as mock_requests_put:
                    mock_requests_put.return_value.status_code = 201
                    mock_requests_put.return_value.json.return_value = test_json
                    odlu = OneDriveLargeUpload("fakefilename")
                    check_value = odlu.upload_file_part("1000", "500", "500-999", b'my fake bytes, definitely not 500 bytes')
                    self.assertEqual(check_value.status_code, 201)
                    self.assertEqual(check_value.json(), test_json)

    def test_unit_upload_file_part_upload_timeout(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                             "start-date-time": "2022-04-14-21:37:09",
                             "size-bytes": 170403564,
                             "onedrive-dir": "backup_test_2",
                             "onedrive-filename": "backup_test_local.tar.gz",
                             "done-date-time": "2022-04-14-21:37:15", 
                             "onedrive-dir-id": "D23D09990A1D5FC9!161"}
            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                with mock.patch("onedrive_offsite.onedrive.requests.put", side_effect=requests.exceptions.Timeout) as mock_requests_put:
                    with mock.patch("onedrive_offsite.onedrive.OneDriveLargeUpload._retry_logic", return_value=False) as mock_retry_logic: # simulate final retry
                        odlu = OneDriveLargeUpload("fakefilename")
                        check_value = odlu.upload_file_part("1000", "500", "500-999", b'my fake bytes, definitely not 500 bytes')
                        self.assertEqual(check_value, False)

    def test_unit_upload_file_part_upload_ssl_error(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                            "start-date-time": "2022-04-14-21:37:09",
                            "size-bytes": 170403564,
                            "onedrive-dir": "backup_test_2",
                            "onedrive-filename": "backup_test_local.tar.gz",
                            "done-date-time": "2022-04-14-21:37:15", 
                            "onedrive-dir-id": "D23D09990A1D5FC9!161"}

            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                with mock.patch("onedrive_offsite.onedrive.requests.put", side_effect=requests.exceptions.SSLError) as mock_requests_put:
                    with mock.patch("onedrive_offsite.onedrive.OneDriveLargeUpload._retry_logic", return_value=False) as mock_retry_logic: # simulate final retry
                        odlu = OneDriveLargeUpload("fakefilename")
                        check_value = odlu.upload_file_part("1000", "500", "500-999", b'my fake bytes, definitely not 500 bytes')
                        self.assertEqual(check_value, False)

    def test_unit_upload_file_part_upload_ssl_conn_err(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                             "start-date-time": "2022-04-14-21:37:09",
                             "size-bytes": 170403564,
                             "onedrive-dir": "backup_test_2",
                             "onedrive-filename": "backup_test_local.tar.gz",
                             "done-date-time": "2022-04-14-21:37:15", 
                             "onedrive-dir-id": "D23D09990A1D5FC9!161"}
            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                with mock.patch("onedrive_offsite.onedrive.requests.put", side_effect=requests.exceptions.ConnectionError) as mock_requests_put:
                    with mock.patch("onedrive_offsite.onedrive.OneDriveLargeUpload._retry_logic", return_value=False) as mock_retry_logic: # simulate final retry
                        odlu = OneDriveLargeUpload("fakefilename")
                        check_value = odlu.upload_file_part("1000", "500", "500-999", b'my fake bytes, definitely not 500 bytes')
                        self.assertEqual(check_value, False)

    def test_unit_upload_file_part_upload_unexpected_exception(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                             "start-date-time": "2022-04-14-21:37:09",
                             "size-bytes": 170403564,
                             "onedrive-dir": "backup_test_2",
                             "onedrive-filename": "backup_test_local.tar.gz",
                             "done-date-time": "2022-04-14-21:37:15", 
                             "onedrive-dir-id": "D23D09990A1D5FC9!161"}

            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                with mock.patch("onedrive_offsite.onedrive.requests.put", side_effect=Exception("unexpected exception")) as mock_requests_put:
                    with mock.patch("onedrive_offsite.onedrive.OneDriveLargeUpload._retry_logic", return_value=False) as mock_retry_logic: # simulate final retry
                        odlu = OneDriveLargeUpload("fakefilename")
                        check_value = odlu.upload_file_part("1000", "500", "500-999", b'my fake bytes, definitely not 500 bytes')
                        self.assertEqual(check_value, False)

    def test_unit_upload_file_part_upload_5xx(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                             "start-date-time": "2022-04-14-21:37:09",
                             "size-bytes": 170403564,
                             "onedrive-dir": "backup_test_2",
                             "onedrive-filename": "backup_test_local.tar.gz",
                             "done-date-time": "2022-04-14-21:37:15", 
                             "onedrive-dir-id": "D23D09990A1D5FC9!161"}

            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                test_json = {"error": {"code": "generalException", "message": "General Exception While Processing"}}
                with mock.patch("onedrive_offsite.onedrive.requests.put") as mock_requests_put:
                    mock_requests_put.return_value.status_code = 500
                    mock_requests_put.return_value.json.return_value = test_json
                    with mock.patch("onedrive_offsite.onedrive.OneDriveLargeUpload._retry_logic", return_value=False) as mock_retry_logic: # simulate final retry
                        odlu = OneDriveLargeUpload("fakefilename")
                        check_value = odlu.upload_file_part("1000", "500", "500-999", b'my fake bytes, definitely not 500 bytes')
                        self.assertEqual(check_value.status_code, 500)
                        self.assertEqual(check_value.json(), test_json)

    def test_unit_upload_file_part_upload_416_first_fail(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                            "start-date-time": "2022-04-14-21:37:09",
                            "size-bytes": 170403564,
                            "onedrive-dir": "backup_test_2",
                            "onedrive-filename": "backup_test_local.tar.gz",
                            "done-date-time": "2022-04-14-21:37:15", 
                            "onedrive-dir-id": "D23D09990A1D5FC9!161"}

            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                test_json = {"error":{"code":"invalidRange", "message":"The uploaded fragment overlaps with data that has already been received.","innererror":{"code":"fragmentOverlap"}}}
                with mock.patch("onedrive_offsite.onedrive.requests.put") as mock_requests_put:
                    mock_requests_put.return_value.status_code = 416
                    mock_requests_put.return_value.json.return_value = test_json
                    with mock.patch("onedrive_offsite.onedrive.OneDriveLargeUpload._retry_partial_fragment", return_value=False) as mock_retry_logic: # simulate final retry
                        odlu = OneDriveLargeUpload("fakefilename")
                        check_value = odlu.upload_file_part("1000", "500", "500-999", b'my fake bytes, definitely not 500 bytes')
                        self.assertEqual(check_value.status_code, 416)
                        self.assertEqual(check_value.json(), test_json)

    def test_unit_upload_file_part_upload_416_move_next(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                            "start-date-time": "2022-04-14-21:37:09",
                            "size-bytes": 170403564,
                            "onedrive-dir": "backup_test_2",
                            "onedrive-filename": "backup_test_local.tar.gz",
                            "done-date-time": "2022-04-14-21:37:15", 
                            "onedrive-dir-id": "D23D09990A1D5FC9!161"}

            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                test_json = {"error":{"code":"invalidRange", "message":"The uploaded fragment overlaps with data that has already been received.","innererror":{"code":"fragmentOverlap"}}}
                with mock.patch("onedrive_offsite.onedrive.requests.put") as mock_requests_put:
                    mock_requests_put.return_value.status_code = 416
                    mock_requests_put.return_value.json.return_value = test_json
                    with mock.patch("onedrive_offsite.onedrive.OneDriveLargeUpload._retry_partial_fragment", return_value="move-next") as mock_retry_logic: # simulate final retry
                        odlu = OneDriveLargeUpload("fakefilename")
                        check_value = odlu.upload_file_part("1000", "500", "500-999", b'my fake bytes, definitely not 500 bytes')
                        self.assertEqual(check_value, "move-next")


    def test_unit_upload_file_part_upload_416_first_success(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                            "start-date-time": "2022-04-14-21:37:09",
                            "size-bytes": 170403564,
                            "onedrive-dir": "backup_test_2",
                            "onedrive-filename": "backup_test_local.tar.gz",
                            "done-date-time": "2022-04-14-21:37:15", 
                            "onedrive-dir-id": "D23D09990A1D5FC9!161"}

            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                test_json = {"error":{"code":"invalidRange", "message":"The uploaded fragment overlaps with data that has already been received.","innererror":{"code":"fragmentOverlap"}}}
                with mock.patch("onedrive_offsite.onedrive.requests.put") as mock_requests_put:
                    mock_requests_put.return_value.status_code = 416
                    mock_requests_put.return_value.json.return_value = test_json
                    with mock.patch("onedrive_offsite.onedrive.OneDriveLargeUpload._retry_partial_fragment") as mock_retry_logic: # simulate successful partial upload
                        test_json_partial = {'expirationDateTime': '2022-01-22T22:49:43.2Z', 'nextExpectedRanges': ['500-999']}
                        mock_retry_logic.return_value.status_code = 202
                        mock_retry_logic.return_value.json.return_value = test_json_partial
                        odlu = OneDriveLargeUpload("fakefilename")
                        check_value = odlu.upload_file_part("1000", "500", "0-499", b'my fake bytes, definitely not 500 bytes')
                        self.assertEqual(check_value.status_code, 202)
                        self.assertEqual(check_value.json(), test_json_partial)

    def test_unit_upload_file_part_upload_416_second_fail(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                            "start-date-time": "2022-04-14-21:37:09",
                            "size-bytes": 170403564,
                            "onedrive-dir": "backup_test_2",
                            "onedrive-filename": "backup_test_local.tar.gz",
                            "done-date-time": "2022-04-14-21:37:15", 
                            "onedrive-dir-id": "D23D09990A1D5FC9!161"}

            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                test_json = {"error":{"code":"invalidRange", "message":"The uploaded fragment overlaps with data that has already been received.","innererror":{"code":"fragmentOverlap"}}}
                with mock.patch("onedrive_offsite.onedrive.requests.put") as mock_requests_put:
                    mock_requests_put.return_value.status_code = 416
                    mock_requests_put.return_value.json.return_value = test_json
                    with mock.patch("onedrive_offsite.onedrive.OneDriveLargeUpload._retry_partial_fragment", return_value=False) as mock_retry_logic: # simulate final retry
                        odlu = OneDriveLargeUpload("fakefilename")
                        check_value = odlu.upload_file_part("1000", "500", "500-999", b'my fake bytes, definitely not 500 bytes', flag_416=True) # flag_416=True indicates 416 already happend before this method was called
                        self.assertEqual(check_value.status_code, 416)
                        self.assertEqual(check_value.json(), test_json)

    def test_unit_upload_file_part_upload_404(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                            "start-date-time": "2022-04-14-21:37:09",
                            "size-bytes": 170403564,
                            "onedrive-dir": "backup_test_2",
                            "onedrive-filename": "backup_test_local.tar.gz",
                            "done-date-time": "2022-04-14-21:37:15", 
                            "onedrive-dir-id": "D23D09990A1D5FC9!161"}

            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                test_json = {"error": "not found"}
                with mock.patch("onedrive_offsite.onedrive.requests.put") as mock_requests_put:
                    mock_requests_put.return_value.status_code = 404
                    mock_requests_put.return_value.json.return_value = test_json
                    with mock.patch("onedrive_offsite.onedrive.OneDriveLargeUpload._retry_logic", return_value=False) as mock_retry_logic: # simulate final retry
                        odlu = OneDriveLargeUpload("fakefilename")
                        check_value = odlu.upload_file_part("1000", "500", "500-999", b'my fake bytes, definitely not 500 bytes')
                        self.assertEqual(check_value.status_code, 404)
                        self.assertEqual(check_value.json(), test_json)


### ---------------------- OneDriveLargeUpload._retry_partial_fragment() ----------------------------------
    def test_partial_retry_upload_fail_upload(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                            "start-date-time": "2022-04-14-21:37:09",
                            "size-bytes": 170403564,
                            "onedrive-dir": "backup_test_2",
                            "onedrive-filename": "backup_test_local.tar.gz",
                            "done-date-time": "2022-04-14-21:37:15", 
                            "onedrive-dir-id": "D23D09990A1D5FC9!161"}

            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                with mock.patch("onedrive_offsite.onedrive.OneDriveLargeUpload.upload_file_part") as mock_up_file_part:
                    mock_resp = mock.Mock()
                    mock_resp.status_code = 500
                    mock_up_file_part.return_value = mock_resp            
                    odlu = OneDriveLargeUpload("fakeuploadfilename")
                
                    check_value = odlu._partial_retry_upload("10", "4", "0-3", b'abcd', flag_416=True)
                    self.assertEqual(check_value, False)

    def test_partial_retry_upload_success(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                            "start-date-time": "2022-04-14-21:37:09",
                            "size-bytes": 170403564,
                            "onedrive-dir": "backup_test_2",
                            "onedrive-filename": "backup_test_local.tar.gz",
                            "done-date-time": "2022-04-14-21:37:15", 
                            "onedrive-dir-id": "D23D09990A1D5FC9!161"}

            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                with mock.patch("onedrive_offsite.onedrive.OneDriveLargeUpload.upload_file_part") as mock_up_file_part:
                    mock_resp = mock.Mock()
                    mock_resp.status_code = 202
                    mock_up_file_part.return_value = mock_resp            
                    odlu = OneDriveLargeUpload("fakeuploadfilename")
                
                    check_value = odlu._partial_retry_upload("10", "4", "0-3", b'abcd', flag_416=True)
                    self.assertEqual(check_value, mock_resp)


### ---------------------- OneDriveLargeUpload._retry_partial_fragment() ----------------------------------
    def test_unit_retry_partial_fragment_everything_works(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                            "start-date-time": "2022-04-14-21:37:09",
                            "size-bytes": 170403564,
                            "onedrive-dir": "backup_test_2",
                            "onedrive-filename": "backup_test_local.tar.gz",
                            "done-date-time": "2022-04-14-21:37:15", 
                            "onedrive-dir-id": "D23D09990A1D5FC9!161"}

            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                with mock.patch("onedrive_offsite.onedrive.requests.get") as mock_requests_get:
                    mock_requests_get.return_value.status_code = 200
                    mock_requests_get.return_value.json.return_value = {'expirationDateTime': '2022-01-22T22:49:43.2Z', 'nextExpectedRanges': ['3-9']}
                    with mock.patch("onedrive_offsite.onedrive.OneDriveLargeUpload._partial_retry_upload") as mock_part_retry_up:
                        with mock.patch("onedrive_offsite.onedrive.sleep", return_value=None) as mock_sleep:
                            mock_part_retry_resp = mock.Mock()
                            mock_part_retry_resp.status_code = 200
                            mock_part_retry_up.return_value = mock_part_retry_resp
                            odlu = OneDriveLargeUpload("fakeuploadfilename")
                            check_value = odlu._retry_partial_fragment("10", "0-4",b'abcd')
                            self.assertEqual(check_value.status_code, 200)

    def test_unit_retry_partial_fragment_fail_fetch_status(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                            "start-date-time": "2022-04-14-21:37:09",
                            "size-bytes": 170403564,
                            "onedrive-dir": "backup_test_2",
                            "onedrive-filename": "backup_test_local.tar.gz",
                            "done-date-time": "2022-04-14-21:37:15", 
                            "onedrive-dir-id": "D23D09990A1D5FC9!161"}

            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                with mock.patch("onedrive_offsite.onedrive.requests.get", side_effect=Exception("fake exception")) as mock_requests_get:
                    odlu = OneDriveLargeUpload("fakeuploadfilename")
                    check_value = odlu._retry_partial_fragment("10", "0-4",b'abcd')
                    self.assertEqual(check_value, False)

    def test_unit_retry_partial_fragment_expected_range_outside_range(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                            "start-date-time": "2022-04-14-21:37:09",
                            "size-bytes": 170403564,
                            "onedrive-dir": "backup_test_2",
                            "onedrive-filename": "backup_test_local.tar.gz",
                            "done-date-time": "2022-04-14-21:37:15", 
                            "onedrive-dir-id": "D23D09990A1D5FC9!161"}

            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                with mock.patch("onedrive_offsite.onedrive.requests.get") as mock_requests_get:
                    mock_requests_get.return_value.status_code = 200
                    mock_requests_get.return_value.json.return_value = {'expirationDateTime': '2022-01-22T22:49:43.2Z', 'nextExpectedRanges': ['0-9']}
                    odlu = OneDriveLargeUpload("fakeuploadfilename")
                    check_value = odlu._retry_partial_fragment("10", "1-4",b'bcd')
                    self.assertEqual(check_value, False)

    def test_unit_retry_partial_fragment_expected_range_1_over(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                            "start-date-time": "2022-04-14-21:37:09",
                            "size-bytes": 170403564,
                            "onedrive-dir": "backup_test_2",
                            "onedrive-filename": "backup_test_local.tar.gz",
                            "done-date-time": "2022-04-14-21:37:15", 
                            "onedrive-dir-id": "D23D09990A1D5FC9!161"}

            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                with mock.patch("onedrive_offsite.onedrive.requests.get") as mock_requests_get:
                    mock_requests_get.return_value.status_code = 200
                    mock_requests_get.return_value.json.return_value = {'expirationDateTime': '2022-01-22T22:49:43.2Z', 'nextExpectedRanges': ['5-9']}
                    odlu = OneDriveLargeUpload("fakeuploadfilename")
                    check_value = odlu._retry_partial_fragment("10", "1-4",b'bcd')
                    self.assertEqual(check_value, "move-next")
    
    def test_unit_retry_partial_fragment_upload_error(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                            "start-date-time": "2022-04-14-21:37:09",
                            "size-bytes": 170403564,
                            "onedrive-dir": "backup_test_2",
                            "onedrive-filename": "backup_test_local.tar.gz",
                            "done-date-time": "2022-04-14-21:37:15", 
                            "onedrive-dir-id": "D23D09990A1D5FC9!161"}

            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                with mock.patch("onedrive_offsite.onedrive.requests.get") as mock_requests_get:
                    mock_requests_get.return_value.status_code = 200
                    mock_requests_get.return_value.json.return_value = {'expirationDateTime': '2022-01-22T22:49:43.2Z', 'nextExpectedRanges': ['3-9']}
                    with mock.patch("onedrive_offsite.onedrive.OneDriveLargeUpload._partial_retry_upload") as mock_part_retry_up:
                        with mock.patch("onedrive_offsite.onedrive.sleep", return_value=None) as mock_sleep:
                            mock_part_retry_up.return_value = False
                            odlu = OneDriveLargeUpload("fakeuploadfilename")
                            check_value = odlu._retry_partial_fragment("10", "0-4",b'abcd')
                            self.assertEqual(check_value, False)
                            self.assertEqual(mock_part_retry_up.call_count, 2)


### -------------------- OneDriveLargeUpload.cancel_upload_session() ---------------------------

    def test_unit_cancel_upload_session_success(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                            "start-date-time": "2022-04-14-21:37:09",
                            "size-bytes": 170403564,
                            "onedrive-dir": "backup_test_2",
                            "onedrive-filename": "backup_test_local.tar.gz",
                            "done-date-time": "2022-04-14-21:37:15", 
                            "onedrive-dir-id": "D23D09990A1D5FC9!161"}

            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                with mock.patch("onedrive_offsite.onedrive.requests.delete") as mock_requests_delete:
                    mock_requests_delete.return_value.status_code = 204
                    odlu = OneDriveLargeUpload("fakename")
                    check_value = odlu.cancel_upload_session()
                    self.assertEqual(check_value, True)

    def test_unit_cancel_upload_session_exception(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                            "start-date-time": "2022-04-14-21:37:09",
                            "size-bytes": 170403564,
                            "onedrive-dir": "backup_test_2",
                            "onedrive-filename": "backup_test_local.tar.gz",
                            "done-date-time": "2022-04-14-21:37:15", 
                            "onedrive-dir-id": "D23D09990A1D5FC9!161"}

            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                with mock.patch("onedrive_offsite.onedrive.requests.delete", side_effect=Exception("fake exception")) as mock_requests_delete:
                    odlu = OneDriveLargeUpload("fakename")
                    check_value = odlu.cancel_upload_session()
                    self.assertEqual(check_value, False)

    def test_unit_cancel_upload_session_5xx(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                            "start-date-time": "2022-04-14-21:37:09",
                            "size-bytes": 170403564,
                            "onedrive-dir": "backup_test_2",
                            "onedrive-filename": "backup_test_local.tar.gz",
                            "done-date-time": "2022-04-14-21:37:15", 
                            "onedrive-dir-id": "D23D09990A1D5FC9!161"}

            with mock.patch("onedrive_offsite.onedrive.json.load", return_value=test_info_json) as mock_json_load:
                with mock.patch("onedrive_offsite.onedrive.requests.delete") as mock_requests_delete:
                    mock_requests_delete.return_value.status_code = 500
                    odlu = OneDriveLargeUpload("fakename")
                    check_value = odlu.cancel_upload_session()
                    self.assertEqual(check_value, False)


