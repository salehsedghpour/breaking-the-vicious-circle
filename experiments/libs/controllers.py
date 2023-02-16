class CB_Controller:
    def __init__(self):
        self.p = 0.95
        self.trgt_rsp_time_95 = 50
        self.cur_rsp_time_95 = 50
        self.cur_que_len = 1024
        self.not_smth_alpha = 1
        self.smth_alpha = 1
        self.cb_thrsh = 1024

    def exec(self):
        self.not_smth_alpha = (self.cur_rsp_time_95/max(self.cur_que_len, 1))
        self.smth_alpha = (self.p * self.smth_alpha) + (1-self.p) * self.not_smth_alpha
        self.cb_thrsh = int(self.trgt_rsp_time_95 / self.smth_alpha)
        if self.cb_thrsh < 0:
            self.cb_thrsh = self.cur_que_len / 2
        if int(self.cb_thrsh) == 0:
            self.cb_thrsh = 1
        if int(self.cb_thrsh) >= 2147483646: # max number in int32
            self.cb_thrsh = 2147483646
        return self.cb_thrsh



class Immediate_Backoff_Controller:
    def __init__(self) -> None:
        self.step = 3
        self.failed_requests = []
        self.retry_attempt = 1
    def detect_increase(self):
        if self.failed_requests[2]> 0:
            # if self.failed_requests[2] != 0:
            #     print(self.failed_requests)
            #     return True
            # else:
            #     return False
            return True
        else:
            return False
            
    def specify_retry_threshold(self):
        if len(self.failed_requests) == 3:
            is_increased = self.detect_increase()
            if is_increased:
                self.failed_requests = []
                self.retry_attempt = 1
            else:
                self.failed_requests = []
                self.retry_attempt = 5
        else:
            print("the length is less than 3")
        



class Retry_Controller:
    # in this formulation I didn't consider the failed request. Maybe we should consider
    # failed ones and then based on them, check the RT and if RT was ok then increase the number of retries 
    # if not, decrease it.
    def __init__(self):
        self.p = 0.95
        self.trgt_rsp_time_95 = 50
        self.cur_rsp_time_95 = 50
        self.cur_que_len = 1024
        self.not_smth_alpha = 1
        self.smth_alpha = 1
        self.retry_thrsh = 2

    def exec(self):
        self.not_smth_alpha = (self.cur_rsp_time_95/max(self.retry_thrsh, 1))
        self.smth_alpha = (self.p * self.smth_alpha) + (1-self.p) * self.not_smth_alpha
        self.retry_thrsh = int(self.trgt_rsp_time_95 / self.smth_alpha)
        if self.retry_thrsh < 0:
            self.retry_thrsh = self.cur_que_len / 2
        if int(self.retry_thrsh) == 0:
            self.retry_thrsh = 1
        if int(self.retry_thrsh) >= 2147483646: # max number in int32
            self.retry_thrsh = 2147483646
        return self.retry_thrsh
