import pandas as pd
from experiments.libs import functions, prom_client
import matplotlib.pyplot as plt
import matplotlib as mpl

df = pd.read_csv(functions.get_project_root()+'/logs/exp-3-cb-none-interval-1ms.csv')


CB_values =['dynamic', 1, 50, None]
retry_values = ['dynamic', 2, 10, None]
traffic_patterns = ['static', 'spike']
challenging_services = ["productcatalogservice"]


fig, axs = plt.subplots(nrows=1, ncols=1, figsize=(4, 4),dpi=300)
# faghat khate 15 ro avaz kardam, inja bayad charte retry attempt ro bekeshi

i = 0
j = 0

# fig.suptitle('Throughput of services when there is a static overload and \n and a dynamic circuit breaker for the third tier')
data = df.loc[(df['traffic'] == "static-110") & (df['cb'] == "none") & (df['retry'] == "dynamic")]

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
        
        attempts = prom_inst.get_retry_attempt()
        attempt = {
            "data": [],
            "timestamp": [],
        }
       



        for item in attempts[0]['values']:
                attempt["data"].append(float(item[1]))
                attempt["timestamp"].append(float(item[0]) - float(attempts[0]['values'][0][0]))
       
        attempt['timestamp'] = [ii for ii in attempt['timestamp'] if ii <= 300]
        attempt['data'] = attempt['data'][:len(attempt['timestamp'])]
        
        axs.grid()
        axs.plot(attempt['timestamp'], attempt['data'], color="green", label="Successful")
        
        #axs[i, j].plot(circuit_broken_sum['timestamp'], circuit_broken_sum['data'], label="Cumulative Circuit broken")
        # axs[i, j].set_xticks([0,60, 120,180,  240])
        #axs[i, j].set_ylim(0, 2000)
        # axs[i, j].set_xlim(0, 240)
        # axs[i, j].set_yscale("log")
        # axs[i, j].set_yticks([10, 100, 1000])
        axs.yaxis.set_major_formatter(mpl.ticker.ScalarFormatter())
        #axs[i, j].yaxis.set_minor_formatter(mpl.ticker.ScalarFormatter())
       

        axs.set_xlabel("Time (sec)")
        axs.set_ylabel("Number of Retry Attempts")
        # if i == 0:

            # if j == 0:
            #     axs[i, j].set_title("First tier")
            # elif j == 1:
            #     axs[i, j].set_title("Second tier")
            # elif j == 2:
            #     axs[i, j].set_title("Third tier")

        # if j == 0:
            
        #     if row['retry'] == "dynamic":
        #         axs[i, j].set_ylabel( "Dynamic Retry Attempt\n(req/sec)")
        #     elif row['retry'] == "2":
        #         axs[i, j].set_ylabel( "2 Retry Attempts\n(req/sec)")
        #     elif row['retry'] == "10":
        #         axs[i, j].set_ylabel( "10 Retry Attempts\n(req/sec)")
        #     elif row['retry'] == "none":
        #         axs[i, j].set_ylabel( "No Retry Attempt\n(req/sec)")
            


plt.xticks([0, 60,120,180,240])

plt.tight_layout()
plt.savefig(functions.get_project_root()+'/experiments/3-immediate-backoff/result-retry-cb-none-interval-1ms.png')

    

    
    
    





