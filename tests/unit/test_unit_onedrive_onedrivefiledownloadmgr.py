import unittest, mock

from onedrive_offsite.onedrive import OneDriveFileDownloadMgr

example_resp_header = {'Cache-Control': 'public', 'Content-Length': '10485760', 'Content-Type': 'application/x-gzip', 'Content-Location': 'https://public.dm.files.1drv.com/y4m2q3NLOINxecteYxSP4Kwrs5rNzyLFRTGGHjVWpJwimfGU02ETiSx86H0N2CFcwDy5Y9TJxjoK8oXuLTANVIPPby5b-eBHisKj2WBcIoCWKGt_31ggMhjrnzqTrvuGnl7PjEeWBHbwUm3XBTB8RuNBYmWUOShTIU1bMsLiBRjkUW6GYpKNnlUI1BvcuVoTMjUDhbeyJajA9ZhfGezkCV_7zuXl5Ytf4KyONYpvybW1Fc', 'Content-Range': 'bytes 146800640-157286399/170403564', 'Expires': 'Sat, 23 Jul 2022 14:35:37 GMT', 'Last-Modified': 'Sat, 23 Apr 2022 17:38:26 GMT', 'Accept-Ranges': 'bytes', 'ETag': 'aRDIzRDA5OTkwQTFENUZDOSExNjkuMQ', 'P3P': 'CP="BUS CUR CONo FIN IVDo ONL OUR PHY SAMo TELo"', 'X-MSNSERVER': 'DM5SCH102221802', 'Strict-Transport-Security': 'max-age=31536000; includeSubDomains', 'MS-CV': 'tlIKn5qcHU6yQCgnkrzzjA.0', 'X-SqlDataOrigin': 'S', 'CTag': 'aYzpEMjNEMDk5OTBBMUQ1RkM5ITE2OS4yNTc', 'X-PreAuthInfo': 'rv;poba;', 'Content-Disposition': "attachment; filename*=UTF-8''offsite_backup.tar%20copy.gz", 'X-Content-Type-Options': 'nosniff', 'X-StreamOrigin': 'X', 'X-AsmVersion': 'UNKNOWN; 19.891.405.2005', 'X-Cache': 'CONFIG_NOCACHE', 'X-MSEdge-Ref': 'Ref A: BC860FE2E730462D80932AB1B419D859 Ref B: PDX31EDGE0121 Ref C: 2022-04-24T14:35:37Z', 'Date': 'Sun, 24 Apr 2022 14:35:38 GMT'}

#### ------------ OneDriveFileDownloadMgr._download_chunk() -------------------------
@mock.patch("onedrive_offsite.onedrive.threading.current_thread")
class TestOneDriveFileDownloadMgr_download_chunk(unittest.TestCase):

    def test_unit_download_chunk_request_exception(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"

        with mock.patch("onedrive_offsite.onedrive.requests.get", side_effect=Exception("fake exception")) as mock_get:

            download_url = "https://fakedownloadurl"
            file_size = 12345
            chunk_size = 15
            download_path = "fakefilepath"
            hash = "0123456789ABCDEF"

            oddlm = OneDriveFileDownloadMgr(download_url, file_size, chunk_size, download_path, hash)
            check_val = oddlm._download_chunk(10, 19)

            self.assertIs(check_val, None)

    def test_unit_download_chunk_request_success(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"

        with mock.patch("onedrive_offsite.onedrive.requests.get") as mock_get:

            mock_get.return_value.status_code = 206
            mock_get.return_value.headers = example_resp_header
            mock_get.return_value.content = b'fakebytes'

            download_url = "https://fakedownloadurl"
            file_size = 12345
            chunk_size = 15
            download_path = "fakefilepath"
            hash = "0123456789ABCDEF"

            oddlm = OneDriveFileDownloadMgr(download_url, file_size, chunk_size, download_path, hash)
            check_val = oddlm._download_chunk(10, 19)

            self.assertEqual(check_val, b'fakebytes')

    def test_unit_download_chunk_request_bad_status(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"

        with mock.patch("onedrive_offsite.onedrive.requests.get") as mock_get:

            mock_get.return_value.status_code = 404
            mock_get.return_value.content = b'error info'

            download_url = "https://fakedownloadurl"
            file_size = 12345
            chunk_size = 15
            download_path = "fakefilepath"
            hash = "0123456789ABCDEF"

            oddlm = OneDriveFileDownloadMgr(download_url, file_size, chunk_size, download_path, hash)
            check_val = oddlm._download_chunk(10, 19)

            self.assertIs(check_val, None)


#### ------------ OneDriveFileDownloadMgr._retry_delay() -------------------------
@mock.patch("onedrive_offsite.onedrive.sleep", return_value=None)
@mock.patch("onedrive_offsite.onedrive.threading.current_thread")
class TestOneDriveFileDownloadMgr_retry_delay(unittest.TestCase):

    def test_unit_retry_delay_1(self, mock_curr_thread, mock_sleep):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        download_url = "https://fakedownloadurl"
        file_size = 12345
        chunk_size = 15
        download_path = "fakefilepath"
        hash = "0123456789ABCDEF"

        oddlm = OneDriveFileDownloadMgr(download_url, file_size, chunk_size, download_path, hash)
        check_val = oddlm._retry_delay(1, 10, 19)

        self.assertIs(check_val, True)

    def test_unit_retry_delay_2(self, mock_curr_thread, mock_sleep):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        download_url = "https://fakedownloadurl"
        file_size = 12345
        chunk_size = 15
        download_path = "fakefilepath"
        hash = "0123456789ABCDEF"

        oddlm = OneDriveFileDownloadMgr(download_url, file_size, chunk_size, download_path, hash)
        check_val = oddlm._retry_delay(2, 10, 19)

        self.assertIs(check_val, True)

    def test_unit_retry_delay_3(self, mock_curr_thread, mock_sleep):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        download_url = "https://fakedownloadurl"
        file_size = 12345
        chunk_size = 15
        download_path = "fakefilepath"
        hash = "0123456789ABCDEF"

        oddlm = OneDriveFileDownloadMgr(download_url, file_size, chunk_size, download_path, hash)
        check_val = oddlm._retry_delay(3, 10, 19)

        self.assertIs(check_val, True)

    def test_unit_retry_delay_4(self, mock_curr_thread, mock_sleep):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        download_url = "https://fakedownloadurl"
        file_size = 12345
        chunk_size = 15
        download_path = "fakefilepath"
        hash = "0123456789ABCDEF"

        oddlm = OneDriveFileDownloadMgr(download_url, file_size, chunk_size, download_path, hash)
        check_val = oddlm._retry_delay(4, 10, 19)

        self.assertIs(check_val, False)


#### ------------ OneDriveFileDownloadMgr._download_with_retry() -------------------------
@mock.patch("onedrive_offsite.onedrive.threading.current_thread")
class TestOneDriveFileDownloadMgr_download_with_retry(unittest.TestCase):

    def test_unit_download_with_retry_exceed_retry(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.OneDriveFileDownloadMgr._download_chunk", return_value=None) as mock_down_chunk:
            with mock.patch("onedrive_offsite.onedrive.OneDriveFileDownloadMgr._retry_delay", return_value=False) as mock_retry_delay:
                download_url = "https://fakedownloadurl"
                file_size = 12345
                chunk_size = 15
                download_path = "fakefilepath"
                hash = "0123456789ABCDEF"

                oddlm = OneDriveFileDownloadMgr(download_url, file_size, chunk_size, download_path, hash)
                check_val = oddlm._download_with_retry(10, 19)

                self.assertIs(check_val, False)


    def test_unit_download_with_retry_get_bytes(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.OneDriveFileDownloadMgr._download_chunk", return_value=b'fakebytes') as mock_down_chunk:            
            download_url = "https://fakedownloadurl"
            file_size = 12345
            chunk_size = 15
            download_path = "fakefilepath"
            hash = "0123456789ABCDEF"

            oddlm = OneDriveFileDownloadMgr(download_url, file_size, chunk_size, download_path, hash)
            check_val = oddlm._download_with_retry(10, 19)

            self.assertEqual(check_val, b'fakebytes')

    def test_unit_download_with_retry_runaway_loop(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.OneDriveFileDownloadMgr._download_chunk", return_value=None) as mock_down_chunk:        
            with mock.patch("onedrive_offsite.onedrive.OneDriveFileDownloadMgr._retry_delay", return_value=True) as mock_retry_delay:    
                download_url = "https://fakedownloadurl"
                file_size = 12345
                chunk_size = 15
                download_path = "fakefilepath"
                hash = "0123456789ABCDEF"

                oddlm = OneDriveFileDownloadMgr(download_url, file_size, chunk_size, download_path, hash)
                check_val = oddlm._download_with_retry(10, 19)

                self.assertIs(check_val, None)


#### ------------ OneDriveFileDownloadMgr._verify_download() -------------------------
@mock.patch("onedrive_offsite.onedrive.threading.current_thread")
class TestOneDriveFileDownloadMgr_verify_download(unittest.TestCase):

    def test_unit_verify_download_no_size_match(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.os.path.getsize", return_value=12344) as mock_getsize:
                download_url = "https://fakedownloadurl"
                file_size = 12345
                chunk_size = 15
                download_path = "fakefilepath"
                hash = "0123456789ABCDEF"

                oddlm = OneDriveFileDownloadMgr(download_url, file_size, chunk_size, download_path, hash)
                check_val = oddlm._verify_download()

                self.assertIs(check_val, False)

    def test_unit_verify_download_size_match_shacalc_fail(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.os.path.getsize", return_value=12345) as mock_getsize:
            with mock.patch("onedrive_offsite.onedrive.Sha256Calc") as mock_shacalc:
                mock_shacalc.return_value.calc.return_value = None

                download_url = "https://fakedownloadurl"
                file_size = 12345
                chunk_size = 15
                download_path = "fakefilepath"
                hash = "0123456789ABCDEF"

                oddlm = OneDriveFileDownloadMgr(download_url, file_size, chunk_size, download_path, hash)
                check_val = oddlm._verify_download()

                self.assertIs(check_val, False)

    def test_unit_verify_download_size_match_shacalc_match(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.os.path.getsize", return_value=12345) as mock_getsize:
            with mock.patch("onedrive_offsite.onedrive.Sha256Calc") as mock_shacalc:
                mock_shacalc.return_value.calc.return_value = "0123456789abcdef"

                download_url = "https://fakedownloadurl"
                file_size = 12345
                chunk_size = 15
                download_path = "fakefilepath"
                hash = "0123456789ABCDEF"

                oddlm = OneDriveFileDownloadMgr(download_url, file_size, chunk_size, download_path, hash)
                check_val = oddlm._verify_download()

                self.assertIs(check_val, True)



#### ------------ OneDriveFileDownloadMgr.download_file() -------------------------
@mock.patch("onedrive_offsite.onedrive.threading.current_thread")
class TestOneDriveFileDownloadMgr_download_file(unittest.TestCase):

    def test_unit_download_file_file_smaller_than_chunk_download_fail(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.OneDriveFileDownloadMgr._download_with_retry", return_value = False) as mock_dl_w_retry:
            download_url = "https://fakedownloadurl"
            file_size = 250
            chunk_size = 300
            download_path = "fakefilepath"
            hash = "0123456789ABCDEF"

            oddlm = OneDriveFileDownloadMgr(download_url, file_size, chunk_size, download_path, hash)
            check_val = oddlm.download_file()

            self.assertIs(check_val, False)     

    def test_unit_download_file_file_bigger_than_chunk_open_except(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.OneDriveFileDownloadMgr._download_with_retry", return_value = b'fakebytes') as mock_dl_w_retry:
            with mock.patch("onedrive_offsite.onedrive.open", side_effect=Exception("fake exception")) as mock_open:
                download_url = "https://fakedownloadurl"
                file_size = 500
                chunk_size = 200
                download_path = "fakefilepath"
                hash = "0123456789ABCDEF"

                oddlm = OneDriveFileDownloadMgr(download_url, file_size, chunk_size, download_path, hash)
                check_val = oddlm.download_file()

                self.assertIs(check_val, False)   


    def test_unit_download_file_file_bigger_than_chunk_fail_verify(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.OneDriveFileDownloadMgr._download_with_retry", return_value = b'fakebytes') as mock_dl_w_retry:
            with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
                with mock.patch("onedrive_offsite.onedrive.OneDriveFileDownloadMgr._verify_download", return_value=False) as mock_verify_dl:
                    download_url = "https://fakedownloadurl"
                    file_size = 500
                    chunk_size = 200
                    download_path = "fakefilepath"
                    hash = "0123456789ABCDEF"

                    oddlm = OneDriveFileDownloadMgr(download_url, file_size, chunk_size, download_path, hash)
                    check_val = oddlm.download_file()

                    self.assertIs(check_val, False)   
                    
    
    def test_unit_download_file_file_bigger_than_chunk_everything_works(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.onedrive.OneDriveFileDownloadMgr._download_with_retry", return_value = b'fakebytes') as mock_dl_w_retry:
            with mock.patch("onedrive_offsite.onedrive.open") as mock_open:
                with mock.patch("onedrive_offsite.onedrive.OneDriveFileDownloadMgr._verify_download", return_value=True) as mock_verify_dl:
                    download_url = "https://fakedownloadurl"
                    file_size = 500
                    chunk_size = 200
                    download_path = "fakefilepath"
                    hash = "0123456789ABCDEF"

                    oddlm = OneDriveFileDownloadMgr(download_url, file_size, chunk_size, download_path, hash)
                    check_val = oddlm.download_file()

                    self.assertIs(check_val, True) 