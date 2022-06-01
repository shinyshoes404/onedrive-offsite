import unittest, mock, os, shutil, json

from onedrive_offsite.onedrive import OneDriveDirMgr


### -------------------------- OneDriveDirMgr.__init__() ----------------------------
@mock.patch("onedrive_offsite.onedrive.threading.current_thread")
class TestOneDriveDirMgr_init(unittest.TestCase):

    def test_unit_onedrivedirmgr_init_read_info_none(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.read_backup_file_info", return_value = None) as mock_read_info:
            oddm = OneDriveDirMgr("fakeaccesstoken")
            self.assertEqual(oddm.dir_name, None)

    def test_unit_onedrivedirmgr_init_dir_name_missing(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.read_backup_file_info") as mock_read_info:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                            "start-date-time": "2022-04-14-21:37:09",
                            "size-bytes": 170403564,                        
                            "onedrive-filename": "backup_test_local.tar.gz",
                            "done-date-time": "2022-04-14-21:37:15"}
            mock_read_info.return_value = test_info_json
            oddm = OneDriveDirMgr("fakeaccesstoken")
            self.assertEqual(oddm.dir_name, None)

    def test_unit_onedrivedirmgr_init_dir_name_present(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.read_backup_file_info") as mock_read_info:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                            "start-date-time": "2022-04-14-21:37:09",
                            "size-bytes": 170403564, 
                            "onedrive-dir": "backup_test_2",                       
                            "onedrive-filename": "backup_test_local.tar.gz",
                            "done-date-time": "2022-04-14-21:37:15"}
            mock_read_info.return_value = test_info_json
            oddm = OneDriveDirMgr("fakeaccesstoken")
            self.assertEqual(oddm.dir_name, "backup_test_2")


### -------------------------- OneDriveDirMgr._write_dir_id() ------------------------
class TestOneDriveDirMgr__write_dir_id(unittest.TestCase):
    ### ------------ fixtures ----------------
    test_dir = os.path.abspath(os.path.dirname(__file__))
    test_json_dir = os.path.join(test_dir,"./test_json_info_files")
    test_json_file = os.path.join(test_json_dir, "./test_backup_file_info.json")

    def setUp(self):        
        os.mkdir(TestOneDriveDirMgr__write_dir_id.test_json_dir)
        with open(TestOneDriveDirMgr__write_dir_id.test_json_file, "w") as test_json_file:
            test_info_json = {"backup-file-path": "/home/user/backup_file.tar",
                "start-date-time": "2022-04-14-21:37:09",
                "size-bytes": 170403564, 
                "onedrive-dir": "backup_test_2",                       
                "onedrive-filename": "backup_test_local.tar.gz",
                "done-date-time": "2022-04-14-21:37:15"}
            json.dump(test_info_json, test_json_file)
    
    def tearDown(self):
        shutil.rmtree(TestOneDriveDirMgr__write_dir_id.test_json_dir)

    
    ### ---------------- test cases ----------------------
    def test_unit_write_dir_id_except(self):
        with mock.patch("onedrive_offsite.onedrive.threading.current_thread") as mock_thread_getname:
            mock_thread_getname.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.onedrive.Config") as mock_config_info:
                mock_config_info.backup_file_info_path = TestOneDriveDirMgr__write_dir_id.test_json_file
                with mock.patch("onedrive_offsite.onedrive.OneDriveDirMgr.__init__", return_value=None) as mock_init:
                    with mock.patch("onedrive_offsite.onedrive.json.load", side_effect=Exception("fake exception")) as mock_json_load:
                        oddm = OneDriveDirMgr("fakeaccesstoken")
                        check_value = oddm._write_dir_id("fake-id")
                        self.assertEqual(check_value, False)

    def test_unit_write_dir_id_successful_write(self):
        with mock.patch("onedrive_offsite.onedrive.threading.current_thread") as mock_thread_getname:
            mock_thread_getname.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.onedrive.Config") as mock_config_info:
                mock_config_info.backup_file_info_path = TestOneDriveDirMgr__write_dir_id.test_json_file
                with mock.patch("onedrive_offsite.onedrive.OneDriveDirMgr.__init__", return_value=None) as mock_init:
                    oddm = OneDriveDirMgr("fakeaccesstoken")
                    oddm.dir_name = "backup_test_2"
                    check_value = oddm._write_dir_id("fake-id")

                    # make sure the json file has been written to
                    with open(TestOneDriveDirMgr__write_dir_id.test_json_file, "r") as test_json_file:
                        test_json = json.load(test_json_file)

                    self.assertEqual(check_value, True)
                    self.assertEqual(test_json.get("onedrive-dir-id"), "fake-id") 



### -------------------------- OneDriveDirMgr._check_dir_exits() ----------------------------
@mock.patch("onedrive_offsite.onedrive.threading.current_thread")
class TestOneDriveDirMgr_check_dir_exits(unittest.TestCase):

    def test_unit_onedrivedirmgr_check_dir_exists_except(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            with mock.patch("onedrive_offsite.onedrive.OneDriveDirMgr.__init__", return_value=None) as mock_init:           
                with mock.patch("onedrive_offsite.onedrive.requests.get", side_effect=Exception("fake exception")) as mock_get:
                    oddm = OneDriveDirMgr("fakeaccesstoken")
                    # manually setting this since we mocked __init__()
                    oddm.dir_name = "backup_test_2"
                    check_value = oddm._check_dir_exists()
                    self.assertEqual(check_value, "error - exception")

    def test_unit_onedrivedirmgr_check_dir_exists_unknown_error(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            with mock.patch("onedrive_offsite.onedrive.OneDriveDirMgr.__init__", return_value=None) as mock_init: 
                with mock.patch("onedrive_offsite.onedrive.requests.get") as mock_get: # will create an unaccounted for error
                    oddm = OneDriveDirMgr("fakeaccesstoken")
                    # manually setting these since we mocked __init__()
                    oddm.dir_name = "backup_test_2"
                    oddm.api_url = "https://fakeurl"
                    oddm.headers = {"fakeheader":"fake header value"}

                    check_value = oddm._check_dir_exists()
                    self.assertEqual(check_value, "error - unknown")

    def test_unit_onedrivedirmgr_check_dir_exists_does_not_exist(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            with mock.patch("onedrive_offsite.onedrive.OneDriveDirMgr.__init__", return_value=None) as mock_init: 
                with mock.patch("onedrive_offsite.onedrive.requests.get") as mock_get: 
                    mock_get.return_value.status_code = 404
                    oddm = OneDriveDirMgr("fakeaccesstoken")
                    # manually setting these since we mocked __init__()
                    oddm.dir_name = "backup_test_2"
                    oddm.api_url = "https://fakeurl"
                    oddm.headers = {"fakeheader":"fake header value"}

                    check_value = oddm._check_dir_exists()
                    self.assertEqual(check_value, False)

    def test_unit_onedrivedirmgr_check_dir_exists_does_exist_successful_write(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            with mock.patch("onedrive_offsite.onedrive.OneDriveDirMgr.__init__", return_value=None) as mock_init: 
                with mock.patch("onedrive_offsite.onedrive.requests.get") as mock_get:
                    mock_get.return_value.status_code = 200
                    mock_get.return_value.json.return_value = {
                            "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#users('test%40hotmail.com')/drive/items/$entity",
                            "createdDateTime": "2022-04-14T01:53:43.093Z",
                            "cTag": "adDpEMjNEMDk5OTBBMUQ1RkM5ITE1Ny42Mzc4NTUwNjAzODkwNzAwMDA",
                            "eTag": "aRDIzRDA5OTkwQTFENUZDOSExNTcuMA",
                            "id": "D23D09990A1D5FC9!157"}                    
                    
                    with mock.patch(__name__ + ".OneDriveDirMgr._write_dir_id", return_value = True) as mock_write:
                        oddm = OneDriveDirMgr("fakeaccesstoken")
                        # manually setting these since we mocked __init__()
                        oddm.dir_name = "backup_test_2"
                        oddm.api_url = "https://fakeurl"
                        oddm.headers = {"fakeheader":"fake header value"}

                        check_value = oddm._check_dir_exists()
                        self.assertEqual(check_value, True)


    def test_unit_onedrivedirmgr_check_dir_exists_does_exist_fail_write(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            with mock.patch("onedrive_offsite.onedrive.OneDriveDirMgr.__init__", return_value=None) as mock_init: 
                with mock.patch("onedrive_offsite.onedrive.requests.get") as mock_get: # will create an unaccounted for error
                    mock_get.return_value.status_code = 200
                    mock_get.return_value.json.return_value = {
                            "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#users('test%40hotmail.com')/drive/items/$entity",
                            "createdDateTime": "2022-04-14T01:53:43.093Z",
                            "cTag": "adDpEMjNEMDk5OTBBMUQ1RkM5ITE1Ny42Mzc4NTUwNjAzODkwNzAwMDA",
                            "eTag": "aRDIzRDA5OTkwQTFENUZDOSExNTcuMA",
                            "id": "D23D09990A1D5FC9!157"}                    
                    
                    with mock.patch(__name__ + ".OneDriveDirMgr._write_dir_id", return_value = False) as mock_write:
                        oddm = OneDriveDirMgr("fakeaccesstoken")
                        # manually setting these since we mocked __init__()
                        oddm.dir_name = "backup_test_2"
                        oddm.api_url = "https://fakeurl"
                        oddm.headers = {"fakeheader":"fake header value"}

                        check_value = oddm._check_dir_exists()
                        self.assertEqual(check_value, "error - write")


### -------------------------- OneDriveDirMgr._create_onedrive_dir() ------------------------
class TestOneDriveDirMgr__create_onedrive_dir(unittest.TestCase):

    def test_unit_create_onedrive_dir_post_exception(self):
        with mock.patch("onedrive_offsite.onedrive.threading.current_thread") as mock_thread_getname:
            mock_thread_getname.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.onedrive.OneDriveDirMgr.__init__", return_value=None) as mock_init: 
                with mock.patch("onedrive_offsite.onedrive.requests.post", side_effect=Exception("fake exception")) as mock_post:
                        oddm = OneDriveDirMgr("fakeaccesstoken")
                        # manually setting these since we mocked __init__()
                        oddm.dir_name = "backup_test_2"
                        oddm.api_url = "https://fakeurl"
                        oddm.headers = {"fakeheader":"fake header value"}

                        check_value = oddm._create_onedrive_dir()
                        self.assertEqual(check_value, None)

    def test_unit_create_onedrive_dir_error_status_code(self):
        with mock.patch("onedrive_offsite.onedrive.threading.current_thread") as mock_thread_getname:
            mock_thread_getname.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.onedrive.OneDriveDirMgr.__init__", return_value=None) as mock_init: 
                with mock.patch("onedrive_offsite.onedrive.requests.post") as mock_post:
                        mock_post.return_value.status_code = 500
                        mock_post.return_value.content = {"err":"fake error msg"}
                        oddm = OneDriveDirMgr("fakeaccesstoken")
                        # manually setting these since we mocked __init__()
                        oddm.dir_name = "backup_test_2"
                        oddm.api_url = "https://fakeurl"
                        oddm.headers = {"fakeheader":"fake header value"}

                        check_value = oddm._create_onedrive_dir()
                        self.assertEqual(check_value, False)

    def test_unit_create_onedrive_dir_create_id_write_fail(self):
        with mock.patch("onedrive_offsite.onedrive.threading.current_thread") as mock_thread_getname:
            mock_thread_getname.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.onedrive.OneDriveDirMgr.__init__", return_value=None) as mock_init: 
                with mock.patch(__name__ + ".OneDriveDirMgr._write_dir_id", return_value = False) as mock_write:
                    with mock.patch("onedrive_offsite.onedrive.requests.post") as mock_post:
                            mock_post.return_value.status_code = 201
                            mock_post.return_value.json.return_value = {
                                "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#users('test%40hotmail.com')/drive/items/$entity",
                                "createdDateTime": "2022-04-14T01:53:43.093Z",
                                "cTag": "adDpEMjNEMDk5OTBBMUQ1RkM5ITE1Ny42Mzc4NTUwNjAzODkwNzAwMDA",
                                "eTag": "aRDIzRDA5OTkwQTFENUZDOSExNTcuMA",
                                "id": "D23D09990A1D5FC9!157"}     

                            oddm = OneDriveDirMgr("fakeaccesstoken")
                            # manually setting these since we mocked __init__()
                            oddm.dir_name = "backup_test_2"
                            oddm.api_url = "https://fakeurl"
                            oddm.headers = {"fakeheader":"fake header value"}

                            check_value = oddm._create_onedrive_dir()
                            self.assertEqual(check_value, None)

    def test_unit_create_onedrive_dir_create_id_write_success(self):
        with mock.patch("onedrive_offsite.onedrive.threading.current_thread") as mock_thread_getname:
            mock_thread_getname.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.onedrive.OneDriveDirMgr.__init__", return_value=None) as mock_init: 
                with mock.patch(__name__ + ".OneDriveDirMgr._write_dir_id", return_value = True) as mock_write:
                    with mock.patch("onedrive_offsite.onedrive.requests.post") as mock_post:
                            mock_post.return_value.status_code = 201
                            mock_post.return_value.json.return_value = {
                                "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#users('test%40hotmail.com')/drive/items/$entity",
                                "createdDateTime": "2022-04-14T01:53:43.093Z",
                                "cTag": "adDpEMjNEMDk5OTBBMUQ1RkM5ITE1Ny42Mzc4NTUwNjAzODkwNzAwMDA",
                                "eTag": "aRDIzRDA5OTkwQTFENUZDOSExNTcuMA",
                                "id": "D23D09990A1D5FC9!157"}     
                                
                            oddm = OneDriveDirMgr("fakeaccesstoken")
                            # manually setting these since we mocked __init__()
                            oddm.dir_name = "backup_test_2"
                            oddm.api_url = "https://fakeurl"
                            oddm.headers = {"fakeheader":"fake header value"}

                            check_value = oddm._create_onedrive_dir()
                            self.assertEqual(check_value, True)


### -------------------------- OneDriveDirMgr.create_dir() ------------------------
class TestOneDriveDirMgr_create_dir(unittest.TestCase):

    def test_create_dir_cannot_check_dir_status(self):
        with mock.patch("onedrive_offsite.onedrive.threading.current_thread") as mock_thread_getname:
            mock_thread_getname.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.onedrive.sleep", return_value = None) as mock_sleep:
                with mock.patch("onedrive_offsite.onedrive.OneDriveDirMgr.__init__", return_value=None) as mock_init: 
                    with mock.patch(__name__ + ".OneDriveDirMgr._check_dir_exists", return_value = None) as mock_write:
                        oddm = OneDriveDirMgr("fakeaccesstoken")
                        check_value = oddm.create_dir()
                        
                        self.assertEqual(check_value, None)

    def test_create_dir_need_to_create_dir_fail_to_create(self):
        with mock.patch("onedrive_offsite.onedrive.threading.current_thread") as mock_thread_getname:
            mock_thread_getname.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.onedrive.sleep", return_value = None) as mock_sleep:
                with mock.patch("onedrive_offsite.onedrive.OneDriveDirMgr.__init__", return_value=None) as mock_init: 
                    with mock.patch(__name__ + ".OneDriveDirMgr._check_dir_exists", return_value = False) as mock_write:
                        with mock.patch(__name__ + ".OneDriveDirMgr._create_onedrive_dir", return_value = None) as mock_create:
                            oddm = OneDriveDirMgr("fakeaccesstoken")
                            # manually setting this since we mocked __init__()
                            oddm.dir_name = "backup_test_2"
                            check_value = oddm.create_dir()
                            
                            self.assertEqual(check_value, None)

    def test_create_dir_need_to_create_dir_create_succeeds(self):
        with mock.patch("onedrive_offsite.onedrive.threading.current_thread") as mock_thread_getname:
            mock_thread_getname.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.onedrive.sleep", return_value = None) as mock_sleep:
                with mock.patch("onedrive_offsite.onedrive.OneDriveDirMgr.__init__", return_value=None) as mock_init: 
                    with mock.patch(__name__ + ".OneDriveDirMgr._check_dir_exists", return_value = False) as mock_write:
                        with mock.patch(__name__ + ".OneDriveDirMgr._create_onedrive_dir", return_value = True) as mock_create:
                            oddm = OneDriveDirMgr("fakeaccesstoken")
                            # manually setting this since we mocked __init__()
                            oddm.dir_name = "backup_test_2"
                            check_value = oddm.create_dir()
                            
                            self.assertEqual(check_value, True)