import pandas as pd
import matplotlib.pyplot as plt
from experiments.libs import functions, prom_client


df = pd.read_csv(functions.get_project_root()+'/logs/exp-8-3-controller-exec-versions.csv')



fig, axs = plt.subplots(nrows=1, ncols=1, figsize=(7, 5), sharex=True,dpi=300)

i = 0
j = 0


data = df.loc[(df['retry_attempt'] != 1)]
# data = df


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


challenging_services = ["frontend"]

for index, row in data.iterrows():
    prom_inst = prom_client.PromQuery()
    prom_inst.prom_host = "labumu.se"
    prom_inst.start = int(row['start'])
    prom_inst.end = int(row['end'])
    prom_inst.namespace = "default"
    prom_inst.warmup = 60000
    prom_inst.step=1
    prom_inst.warmdown = 0
    prom_inst.service = challenging_services[0]
    status_code = prom_inst.get_status_codes()
    success, failed, cb = clean_prom_status_codes(status_code)

    ratio = []
    for i in range(len(success['data'])):
        ratio.append(int(100*success['data'][i]/(success['data'][i]+failed['data'][i])))

    throughput = int(sum(success['data']))
    failed = int(sum(failed['data']))
    if row['retry_controller'] == 1:
        retry_print = "Adaptive Retry - Total Success Rate = "+ str(throughput)
    else:
        retry_print = "Static Retry with "+str(row['retry_attempt']) + ' attempts and ' +str(row['retry_interval']) + " timeout - Total Success Rate = "+ str(throughput)
    
    axs.plot( success['timestamp'], ratio, label=retry_print,alpha=0.8)
    axs.legend(loc='lower center', bbox_to_anchor=(0.5, 1.05),
           fancybox=True, shadow=True)
    axs.set_ylabel("Carried Throughput Ratio (%)")
    axs.yaxis.set_major_formatter('{x:1.0f}%')
    axs.set_xlabel("Time (s)")
    axs.set_ylim(ymin=0, ymax=100)
    axs.set_xlim(xmin=0, xmax=240)
    axs.set_xticks([60, 120, 180, 240], minor=False)

    if row['cb_controller'] == 0:
        cb_print = "Default CB"
    else:
        cb_print = "Adatpive CB"

    
    str_out = cb_print + " and " + retry_print + ": Succesful requests=" + str(throughput) +", Failed requests=" + str(failed)
    print(str_out)

plt.yscale("symlog")


plt.tight_layout()
# plt.show()

plt.savefig(functions.get_project_root()+'/experiments/8-paper-experiments/figure-7-a-static.pdf',format='pdf', bbox_inches='tight', pad_inches = 0.1)
