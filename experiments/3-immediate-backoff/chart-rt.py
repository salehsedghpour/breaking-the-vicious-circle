import pandas as pd
from experiments.libs import functions, prom_client
import matplotlib.pyplot as plt
import matplotlib as mpl

df = pd.read_csv(functions.get_project_root()+'/logs/exp-3-immediate-controller.csv')


CB_values =['dynamic', 1, 50, None]
retry_values = ['dynamic', 2, 10, None]
traffic_patterns = ['static', 'spike']
challenging_services = ["frontend", "recommendationservice", "productcatalogservice"]

fig, axs = plt.subplots(nrows=4, ncols=3, figsize=(8, 8), sharex=True,dpi=300)

i = 0
j = 0
fig.suptitle('Response time of services when there is an overload with spikes and \n and a dynamic circuit breaker for the third tier')


data = df.loc[(df['traffic'] == "spike-110-160") & (df['cb'] == 'dynamic')]

for index, row in data.iterrows():
    for service in challenging_services:
        prom_inst = prom_client.PromQuery()
        prom_inst.prom_host = "labumu.se"
        prom_inst.start = int(row['start'])
        prom_inst.end = int(row['end'])
        prom_inst.response_code = "200"
        prom_inst.namespace = "default"
        prom_inst.percentile = "0.95"
        prom_inst.warmup = 30000
        prom_inst.warmdown = 0
        prom_inst.service = service
        if row['retry'] == "dynamic" and service == "frontend":
            i = 0
            j = 0
        elif row['retry'] == "dynamic" and service == "recommendationservice":
            i = 0
            j = 1
        elif row['retry'] == "dynamic" and service == "productcatalogservice":
            i = 0
            j = 2

        
        elif row['retry'] == '2' and service == "frontend":
            i = 1
            j = 0
        elif row['retry'] == '2' and service == "recommendationservice":
            i = 1
            j = 1
        elif row['retry'] == '2' and service == "productcatalogservice":
            i = 1
            j = 2
        
        elif row['retry'] == '10' and service == "frontend":
            i = 2
            j = 0
        elif row['retry'] == '10' and service == "recommendationservice":
            i = 2
            j = 1
        elif row['retry'] == '10' and service == "productcatalogservice":
            i = 2
            j = 2
        
        elif row['retry'] == 'none' and service == "frontend":
            i = 3
            j = 0
        elif row['retry'] == 'none' and service == "recommendationservice":
            i = 3
            j = 1
        elif row['retry'] == 'none' and service == "productcatalogservice":
            i = 3
            j = 2

        response_time_prom_data = prom_inst.get_response_time()
        response_time = {
            "data": [],
            "timestamp": []
        }
        if len(response_time_prom_data) > 0:
            for item in response_time_prom_data[0]['values']:
                response_time['data'].append(float(item[1]) * 1000)
                # response_time['timestamp'].append(int(item[0]))
                response_time['timestamp'].append(int(item[0])- int(response_time_prom_data[0]['values'][0][0]))
        # for item in data_sum_col:
        #     #if item['metric']['response_code'] == "200" and item['metric']['response_flags'] == "UO":
        #         for val in item['values']:
        #             circuit_broken_sum["data"].append(float(val[1]))
        #             circuit_broken_sum["timestamp"].append(float(val[0]) - item['values'][0][0])
        
        #axs[i, j].plot(circuit_broken_sum['timestamp'], circuit_broken_sum['data'], label="Cumulative Circuit broken")
        axs[i, j].plot(response_time['timestamp'], response_time['data'], )
        # axs[i, j].set_xticks([0,60, 120,180,  240])
        #axs[i, j].set_ylim(0, 2000)
        # axs[i, j].set_xlim(0, 240)
        # axs[i, j].set_yscale("log")
        # axs[i, j].set_yticks([10, 100, 1000])
        axs[i, j].yaxis.set_major_formatter(mpl.ticker.ScalarFormatter())
        #axs[i, j].yaxis.set_minor_formatter(mpl.ticker.ScalarFormatter())
        if i == 2:
            # if j == 2:
            #     axs[i, j].legend()
            axs[i, j].set_xlabel("Time (sec)")
        if i == 0:
            if j == 0:
                axs[i, j].set_title("First tier")
            elif j == 1:
                axs[i, j].set_title("Second tier")
            elif j == 2:
                axs[i, j].set_title("Third tier")

        if j == 0:
            if row['retry'] == "dynamic":
                axs[i, j].set_ylabel( "Dynamic Retry Attempt\n(ms)")
            elif row['retry'] == "2":
                axs[i, j].set_ylabel( "2 Retry Attempts\n(ms)")
            elif row['retry'] == "10":
                axs[i, j].set_ylabel( "10 Retry Attempts\n(ms)")
            elif row['retry'] == "none":
                axs[i, j].set_ylabel( "No Retry Attempt\n(ms)")
            


plt.xticks([0, 60,120,180,240])

plt.tight_layout()

plt.savefig("experimentstest.png")
plt.savefig(functions.get_project_root()+'/experiments/3-immediate-backoff/result-rt-overload-spike-cb-dynamic.png')

    

    
    
    





