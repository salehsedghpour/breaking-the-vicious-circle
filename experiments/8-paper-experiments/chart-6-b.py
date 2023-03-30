import pandas as pd
import matplotlib.pyplot as plt
from experiments.libs import functions, prom_client


df = pd.read_csv(functions.get_project_root()+'/logs/exp-8-3-controller-exec-versions.csv')



fig, axs = plt.subplots(nrows=1, ncols=1, figsize=(7, 5), sharex=True,dpi=300)

i = 0
j = 0


data = df.loc[(df['retry_attempt'] != 1)]

# data = df
challenging_services = ["frontend"]

for index, row in data.iterrows():
    prom_inst = prom_client.PromQuery()
    prom_inst.prom_host = "labumu.se"
    prom_inst.start = int(row['start'])
    prom_inst.end = int(row['end'])
    prom_inst.namespace = "default"
    prom_inst.warmup = 60000
    prom_inst.warmdown = 0
    prom_inst.service = challenging_services[0]
    prom_inst.step = 1
    prom_inst.response_code="200"
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
    else:
        retry_print = "Static Retry with "+str(row['retry_attempt']) + ' attempts and ' +str(row['retry_interval']) + " timeout"
    if len(response_time_cr['data']) != 0:
        axs.plot(response_time_cr['data'],response_time_cr['timestamp'], label=retry_print, alpha=0.5, linestyle="dashed")

    axs.set_yticks([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1], minor=False)
    axs.set_yticks([0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95], minor=True)
    axs.set_ylim(ymin=0, ymax=1.0)
    axs.set_xlim(xmin=0, xmax=0.8)


    axs.legend(loc="lower right")
    axs.xaxis.grid(True, which='minor')
    axs.xaxis.grid(True, which='major')
    axs.yaxis.grid(True, which='major')
    axs.yaxis.grid(True, which='minor')
    axs.set_ylabel("Probability")
    axs.set_xlabel("Response Time (sec)")

plt.tight_layout()
# plt.show()
plt.savefig(functions.get_project_root()+'/experiments/8-paper-experiments/figure-7-b-static.pdf',format='pdf', bbox_inches='tight', pad_inches = 0.1)



# target response time static bashe  baraye har 2 controller => response time behtar mishe va throughput bisthar mishe

