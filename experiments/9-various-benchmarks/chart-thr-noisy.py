import pandas as pd
import matplotlib.pyplot as plt
from experiments.libs import functions, prom_client
from math import pi


df = pd.read_csv(functions.get_project_root()+'/logs/exp-8-4-controller-exec-versions-new.csv')


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


# fig, axs = plt.subplots(nrows=1, ncols=1, figsize=(7, 4),dpi=300)

challenging_services = ["frontend"]

# df = df.loc[(df['spike_duration'] == 10)]

data_dict = {
    "spike_duration": [1],
    "Adaptive retry":[],
    "1 attempt(s)\n1ms timeout":[],
    "1 attempt(s)\n25ms timeout":[],
    "1 attempt(s)\n50ms timeout":[],
    "2 attempt(s)\n1ms timeout":[],
    "2 attempt(s)\n25ms timeout\n(Default Configuration)":[],
    "2 attempt(s)\n50ms timeout":[],
    "5 attempt(s)\n1ms timeout":[],
    "5 attempt(s)\n25ms timeout":[],
    "5 attempt(s)\n50ms timeout":[],


}

for index, row in df.iterrows():
    prom_inst = prom_client.PromQuery()
    prom_inst.prom_host = "labumu.se"
    prom_inst.start = int(row['start'])
    prom_inst.end = int(row['end'])
    prom_inst.namespace = "default"
    prom_inst.warmup = 0
    prom_inst.warmdown = 0
    prom_inst.service = challenging_services[0]
    status_code = prom_inst.get_status_codes()
    success, failed, cb = clean_prom_status_codes(status_code)

    ratio = sum(success['data'])/(sum(success['data'])+ sum(failed['data'])) * 100
    # if row['app'] == 'DeathStarBench':

        # if row['spike_duration'] not in data_dict["spike_duration"]:
        #     data_dict["spike_duration"].append(row['spike_duration'])
        
    if row['retry_controller'] == 1:
        data_dict['Adaptive retry'].append(ratio)
    elif row['retry_attempt'] == 2 and row['retry_interval'] == '25ms':
        data_dict["2 attempt(s)\n25ms timeout\n(Default Configuration)"].append(ratio)

    else:
        data_dict[str(row['retry_attempt'])+" attempt(s)\n"+str(row['retry_interval'])+" timeout"].append(ratio)
        
        # # # if row['spike_duration'] == 1:
        # # #     loc_x = 1
        # # if row['spike_duration'] == 5:
        # #     loc_x = 2
        # # # elif row['spike_duration'] == 10:
        # # #     loc_x = 3
        # # # elif row['spike_duration'] == 15:
        # # #     loc_x = 4
        # # # else:
        # # #     loc_x = 5
        # retry_intervals = ['1ms','25ms', '50ms']
        # retry_attempts = [1, 2, 5]
        # if row['retry_controller'] == 1:
        #     loc_x = 1
        # elif row['retry_attempt'] == 1 and row['retry_interval'] == '1ms':
        #     loc_x = 2
        # elif row['retry_attempt'] == 1 and row['retry_interval'] == '25ms':
        #     loc_x = 3
        # elif row['retry_attempt'] == 1 and row['retry_interval'] == '50ms':
        #     loc_x = 4
        # elif row['retry_attempt'] == 2 and row['retry_interval'] == '1ms':
        #     loc_x = 5
        # elif row['retry_attempt'] == 2 and row['retry_interval'] == '25ms':
        #     loc_x = 6
        # elif row['retry_attempt'] == 2 and row['retry_interval'] == '50ms':
        #     loc_x = 7
        # elif row['retry_attempt'] == 5 and row['retry_interval'] == '1ms':
        #     loc_x = 8
        # elif row['retry_attempt'] == 5 and row['retry_interval'] == '25ms':
        #     loc_x = 9
        # elif row['retry_attempt'] == 5 and row['retry_interval'] == '50ms':
        #     loc_x = 10

        # labels =[
        #     'Adaptive Controller',
        #     '1 attempt with 1ms timeout',
        #     '1 attempt with 25ms timeout',
        #     '1 attempt with 50ms timeout',
        #     '2 attempts with 1ms timeout',
        #     '2 attempts with 25ms timeout',
        #     '2 attempts with 50ms timeout',
        #     '5 attempts with 1ms timeout',
        #     '5 attempts with 25ms timeout',
        #     '5 attempts with 50ms timeout',
           
        #     ]
        # x = [1,2,3,4,5,6,7,8,9,10]
        # axs.set_xticks(x, labels, rotation='vertical')
        # if (row['retry_attempt'] == 2) and (row['retry_interval'] == '25ms'):
        #     marker = "*"
        # elif row['retry_controller'] == 1:
        #     marker = "P"
        # else:
        #     marker = "^"
        # axs.scatter(loc_x, ratio, marker=marker)




# plt.show()


df = pd.DataFrame(data_dict)

categories=list(df)[1:]
N = len(categories)

# What will be the angle of each axis in the plot? (we divide the plot / number of variable)
angles = [n / float(N) * 2 * pi for n in range(N)]
angles += angles[:1]

ax = plt.subplot(111, polar=True)

ax.set_theta_offset(pi / 2)
ax.set_theta_direction(-1)

plt.xticks(angles[:-1], categories)


ax.set_rlabel_position(0)


values=df.loc[0].drop('spike_duration').values.flatten().tolist()
values += values[:1]
ax.plot(angles, values, linewidth=1, linestyle='solid', label=data_dict['spike_duration'][0])
ax.fill(angles, values, 'b', alpha=0.1)


# values=df.loc[1].drop('spike_duration').values.flatten().tolist()
# values += values[:1]
# ax.plot(angles, values, linewidth=1, linestyle='solid', label=data_dict['spike_duration'][1])
# ax.fill(angles, values, 'r', alpha=0.1)

# values=df.loc[2].drop('spike_duration').values.flatten().tolist()
# values += values[:1]
# ax.plot(angles, values, linewidth=1, linestyle='solid', label=data_dict['spike_duration'][2])
# ax.fill(angles, values, 'g', alpha=0.1)

# values=df.loc[3].drop('spike_duration').values.flatten().tolist()
# values += values[:1]
# ax.plot(angles, values, linewidth=1, linestyle='solid', label=data_dict['spike_duration'][3])
# ax.fill(angles, values, 'p', alpha=0.1)


# values=df.loc[4].drop('spike_duration').values.flatten().tolist()
# values += values[:1]
# ax.plot(angles, values, linewidth=1, linestyle='solid', label=data_dict['spike_duration'][4])
# ax.fill(angles, values, 'orange', alpha=0.1)

# plt.yticks([10, 20, 30, 40, 50, 60], ["10%","20%","30%", "40%","50%","60%"], color="grey", size=7)
# plt.ylim(0,65)

# plt.yticks([50, 60, 70, 80, 90, 100], ["50%","60%","70%", "80%","90%","100%"], color="grey", size=7)
plt.ylim(0,100)
# plt.ylabel("Success Rate (%)")

# plt.yscale("symlog")
ax.tick_params(axis='both', which='major', pad=25)

# plt.legend(loc='upper right', bbox_to_anchor=(0, 0.1), title="Spike Duration (sec):")

# Show the graph
# plt.show()
plt.savefig(functions.get_project_root()+'/experiments/9-various-benchmarks/noisy-thr-ob.pdf',format='pdf', bbox_inches='tight', pad_inches = 0.1)
