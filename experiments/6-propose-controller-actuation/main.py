
import matplotlib.pyplot as plt
import math



class retryController:
    def __init__(self):
        self.p = 0.9
        self.trgt_rsp_time_95 = 100
        self.cur_rsp_time_95 = 50
        self.curr_failed = 0
        self.curr_cb = 0
        self.not_smth_alpha = 1
        self.smth_alpha = 1
        self.retry_attempt = 2
        self.retry_interval = 25
        self.max_retry_attmept = self.trgt_rsp_time_95
        self.cwnd = 1


    def exec(self):
        self.cwnd = max(1, self.cwnd)
        not_responded = self.curr_failed + self.curr_cb
        # if :
        #     self.cwnd = max(1, self.cwnd // 2)
        # else:
        #     self.cwnd = max(1, self.cwnd + 1)
        if self.cur_rsp_time_95 > self.trgt_rsp_time_95 or not_responded > 0:
            self.retry_attempt = max(int(self.retry_attempt/2), 1)
            self.retry_interval = max(int(self.trgt_rsp_time_95/self.retry_attempt),1)
        else:
            self.retry_attempt += 1
            self.retry_interval = max(int(self.trgt_rsp_time_95/self.retry_attempt),1)
        
            
            
       

        # self.not_smth_alpha =  self.cur_rsp_time_95/self.retry_interval
        # self.smth_alpha = (self.p * self.smth_alpha) + (1-self.p) * self.not_smth_alpha
        # self.retry_attempt = self.trgt_rsp_time_95 / self.smth_alpha
        # self.retry_interval = max(int(self.trgt_rsp_time_95/self.retry_attempt),1)
        print( self.retry_attempt , self.retry_interval)

        return self.retry_attempt, self.retry_interval




def test(resp, failed,cb):
    cont = retryController()
    retry_attempts = []
    retry_intervals = []
    for i in range(len(resp)):
        cont.curr_cb = cb[i]
        cont.cur_rsp_time_95 = resp[i]
        cont.curr_failed = failed[i]
        retry_attempt, retry_interval = cont.exec()
        retry_attempts.append(retry_attempt)
        retry_intervals.append(retry_interval)
    plt.plot(resp, label="RT")
    # plt.plot(failed, label="Failed")
    plt.plot(cb, label="CB")
    # plt.plot(retry_attempts, label="Attempt")
    # plt.plot(retry_intervals, label="Interval")
    plt.legend()
    plt.savefig("experiments/6-propose-controller-actuation/thr-lat.png")




resp_increased = [80, 85, 90, 95, 100, 100, 100, 105, 110, 150, 200]
resp_static = [80, 85, 90, 80, 85, 90, 80, 85, 90, 90]
resp_decreased = [80, 85, 90, 80, 85, 90, 80, 85, 90, 90]
resp_spike = []

failed_increased = [0, 0, 10, 15, 20, 20, 30, 40, 40, 50, 50]
failed_static = [0, 1, 2, 3, 1, 2, 1, 1,2,2 ]
failed_decreased = [50, 40, 10, 20, 3, 1, 0, 0, 0, 0]
failed_spike = []

cb_increased = []
cb_static = []
cb_decreased = []
cb_spike = []


resp = [80, 85, 90, 95, 100, 100, 100, 105, 110, 150, 200, 80, 85, 90, 95]
failed = [0, 0, 0, 0, 100, 10, 20, 20, 90, 150, 200, 10, 0, 0, 0]



test(resp=resp, failed=[0]*len(failed), cb=failed)







