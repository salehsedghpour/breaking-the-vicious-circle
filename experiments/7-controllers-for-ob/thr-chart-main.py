import pandas as pd
from experiments.libs import functions, prom_client
import matplotlib.pyplot as plt
import matplotlib as mpl

df = pd.read_csv(functions.get_project_root()+'/logs/exp-7-1-main-3-ver.csv')
data = df.loc[(df['traffic'] == 40)]

"""
        retry mechanism         cb
1-      default                 default
2-      controller              default
3-      default                 controller
4-      controller              controller

"""


# fig, axs = plt.subplots(nrows=4, ncols=3, figsize=(8, 8), sharex=True,dpi=300)
challenging_services = ["frontend"]
for index, row in data.iterrows():
    for service in challenging_services:
        prom_inst = prom_client.PromQuery()
        prom_inst.prom_host = "labumu.se"
        prom_inst.start = int(row['start'])
        prom_inst.end = int(row['end'])
        prom_inst.response_code = "200"
        prom_inst.namespace = "default"
        prom_inst.percentile = "0.95"
        prom_inst.warmup = 0
        prom_inst.warmdown = 0
        prom_inst.service = service
        status_code_prom_data = prom_inst.get_status_codes()
        success = {
            "data": [],
            "timestamp": [],
        }
        failed = {
            "data": [],
            "timestamp": []
        }
        circuit_broken = {
            "data": [],
            "timestamp": [],
        }


        for item in status_code_prom_data:

            if item['metric']['response_code'] == "200" and item['metric']['response_flags'] == "-":
                for val in item['values']:
                    success["data"].append(float(val[1]))
                    success["timestamp"].append(float(val[0]) - item['values'][0][0])
            elif item['metric']['response_flags'] == "UO":
                for val in item['values']:
                    circuit_broken["data"].append(float(val[1]))
                    circuit_broken["timestamp"].append(float(val[0]) - item['values'][0][0])
            elif item['metric']['response_flags'] != "UO":
                for val in item['values']:
                    cur_val = (float(val[0]) - float(item['values'][0][0]))
                    if cur_val in failed["timestamp"]:
                        failed['data'][failed['timestamp'].index(cur_val)] = failed['data'][failed['timestamp'].index(
                            cur_val)] + float(val[1])
                    else:
                        failed["data"].append(float(val[1]))
                        failed["timestamp"].append(float(val[0]) - float(item['values'][0][0]))
        response_time_prom_data = prom_inst.get_response_time()
        response_time = {
            "data": [],
            "timestamp": []
        }
        if len(response_time_prom_data) > 0:
            for item in response_time_prom_data[0]['values']:
                response_time['data'].append(float(item[1]) * 1000)
                response_time['timestamp'].append(int(item[0]))
        
        if row['cb_controller'] == 0:
            cb_print = "Default CB"
        else:
            cb_print = "Adatpive CB"
        
        if row['retry_controller'] == 1:
            retry_print = "Adaptive Retry"
        else:
            retry_print = "Static Retry with "+str(row['retry_attempt']) + ' attempts and ' +str(row['retry_interval']) + " interval"
        
        throughput = int(sum(success['data']))
        failed = int(sum(failed['data']))
        avg_rt_list = []
        import math
        for i in response_time['data']:
            if not math.isnan(i):
                avg_rt_list.append(i)
        if len(avg_rt_list) != 0:
            avg_rt = sum(avg_rt_list)/ len(avg_rt_list)
        else:
            avg_rt = 0
        str_out = cb_print + " and " + retry_print + ": Succesful requests=" + str(throughput) +", Failed requests=" + str(failed) + ", Avg. Carried Resposne time="+ str(avg_rt) 
        # print(row)
        print(str_out)
        # print("---------")