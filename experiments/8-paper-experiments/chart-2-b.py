import pandas as pd
import matplotlib.pyplot as plt
from experiments.libs import functions, prom_client

df = pd.read_csv(functions.get_project_root()+'/logs/exp-5-1-static-cb-retry-3-rep.csv')

data_no_config = df.loc[(df['traffic'] == 40) & (df['cb_v1'] == 1000) & (df['cv_v2'] == 1000) & (df['cv_v3'] == 1000) & (df['retry']==2) & (df['interval']=="25ms")].reset_index()

data_limited_cb_high_retry_short_interval = df.loc[(df['traffic'] == 40) & (df['cb_v1'] == 1) & (df['cv_v2'] == 1000) & (df['cv_v3'] == 1000) & (df['retry']==5) & (df['interval']=="1ms")].reset_index()

data_limited_cb_high_retry_long_interval= df.loc[(df['traffic'] == 40) & (df['cb_v1'] == 1) & (df['cv_v2'] == 1000) & (df['cv_v3'] == 1000) & (df['retry']==5) & (df['interval']=="50ms")].reset_index()


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
    prom_inst.response_code="503"
    prom_data = {}
    for percentile in [x / 100 for x in range(0, 100, 1)]:
        prom_inst.percentile = percentile
        prom_data[str(percentile)] = []
        prom_data[str(percentile)] = prom_inst.get_response_time()
    response_time_ar = {
        "data": [],
        "timestamp": [],
        "bins": []
    }
    for item in prom_data:
        response_time_ar['timestamp'].append(float(item))
        ival_list = []
        for ival in prom_data[str(item)][0]['values']:
            ival_list.append(float(ival[1]))
        response_time_ar['data'].append(sum(ival_list) / len(ival_list))
    prom_data = {}
    prom_inst.response_code = "200"
    response_time_cr = {
        "data": [],
        "timestamp": [],
        "bins": []
    }

    for percentile in [x / 100 for x in range(0, 100, 1)]:
        prom_inst.percentile = percentile
        prom_data[str(percentile)] = []
        prom_data[str(percentile)] = prom_inst.get_response_time()
    for item in prom_data:
        response_time_cr['timestamp'].append(float(item))
        ival_list = []
        for ival in prom_data[str(item)][0]['values']:
            ival_list.append(float(ival[1]))
        response_time_cr['data'].append(sum(ival_list) / len(ival_list))
    prom_data = {}
    

    axs.plot(response_time_ar['data'],response_time_ar['timestamp'], label=timestamp['case']+'- FR', alpha=0.5, linestyle="dotted")
    axs.plot(response_time_cr['data'],response_time_cr['timestamp'], label=timestamp['case']+'- CR', alpha=0.5, linestyle="dashed")

    axs.set_yticks([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1], minor=False)
    axs.set_yticks([0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95], minor=True)
    axs.set_ylim(ymin=0, ymax=1.0)
    axs.set_xlim(xmin=0, xmax=0.45)

    axs.legend(loc="lower right", title="CB values:")
    axs.xaxis.grid(True, which='minor')
    axs.xaxis.grid(True, which='major')
    axs.yaxis.grid(True, which='major')
    axs.yaxis.grid(True, which='minor')
    axs.set_ylabel("Probability")
    axs.set_xlabel("Response Time (sec)")

plt.tight_layout()
# plt.show()

plt.savefig(functions.get_project_root()+'/experiments/8-paper-experiments/figure-2-b.pdf',format='pdf', bbox_inches='tight', pad_inches = 0.1)




