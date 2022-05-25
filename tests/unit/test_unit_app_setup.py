import unittest, mock, os, json

from onedrive_offsite.app_setup import signin, app_info_setup, create_key


class Testsignin(unittest.TestCase):
    test_dir = os.path.abspath(os.path.dirname(__file__))

    test_app_json_path = os.path.join(test_dir, "test_app.json")
    app_json = {"signin_url":"fakesigninurl", "client_id":"fakeclientid","client_secret":"fakeclientsecret","redirect_uri":"fakeredirecturi"}
    test_oauth_json_path = os.path.join(test_dir, "test_oauth.json")

    def setUp(self):
        with open(Testsignin.test_app_json_path, "w") as app_json_file:
            json.dump(Testsignin.app_json, app_json_file)

    def tearDown(self):
        if os.path.isfile(Testsignin.test_app_json_path):
            os.remove(Testsignin.test_app_json_path)
        if os.path.isfile(Testsignin.test_oauth_json_path):
            os.remove(Testsignin.test_oauth_json_path)

    def test_unit_signin_successful_signin(self):
        with mock.patch("onedrive_offsite.app_setup.Config") as mock_config:
            mock_config.app_json_path = Testsignin.test_app_json_path
            mock_config.oauth2_json_path = Testsignin.test_oauth_json_path
            mock_config.api_timeout = (5,60)
            with mock.patch("onedrive_offsite.app_setup.input", return_value="fakecode") as mock_input:
                with mock.patch("onedrive_offsite.app_setup.requests.post") as mock_post:
                    with mock.patch("onedrive_offsite.app_setup.requests.get") as mock_get:
                        mock_post.return_value.status_code = 200
                        mock_post.return_value.json.return_value = {"access_token":"fakeaccesstoken", "refresh_token":"fakerefreshtoken", "expires_in": 3600}

                        mock_get.return_value.status_code = 200
                        check_value1 = signin()
                        check_value2 = os.path.isfile(Testsignin.test_oauth_json_path)
                        self.assertEqual(check_value1, True)
                        self.assertEqual(check_value2, True)

    def test_unit_signin_no_app_file(self):
        with mock.patch("onedrive_offsite.app_setup.Config") as mock_config:
            mock_config.app_json_path = Testsignin.test_app_json_path
            mock_config.oauth2_json_path = Testsignin.test_oauth_json_path
            os.remove(Testsignin.test_app_json_path) # intentionally remove the file created in setUp()
            check_value1 = signin()
            check_value2 = os.path.isfile(Testsignin.test_oauth_json_path)
            self.assertEqual(check_value1, False)
            self.assertEqual(check_value2, False)

    def test_unit_signin_error_status_code(self):
        with mock.patch("onedrive_offsite.app_setup.Config") as mock_config:
            mock_config.app_json_path = Testsignin.test_app_json_path
            mock_config.oauth2_json_path = Testsignin.test_oauth_json_path
            with mock.patch("onedrive_offsite.app_setup.input", return_value="fakecode") as mock_input:
                with mock.patch("onedrive_offsite.app_setup.requests.post") as mock_post:
                    mock_post.return_value.status_code = 500
                    mock_post.return_value.json.return_value = {"error":"fake error"}
                    check_value1 = signin()
                    check_value2 = os.path.isfile(Testsignin.test_oauth_json_path)
                    self.assertEqual(check_value1, False)
                    self.assertEqual(check_value2, False)


class Testappinfosetup(unittest.TestCase):
    test_dir = os.path.abspath(os.path.dirname(__file__))
    test_app_json_path = os.path.join(test_dir, "test_app.json")

    def tearDown(self):
        if os.path.isfile(Testsignin.test_app_json_path):
            os.remove(Testsignin.test_app_json_path)

    def test_unit_app_info_setup_successful_app_info(self):
        with mock.patch("onedrive_offsite.app_setup.Config") as mock_config:
            mock_config.app_json_path = Testsignin.test_app_json_path
            with mock.patch("onedrive_offsite.app_setup.input", side_effect=["","fake-client-id","fake-client-secret","",""]) as mock_input:
                check_value = app_info_setup()
                self.assertEqual(check_value, True)

    def test_unit_app_info_setup_file_exists(self):
        with mock.patch("onedrive_offsite.app_setup.Config") as mock_config:
            mock_config.app_json_path = Testsignin.test_app_json_path
            with mock.patch("onedrive_offsite.app_setup.input", side_effect=["","fake-client-id","fake-client-secret","",""]) as mock_input:
                app_info_setup()
                check_value = os.path.isfile(Testappinfosetup.test_app_json_path)
                self.assertEqual(check_value, True)

    def test_unit_app_info_setup_verify_client_secret(self):
        with mock.patch("onedrive_offsite.app_setup.Config") as mock_config:
            mock_config.app_json_path = Testsignin.test_app_json_path
            with mock.patch("onedrive_offsite.app_setup.input", side_effect=["","fake-client-id","fake-client-secret","",""]) as mock_input:
                app_info_setup()
                with open(Testappinfosetup.test_app_json_path, "r") as json_file:
                    app_json = json.load(json_file)
                    check_value = app_json.get("client_secret")
                    self.assertEqual(check_value, "fake-client-secret")

    def test_unit_app_info_setup_exit_start(self):
        with mock.patch("onedrive_offsite.app_setup.Config") as mock_config:
            mock_config.app_json_path = Testsignin.test_app_json_path
            with mock.patch("onedrive_offsite.app_setup.input", side_effect=["exit"]) as mock_input:
                check_value = app_info_setup()
                self.assertEqual(check_value, False)

    def test_unit_app_info_setup_exit_client_id(self):
        with mock.patch("onedrive_offsite.app_setup.Config") as mock_config:
            mock_config.app_json_path = Testsignin.test_app_json_path
            with mock.patch("onedrive_offsite.app_setup.input", side_effect=["", "exit"]) as mock_input:
                check_value = app_info_setup()
                self.assertEqual(check_value, False)

    def test_unit_app_info_setup_exit_client_secret(self):
        with mock.patch("onedrive_offsite.app_setup.Config") as mock_config:
            mock_config.app_json_path = Testsignin.test_app_json_path
            with mock.patch("onedrive_offsite.app_setup.input", side_effect=["", "fake-client-id", "exit"]) as mock_input:
                check_value = app_info_setup()
                self.assertEqual(check_value, False)

    def test_unit_app_info_setup_exit_uri(self):
        with mock.patch("onedrive_offsite.app_setup.Config") as mock_config:
            mock_config.app_json_path = Testsignin.test_app_json_path
            with mock.patch("onedrive_offsite.app_setup.input", side_effect=["", "fake-client-id", "fake-client-secret", "exit" ]) as mock_input:
                check_value = app_info_setup()
                self.assertEqual(check_value, False)

    def test_unit_app_info_setup_exit_scopes(self):
        with mock.patch("onedrive_offsite.app_setup.Config") as mock_config:
            mock_config.app_json_path = Testsignin.test_app_json_path
            with mock.patch("onedrive_offsite.app_setup.input", side_effect=["", "fake-client-id", "fake-client-secret", "", "exit" ]) as mock_input:
                check_value = app_info_setup()
                self.assertEqual(check_value, False)

    def test_unit_app_info_setup_except(self):
        with mock.patch("onedrive_offsite.app_setup.Config") as mock_config:
            mock_config.app_json_path = Testsignin.test_app_json_path
            with mock.patch("onedrive_offsite.app_setup.input", side_effect=["", "fake-client-id", "fake-client-secret", "", "" ]) as mock_input:
                with mock.patch("onedrive_offsite.app_setup.open", side_effect=Exception("fake exception")) as mock_open:
                    check_value = app_info_setup()
                    self.assertEqual(check_value, False)


class Testcreatekey(unittest.TestCase):
    test_dir = os.path.abspath(os.path.dirname(__file__))
    test_key_path = os.path.join(test_dir, "fakekey.key")
    test_key_copy_path = os.path.join(test_dir, "fakekey_copy.key")
    key_name = "fakekey"
    key_ext = ".key"

    def setUp(self):
        with open(Testcreatekey.test_key_path, "w") as test_key_file:
            test_key_file.write("fakekeyvalue")

    def tearDown(self):
        if os.path.isfile(Testcreatekey.test_key_path):
            os.remove(Testcreatekey.test_key_path)

        if os.path.isfile(Testcreatekey.test_key_copy_path):
            os.remove(Testcreatekey.test_key_copy_path)

    def test_unit_create_key_no_existing_key_success(self):
        with mock.patch("onedrive_offsite.app_setup.Config") as mock_config:
            mock_config.key_path = Testcreatekey.test_key_path
            with mock.patch("onedrive_offsite.app_setup.os.path.isfile", return_value = False) as mock_isfile:
                with mock.patch("onedrive_offsite.app_setup.Crypt") as mock_crypt:
                    mock_crypt.return_value.gen_key_file.return_value = True
                    check_value = create_key()
                    self.assertEqual(check_value, True)

    def test_unit_create_key_no_existing_key_no_proceed(self):
        with mock.patch("onedrive_offsite.app_setup.Config") as mock_config:
            mock_config.key_path = Testcreatekey.test_key_path
            with mock.patch("onedrive_offsite.app_setup.os.path.isfile", return_value = True) as mock_isfile:
                with mock.patch("onedrive_offsite.app_setup.input", return_value="N") as mock_input:
                    with mock.patch("onedrive_offsite.app_setup.Crypt") as mock_crypt:
                        mock_crypt.return_value.gen_key_file.return_value = True
                        check_value = create_key()
                        self.assertEqual(check_value, False)

    def test_unit_create_key_no_existing_key_yes_proceed(self):
        with mock.patch("onedrive_offsite.app_setup.Config") as mock_config:
            mock_config.key_path = Testcreatekey.test_key_path
            mock_config.key_name = "fakekey"
            mock_config.key_extension = ".key"
            mock_config.etc_basedir = Testcreatekey.test_dir
            with mock.patch("onedrive_offsite.app_setup.os.path.isfile", return_value = True) as mock_isfile:
                with mock.patch("onedrive_offsite.app_setup.input", return_value="Y") as mock_input:
                    with mock.patch("onedrive_offsite.app_setup.datetime.datetime") as mock_datetime:
                        mock_datetime.now.return_value.strftime.return_value = "copy"
                        with mock.patch("onedrive_offsite.app_setup.Crypt") as mock_crypt:
                            mock_crypt.return_value.gen_key_file.return_value = True
                            check_value = create_key()
                            self.assertEqual(check_value, True)

    def test_unit_create_key_no_existing_key_yes_proceed_verify_copy(self):
        with mock.patch("onedrive_offsite.app_setup.Config") as mock_config:
            mock_config.key_path = Testcreatekey.test_key_path
            mock_config.key_name = "fakekey"
            mock_config.key_extension = ".key"
            mock_config.etc_basedir = Testcreatekey.test_dir
            with mock.patch("onedrive_offsite.app_setup.os.path.isfile", return_value = True) as mock_isfile:
                with mock.patch("onedrive_offsite.app_setup.input", return_value="Y") as mock_input:
                    with mock.patch("onedrive_offsite.app_setup.datetime.datetime") as mock_datetime:
                        mock_datetime.now.return_value.strftime.return_value = "copy"
                        with mock.patch("onedrive_offsite.app_setup.Crypt") as mock_crypt:
                            mock_crypt.return_value.gen_key_file.return_value = True
                            create_key()
                            with open(Testcreatekey.test_key_copy_path) as key_copy:
                                check_value = key_copy.read()
                            self.assertEqual(check_value, "fakekeyvalue")

    def test_unit_create_key_no_existing_key_fail(self):
        with mock.patch("onedrive_offsite.app_setup.Config") as mock_config:
            mock_config.key_path = Testcreatekey.test_key_path
            with mock.patch("onedrive_offsite.app_setup.os.path.isfile", return_value = False) as mock_isfile:
                with mock.patch("onedrive_offsite.app_setup.Crypt") as mock_crypt:
                    mock_crypt.return_value.gen_key_file.return_value = False
                    check_value = create_key()
                    self.assertEqual(check_value, False)