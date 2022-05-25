import unittest, mock, queue, datetime

from onedrive_offsite.workers import flood_kill_queue, upload_status_gen, write_to_error_q, publish_to_attempted_q, token_refresh_cycle, token_refresh_worker, _token_refresh_get_offset
from onedrive_offsite.workers import _check_token_read, _worker_upload, _worker_chunk_loop, _worker_start_upload_session, file_upload_worker, _prime_to_upload_q, _put_file_back_on_q
from onedrive_offsite.workers import _evaluate_upload_mgmt, _empty_check, upload_manager, dir_manager, _lock_file_check, _write_to_lock_file, DownloadManager, DownloadWorker, DownloadDecrypter

class TestHelpers(unittest.TestCase):
#### ----------------------------------- write_to_error_q() -----------------------------------------------
    def test_write_to_error_q_success(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            error_q = queue.Queue()
            check_value = write_to_error_q(error_q)
            self.assertEqual(check_value, True)
            self.assertEqual(error_q.empty(), False)
    
    def test_write_to_error_q_except(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"            
            mock_error_q = mock.Mock()
            mock_error_q.put = mock.PropertyMock(side_effect=Exception("fake exception"))
            check_value = write_to_error_q(mock_error_q)
            self.assertEqual(check_value, False)

#### ----------------------------------- _check_token_read() -----------------------------------------------
    def test_check_token_read_fail(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            mock_msgcm = mock.Mock()
            mock_msgcm.read_tokens = mock.PropertyMock(return_value=False)
            with mock.patch("onedrive_offsite.workers.upload_status_gen") as mock_upload_status_gen:
                with mock.patch("onedrive_offsite.workers.publish_to_attempted_q") as mock_pub_att_q:
                    targz_file = "faketargzfile"
                    upload_attempted_q = queue.Queue()
                    kill_q = queue.Queue()
                    check_value = _check_token_read(mock_msgcm, targz_file, upload_attempted_q, kill_q)
                    self.assertEqual(check_value, False)

    def test_check_token_read_success(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            mock_msgcm = mock.Mock()
            mock_msgcm.read_tokens = mock.PropertyMock(return_value=True)
            targz_file = "faketargzfile"
            upload_attempted_q = queue.Queue()
            kill_q = queue.Queue()
            check_value = _check_token_read(mock_msgcm, targz_file, upload_attempted_q, kill_q)
            self.assertEqual(check_value, True)

#### ----------------------------------- flood_kill_queue() -----------------------------------------------
    def test_unit_flood_kill_queue(self):
        kill_q = queue.Queue()
        flood_kill_queue(kill_q)
        self.assertEqual(kill_q.qsize(), 20)        # expecting 20 items in our kill queue
        self.assertEqual(kill_q.get(), "kill")      # expecting 'kill" in our kill queue
    
#### ----------------------------------- upload_status_gen() -----------------------------------------------
    def test_unit_upload_status_gen(self):
        check_value = upload_status_gen("testfilename", "teststatus", "testmsg")
        self.assertEqual(check_value, {"filename":"testfilename","status":"teststatus","msg":"testmsg"})
    
#### ----------------------------------- publish_to_attempted_q() -----------------------------------------------
    def test_publish_to_attempted_q_success(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            kill_q = queue.Queue()
            upload_attempted_q = queue.Queue()
            test_msg = "test msg"
            check_value = publish_to_attempted_q(test_msg, upload_attempted_q, kill_q)
            self.assertEqual(check_value, True)
            self.assertEqual(upload_attempted_q.get_nowait(), test_msg)

    def test_publish_to_attempted_q_except(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            kill_q = queue.Queue()
            upload_attempted_q = mock.Mock()
            upload_attempted_q.put = mock.PropertyMock(side_effect=Exception("fake exception"))
            test_msg = "test msg"
            check_value = publish_to_attempted_q(test_msg, upload_attempted_q, kill_q)
            self.assertEqual(check_value, False)

#### ----------------------------------- token_refresh_cycle() -----------------------------------------------
    def test_token_refresh_cycle_fail_read(self):
        with mock.patch("onedrive_offsite.workers.MSGraphCredMgr") as mock_msgraphmgr:
            mock_msgraphmgr.return_value.read_tokens = mock.PropertyMock(return_value=False)
            check_value = token_refresh_cycle()
            self.assertEqual(check_value, False)

    def test_token_refresh_cycle_fail_refresh(self):
        with mock.patch("onedrive_offsite.workers.MSGraphCredMgr") as mock_msgraphmgr:
            mock_msgraphmgr.return_value.read_tokens = mock.PropertyMock(return_value=True)
            mock_msgraphmgr.return_value.refresh_tokens = mock.PropertyMock(return_value=False)
            check_value = token_refresh_cycle()
            self.assertEqual(check_value, False)

    def test_token_refresh_cycle_fail_success(self):
        with mock.patch("onedrive_offsite.workers.MSGraphCredMgr") as mock_msgraphmgr:
            mock_ret_msgraphmgr = mock.Mock()
            mock_msgraphmgr.return_value = mock_ret_msgraphmgr
            mock_ret_msgraphmgr.read_tokens = mock.PropertyMock(return_value=True)
            mock_ret_msgraphmgr.refresh_tokens = mock.PropertyMock(return_value=True)
            check_value = token_refresh_cycle()
            self.assertEqual(check_value, mock_ret_msgraphmgr)

#### ----------------------------------- _token_refresh_get_offset() -----------------------------------------------
    def test_token_refresh_get_offset_0(self):
        check_value = _token_refresh_get_offset(0)
        self.assertEqual(check_value, 1200)

    def test_token_refresh_get_offset_1(self):
        check_value = _token_refresh_get_offset(1)
        self.assertEqual(check_value, 600)

    def test_token_refresh_get_offset_2(self):
        check_value = _token_refresh_get_offset(2)
        self.assertEqual(check_value, 300)

#### ----------------------------------- _lock_file_check() -----------------------------------------------

    @mock.patch("onedrive_offsite.workers.Config")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_lock_file_check_no_file(self, mock_cur_thread, mock_config):
        mock_cur_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.os.path.isfile", return_value=False) as mock_isfile:
            check_val = _lock_file_check()
            self.assertIs(check_val, False)

    @mock.patch("onedrive_offsite.workers.Config")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_lock_file_check_file_exists_open_except(self, mock_cur_thread, mock_config):
        mock_cur_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.os.path.isfile", return_value=True) as mock_isfile:
            with mock.patch("onedrive_offsite.workers.open", side_effect=Exception("fake exception")) as mock_open:
                check_val = _lock_file_check()
                self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.workers.Config")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_lock_file_check_file_exists_is_locked(self, mock_cur_thread, mock_config):
        mock_cur_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.os.path.isfile", return_value=True) as mock_isfile:
            with mock.patch("onedrive_offsite.workers.open", new_callable=mock.mock_open, read_data="locked") as mock_open:
                check_val = _lock_file_check()
                self.assertIs(check_val, True)

    @mock.patch("onedrive_offsite.workers.Config")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_lock_file_check_file_exists_not_locked(self, mock_cur_thread, mock_config):
        mock_cur_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.os.path.isfile", return_value=True) as mock_isfile:
            with mock.patch("onedrive_offsite.workers.open", new_callable=mock.mock_open, read_data="not locked") as mock_open:
                check_val = _lock_file_check()
                self.assertIs(check_val, False)

    @mock.patch("onedrive_offsite.workers.Config")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_lock_file_check_file_exists_unexpected_text(self, mock_cur_thread, mock_config):
        mock_cur_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.os.path.isfile", return_value=True) as mock_isfile:
            with mock.patch("onedrive_offsite.workers.open", new_callable=mock.mock_open, read_data="unexpected") as mock_open:
                check_val = _lock_file_check()
                self.assertIs(check_val, None)

    
#### ----------------------------------- _write_to_lock_file() -----------------------------------------------

    @mock.patch("onedrive_offsite.workers.Config")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_write_to_lock_file_successful_write(self, mock_cur_thread, mock_config):
        mock_cur_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.open") as mock_open:
            check_val = _write_to_lock_file("lock")
            self.assertIs(check_val, True)

    @mock.patch("onedrive_offsite.workers.Config")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_write_to_lock_file_open_except(self, mock_cur_thread, mock_config):
        mock_cur_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.open", side_effect=Exception("fake exception")) as mock_open:
            check_val = _write_to_lock_file("lock")
            self.assertIs(check_val, None)

class TestTokenRefreshWorker(unittest.TestCase):

#### ----------------------------------- token_refresh_worker() -----------------------------------------------
    @mock.patch("onedrive_offsite.workers._write_to_lock_file", return_value=True)
    @mock.patch("onedrive_offsite.workers._lock_file_check", side_effect=[True, False])
    @mock.patch("onedrive_offsite.workers.sleep", return_value=None)
    def test_token_refresh_worker_lock_once_write_lock_fail_token_refresh(self, mock_sleep, mock_lock, mock_write_lock):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers.token_refresh_cycle") as mock_tok_ref_cyl:
                mock_tok_ref_cyl.return_value = False
                with mock.patch("onedrive_offsite.workers.flood_kill_queue") as mock_flood:
                    with mock.patch("onedrive_offsite.workers.write_to_error_q") as mock_write_to_error:
                        
                        kill_q = queue.Queue()
                        error_q = queue.Queue()
                        check_value = token_refresh_worker(kill_q, error_q)
                        self.assertEqual(check_value, False)
    
    @mock.patch("onedrive_offsite.workers._write_to_lock_file", return_value=True)
    @mock.patch("onedrive_offsite.workers._lock_file_check", side_effect=[True, False])
    @mock.patch("onedrive_offsite.workers.sleep", return_value=None)
    def test_token_refresh_worker_lock_once_write_lock_fail_token_refresh_exceed_retry(self, mock_sleep, mock_lock, mock_write_lock):
         with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers.token_refresh_cycle") as mock_tok_ref_cyl:
                mock_msgcm_ret = mock.Mock()
                mock_msgcm_ret.read_tokens = mock.PropertyMock(return_value=True)
                mock_msgcm_ret.expires = datetime.datetime(2022, 3, 30, 0, 0)
                mock_tok_ref_cyl.side_effect = [mock_msgcm_ret, False, False, False]
                with mock.patch("onedrive_offsite.workers._token_refresh_get_offset", return_value=300) as mock_get_offset:
                    with mock.patch("onedrive_offsite.workers.datetime") as mock_datetime:
                            mock_datetime.now.return_value = datetime.datetime(2022, 3, 30, 0, 6)
                            with mock.patch("onedrive_offsite.workers._token_refresh_get_offset", return_value=300) as mock_get_offset:
                                with mock.patch("onedrive_offsite.workers.flood_kill_queue") as mock_flood:
                                    with mock.patch("onedrive_offsite.workers.write_to_error_q") as mock_write_to_error:
                                    
                                        kill_q = queue.Queue()
                                        error_q = queue.Queue()
                                        check_value = token_refresh_worker(kill_q, error_q)
                                        self.assertEqual(check_value, False)
                                        self.assertAlmostEqual(mock_sleep.call_count, 3) # two for the retry and one from the lock check loop


    @mock.patch("onedrive_offsite.workers._write_to_lock_file", side_effect=[True, False])
    @mock.patch("onedrive_offsite.workers._lock_file_check", side_effect=[True, False])
    @mock.patch("onedrive_offsite.workers.sleep", return_value=None)
    def test_token_refresh_worker_lock_once_write_lock_once_kill_q_not_empty_fail_write_lock(self, mock_sleep, mock_lock, mock_write_lock):
         with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers.token_refresh_cycle") as mock_tok_ref_cyl:
                mock_msgcm_ret = mock.Mock()
                mock_tok_ref_cyl.return_value = mock_msgcm_ret

                kill_q = mock.Mock()
                kill_q.empty.side_effect = [True, False]    # empty for lock check loop, not empty for refresh loop
                error_q = queue.Queue()
                check_value = token_refresh_worker(kill_q, error_q)
                self.assertEqual(check_value, True)

    @mock.patch("onedrive_offsite.workers._write_to_lock_file", return_value=True)
    @mock.patch("onedrive_offsite.workers._lock_file_check", side_effect=[True, False])
    @mock.patch("onedrive_offsite.workers.sleep", return_value=None)
    def test_token_refresh_worker_lock_once_write_lock_no_token_refresh_needed_in_loop(self, mock_sleep, mock_lock, mock_write_lock):
         with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers.token_refresh_cycle") as mock_tok_ref_cyl:
                mock_msgcm_ret = mock.Mock()
                mock_msgcm_ret.read_tokens = mock.PropertyMock(return_value=True)
                mock_msgcm_ret.expires = datetime.datetime(2022, 3, 30, 0, 0)
                mock_tok_ref_cyl.return_value = mock_msgcm_ret
                with mock.patch("onedrive_offsite.workers.datetime") as mock_datetime:
                    mock_datetime.now.return_value = datetime.datetime(2022, 3, 30, 0, 2)   # should not cause token_refresh_cycle(), under 300 seconds
                    with mock.patch("onedrive_offsite.workers.flood_kill_queue") as mock_flood:
                        with mock.patch("onedrive_offsite.workers.write_to_error_q") as mock_write_to_error:

                            kill_q = mock.Mock()
                            kill_q.empty.side_effect = [True, True, False]
                            error_q = queue.Queue()
                            check_value = token_refresh_worker(kill_q, error_q)
                            self.assertIs(check_value, True)


    @mock.patch("onedrive_offsite.workers._write_to_lock_file", return_value=False)
    @mock.patch("onedrive_offsite.workers._lock_file_check", side_effect=[True, False])
    @mock.patch("onedrive_offsite.workers.sleep", return_value=None)
    def test_token_refresh_worker_lock_once_fail_write_lock(self, mock_sleep, mock_lock, mock_write_lock):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers.flood_kill_queue") as mock_flood:
                with mock.patch("onedrive_offsite.workers.write_to_error_q") as mock_write_to_error:
                    
                    kill_q = queue.Queue()
                    error_q = queue.Queue()
                    check_value = token_refresh_worker(kill_q, error_q)
                    self.assertIs(check_value, None)

    @mock.patch("onedrive_offsite.workers._write_to_lock_file", return_value=False)
    @mock.patch("onedrive_offsite.workers._lock_file_check", return_value=True)
    @mock.patch("onedrive_offsite.workers.sleep", return_value=None)
    def test_token_refresh_worker_lock_once_kill_q_not_empty(self, mock_sleep, mock_lock, mock_write_lock):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
                    
            kill_q = mock.Mock()
            kill_q.empty.return_value = False
            error_q = queue.Queue()
            check_value = token_refresh_worker(kill_q, error_q)
            self.assertIs(check_value, None)


class TestFileUploadWorker(unittest.TestCase):

#### ----------------------------------- _worker_upload() -----------------------------------------------
    def test_worker_upload_bytes_none(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers.upload_status_gen") as mock_upload_status_gen:
                with mock.patch("onedrive_offsite.workers.publish_to_attempted_q") as mock_pub_to_att_q:
                    bytes_to_send = None
                    targz_file = "faketargzfile"
                    chunks = []
                    fpr = mock.Mock()
                    upload_attempted_q = queue.Queue()
                    kill_q = queue.Queue()
                    odlu = mock.Mock()

                    check_value = _worker_upload(bytes_to_send, targz_file, chunks, fpr, upload_attempted_q, kill_q, odlu)
                    self.assertEqual(check_value, "error-empty-bytes")

    def test_worker_upload_upload_failed(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers.upload_status_gen") as mock_upload_status_gen:
                with mock.patch("onedrive_offsite.workers.publish_to_attempted_q") as mock_pub_to_att_q:
                    bytes_to_send = b'bytes'
                    targz_file = "faketargzfile"
                    chunks = [1,2,3]
                    fpr = mock.Mock()
                    upload_attempted_q = queue.Queue()
                    kill_q = queue.Queue()
                    odlu = mock.Mock()
                    odlu.upload_file_part = mock.PropertyMock(return_value=False)

                    check_value = _worker_upload(bytes_to_send, targz_file, chunks, fpr, upload_attempted_q, kill_q, odlu)
                    self.assertEqual(check_value, "upload-failed")                   
    
    def test_worker_upload_upload_success(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            bytes_to_send = b'bytes'
            targz_file = "faketargzfile"
            chunks = [1,2,3]
            fpr = mock.Mock()
            upload_attempted_q = queue.Queue()
            kill_q = queue.Queue()
            mock_resp = mock.Mock()
            mock_resp.status_code = 201
            odlu = mock.Mock()
            odlu.upload_file_part = mock.PropertyMock(return_value=mock_resp)

            check_value = _worker_upload(bytes_to_send, targz_file, chunks, fpr, upload_attempted_q, kill_q, odlu)
            self.assertEqual(check_value, "upload-succeeded")  

    def test_worker_upload_upload_move_next(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            bytes_to_send = b'bytes'
            targz_file = "faketargzfile"
            chunks = [1,2,3]
            fpr = mock.Mock()
            upload_attempted_q = queue.Queue()
            kill_q = queue.Queue()
            odlu = mock.Mock()
            odlu.upload_file_part = mock.PropertyMock(return_value="move-next")

            check_value = _worker_upload(bytes_to_send, targz_file, chunks, fpr, upload_attempted_q, kill_q, odlu)
            self.assertEqual(check_value, "upload-succeeded")  

    def test_worker_upload_upload_exception(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            bytes_to_send = b'bytes'
            targz_file = "faketargzfile"
            chunks = [1,2,3]
            fpr = mock.Mock()
            upload_attempted_q = queue.Queue()
            kill_q = queue.Queue()
            odlu = mock.Mock()
            odlu.upload_file_part = mock.PropertyMock(side_effect=Exception("fake exception"))

            check_value = _worker_upload(bytes_to_send, targz_file, chunks, fpr, upload_attempted_q, kill_q, odlu)
            self.assertEqual(check_value, "upload-failed")

#### ----------------------------------- _worker_chunk_loop() -----------------------------------------------
    def test_worker_chunk_loop_upload_failed(self):
        with mock.patch("onedrive_offsite.workers._worker_upload", return_value="upload-failed") as mock_work_up:
            fpr = mock.Mock()
            fpr.upload_array = [[1, 2]]
            fpr.read_file_bytes = mock.PropertyMock(return_value=b'bytestosend')
            odlu = mock.Mock()
            targz_file = "faketargzfile"
            upload_attempted_q = queue.Queue()
            kill_q = queue.Queue()

            check_value = _worker_chunk_loop(fpr, targz_file, upload_attempted_q, kill_q, odlu)
            self.assertEqual(check_value, "upload-failed")

    def test_worker_chunk_loop_kill_q(self):
        fpr = mock.Mock()
        fpr.upload_array = [[1, 2]]
        fpr.read_file_bytes = mock.PropertyMock(return_value=b'bytestosend')
        odlu = mock.Mock()
        targz_file = "faketargzfile"
        upload_attempted_q = queue.Queue()
        kill_q = queue.Queue()
        kill_q.put("kill")

        check_value = _worker_chunk_loop(fpr, targz_file, upload_attempted_q, kill_q, odlu)
        self.assertEqual(check_value, "kill-q")

    def test_worker_chunk_loop_success(self):
        with mock.patch("onedrive_offsite.workers._worker_upload", return_value="upload-succeeded") as mock_work_up:
            fpr = mock.Mock()
            fpr.upload_array = [[1, 2]]
            fpr.read_file_bytes = mock.PropertyMock(return_value=b'bytestosend')
            odlu = mock.Mock()
            targz_file = "faketargzfile"
            upload_attempted_q = queue.Queue()
            kill_q = queue.Queue()

            check_value = _worker_chunk_loop(fpr, targz_file, upload_attempted_q, kill_q, odlu)
            self.assertEqual(check_value, "upload-success")

#### ----------------------------------- _worker_start_upload_session() -----------------------------------------------
    def test_worker_start_upload_session_fail(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers.upload_status_gen") as mock_up_stat_gen:
                mock_up_stat_gen.return_value = "fake queue message"
                with mock.patch("onedrive_offsite.workers.publish_to_attempted_q") as mock_pub_att_q:
                    odlu = mock.Mock()
                    odlu.initiate_upload_session = mock.PropertyMock(return_value=False)        
                    msgcm = mock.Mock()
                    msgcm.access_token = "fakeaccesstoken"
                    targz_file = "faketargzfile"
                    upload_attempted_q = queue.Queue()
                    kill_q = queue.Queue()

                    check_value = _worker_start_upload_session(odlu, msgcm, targz_file, upload_attempted_q, kill_q)
                    self.assertEqual(check_value, False)

    def test_worker_start_upload_session_succeed(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            odlu = mock.Mock()
            odlu.initiate_upload_session = mock.PropertyMock(return_value=True)        
            msgcm = mock.Mock()
            msgcm.access_token = "fakeaccesstoken"
            targz_file = "faketargzfile"
            upload_attempted_q = queue.Queue()
            kill_q = queue.Queue()

            check_value = _worker_start_upload_session(odlu, msgcm, targz_file, upload_attempted_q, kill_q)
            self.assertEqual(check_value, True)


#### ----------------------------------- file_upload_worker() -----------------------------------------------
    def test_file_upload_worker_cant_read_tokens(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers.datetime") as mock_datetime:
                mock_datetime.now.side_effect = [datetime.datetime(2022, 3, 30, 0, 6), datetime.datetime(2022, 3, 30, 0, 6)]
                with mock.patch("onedrive_offsite.workers.OneDriveLargeUpload") as mock_odlu:
                    with mock.patch("onedrive_offsite.workers.MSGraphCredMgr") as mock_msgcm:
                        with mock.patch("onedrive_offsite.workers._check_token_read", return_value=False) as mock_ch_tok_rd: # can't read tokens
                            with mock.patch("onedrive_offsite.workers.flood_kill_queue") as mock_flood_kill:
                                
                                kill_q = mock.Mock()
                                kill_q.empty = mock.PropertyMock(side_effect=[True, False])
                                kill_q.get_nowait = mock.PropertyMock(return_value="kill")

                                to_upload_q = mock.Mock()
                                to_upload_q.get_nowait = mock.PropertyMock(return_value="faketargzfile")

                                upload_attempted_q = queue.Queue()

                                check_value = file_upload_worker(to_upload_q, upload_attempted_q, kill_q)
                                self.assertEqual(check_value, "token-read-fail")

    def test_file_upload_worker_cant_start_upload(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers.datetime") as mock_datetime:
                mock_datetime.now.side_effect = [datetime.datetime(2022, 3, 30, 0, 6), datetime.datetime(2022, 3, 30, 0, 6)]
                with mock.patch("onedrive_offsite.workers.OneDriveLargeUpload") as mock_odlu:
                    with mock.patch("onedrive_offsite.workers.MSGraphCredMgr") as mock_msgcm:
                        with mock.patch("onedrive_offsite.workers._check_token_read", return_value=True) as mock_ch_tok_rd:
                            with mock.patch("onedrive_offsite.workers._worker_start_upload_session", return_value=False) as mock_st_up: # can't start upload session
                                with mock.patch("onedrive_offsite.workers.flood_kill_queue") as mock_flood_kill:
                                    
                                    kill_q = mock.Mock()
                                    kill_q.empty = mock.PropertyMock(side_effect=[True, False])
                                    kill_q.get_nowait = mock.PropertyMock(return_value="kill")

                                    to_upload_q = mock.Mock()
                                    to_upload_q.get_nowait = mock.PropertyMock(return_value="faketargzfile")

                                    upload_attempted_q = queue.Queue()

                                    check_value = file_upload_worker(to_upload_q, upload_attempted_q, kill_q)
                                    self.assertEqual(check_value, "upload-start-fail")

    def test_file_upload_worker_chunk_upload_complete_success(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers.datetime") as mock_datetime:
                mock_datetime.now.side_effect = [datetime.datetime(2022, 3, 30, 0, 6), datetime.datetime(2022, 3, 30, 0, 6)]
                with mock.patch("onedrive_offsite.workers.OneDriveLargeUpload") as mock_odlu:
                    with mock.patch("onedrive_offsite.workers.MSGraphCredMgr") as mock_msgcm:
                        with mock.patch("onedrive_offsite.workers._check_token_read", return_value=True) as mock_ch_tok_rd:
                            with mock.patch("onedrive_offsite.workers._worker_start_upload_session", return_value=True) as mock_st_up:
                                with mock.patch("onedrive_offsite.workers.FilePartialRead") as mock_fpr:
                                    with mock.patch("onedrive_offsite.workers._worker_chunk_loop", return_value="upload-success") as mock_chunk_loop: # upload succeeded
                                        with mock.patch("onedrive_offsite.workers.upload_status_gen", return_value="fakesuccessmsg") as mock_up_st_gen:
                                            with mock.patch("onedrive_offsite.workers.publish_to_attempted_q") as mock_pub_att_q:
                                                with mock.patch("onedrive_offsite.workers.flood_kill_queue") as mock_flood_kill:
                                                    
                                                    kill_q = mock.Mock()
                                                    kill_q.empty = mock.PropertyMock(side_effect=[True, True, False])
                                                    kill_q.get_nowait = mock.PropertyMock(return_value="kill")

                                                    to_upload_q = mock.Mock()
                                                    to_upload_q.get_nowait = mock.PropertyMock(return_value="faketargzfile")

                                                    upload_attempted_q = queue.Queue()

                                                    check_value = file_upload_worker(to_upload_q, upload_attempted_q, kill_q)
                                                    self.assertEqual(check_value, "upload-success")

    def test_file_upload_worker_chunk_upload_fail(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers.datetime") as mock_datetime:
                mock_datetime.now.side_effect = [datetime.datetime(2022, 3, 30, 0, 6), datetime.datetime(2022, 3, 30, 0, 6)]
                with mock.patch("onedrive_offsite.workers.OneDriveLargeUpload") as mock_odlu:
                    with mock.patch("onedrive_offsite.workers.MSGraphCredMgr") as mock_msgcm:
                        with mock.patch("onedrive_offsite.workers._check_token_read", return_value=True) as mock_ch_tok_rd:
                            with mock.patch("onedrive_offsite.workers._worker_start_upload_session", return_value=True) as mock_st_up:
                                with mock.patch("onedrive_offsite.workers.FilePartialRead") as mock_fpr:
                                    with mock.patch("onedrive_offsite.workers._worker_chunk_loop", return_value="upload-fail") as mock_chunk_loop: # upload failed
                                        with mock.patch("onedrive_offsite.workers.flood_kill_queue") as mock_flood_kill:
                                            
                                            kill_q = mock.Mock()
                                            kill_q.empty = mock.PropertyMock(side_effect=[True, False])
                                            kill_q.get_nowait = mock.PropertyMock(return_value="kill")

                                            to_upload_q = mock.Mock()
                                            to_upload_q.get_nowait = mock.PropertyMock(return_value="faketargzfile")

                                            upload_attempted_q = queue.Queue()

                                            check_value = file_upload_worker(to_upload_q, upload_attempted_q, kill_q)
                                            self.assertEqual(check_value, "upload-fail")

    def test_file_upload_to_upload_empty_too_long(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers.datetime") as mock_datetime:
                mock_datetime.now.side_effect = [datetime.datetime(2022, 3, 30, 0, 0), datetime.datetime(2022, 3, 30, 0, 0), datetime.datetime(2022, 3, 30, 1, 59), datetime.datetime(2022, 3, 30, 2, 0), datetime.datetime(2022, 3, 30, 4, 1)] # 2nd time through loop q will be empty for should be 2 hrs 1 min 
                with mock.patch("onedrive_offsite.workers.sleep", return_value=None) as mock_sleep:
                    with mock.patch("onedrive_offsite.workers.flood_kill_queue") as mock_flood_kill:
                        
                        kill_q = mock.Mock()
                        kill_q.empty = mock.PropertyMock(side_effect=[True, True, False])
                        kill_q.get_nowait = mock.PropertyMock(side_effect=queue.Empty)

                        to_upload_q = mock.Mock()
                        to_upload_q.get_nowait = mock.PropertyMock(side_effect=[queue.Empty, queue.Empty]) # to upload q empty

                        upload_attempted_q = queue.Queue()

                        check_value = file_upload_worker(to_upload_q, upload_attempted_q, kill_q)
                        self.assertEqual(check_value, "to-upload-empty-too-long")


class TestFileUploadManager(unittest.TestCase):

### -------------------------------------- _prime_to_upload_q() ---------------------------------------
    def test_prime_to_upload_q_success(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"

            file_list = ["file1", "file2", "file3"]
            to_upload_q = queue.Queue()
            kill_q = queue.Queue()
            error_q = queue.Queue()

            check_value = _prime_to_upload_q(file_list, to_upload_q, kill_q, error_q)
            expected_upload_mgmt = {"file1":{"status":"not started","retry_attempts":0},
                                    "file2":{"status":"not started","retry_attempts":0},
                                    "file3":{"status":"not started", "retry_attempts":0}}
            self.assertEqual(check_value, expected_upload_mgmt)
            self.assertEqual(to_upload_q.qsize(), 3)

    def test_prime_to_upload_q_except(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers.flood_kill_queue") as mock_flood_kill:
                with mock.patch("onedrive_offsite.workers.write_to_error_q") as mock_wr_to_err_q:

                    file_list = ["file1", "file2", "file3"]
                    to_upload_q = mock.Mock()
                    to_upload_q.put = mock.PropertyMock(side_effect=Exception("fake exception"))
                    kill_q = queue.Queue()
                    error_q = queue.Queue()

                    check_value = _prime_to_upload_q(file_list, to_upload_q, kill_q, error_q)

                    self.assertEqual(check_value, False)


### -------------------------------------- _put_file_back_on_q() ---------------------------------------

    def test_put_file_back_on_q_success(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"

            to_upload_q = mock.Mock()
            to_upload_q.put = mock.PropertyMock(return_value=None)

            filename = "fakefile"
            kill_q = queue.Queue()
            error_q = queue.Queue()

            check_value = _put_file_back_on_q(filename, to_upload_q, kill_q, error_q)
            self.assertEqual(check_value, True)
            

    def test_put_file_back_on_q_except(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers.write_to_error_q") as mock_wr_to_err_q:
                with mock.patch("onedrive_offsite.workers.flood_kill_queue") as mock_flood_kill_q:

                    to_upload_q = mock.Mock()
                    to_upload_q.put = mock.PropertyMock(side_effect=Exception("fake exception"))

                    filename = "fakefile"
                    kill_q = queue.Queue()
                    error_q = queue.Queue()

                    check_value = _put_file_back_on_q(filename, to_upload_q, kill_q, error_q)
                    self.assertEqual(check_value, False)


### -------------------------------------- _evaluate_upload_mgmt() ---------------------------------------

    def test_evaluate_upload_mgmt_keep_going(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"

            upload_mgmt = {"file1":{"status":"complete","retry_attempts":0},
                            "file2":{"status":"not started","retry_attempts":0},
                            "file3":{"status":"not started", "retry_attempts":0}}
            
            kill_q = queue.Queue()
            error_q = queue.Queue()

            check_value = _evaluate_upload_mgmt(upload_mgmt, kill_q, error_q)
            self.assertEqual(check_value, None)

    def test_evaluate_upload_mgmt_keep_complete(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers.flood_kill_queue") as mock_flood_kill:

                upload_mgmt = {"file1":{"status":"complete","retry_attempts":0},
                                "file2":{"status":"complete","retry_attempts":0},
                                "file3":{"status":"complete", "retry_attempts":0}}
            
                kill_q = queue.Queue()
                error_q = queue.Queue()

                check_value = _evaluate_upload_mgmt(upload_mgmt, kill_q, error_q)
                self.assertEqual(check_value, True)
                self.assertEqual(mock_flood_kill.call_count, 1)

    def test_evaluate_upload_mgmt_keep_exceed_retries(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers.flood_kill_queue") as mock_flood_kill:
                with mock.patch("onedrive_offsite.workers.write_to_error_q") as mock_write_err:

                    upload_mgmt = {"file1":{"status":"complete","retry_attempts":0},
                                    "file2":{"status":"error","retry_attempts":6},
                                    "file3":{"status":"not started", "retry_attempts":0}}
                
                    kill_q = queue.Queue()
                    error_q = queue.Queue()

                    check_value = _evaluate_upload_mgmt(upload_mgmt, kill_q, error_q)
                    self.assertEqual(check_value, False)
                    self.assertEqual(mock_flood_kill.call_count, 1)
                    self.assertEqual(mock_write_err.call_count, 1)

### -------------------------------------- _empty_check() ---------------------------------------
    
    def test_empty_check_not_too_long(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers.datetime") as mock_datetime: 
                mock_datetime.now.return_value = datetime.datetime(2022, 3, 1, 3, 0) # mock 3AM
                with mock.patch("onedrive_offsite.workers.sleep", return_value=None) as mock_sleep:
                    start_time = datetime.datetime(2022, 3, 1, 0, 0) # set start time to midnight
                    kill_q = queue.Queue()
                    error_q = queue.Queue()
                    check_value = _empty_check(start_time, kill_q, error_q)
                    self.assertEqual(check_value, None)

    def test_empty_check_too_long(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers.datetime") as mock_datetime: 
                mock_datetime.now.return_value = datetime.datetime(2022, 3, 1, 4, 1) # mock 4:01 AM
                with mock.patch("onedrive_offsite.workers.flood_kill_queue") as mock_flood_kill:
                    with mock.patch("onedrive_offsite.workers.write_to_error_q") as mock_wr_err:
                        start_time = datetime.datetime(2022, 3, 1, 0, 0) # set start time to midnight
                        kill_q = queue.Queue()
                        error_q = queue.Queue()
                        check_value = _empty_check(start_time, kill_q, error_q)
                        self.assertEqual(check_value, False)


### -------------------------------------- upload_manager() ---------------------------------------

    def test_upload_manager_fail_to_prime_q(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers._prime_to_upload_q", return_value=False) as mock_prime_q:
                file_list = ["file1", "file2", "file3"]
                to_upload_q = queue.Queue()
                upload_attempted_q = queue.Queue()
                kill_q = queue.Queue()
                error_q = queue.Queue()
                check_value = upload_manager(file_list, to_upload_q,upload_attempted_q, kill_q, error_q)

                self.assertEqual(check_value, False)

    def test_upload_manager_upload_attempted_empty_too_long(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers._prime_to_upload_q", return_value=True) as mock_prime_q:
                test_upload_mgmt = {"file1":{"status":"not started","retry_attempts":0},
                                "file2":{"status":"not started","retry_attempts":0},
                                "file3":{"status":"not started", "retry_attempts":0}}
                mock_prime_q.return_value = test_upload_mgmt
                with mock.patch("onedrive_offsite.workers.datetime") as mock_datetime:
                    mock_datetime.now.return_value = datetime.datetime(2022, 3, 1, 0, 0)
                    with mock.patch("onedrive_offsite.workers._empty_check", return_value=False) as mock_empty_check:
                
                        kill_q = mock.Mock()
                        kill_q.empty = mock.PropertyMock(side_effect=[True])

                        upload_attempted_q = mock.Mock()
                        upload_attempted_q.get_nowait = mock.PropertyMock(side_effect=[queue.Empty])

                        file_list = ["file1", "file2", "file3"]
                        to_upload_q = queue.Queue()                
                        error_q = queue.Queue()
                        check_value = upload_manager(file_list, to_upload_q,upload_attempted_q, kill_q, error_q)

                        self.assertEqual(check_value, False)

    def test_upload_manager_error_fail_to_put_file_on_to_be_uploaded(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers._prime_to_upload_q", return_value=True) as mock_prime_q:
                test_upload_mgmt = {"file1":{"status":"not started","retry_attempts":0},
                                "file2":{"status":"not started","retry_attempts":0},
                                "file3":{"status":"not started", "retry_attempts":0}}
                mock_prime_q.return_value = test_upload_mgmt
                with mock.patch("onedrive_offsite.workers.datetime") as mock_datetime:
                    mock_datetime.now.side_effect = [datetime.datetime(2022, 3, 1, 0, 0), datetime.datetime(2022, 3, 1, 0, 0)]
                    with mock.patch("onedrive_offsite.workers._put_file_back_on_q", return_value=False) as mock_put_back:
                
                        kill_q = mock.Mock()
                        kill_q.empty = mock.PropertyMock(side_effect=[True])

                        upload_attempted_q = mock.Mock()
                        upload_attempted_q.get_nowait = mock.PropertyMock(return_value={"filename": "file1", "status": "error", "msg": "fake err msg"})

                        file_list = ["file1", "file2", "file3"]
                        to_upload_q = queue.Queue()                
                        error_q = queue.Queue()
                        check_value = upload_manager(file_list, to_upload_q,upload_attempted_q, kill_q, error_q)

                        self.assertEqual(check_value, False)

    def test_upload_manager_uploads_complete(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers._prime_to_upload_q", return_value=True) as mock_prime_q:
                test_upload_mgmt = {"file1":{"status":"not started","retry_attempts":0},
                                "file2":{"status":"not started","retry_attempts":0},
                                "file3":{"status":"not started", "retry_attempts":0}}
                mock_prime_q.return_value = test_upload_mgmt
                with mock.patch("onedrive_offsite.workers.datetime") as mock_datetime:
                    mock_datetime.now.side_effect = [datetime.datetime(2022, 3, 1, 0, 0), datetime.datetime(2022, 3, 1, 0, 0)]
                    with mock.patch("onedrive_offsite.workers._evaluate_upload_mgmt", return_value=True) as mock_eval_up: # indicates all uploads have comleted
                
                        kill_q = mock.Mock()
                        kill_q.empty = mock.PropertyMock(side_effect=[True])

                        upload_attempted_q = mock.Mock()
                        upload_attempted_q.get_nowait = mock.PropertyMock(return_value={"filename": "file1", "status": "complete", "msg": "fake comlete msg"})

                        file_list = ["file1", "file2", "file3"]
                        to_upload_q = queue.Queue()                
                        error_q = queue.Queue()
                        check_value = upload_manager(file_list, to_upload_q,upload_attempted_q, kill_q, error_q)

                        self.assertEqual(check_value, True)

    def test_upload_manager_too_many_retries(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers._prime_to_upload_q", return_value=True) as mock_prime_q:
                test_upload_mgmt = {"file1":{"status":"not started","retry_attempts":0},
                                "file2":{"status":"not started","retry_attempts":0},
                                "file3":{"status":"not started", "retry_attempts":0}}
                mock_prime_q.return_value = test_upload_mgmt
                with mock.patch("onedrive_offsite.workers.datetime") as mock_datetime:
                    mock_datetime.now.side_effect = [datetime.datetime(2022, 3, 1, 0, 0), datetime.datetime(2022, 3, 1, 0, 0)]
                    with mock.patch("onedrive_offsite.workers._put_file_back_on_q", return_value=True) as mock_put_file_back:
                        with mock.patch("onedrive_offsite.workers._evaluate_upload_mgmt", return_value=False) as mock_eval_up: # indicates too many retries
                    
                            kill_q = mock.Mock()
                            kill_q.empty = mock.PropertyMock(side_effect=[True])

                            upload_attempted_q = mock.Mock()
                            upload_attempted_q.get_nowait = mock.PropertyMock(return_value={"filename": "file1", "status": "error", "msg": "fake err msg"})

                            file_list = ["file1", "file2", "file3"]
                            to_upload_q = queue.Queue()                
                            error_q = queue.Queue()
                            check_value = upload_manager(file_list, to_upload_q,upload_attempted_q, kill_q, error_q)

                            self.assertEqual(check_value, False)


    def test_upload_manager_kill_q_not_empty(self):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers._prime_to_upload_q", return_value=True) as mock_prime_q:
                test_upload_mgmt = {"file1":{"status":"not started","retry_attempts":0},
                                "file2":{"status":"not started","retry_attempts":0},
                                "file3":{"status":"not started", "retry_attempts":0}}
                mock_prime_q.return_value = test_upload_mgmt
                with mock.patch("onedrive_offsite.workers.datetime") as mock_datetime:
                    mock_datetime.now.return_value = datetime.datetime(2022, 3, 1, 0, 0)
               
                    kill_q = mock.Mock()
                    kill_q.empty = mock.PropertyMock(side_effect=[False])

                    upload_attempted_q = queue.Queue()

                    file_list = ["file1", "file2", "file3"]
                    to_upload_q = queue.Queue()                
                    error_q = queue.Queue()
                    check_value = upload_manager(file_list, to_upload_q,upload_attempted_q, kill_q, error_q)

                    self.assertEqual(check_value, False)


class TestDirManager(unittest.TestCase):

### -------------------------------------- dir_manager() ---------------------------------------
    @mock.patch("onedrive_offsite.workers.flood_kill_queue")
    @mock.patch("onedrive_offsite.workers.write_to_error_q")
    def test_unit_dir_manager_fail_token_read(self, mock_wr_err, mock_fl_kill):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers.MSGraphCredMgr") as mock_msgrcrmgr:
                mock_msgrcrmgr.return_value.read_tokens.return_value = False

                kill_q = queue.Queue()
                error_q = queue.Queue()

                check_val = dir_manager(kill_q, error_q)
                self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.workers.flood_kill_queue")
    @mock.patch("onedrive_offsite.workers.write_to_error_q")
    def test_unit_dir_manager_no_dir_name(self, mock_wr_err, mock_fl_kill):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers.MSGraphCredMgr") as mock_msgrcrmgr:
                mock_msgrcrmgr.return_value.read_tokens.return_value = True
                mock_msgrcrmgr.return_value.access_token = "fakeaccesstoken"
                with mock.patch("onedrive_offsite.workers.OneDriveDirMgr") as mock_oddm:
                    mock_oddm.return_value.dir_name = None

                    kill_q = queue.Queue()
                    error_q = queue.Queue()

                    check_val = dir_manager(kill_q, error_q)
                    self.assertIs(check_val, None)


    @mock.patch("onedrive_offsite.workers.flood_kill_queue")
    @mock.patch("onedrive_offsite.workers.write_to_error_q")
    def test_unit_dir_manager_fail_create_dir(self, mock_wr_err, mock_fl_kill):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers.MSGraphCredMgr") as mock_msgrcrmgr:
                mock_msgrcrmgr.return_value.read_tokens.return_value = True
                mock_msgrcrmgr.return_value.access_token = "fakeaccesstoken"
                with mock.patch("onedrive_offsite.workers.OneDriveDirMgr") as mock_oddm:
                    mock_oddm.return_value.dir_name = "fake-dir-name"
                    mock_oddm.return_value.create_dir.return_value = None

                    kill_q = queue.Queue()
                    error_q = queue.Queue()

                    check_val = dir_manager(kill_q, error_q)
                    self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.workers.flood_kill_queue")
    @mock.patch("onedrive_offsite.workers.write_to_error_q")
    def test_unit_dir_manager_everything_works(self, mock_wr_err, mock_fl_kill):
        with mock.patch("onedrive_offsite.workers.threading.current_thread") as mock_curr_thread:
            mock_curr_thread.return_value.getName.return_value = "fake-thread"
            with mock.patch("onedrive_offsite.workers.MSGraphCredMgr") as mock_msgrcrmgr:
                mock_msgrcrmgr.return_value.read_tokens.return_value = True
                mock_msgrcrmgr.return_value.access_token = "fakeaccesstoken"
                with mock.patch("onedrive_offsite.workers.OneDriveDirMgr") as mock_oddm:
                    mock_oddm.return_value.dir_name = "fake-dir-name"
                    mock_oddm.return_value.create_dir.return_value = True

                    kill_q = queue.Queue()
                    error_q = queue.Queue()

                    check_val = dir_manager(kill_q, error_q)
                    self.assertIs(check_val, True)

class TestDownloadManager(unittest.TestCase):

### -------------------------------------- _get_download_info() ---------------------------------------
    @mock.patch("onedrive_offsite.workers.Config")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_get_download_info_open_except(self, mock_curr_thread, mock_config):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.open", side_effect=Exception("fake exception")) as mock_open:
            check_val = DownloadManager._get_download_info()
            self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.workers.Config")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_get_download_info_fail_verify_json(self, mock_curr_thread, mock_config):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.open") as mock_open:
            with mock.patch("onedrive_offsite.workers.json.load", return_value={"onedrive-dir": "fake-dir"}) as mock_json_load:
                with mock.patch("onedrive_offsite.workers.DownloadManager._verify_dl_json", return_value=None) as mock_verify_dl_json:
                    check_val = DownloadManager._get_download_info()
                    self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.workers.Config")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_get_download_info_pass_verify_json(self, mock_curr_thread, mock_config):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.open") as mock_open:
            with mock.patch("onedrive_offsite.workers.json.load", return_value={"onedrive-dir": "fake-dir"}) as mock_json_load:
                with mock.patch("onedrive_offsite.workers.DownloadManager._verify_dl_json", return_value=True) as mock_verify_dl_json:
                    check_val = DownloadManager._get_download_info()
                    self.assertEqual(check_val, {"onedrive-dir": "fake-dir"})


### -------------------------------------- _verify_dl_json() ---------------------------------------

    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_verify_dl_json_missing_onedrive_dir(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        check_val = DownloadManager._verify_dl_json({"fake-key": "fake-value"})
        self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_verify_dl_json_onedrive_dir_present(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        check_val = DownloadManager._verify_dl_json({"onedrive-dir": "fake-dir"})
        self.assertIs(check_val, True)


### -------------------------------------- _prime_to_download_q() ---------------------------------------

    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_prime_to_download_q_put_except(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        to_download_q = mock.Mock()
        to_download_q.put.side_effect = Exception("fake exception")
        items_to_download = [{"id":"id1", "name":"name1"},{"id":"id2", "name":"name2"}]
        check_val = DownloadManager._prime_to_download_q(to_download_q, items_to_download)
        self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_prime_to_download_q_success(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        to_download_q = queue.Queue()
        items_to_download = [{"id":"id1", "name":"name1"},{"id":"id2", "name":"name2"}]
        check_val = DownloadManager._prime_to_download_q(to_download_q, items_to_download)
        self.assertEqual(check_val, {"id1":{"name":"name1","retry":0, "status":"not started"}, "id2":{"name":"name2","retry":0, "status":"not started"}})
        self.assertEqual(to_download_q.qsize(), 2)


### -------------------------------------- _get_download_list() ---------------------------------------

    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_get_download_list_no_dir_name_none(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.DownloadManager._get_download_info", return_value=None) as mock_get_dl_list:
            check_val = DownloadManager._get_download_list()
            self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_get_download_list_missing_dir_name(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.DownloadManager._get_download_info", return_value={"missing-dir": "fake-dir"}) as mock_get_dl_list:
            check_val = DownloadManager._get_download_list()
            self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_get_download_list_dir_present_read_token_fail(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.DownloadManager._get_download_info", return_value={"onedrive-dir": "fake-dir"}) as mock_get_dl_list:
            with mock.patch("onedrive_offsite.workers.MSGraphCredMgr") as mock_msgcm:
                mock_msgcm.return_value.read_tokens.return_value = False

                check_val = DownloadManager._get_download_list()
                self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_get_download_list_dir_present_read_tokens_no_file_list(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.DownloadManager._get_download_info", return_value={"onedrive-dir": "fake-dir"}) as mock_get_dl_list:
            with mock.patch("onedrive_offsite.workers.MSGraphCredMgr") as mock_msgcm:
                mock_msgcm.return_value.read_tokens.return_value = True
                with mock.patch("onedrive_offsite.workers.OneDriveItemGetter") as mock_odig:
                    mock_odig.return_value.get_dir_items.return_value = None

                    check_val = DownloadManager._get_download_list()
                    self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_get_download_list_dir_present_read_tokens_return_file_list(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.DownloadManager._get_download_info", return_value={"onedrive-dir": "fake-dir"}) as mock_get_dl_list:
            with mock.patch("onedrive_offsite.workers.MSGraphCredMgr") as mock_msgcm:
                mock_msgcm.return_value.read_tokens.return_value = True
                with mock.patch("onedrive_offsite.workers.OneDriveItemGetter") as mock_odig:
                    mock_odig.return_value.get_dir_items.return_value = [{"id": "id1", "name": "name1"}, {"id": "id2", "name": "name2"}]

                    check_val = DownloadManager._get_download_list()
                    self.assertEqual(check_val, [{"id": "id1", "name": "name1"}, {"id": "id2", "name": "name2"}])


### -------------------------------------- _put_file_back_on_q() ---------------------------------------

    @mock.patch("onedrive_offsite.workers.flood_kill_queue")
    @mock.patch("onedrive_offsite.workers.write_to_error_q")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_put_file_back_on_q_put_except(self, mock_curr_thread, mock_wr_to_err_q, mock_flood_kill_q):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"  

        to_download_q = mock.Mock()
        to_download_q.put.side_effect = Exception("fake exception")

        id = "fake-id"
        name = "fake-name"
        kill_q = queue.Queue()
        error_q = queue.Queue()

        check_val = DownloadManager._put_file_back_on_q(id, name, to_download_q, kill_q, error_q)
        self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_put_file_back_on_q_success(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"  

        to_download_q = queue.Queue()
        id = "fake-id"
        name = "fake-name"
        kill_q = queue.Queue()
        error_q = queue.Queue()

        check_val = DownloadManager._put_file_back_on_q(id, name, to_download_q, kill_q, error_q)
        check_val2 = to_download_q.get_nowait()
        self.assertIs(check_val, True)
        self.assertEqual(check_val2, {"id":"fake-id", "name":"fake-name"})


### -------------------------------------- _evaluate_download_mgr() ---------------------------------------

    @mock.patch("onedrive_offsite.workers.flood_kill_queue")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_evaluate_download_mgr_complete(self, mock_curr_thread, mock_flood):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"

        download_mgr = {"id1":{"name":"name1","retry":0, "status":"complete"}, "id2":{"name":"name2","retry":0, "status":"complete"}}
        kill_q = queue.Queue()
        error_q = queue.Queue()

        check_val = DownloadManager._evaluate_download_mgr(download_mgr, kill_q, error_q)
        self.assertIs(check_val, True)

    @mock.patch("onedrive_offsite.workers.write_to_error_q")
    @mock.patch("onedrive_offsite.workers.flood_kill_queue")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_evaluate_download_mgr_exceed_retry(self, mock_curr_thread, mock_flood, mock_write_err_q):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"

        download_mgr = {"id1":{"name":"name1","retry":0, "status":"complete"}, "id2":{"name":"name2","retry":3, "status":"error"}}
        kill_q = queue.Queue()
        error_q = queue.Queue()

        check_val = DownloadManager._evaluate_download_mgr(download_mgr, kill_q, error_q)
        self.assertIs(check_val, False)

    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_evaluate_download_mgr_not_done(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"

        download_mgr = {"id1":{"name":"name1","retry":0, "status":"complete"}, "id2":{"name":"name2","retry":1, "status":"error"}}
        kill_q = queue.Queue()
        error_q = queue.Queue()

        check_val = DownloadManager._evaluate_download_mgr(download_mgr, kill_q, error_q)
        self.assertIs(check_val, None)


### -------------------------------------- _create_download_dir() ---------------------------------------

    @mock.patch("onedrive_offsite.workers.Config")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_create_download_dir_dir_exists(self, mock_curr_thread, mock_config):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.os.path.isdir", return_value=True) as mock_isdir:

            kill_q = queue.Queue()
            error_q = queue.Queue()
            check_val = DownloadManager._create_download_dir(kill_q, error_q)
            self.assertIs(check_val, False)

    @mock.patch("onedrive_offsite.workers.Config")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_create_download_dir_no_dir_create_success(self, mock_curr_thread, mock_config):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.os.path.isdir", return_value=False) as mock_isdir:
            with mock.patch("onedrive_offsite.workers.os.mkdir", return_value=True) as mock_mkdir:

                kill_q = queue.Queue()
                error_q = queue.Queue()
                check_val = DownloadManager._create_download_dir(kill_q, error_q)
                self.assertIs(check_val, True)

    @mock.patch("onedrive_offsite.workers.write_to_error_q")
    @mock.patch("onedrive_offsite.workers.flood_kill_queue")
    @mock.patch("onedrive_offsite.workers.Config")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_create_download_dir_no_dir_create_except(self, mock_curr_thread, mock_config, mock_flood, mock_wr_to_err):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.os.path.isdir", return_value=False) as mock_isdir:
            with mock.patch("onedrive_offsite.workers.os.mkdir", side_effect=Exception("fake exception")) as mock_mkdir:

                kill_q = queue.Queue()
                error_q = queue.Queue()
                check_val = DownloadManager._create_download_dir(kill_q, error_q)
                self.assertIs(check_val, None)

### -------------------------------------- manage_downloads() ---------------------------------------

    @mock.patch("onedrive_offsite.workers.write_to_error_q")
    @mock.patch("onedrive_offsite.workers.flood_kill_queue")
    @mock.patch("onedrive_offsite.workers.DownloadManager._create_download_dir")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_manage_downloads_no_download_list(self, mock_curr_thread, mock_cr_dl_dir, mock_flood, mock_wr_err):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.DownloadManager._get_download_list", return_value=None) as mock_get_dl_list:
            to_download_q = queue.Queue()
            download_attempted_q = queue.Queue()
            kill_q = queue.Queue()
            error_q = queue.Queue()

            check_val = DownloadManager.manage_downloads(to_download_q, download_attempted_q, kill_q, error_q)
            self.assertIs(check_val, None)


    @mock.patch("onedrive_offsite.workers.write_to_error_q")
    @mock.patch("onedrive_offsite.workers.flood_kill_queue")
    @mock.patch("onedrive_offsite.workers.DownloadManager._create_download_dir")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_manage_downloads_fail_to_prime_q(self, mock_curr_thread, mock_cr_dl_dir, mock_flood, mock_wr_err):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.DownloadManager._get_download_list", return_value=[{"id":"id1","name":"name1"},{"id":"id2","name":"name2"}]) as mock_get_dl_list:
            with mock.patch("onedrive_offsite.workers.DownloadManager._prime_to_download_q", return_value=None) as mock_prime_dl_q:
                to_download_q = mock.Mock()
                download_attempted_q = mock.Mock()
                kill_q = mock.Mock()
                error_q = mock.Mock()

                check_val = DownloadManager.manage_downloads(to_download_q, download_attempted_q, kill_q, error_q)
                self.assertIs(check_val, None)


    @mock.patch("onedrive_offsite.workers.write_to_error_q")
    @mock.patch("onedrive_offsite.workers.DownloadManager._create_download_dir")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_manage_downloads_kill_not_empty(self, mock_curr_thread, mock_cr_dl_dir, mock_wr_err):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.DownloadManager._get_download_list", return_value=[{"id":"id1","name":"name1"},{"id":"id2","name":"name2"}]) as mock_get_dl_list:
            with mock.patch("onedrive_offsite.workers.DownloadManager._prime_to_download_q", return_value={"id1":{"name":"name1","retry":0, "status":"not started"}, "id2":{"name":"name2","retry":0, "status":"not started"}}) as mock_prime_dl_q:
                with mock.patch("onedrive_offsite.workers.datetime") as mock_datetime:
                    mock_datetime.now.return_value = datetime.datetime(2022, 3, 30, 0, 0)

                    to_download_q = mock.Mock()
                    download_attempted_q = mock.Mock()
                    kill_q = mock.Mock()
                    kill_q.empty.return_value = False
                    error_q = mock.Mock()

                    check_val = DownloadManager.manage_downloads(to_download_q, download_attempted_q, kill_q, error_q)
                    self.assertIs(check_val, False)


    @mock.patch("onedrive_offsite.workers.DownloadManager._create_download_dir")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_manage_downloads_to_download_empty_too_long(self, mock_curr_thread, mock_cr_dl_dir):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.DownloadManager._get_download_list", return_value=[{"id":"id1","name":"name1"},{"id":"id2","name":"name2"}]) as mock_get_dl_list:
            with mock.patch("onedrive_offsite.workers.DownloadManager._prime_to_download_q", return_value={"id1":{"name":"name1","retry":0, "status":"not started"}, "id2":{"name":"name2","retry":0, "status":"not started"}}) as mock_prime_dl_q:
                with mock.patch("onedrive_offsite.workers.datetime") as mock_datetime:
                    mock_datetime.now.return_value = datetime.datetime(2022, 3, 30, 0, 0)
                    with mock.patch("onedrive_offsite.workers._empty_check", return_value=False) as mock_empty_check:

                        to_download_q = mock.Mock()
                        download_attempted_q = mock.Mock()
                        download_attempted_q.get_nowait.side_effect = queue.Empty
                        kill_q = mock.Mock()
                        kill_q.empty.return_value = True
                        error_q = mock.Mock()

                        check_val = DownloadManager.manage_downloads(to_download_q, download_attempted_q, kill_q, error_q)
                        self.assertIs(check_val, False)

    @mock.patch("onedrive_offsite.workers.DownloadManager._create_download_dir")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_manage_downloads_fail_put_back_on_q(self, mock_curr_thread, mock_cr_dl_dir):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.DownloadManager._get_download_list", return_value=[{"id":"id1","name":"name1"},{"id":"id2","name":"name2"}]) as mock_get_dl_list:
            with mock.patch("onedrive_offsite.workers.DownloadManager._prime_to_download_q", return_value={"id1":{"name":"name1","retry":0, "status":"not started"}, "id2":{"name":"name2","retry":0, "status":"not started"}}) as mock_prime_dl_q:
                with mock.patch("onedrive_offsite.workers.datetime") as mock_datetime:
                    mock_datetime.now.return_value = datetime.datetime(2022, 3, 30, 0, 0)
                    with mock.patch("onedrive_offsite.workers.DownloadManager._put_file_back_on_q", return_value=None) as mock_put_back:

                        to_download_q = mock.Mock()
                        download_attempted_q = mock.Mock()
                        download_attempted_q.get_nowait = mock.PropertyMock(return_value = {"id":"id1","name":"name1","status":"error"})
                        kill_q = mock.Mock()
                        kill_q.empty.return_value = True
                        error_q = queue.Queue()

                        check_val = DownloadManager.manage_downloads(to_download_q, download_attempted_q, kill_q, error_q)
                        self.assertIs(check_val, None)


    @mock.patch("onedrive_offsite.workers.DownloadManager._create_download_dir")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_manage_downloads_complete(self, mock_curr_thread, mock_cr_dl_dir):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.DownloadManager._get_download_list", return_value=[{"id":"id1","name":"name1"},{"id":"id2","name":"name2"}]) as mock_get_dl_list:
            with mock.patch("onedrive_offsite.workers.DownloadManager._prime_to_download_q", return_value={"id1":{"name":"name1","retry":0, "status":"not started"}, "id2":{"name":"name2","retry":0, "status":"not started"}}) as mock_prime_dl_q:
                with mock.patch("onedrive_offsite.workers.datetime") as mock_datetime:
                    mock_datetime.now.return_value = datetime.datetime(2022, 3, 30, 0, 0)
                    with mock.patch("onedrive_offsite.workers.DownloadManager._evaluate_download_mgr", return_value=True) as mock_put_back:

                        to_download_q = mock.Mock()
                        download_attempted_q = mock.Mock()
                        download_attempted_q.get_nowait = mock.PropertyMock(return_value = {"id":"id1","name":"name1","status":"complete"})
                        kill_q = mock.Mock()
                        kill_q.empty.return_value = True
                        error_q = queue.Queue()

                        check_val = DownloadManager.manage_downloads(to_download_q, download_attempted_q, kill_q, error_q)
                        self.assertIs(check_val, True)



class TestDownloadWorker(unittest.TestCase):

### -------------------------------------- _publish_to_attempted_q() ---------------------------------------
    @mock.patch("onedrive_offsite.workers.flood_kill_queue")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_publish_to_attempted_q_put_except(self, mock_curr_thread, mock_flood):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"

        q_msg = {"id":"id1","name":"name1", "status":"complete"}
        kill_q = mock.Mock()
        download_attempted_q = mock.Mock()
        download_attempted_q.put.side_effect = Exception("fake exception")

        check_val = DownloadWorker._publish_to_attempted_q(q_msg, download_attempted_q, kill_q)
        self.assertIs(check_val, False)

    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_publish_to_attempted_q_put_success(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"

        q_msg = {"id":"id1","name":"name1", "status":"complete"}
        kill_q = mock.Mock()
        download_attempted_q = mock.Mock()
        check_val = DownloadWorker._publish_to_attempted_q(q_msg, download_attempted_q, kill_q)
        self.assertIs(check_val, True)

### -------------------------------------- _check_token_read() ---------------------------------------
    
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_check_token_read_success(self, mock_curr_thread):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"

        msgcm = mock.Mock()
        msgcm.read_tokens.return_value = True
        
        kill_q = mock.Mock()
        download_attempted_q = mock.Mock()
        id = "id1"
        name = "name1"

        check_val = DownloadWorker._check_token_read(msgcm, download_attempted_q, kill_q, name, id)
        self.assertIs(check_val, True)

    @mock.patch("onedrive_offsite.workers.DownloadWorker._publish_to_attempted_q")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_check_token_read_fail(self, mock_curr_thread, mock_pub_att_q):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"

        msgcm = mock.Mock()
        msgcm.read_tokens.return_value = False
        
        kill_q = mock.Mock()
        download_attempted_q = mock.Mock()
        id = "id1"
        name = "name1"

        check_val = DownloadWorker._check_token_read(msgcm, download_attempted_q, kill_q, name, id)
        self.assertIs(check_val, False)


### -------------------------------------- _remove_failed_download() ---------------------------------------

    @mock.patch("onedrive_offsite.workers.os.path.join")
    @mock.patch("onedrive_offsite.workers.Config")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_remove_failed_download_no_file(self, mock_curr_thread, mock_config, mock_join):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.os.path.isfile", return_value=False) as mock_isfile:
        
            kill_q = mock.Mock()
            error_q = mock.Mock()
            file_name = "fake-file-name"

            check_val = DownloadWorker._remove_failed_download(file_name, kill_q, error_q)
            self.assertIs(check_val, True)

    @mock.patch("onedrive_offsite.workers.os.path.join")
    @mock.patch("onedrive_offsite.workers.Config")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_remove_failed_download_file_removed(self, mock_curr_thread, mock_config, mock_join):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.os.path.isfile", return_value=True) as mock_isfile:
            with mock.patch("onedrive_offsite.workers.os.remove", return_value=True) as mock_rm:
        
                kill_q = mock.Mock()
                error_q = mock.Mock()
                file_name = "fake-file-name"

                check_val = DownloadWorker._remove_failed_download(file_name, kill_q, error_q)
                self.assertIs(check_val, True)

    @mock.patch("onedrive_offsite.workers.write_to_error_q")
    @mock.patch("onedrive_offsite.workers.flood_kill_queue")
    @mock.patch("onedrive_offsite.workers.os.path.join")
    @mock.patch("onedrive_offsite.workers.Config")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_remove_failed_download_file_remove_except(self, mock_curr_thread, mock_config, mock_join, mock_flood, mock_wr_err):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.os.path.isfile", return_value=True) as mock_isfile:
            with mock.patch("onedrive_offsite.workers.os.remove", side_effect=Exception("fake exception")) as mock_rm:
        
                kill_q = mock.Mock()
                error_q = mock.Mock()
                file_name = "fake-file-name"

                check_val = DownloadWorker._remove_failed_download(file_name, kill_q, error_q)
                self.assertIs(check_val, None)


### -------------------------------------- download_worker() ---------------------------------------

    @mock.patch("onedrive_offsite.workers.flood_kill_queue")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_download_worker_kill_q_empty(self, mock_curr_thread, mock_flood):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime.datetime(2022, 3, 30, 0, 0)

            kill_q = mock.Mock()
            kill_q.empty.return_value = False
            kill_q.get_nowait.return_value = "kill"

            to_download_q = mock.Mock()
            to_download_q.get_nowait.return_value = {"id":"id1","name":"name1"}
            download_attempted_q = mock.Mock()
            error_q = mock.Mock()

            check_val = DownloadWorker.download_worker(to_download_q, download_attempted_q, kill_q, error_q)
            self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.workers.flood_kill_queue")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_download_worker_download_success(self, mock_curr_thread, mock_flood):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime.datetime(2022, 3, 30, 0, 0)
            with mock.patch("onedrive_offsite.workers.MSGraphCredMgr") as mock_msgcm:
                mock_msgcm.access_token = "faketoken"
                with mock.patch("onedrive_offsite.workers.DownloadWorker._check_token_read", return_value=True) as mock_chk_tok_rd:
                    with mock.patch("onedrive_offsite.workers.OneDriveGetItemDetails.get_details") as mock_odgid:
                        with mock.patch("onedrive_offsite.workers.OneDriveFileDownloadMgr") as mock_odfdm:
                            mock_odfdm.return_value.download_file.return_value = True
                            with mock.patch("onedrive_offsite.workers.DownloadWorker._publish_to_attempted_q") as mock_pub_to_att_q:

                                kill_q = mock.Mock()
                                kill_q.empty.side_effect = [True, False]
                                kill_q.get_nowait.return_value = "kill"

                                to_download_q = mock.Mock()
                                to_download_q.get_nowait.return_value = {"id":"id1","name":"name1"}
                                download_attempted_q = mock.Mock()
                                error_q = mock.Mock()

                                check_val = DownloadWorker.download_worker(to_download_q, download_attempted_q, kill_q, error_q)
                                self.assertIs(check_val, None)


    @mock.patch("onedrive_offsite.workers.flood_kill_queue")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_download_worker_fail_download(self, mock_curr_thread, mock_flood):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime.datetime(2022, 3, 30, 0, 0)
            with mock.patch("onedrive_offsite.workers.MSGraphCredMgr") as mock_msgcm:
                mock_msgcm.access_token = "faketoken"
                with mock.patch("onedrive_offsite.workers.DownloadWorker._check_token_read", return_value=True) as mock_chk_tok_rd:
                    with mock.patch("onedrive_offsite.workers.OneDriveGetItemDetails.get_details") as mock_odgid:
                        with mock.patch("onedrive_offsite.workers.OneDriveFileDownloadMgr") as mock_odfdm:
                            mock_odfdm.return_value.download_file.return_value = False
                            with mock.patch("onedrive_offsite.workers.DownloadWorker._remove_failed_download") as mock_rm_failed_dl:
                                with mock.patch("onedrive_offsite.workers.DownloadWorker._publish_to_attempted_q") as mock_pub_to_att_q:

                                    kill_q = mock.Mock()
                                    kill_q.empty.side_effect = [True, False]
                                    kill_q.get_nowait.return_value = "kill"

                                    to_download_q = mock.Mock()
                                    to_download_q.get_nowait.return_value = {"id":"id1","name":"name1"}
                                    download_attempted_q = mock.Mock()
                                    error_q = mock.Mock()

                                    check_val = DownloadWorker.download_worker(to_download_q, download_attempted_q, kill_q, error_q)
                                    self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.workers.sleep", return_value=None)
    @mock.patch("onedrive_offsite.workers.flood_kill_queue")
    @mock.patch("onedrive_offsite.workers.threading.current_thread")
    def test_unit_download_worker_to_download_emtpy_too_long(self, mock_curr_thread, mock_flood, mock_sleep):
        mock_curr_thread.return_value.getName.return_value = "fake-thread"
        with mock.patch("onedrive_offsite.workers.datetime") as mock_datetime:
            mock_datetime.now.side_effect = [datetime.datetime(2022, 3, 30, 0, 0), datetime.datetime(2022, 3, 30, 0, 0), datetime.datetime(2022, 3, 30, 1, 0), datetime.datetime(2022, 3, 30, 0, 0), datetime.datetime(2022, 3, 30, 2, 1)]

            kill_q = mock.Mock()
            kill_q.empty.side_effect = [True, True, False]
            kill_q.get_nowait.side_effect = queue.Empty

            to_download_q = mock.Mock()
            to_download_q.get_nowait.side_effect = queue.Empty
            download_attempted_q = mock.Mock()
            error_q = mock.Mock()

            check_val = DownloadWorker.download_worker(to_download_q, download_attempted_q, kill_q, error_q)
            self.assertIs(check_val, None)


### -------------------------------------- DownloadDecrypter ---------------------------------------
class TestDownloadDecrypter(unittest.TestCase):

    ### -------------------------------------- _get_downloaded_gz_files() ---------------------------------------
    def test_unit_get_download_gz_files_listdir_except(self):
        with mock.patch("onedrive_offsite.workers.os.listdir", side_effect=Exception("fake exception")) as mock_listdir:
            check_val = DownloadDecrypter._get_downloaded_gz_files()
            self.assertIs(check_val, None)

    def test_unit_get_download_gz_files_empty_file_list(self):
        with mock.patch("onedrive_offsite.workers.os.listdir", return_value=[]) as mock_listdir:
            check_val = DownloadDecrypter._get_downloaded_gz_files()
            self.assertIs(check_val, None)

    def test_unit_get_download_gz_files_return_list(self):
        with mock.patch("onedrive_offsite.workers.os.listdir", return_value=["file1","file2"]) as mock_listdir:
            check_val = DownloadDecrypter._get_downloaded_gz_files()
            self.assertEqual(check_val, ["file1","file2"])

    ### -------------------------------------- _extract_tar_gzs() ---------------------------------------
    def test_unit_extract_tar_gzs_extract_fail(self):
        with mock.patch("onedrive_offsite.workers.os.path.join") as mock_join:
            with mock.patch("onedrive_offsite.workers.extract_tar_gz", return_value=None) as mock_extract_tar_gz:
                file_list = ["file1","file2"]
                check_val = DownloadDecrypter._extract_tar_gzs(file_list)
                self.assertIs(check_val, None)
                self.assertEqual(mock_join.call_count, 1)

    def test_unit_extract_tar_gzs_extract_succeed(self):
        with mock.patch("onedrive_offsite.workers.os.path.join") as mock_join:
            with mock.patch("onedrive_offsite.workers.extract_tar_gz", return_value=True) as mock_extract_tar_gz:
                file_list = ["file1","file2"]
                check_val = DownloadDecrypter._extract_tar_gzs(file_list)
                self.assertIs(check_val, True)
                self.assertEqual(mock_join.call_count, 2)

### -------------------------------------- _decrypt() ---------------------------------------
    def test_unit_decrypt_no_json(self):
        with mock.patch("onedrive_offsite.workers.DownloadManager._get_download_info", return_value=None) as mock_get_dl_info:
            check_val = DownloadDecrypter._decrypt()
            self.assertIs(check_val, None)

    def test_unit_decrypt_no_onedrive_dir(self):
        with mock.patch("onedrive_offsite.workers.DownloadManager._get_download_info", return_value={"start-date-time": "2022-05-01-10:33:01", "dir": "fake-dir"}) as mock_get_dl_info:
            check_val = DownloadDecrypter._decrypt()
            self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.workers.os.path.join")
    @mock.patch("onedrive_offsite.workers.Config")
    def test_unit_decrypt_chunk_decrypt_fail(self, mock_config, mock_join):
        with mock.patch("onedrive_offsite.workers.DownloadManager._get_download_info", return_value={"start-date-time": "2022-05-01-10:33:01", "onedrive-dir": "fake-dir"}) as mock_get_dl_info:
            with mock.patch("onedrive_offsite.workers.Crypt") as mock_crypt:
                mock_crypt.return_value.chunk_decrypt.return_value = None
                check_val = DownloadDecrypter._decrypt()
                self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.workers.os.path.join")
    @mock.patch("onedrive_offsite.workers.Config")
    def test_unit_decrypt_chunk_decrypt_succeed(self, mock_config, mock_join):
        with mock.patch("onedrive_offsite.workers.DownloadManager._get_download_info", return_value={"start-date-time": "2022-05-01-10:33:01", "onedrive-dir": "fake-dir"}) as mock_get_dl_info:
            with mock.patch("onedrive_offsite.workers.Crypt") as mock_crypt:
                mock_crypt.return_value.chunk_decrypt.return_value = True
                check_val = DownloadDecrypter._decrypt()
                self.assertIs(check_val, True)

### -------------------------------------- _fetch_hash() ---------------------------------------
    @mock.patch("onedrive_offsite.workers.Config")
    def test_unit_fetch_hash_except(self, mock_config):
        with mock.patch("onedrive_offsite.workers.open", side_effect=Exception("fake exception")) as mock_open:
            check_val = DownloadDecrypter._fetch_hash("fake-dir")
            self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.workers.Config")
    def test_unit_fetch_hash_works(self, mock_config):
        with mock.patch("onedrive_offsite.workers.open", new_callable=mock.mock_open, read_data="fake-hash") as mock_open:
            check_val = DownloadDecrypter._fetch_hash("fake-dir")
            self.assertEqual(check_val, "fake-hash")

### -------------------------------------- _verify_hash() ---------------------------------------
    @mock.patch("onedrive_offsite.workers.Config")
    def test_unit_verfy_hash_open_except(self, mock_config):
        with mock.patch("onedrive_offsite.workers.open", side_effect=Exception("fake exception")) as mock_open:
            check_val = DownloadDecrypter._verify_hash()
            self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.workers.Config")
    def test_unit_verfy_hash_fetch_hash_fail(self, mock_config):
        with mock.patch("onedrive_offsite.workers.open") as mock_open:
            with mock.patch("onedrive_offsite.workers.json.load", return_value={"onedrive-dir":"fake-dir"}) as mock_json_load:
                with mock.patch("onedrive_offsite.workers.DownloadDecrypter._fetch_hash", return_value=None) as mock_fetch_hash:
                    check_val = DownloadDecrypter._verify_hash()
                    self.assertIs(check_val, None)
    
    @mock.patch("onedrive_offsite.workers.Config")
    def test_unit_verify_hash_download_hash_calc_fail(self, mock_config):
        with mock.patch("onedrive_offsite.workers.open") as mock_open:
            with mock.patch("onedrive_offsite.workers.json.load", return_value={"onedrive-dir":"fake-dir"}) as mock_json_load:
                with mock.patch("onedrive_offsite.workers.DownloadDecrypter._fetch_hash", return_value="fake-hash") as mock_fetch_hash:
                    with mock.patch("onedrive_offsite.workers.Sha256Calc") as mock_sha256calc:
                        mock_sha256calc.return_value.calc.return_value = None
                        check_val = DownloadDecrypter._verify_hash()
                        self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.workers.Config")
    def test_unit_verify_hash_download_hash_doesnt_match(self, mock_config):
        with mock.patch("onedrive_offsite.workers.open") as mock_open:
            with mock.patch("onedrive_offsite.workers.json.load", return_value={"onedrive-dir":"fake-dir"}) as mock_json_load:
                with mock.patch("onedrive_offsite.workers.DownloadDecrypter._fetch_hash", return_value="fake-hash") as mock_fetch_hash:
                    with mock.patch("onedrive_offsite.workers.Sha256Calc") as mock_sha256calc:
                        mock_sha256calc.return_value.calc.return_value = "hash-doesnt-match"
                        check_val = DownloadDecrypter._verify_hash()
                        self.assertIs(check_val, None)

    @mock.patch("onedrive_offsite.workers.Config")
    def test_unit_verify_hash_download_hash_matches(self, mock_config):
        with mock.patch("onedrive_offsite.workers.open") as mock_open:
            with mock.patch("onedrive_offsite.workers.json.load", return_value={"onedrive-dir":"fake-dir"}) as mock_json_load:
                with mock.patch("onedrive_offsite.workers.DownloadDecrypter._fetch_hash", return_value="fake-hash") as mock_fetch_hash:
                    with mock.patch("onedrive_offsite.workers.Sha256Calc") as mock_sha256calc:
                        mock_sha256calc.return_value.calc.return_value = "fake-hash"
                        check_val = DownloadDecrypter._verify_hash()
                        self.assertIs(check_val, True)


### -------------------------------------- decrypt_and_combine() ---------------------------------------

    def test_unit_decrypt_and_combine_no_downloaded_files(self):
        with mock.patch("onedrive_offsite.workers.DownloadDecrypter._get_downloaded_gz_files", return_value=[]) as mock_get_dl_files:
            check_val = DownloadDecrypter.decrypt_and_combine()
            self.assertIs(check_val, None)

    def test_unit_decrypt_and_combine_extract_fails(self):
        with mock.patch("onedrive_offsite.workers.DownloadDecrypter._get_downloaded_gz_files", return_value=["file1", "file2"]) as mock_get_dl_files:
            with mock.patch("onedrive_offsite.workers.DownloadDecrypter._extract_tar_gzs", return_value=None) as mock_extract:
                check_val = DownloadDecrypter.decrypt_and_combine()
                self.assertIs(check_val, None)

    def test_unit_decrypt_and_combine_decrypt_success_hash_verified(self):
        with mock.patch("onedrive_offsite.workers.DownloadDecrypter._get_downloaded_gz_files", return_value=["file1", "file2"]) as mock_get_dl_files:
            with mock.patch("onedrive_offsite.workers.DownloadDecrypter._extract_tar_gzs", return_value=True) as mock_extract:
                with mock.patch("onedrive_offsite.workers.DownloadDecrypter._decrypt", return_value=True) as mock_decrypt:
                    with mock.patch("onedrive_offsite.workers.DownloadDecrypter._verify_hash", return_value=True) as mock_verify_hash:
                        check_val = DownloadDecrypter.decrypt_and_combine()
                        self.assertIs(check_val, True)

    def test_unit_decrypt_and_combine_decrypt_success_hash_fail(self):
        with mock.patch("onedrive_offsite.workers.DownloadDecrypter._get_downloaded_gz_files", return_value=["file1", "file2"]) as mock_get_dl_files:
            with mock.patch("onedrive_offsite.workers.DownloadDecrypter._extract_tar_gzs", return_value=True) as mock_extract:
                with mock.patch("onedrive_offsite.workers.DownloadDecrypter._decrypt", return_value=True) as mock_decrypt:
                    with mock.patch("onedrive_offsite.workers.DownloadDecrypter._verify_hash", return_value=False) as mock_verify_hash:
                        check_val = DownloadDecrypter.decrypt_and_combine()
                        self.assertIs(check_val, None)

    def test_unit_decrypt_and_combine_decrypt_fail(self):
        with mock.patch("onedrive_offsite.workers.DownloadDecrypter._get_downloaded_gz_files", return_value=["file1", "file2"]) as mock_get_dl_files:
            with mock.patch("onedrive_offsite.workers.DownloadDecrypter._extract_tar_gzs", return_value=True) as mock_extract:
                with mock.patch("onedrive_offsite.workers.DownloadDecrypter._decrypt", return_value=False) as mock_decrypt:
                    check_val = DownloadDecrypter.decrypt_and_combine()
                    self.assertIs(check_val, None)