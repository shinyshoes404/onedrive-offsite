import unittest, mock

from onedrive_offsite.onedrive import OneDriveGetItemDetails

#### ------------------ OneDriveGetItemDetails --------------------------
@mock.patch("onedrive_offsite.onedrive.threading.current_thread")
class TestOneDriveGetItemDetails(unittest.TestCase):

    #### ------------------ OneDriveGetItemDetails.get_details() --------------------------
    @mock.patch("onedrive_offsite.onedrive.Config")
    def test_unit_get_details_get_except(self, mock_curr_thread, mock_config):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.requests.get", side_effect=Exception("fake exception")) as mock_get:
            access_token = "fakeaccesstoken"
            item_id = "fake-item-id"            
            check_val = OneDriveGetItemDetails.get_details(item_id,access_token)
            self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.onedrive.Config")
    def test_unit_get_details_get_401(self, mock_curr_thread, mock_config):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.requests.get") as mock_get:
            mock_get.return_value.status_code = 401
            access_token = "fakeaccesstoken"
            item_id = "fake-item-id"            
            check_val = OneDriveGetItemDetails.get_details(item_id,access_token)
            self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.onedrive.Config")
    def test_unit_get_details_get_resp_json_except(self, mock_curr_thread, mock_config):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.side_effect = Exception("fake exception")
            access_token = "fakeaccesstoken"
            item_id = "fake-item-id"            
            check_val = OneDriveGetItemDetails.get_details(item_id,access_token)
            self.assertIs(check_val, None)
  
    @mock.patch("onedrive_offsite.onedrive.Config")
    def test_unit_get_details_no_download_url(self, mock_curr_thread, mock_config):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"error":"err msg"}
            access_token = "fakeaccesstoken"
            item_id = "fake-item-id"            
            check_val = OneDriveGetItemDetails.get_details(item_id,access_token)
            self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.onedrive.Config")
    def test_unit_get_details_no_size(self, mock_curr_thread, mock_config):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"@microsoft.graph.downloadUrl":"fake-url"}
            access_token = "fakeaccesstoken"
            item_id = "fake-item-id"            
            check_val = OneDriveGetItemDetails.get_details(item_id,access_token)
            self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.onedrive.Config")
    def test_unit_get_details_no_file(self, mock_curr_thread, mock_config):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"@microsoft.graph.downloadUrl":"fake-url", "size":10}
            access_token = "fakeaccesstoken"
            item_id = "fake-item-id"            
            check_val = OneDriveGetItemDetails.get_details(item_id,access_token)
            self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.onedrive.Config")
    def test_unit_get_details_no_hashes(self, mock_curr_thread, mock_config):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"@microsoft.graph.downloadUrl":"fake-url", "size":10, "file": {"fake":"fake"}}
            access_token = "fakeaccesstoken"
            item_id = "fake-item-id"            
            check_val = OneDriveGetItemDetails.get_details(item_id,access_token)
            self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.onedrive.Config")
    def test_unit_get_details_no_sha256(self, mock_curr_thread, mock_config):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"@microsoft.graph.downloadUrl":"fake-url", "size":10, "file": {"hashes":{"fake": "fake"}}}
            access_token = "fakeaccesstoken"
            item_id = "fake-item-id"            
            check_val = OneDriveGetItemDetails.get_details(item_id,access_token)
            self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.onedrive.Config")
    def test_unit_get_details_no_has_everything(self, mock_curr_thread, mock_config):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"@microsoft.graph.downloadUrl":"fake-url", "size":10, "file": {"hashes":{"sha256Hash": "0123456789abcdef"}}}
            access_token = "fakeaccesstoken"
            item_id = "fake-item-id"            
            check_val = OneDriveGetItemDetails.get_details(item_id,access_token)
            self.assertEqual(check_val, {"download_url": "fake-url", "size_bytes": 10, "sha256hash": "0123456789abcdef"} )