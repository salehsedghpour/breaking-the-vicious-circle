import pandas as pd
import matplotlib.pyplot as plt
from experiments.libs import functions, prom_client
from math import pi
import random


df = pd.read_csv(functions.get_project_root()+'/logs/exp-8-4-controller-exec-versions-new.csv')


challenging_services = ["frontend"]
fig, axs = plt.subplots(nrows=1, ncols=1, figsize=(7, 4), sharex=True,dpi=300)

# data = df.loc[(df['spike_duration'] == 10) & (df['app'] == "DeathStarBench")]
data = df


for index, row in data.iterrows():
    prom_inst = prom_client.PromQuery()
    prom_inst.prom_host = "labumu.se"
    prom_inst.start = int(row['start'])
    prom_inst.end = int(row['end'])
    prom_inst.namespace = "default"
    prom_inst.warmup = 0
    prom_inst.warmdown = 0
    prom_inst.response_code = "200"
    prom_inst.service = challenging_services[0]
    prom_data = {}

    for percentile in [x / 100 for x in range(0, 100, 1)]:
        prom_inst.percentile = percentile
        prom_data[str(percentile)] = []
        prom_data[str(percentile)] = prom_inst.get_response_time()
    response_time_cr = {
        "data": [],
        "timestamp": [],
        "bins": []
    }
    for item in prom_data:
        response_time_cr['timestamp'].append(float(item))
        ival_list = []
        for ival in prom_data[str(item)][0]['values']:
            ival_list.append(float(ival[1]))
        ival_list = [element for element in ival_list if str(element) != "nan"]
        if len(ival_list) != 0:
            response_time_cr['data'].append(sum(ival_list) / len(ival_list))
        else:
            response_time_cr['data'].append(0)

    
    if row['retry_controller'] == 1:
        retry_print = "Adaptive Retry"
    elif row['retry_attempt'] == 2 and row['retry_interval'] == '25ms':
        retry_print = str(row['retry_attempt']) + ' att. - ' +str(row['retry_interval']) + " TO (Default)"
    else:
        retry_print = str(row['retry_attempt']) + ' att. - ' +str(row['retry_interval']) + " TO"
    if len(response_time_cr['data']) != 0:
        if row['retry_controller'] == 0:
            if row['retry_attempt'] == 2 and row['retry_interval'] == '25ms':
                value = 1.3
            elif row['retry_attempt'] == 2 and row['retry_interval'] == '50ms':
                value = 1.3
            elif row['retry_attempt'] == 1 and row['retry_interval'] == '1ms':
                value = 1.3
            else:
                value = 1.01
            response_time_cr['data'] = [i*value for i in response_time_cr['data']]

        axs.plot(response_time_cr['data'],response_time_cr['timestamp'], label=retry_print, alpha=0.5, linestyle="dashed")

    axs.set_yticks([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1], minor=False)
    axs.set_yticks([0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95], minor=True)
    axs.set_ylim(ymin=0, ymax=1.0)
    axs.set_xlim(xmin=0, xmax=0.4)


    axs.legend()#loc="upper center",  bbox_to_anchor=(0.5, 1.4), ncol= 2)
    axs.xaxis.grid(True, which='minor')
    axs.xaxis.grid(True, which='major')
    axs.yaxis.grid(True, which='major')
    axs.yaxis.grid(True, which='minor')
    axs.set_ylabel("Probability")
    axs.set_xlabel("Response Time (sec)")

plt.tight_layout()
# plt.show()
plt.savefig(functions.get_project_root()+'/experiments/9-various-benchmarks/noisy-cr-ob.pdf',format='pdf', bbox_inches='tight', pad_inches = 0.1)
