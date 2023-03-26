import pandas as pd
import matplotlib.pyplot as plt
from experiments.libs import functions, prom_client

df = pd.read_csv(functions.get_project_root()+'/logs/exp-5-1-static-cb-retry-3-rep.csv')

data_no_config = df.loc[(df['traffic'] == 40) & (df['cb_v1'] == 1000) & (df['cv_v2'] == 1000) & (df['cv_v3'] == 1000) & (df['retry']==2) & (df['interval']=="25ms")].reset_index()

data_limited_cb_high_retry_short_interval = df.loc[(df['traffic'] == 40) & (df['cb_v1'] == 1) & (df['cv_v2'] == 1000) & (df['cv_v3'] == 1000) & (df['retry']==5) & (df['interval']=="1ms")].reset_index()

data_limited_cb_high_retry_long_interval= df.loc[(df['traffic'] == 40) & (df['cb_v1'] == 1) & (df['cv_v2'] == 1000) & (df['cv_v3'] == 1000) & (df['retry']==5) & (df['interval']=="50ms")].reset_index()
def clean_prom_status_codes(status_code_prom_data):
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
    
    return success, failed, circuit_broken


time_stamps = [
    {
        "case": 'Default Configuration',
        "start": data_no_config.loc[0]['start'],
        "end": data_no_config.loc[0]['end']
    },
    {
        "case": 'A possible misconfiguration',
        "start": data_limited_cb_high_retry_short_interval.loc[0]['start'],
        "end": data_limited_cb_high_retry_short_interval.loc[0]['end']
    },
    #     {
    #     "case": 'Sensitive CB - High retry attempts with long intervals',
    #     "start": data_limited_cb_high_retry_long_interval.loc[0]['start'],
    #     "end": data_limited_cb_high_retry_long_interval.loc[0]['end']
    # },

]
fig, axs = plt.subplots(nrows=1, ncols=1, figsize=(7, 4),dpi=300)


challenging_services = ["frontend"]

for timestamp in time_stamps:
    prom_inst = prom_client.PromQuery()
    prom_inst.prom_host = "labumu.se"
    prom_inst.start = int(timestamp['start'])
    prom_inst.end = int(timestamp['end'])
    prom_inst.namespace = "default"
    prom_inst.warmup = 0
    prom_inst.warmdown = 0
    prom_inst.service = challenging_services[0]
    status_code = prom_inst.get_status_codes()
    success, failed, cb = clean_prom_status_codes(status_code)

    ratio = []
    for i in range(len(success['data'])):
        ratio.append(int(100*success['data'][i]/(success['data'][i]+failed['data'][i])))
    axs.plot( success['timestamp'], ratio, label=timestamp['case'],alpha=0.8)    
#     axs.plot(response_time_ar['data'],response_time_ar['timestamp'], label=timestamp['case']+'- FR', alpha=0.5, linestyle="dotted")
#     axs.plot(response_time_cr['data'],response_time_cr['timestamp'], label=timestamp['case']+'- CR', alpha=0.5, linestyle="dashed")

#     axs.set_yticks([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1], minor=False)
#     axs.set_yticks([0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95], minor=True)
    axs.set_ylim(ymin=0, ymax=100)
    axs.set_xlim(xmin=0, xmax=60)

    axs.legend()
#     axs.xaxis.grid(True, which='minor')
#     axs.xaxis.grid(True, which='major')
#     axs.yaxis.grid(True, which='major')
#     axs.yaxis.grid(True, which='minor')
    axs.set_ylabel("Carried Throughput Ratio (%)")
    axs.yaxis.set_major_formatter('{x:1.0f}%')
    axs.set_xlabel("Time (s)")

plt.tight_layout()
# plt.show()

plt.savefig(functions.get_project_root()+'/experiments/8-paper-experiments/figure-2-a.pdf',format='pdf', bbox_inches='tight', pad_inches = 0.1)




