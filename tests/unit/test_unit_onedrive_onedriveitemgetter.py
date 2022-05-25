import unittest, mock

from onedrive_offsite.onedrive import OneDriveItemGetter

#### ------------------ OneDriveItemGetter --------------------------
@mock.patch("onedrive_offsite.onedrive.threading.current_thread")
class TestOneDriveItemGetter(unittest.TestCase):

    #### ------------------ OneDriveItemGetter._get_dir_details() --------------------------
    @mock.patch("onedrive_offsite.onedrive.Config")
    def test_unit_get_dir_details_get_except(self, mock_curr_thread, mock_config):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"

        with mock.patch("onedrive_offsite.onedrive.requests.get", side_effect=Exception("fake exception")) as mock_get:
            access_token = "fakeaccesstoken"
            dir_name = "fake_dir_name"
            
            odig = OneDriveItemGetter(access_token, dir_name)
            check_val = odig._get_dir_details()
            self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.onedrive.Config")
    def test_unit_get_dir_details_get_404(self, mock_curr_thread, mock_config):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"

        with mock.patch("onedrive_offsite.onedrive.requests.get") as mock_get:
            mock_resp = mock.Mock()
            mock_resp.status_code = 404
            mock_resp.content = b'some fake content'
            mock_get.return_value = mock_resp
            access_token = "fakeaccesstoken"
            dir_name = "fake_dir_name"
            
            odig = OneDriveItemGetter(access_token, dir_name)
            check_val = odig._get_dir_details()
            self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.onedrive.Config")
    def test_unit_get_dir_details_json_except(self, mock_curr_thread, mock_config):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"

        with mock.patch("onedrive_offsite.onedrive.requests.get") as mock_get:
            mock_resp = mock.Mock()
            mock_resp.status_code = 200
            mock_resp.content = b'some fake content'
            mock_resp.json.side_effect = Exception("fake exception")
            mock_get.return_value = mock_resp
            access_token = "fakeaccesstoken"
            dir_name = "fake_dir_name"
            
            odig = OneDriveItemGetter(access_token, dir_name)
            check_val = odig._get_dir_details()
            self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.onedrive.Config")
    def test_unit_get_dir_details_everything_works(self, mock_curr_thread, mock_config):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"

        with mock.patch("onedrive_offsite.onedrive.requests.get") as mock_get:
            mock_resp = mock.Mock()
            mock_resp.status_code = 200
            mock_resp.content = b'some fake content'
            mock_resp.json.return_value = {"id":"fake-id"}
            mock_get.return_value = mock_resp
            access_token = "fakeaccesstoken"
            dir_name = "fake_dir_name"
            
            odig = OneDriveItemGetter(access_token, dir_name)
            check_val = odig._get_dir_details()
            self.assertIs(check_val, "fake-id")


    #### ------------------ OneDriveItemGetter._process_json() --------------------------

    def test_unit_process_json_missing_value_key(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"

        access_token = "fakeaccesstoken"
        dir_name = "fake_dir_name"        
        odig = OneDriveItemGetter(access_token, dir_name)
        check_val = odig._process_json({"fake-key":"fake-value"})
        self.assertIs(check_val, None)

    def test_unit_process_json_missing_id_key(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"

        access_token = "fakeaccesstoken"
        dir_name = "fake_dir_name"        
        odig = OneDriveItemGetter(access_token, dir_name)
        check_val = odig._process_json({"value":[{"no-id": "no-value"}]})
        self.assertIs(check_val, None)
        
    def test_unit_process_json_missing_name_key(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"

        access_token = "fakeaccesstoken"
        dir_name = "fake_dir_name"        
        odig = OneDriveItemGetter(access_token, dir_name)
        check_val = odig._process_json({"value":[{"id": "id1", "no-name": "no-name-value"}]})
        self.assertIs(check_val, None)

    def test_unit_process_json_works_two_items(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"

        access_token = "fakeaccesstoken"
        dir_name = "fake_dir_name"        
        odig = OneDriveItemGetter(access_token, dir_name)
        check_val = odig._process_json({"value":[{"id": "id-1", "name": "name-1"}, {"id": "id-2", "name": "name-2"}]})
        self.assertEqual(check_val, [{"id": "id-1", "name": "name-1"}, {"id": "id-2", "name": "name-2"}])


    #### ------------------ OneDriveItemGetter._get_dir_items() --------------------------
    @mock.patch("onedrive_offsite.onedrive.Config")
    def test_unit_get_dir_items_no_dir_item(self, mock_curr_thread, mock_config):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.OneDriveItemGetter._get_dir_details", return_value = None) as mock_get_dir_details:
            access_token = "fakeaccesstoken"
            dir_name = "fake_dir_name"        
            odig = OneDriveItemGetter(access_token, dir_name)
            
            check_val = odig.get_dir_items()
            self.assertIs(check_val, None)
    
    @mock.patch("onedrive_offsite.onedrive.Config")
    def test_unit_get_dir_items_get_except(self, mock_curr_thread, mock_config):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.OneDriveItemGetter._get_dir_details", return_value = "D23D09990A1D5FC9!169") as mock_get_dir_details:
            with mock.patch("onedrive_offsite.onedrive.requests.get", side_effect=Exception("fake exception")) as mock_get:

                access_token = "fakeaccesstoken"
                dir_name = "fake_dir_name"        
                odig = OneDriveItemGetter(access_token, dir_name)
                
                check_val = odig.get_dir_items()
                self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.onedrive.Config")
    def test_unit_get_dir_items_get_resp_json_Except(self, mock_curr_thread, mock_config):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.OneDriveItemGetter._get_dir_details", return_value = "D23D09990A1D5FC9!169") as mock_get_dir_details:
            with mock.patch("onedrive_offsite.onedrive.requests.get") as mock_get:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.side_effect = Exception("fake exception")

                access_token = "fakeaccesstoken"
                dir_name = "fake_dir_name"        
                odig = OneDriveItemGetter(access_token, dir_name)
                
                check_val = odig.get_dir_items()
                self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.onedrive.Config")
    def test_unit_get_dir_items_get_proc_json_none(self, mock_curr_thread, mock_config):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.OneDriveItemGetter._get_dir_details", return_value = "D23D09990A1D5FC9!169") as mock_get_dir_details:
            with mock.patch("onedrive_offsite.onedrive.requests.get") as mock_get:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = {"value":[{"id": "id-1", "name": "name-1"}, {"id": "id-2", "name": "name-2"}]}
                with mock.patch("onedrive_offsite.onedrive.OneDriveItemGetter._process_json", return_value=None) as mock_proc_json:

                    access_token = "fakeaccesstoken"
                    dir_name = "fake_dir_name"        
                    odig = OneDriveItemGetter(access_token, dir_name)
                    
                    check_val = odig.get_dir_items()
                    self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.onedrive.Config")
    def test_unit_get_dir_items_get_status_401(self, mock_curr_thread, mock_config):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.OneDriveItemGetter._get_dir_details", return_value = "D23D09990A1D5FC9!169") as mock_get_dir_details:
            with mock.patch("onedrive_offsite.onedrive.requests.get") as mock_get:
                mock_get.return_value.status_code = 401

                access_token = "fakeaccesstoken"
                dir_name = "fake_dir_name"        
                odig = OneDriveItemGetter(access_token, dir_name)
                
                check_val = odig.get_dir_items()
                self.assertIs(check_val, None)