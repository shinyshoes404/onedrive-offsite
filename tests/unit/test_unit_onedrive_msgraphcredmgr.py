import unittest, mock, requests

from onedrive_offsite.onedrive import MSGraphCredMgr

@mock.patch("onedrive_offsite.onedrive.threading.current_thread")
class TestMSGraphCredMgr(unittest.TestCase):

#### ------------ OneDriveLargeUpload.read_tokens() -------------------------
    def test_unit_read_tokens_success(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        test_json = {"access_token":"fake-access-token", "refresh_token":"fake-refresh-token", "expires":"2022-01-23 14:25:37"}
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            with mock.patch("onedrive_offsite.onedrive.json") as mock_json:
                mock_json.load.return_value = test_json
                msgcm = MSGraphCredMgr()
                check_value = msgcm.read_tokens()
                self.assertEqual(check_value, True)

    def test_unit_read_tokens_exeption(self,mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            with mock.patch("onedrive_offsite.onedrive.json") as mock_json:
                mock_json.load.side_effect = Exception("fake exception")
                msgcm = MSGraphCredMgr("/fake/path/to/oauth2_file", "fake/path/to/app_file")
                check_value = msgcm.read_tokens()
                self.assertEqual(check_value, False)

#### ------------ OneDriveLargeUpload.refresh_tokens() -------------------------
    def test_unit_refresh_tokens_read_success_refresh_success(self,mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        test_json = {"client_id":"fake-client-id", "client_secret":"fake-client-secret", "redirect_uri":"http://localhost:8080"}
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            with mock.patch("onedrive_offsite.onedrive.json") as mock_json:
                mock_json.load.return_value = test_json
                with mock.patch("onedrive_offsite.onedrive.requests.post") as mock_post:
                    mock_post.return_value.status_code = 200
                    mock_post.return_value.json.return_value = {"access_token":"fake-access-token2", "refresh_token":"fake-refresh-token2", "expires_in":3600}
                    msgcm = MSGraphCredMgr()
                    msgcm.refresh_token = "fake-refresh-token1"
                    msgcm.access_token = "fake-access-token1"
                    check_value = msgcm.refresh_tokens()
                    self.assertEqual(check_value, True)
    
    def test_unit_refresh_tokens_read_exception(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            with mock.patch("onedrive_offsite.onedrive.json") as mock_json:
                    mock_json.load.side_effect = Exception("fake exception")
                    msgcm = MSGraphCredMgr()
                    msgcm.refresh_token = "fake-refresh-token1"
                    msgcm.access_token = "fake-access-token1"
                    check_value = msgcm.refresh_tokens()
                    self.assertEqual(check_value, False)
                    
    def test_unit_refresh_tokens_read_success_requests_exception(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        test_json = {"client_id":"fake-client-id", "client_secret":"fake-client-secret", "redirect_uri":"http://localhost:8080"}
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            with mock.patch("onedrive_offsite.onedrive.json") as mock_json:
                mock_json.load.return_value = test_json
                with mock.patch("onedrive_offsite.onedrive.requests.post") as mock_post:
                    mock_post.side_effect = requests.exceptions.Timeout
                    msgcm = MSGraphCredMgr()
                    msgcm.refresh_token = "fake-refresh-token1"
                    msgcm.access_token = "fake-access-token1"
                    check_value = msgcm.refresh_tokens()
                    self.assertEqual(check_value, False)

    def test_unit_refresh_tokens_read_success_refresh_success_write_exception(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        test_json = {"client_id":"fake-client-id", "client_secret":"fake-client-secret", "redirect_uri":"http://localhost:8080"}
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            with mock.patch("onedrive_offsite.onedrive.json") as mock_json:
                mock_json.load.return_value = test_json
                mock_json.dump.side_effect = Exception("fake exception")
                with mock.patch("onedrive_offsite.onedrive.requests.post") as mock_post:
                    mock_post.return_value.status_code = 200
                    mock_post.return_value.json.return_value = {"access_token":"fake-access-token2", "refresh_token":"fake-refresh-token2"}
                    msgcm = MSGraphCredMgr()
                    msgcm.refresh_token = "fake-refresh-token1"
                    msgcm.access_token = "fake-access-token1"
                    check_value = msgcm.refresh_tokens()
                    self.assertEqual(check_value, False)

    def test_unit_refresh_tokens_read_success_refresh_5xxn(self, mock_thread_getname):
        mock_thread_getname.return_value.getName.return_value = "fake-thread"
        test_json = {"client_id":"fake-client-id", "client_secret":"fake-client-secret", "redirect_uri":"http://localhost:8080"}
        with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
            with mock.patch("onedrive_offsite.onedrive.json") as mock_json:
                mock_json.load.return_value = test_json
                with mock.patch("onedrive_offsite.onedrive.requests.post") as mock_post:
                    mock_post.return_value.status_code = 500
                    msgcm = MSGraphCredMgr()
                    msgcm.refresh_token = "fake-refresh-token1"
                    msgcm.access_token = "fake-access-token1"
                    check_value = msgcm.refresh_tokens()
                    self.assertEqual(check_value, False)
