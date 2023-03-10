import pandas as pd
from experiments.libs import functions, prom_client
import glob, re

log_file_names = glob.glob('./logs/exp-4.2-capacity33.csv')

services = ['productcatalogservice', 'frontend']

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

def clean_prom_rt(response_time_prom_data):
    response_time = {
        "data": [],
        "timestamp": []
    }
    if len(response_time_prom_data) > 0:
        for item in response_time_prom_data[0]['values']:
            response_time['data'].append(float(item[1]))
            response_time['timestamp'].append(float(item[0]) - float(response_time_prom_data[0]['values'][0][0]))
    return response_time

#main_df = pd.DataFrame(columns=['traffic','retry_attempt', 'retry_interval', 'cb', 'successful_req', 'failed_req', 'cb_req', 'c_response_time', 'response_time'])
#print(main_df)
main_data = {
    "traffic": [],
    "retry_attempt": [],
    "retry_interval": [],
    "cb": [],
    "pc_succ_req": [],
    "pc_fail_req": [],
    "pc_cb_req": [],
    "pc_c_rt": [],
    "f_succ_req": [],
    "f_fail_req": [],
    "f_cb_req": [],
    "f_c_rt": [],
}




def align_timestamps(dicts_dict):
    # Find the union of all timestamps
    all_timestamps = set()
    for key in dicts_dict:
        all_timestamps.update(dicts_dict[key]["timestamp"])
    
    # Create a new dictionary with aligned timestamps
    aligned_dict = {}
    for key in dicts_dict:
        data = dicts_dict[key]["data"]
        timestamp = dicts_dict[key]["timestamp"]
        new_data = [0] * len(all_timestamps)
        for i, ts in enumerate(all_timestamps):
            if ts in timestamp:
                new_data[i] = data[timestamp.index(ts)]
        aligned_dict[key] = {"data": new_data, "timestamp": list(all_timestamps)}
    
    return aligned_dict



def extract_interval(name_string):
    match = re.search(r'(\d+)ms', name_string)

    if match:
        interval = match.group(1)
        return(float(interval)/1000)
    else:
        print("No match found.")







for log_file in log_file_names:
    
    df = pd.read_csv(log_file)
    for index, row in df.iterrows():
        prom_inst = prom_client.PromQuery()
        prom_inst.prom_host = "labumu.se"
        prom_inst.start = int(row['start'])
        prom_inst.end = int(row['end'])
        prom_inst.response_code = "200"
        prom_inst.namespace = "default"
        prom_inst.percentile = "0.95"
        prom_inst.warmup = 90000
        prom_inst.warmdown = 90000

        prom_inst.service = services[0] # productcatalogue
        pc_succ_req, pc_fail_req, pc_cb_req = clean_prom_status_codes(prom_inst.get_status_codes())
        pc_rt = clean_prom_rt(prom_inst.get_response_time())
        prom_inst.service = services[1] # productcatalogue
        f_succ_req, f_fail_req, f_cb_req = clean_prom_status_codes(prom_inst.get_status_codes())
        f_rt = clean_prom_rt(prom_inst.get_response_time())

        not_aligned_dict = {
            "pc_succ_req": pc_succ_req,
            "pc_fail_req": pc_fail_req,
            "pc_cb_req": pc_cb_req,
            "pc_rt": pc_rt,
            "f_succ_req": f_succ_req,
            "f_fail_req": f_fail_req,
            "f_cb_req": f_cb_req,
            "f_rt": f_rt
        }
        # print(not_aligned_dict)
        if row['cb'] == 'none':
            cb_value = 1024
        else:
            cb_value = row['cb']
        if row['retry_attempt'] == 'none':
            retry_value = 2
        else:
            retry_value = row['retry_attempt']
        aligned_dict = align_timestamps(not_aligned_dict)
        # print(aligned_dict)

        # print("----------------")


        number_of_rows = len(aligned_dict['pc_succ_req']['data'])
        main_data['traffic'].extend([int(float(row['traffic'])*33)]*number_of_rows)
        main_data['retry_attempt'].extend([retry_value]*number_of_rows)
        main_data['retry_interval'].extend([extract_interval(row['retry_interval'])]*number_of_rows)
        main_data['cb'].extend([cb_value]*number_of_rows)
        main_data['pc_succ_req'].extend(aligned_dict['pc_succ_req']['data'])
        main_data['pc_fail_req'].extend(aligned_dict['pc_fail_req']['data'])
        main_data['pc_cb_req'].extend(aligned_dict['pc_cb_req']['data'])
        main_data['pc_c_rt'].extend(aligned_dict['pc_rt']['data'])
        main_data['f_succ_req'].extend(aligned_dict['f_succ_req']['data'])
        main_data['f_fail_req'].extend(aligned_dict['f_fail_req']['data'])
        main_data['f_cb_req'].extend(aligned_dict['f_cb_req']['data'])
        main_data['f_c_rt'].extend(aligned_dict['f_rt']['data'])
        

        

main_df = pd.DataFrame(main_data)


main_df.to_csv("./datasets/exp4-main-2.csv", index=False)

            
        

    