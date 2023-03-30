from experiments.libs import controllers, virtual_service_crud, destination_rule_crud, prom_client
import time
target_reponse_times = {
        'adservice':30, 
        'cartservice': 30, 
        'checkoutservice': 30, 
        'currencyservice': 30, 
        'emailservice':30,
        'frontend': 100, 
        'paymentservice': 30, 
        'productcatalogservice': 30, 
        'recommendationservice': 30,
        'redis-cart':30, 
        'shippingservice':30
    }
def initialize_cb_controllers(service_list):
    cb_controllers = {}
    
    for service in service_list:
        # initialize cb controllers
        cb_controllers[service+'-cb'] = controllers.CB_Controller()
        cb_controllers[service+'-cb'].trgt_rsp_time_95 = 100
        cb_controllers[service+'-cb'].p = 0.95
    return cb_controllers

def initialize_retry_controller(service_list):
    retry_controllers = {}
    for service in service_list:
        # initialize retry controller
        retry_controllers[service+'-retry'] = controllers.retryControllerTCP()
        retry_controllers[service+'-retry'].trgt_rsp_time_95 = 100
    return retry_controllers


def deploy_same_retrys(service_list , retry_attempt, retry_interval):
    for service in service_list:
        virtual_service_crud.create_retry(service_name=service, retry_attempt=retry_attempt, interval=retry_interval)


def delete_retrys(service_list , retry_attempt, retry_interval):
    for service in service_list:
        virtual_service_crud.delete_retry(service_name=service, retry_attempt=retry_attempt, interval=retry_interval)

def deploy_same_cbs(service_list, cb):
     for service in service_list:
        destination_rule_crud.create_circuit_breaker(service_name=service,name_space="default", max_requests=cb)


def delete_same_cbs(service_list):
     for service in service_list:
        destination_rule_crud.delete_circuit_breaker(service_name=service,name_space="default")




def monitor_services(service_list, version=False):
    prom_inst = prom_client.PromQuery()
    prom_inst.response_code = "200"
    prom_inst.namespace = "default"
    prom_inst.percentile = "0.95"
    prom_inst.warmup = 0
    prom_inst.warmdown = 0
    prom_inst.start = int(time.time() * 1000)
    prom_inst.end = prom_inst.start
    result = {}
    for service in service_list:
        prom_inst.service = service
       
        result[service] = {}
        rt = prom_inst.get_response_time()
        if len(rt) > 0:
            if len(rt[0])> 0:
                if len(rt[0]['values']) >0 :
                    result[service]['rt'] = float(rt[0]['values'][0][1]) * 1000
                else:
                    result[service]['rt'] = 0.0
            else:
                result[service]['rt'] = 0.0
        else:
            result[service]['rt'] = 0.0
        statuses = prom_inst.get_status_codes()
        failed , cb = clean_prom_status_codes(statuses)
        result[service]['failed'] = failed
        result[service]['cb'] = cb


    # if version == False:
    #     for service in service_list:
    #         prom_inst.service = service
    #         result[service] = {}
    #         rt = prom_inst.get_response_time()
    #         if len(rt) > 0:
    #             if len(rt[0])> 0:
    #                 if len(rt[0]['values']) >0 :
    #                     result[service]['rt'] = float(rt[0]['values'][0][1]) * 1000
    #                 else:
    #                     result[service]['rt'] = 0.0
    #             else:
    #                 result[service]['rt'] = 0.0
    #         else:
    #             result[service]['rt'] = 0.0
    #         statuses = prom_inst.get_status_codes()
    #         failed , cb = clean_prom_status_codes(statuses)
    #         result[service]['failed'] = failed
    #         result[service]['cb'] = cb
    # else:
    #     for service in service_list:
    #         prom_inst.service = service
    #         if service == 'productcatalogservice':
    #             for version in pc_ver_list:
    #                 result[service+'-'+version] = {}
                    
    #                 rt = prom_inst.get_response_time(version=version)
    #                 if len(rt) > 0:
    #                     if len(rt[0])> 0:
    #                         if len(rt[0]['values']) >0 :
    #                             result[service+'-'+version]['rt'] = float(rt[0]['values'][0][1]) * 1000
    #                         else:
    #                             result[service+'-'+version]['rt'] = 0.0
    #                     else:
    #                         result[service+'-'+version]['rt'] = 0.0
    #                 else:
    #                     result[service+'-'+version]['rt'] = 0.0
    #                 statuses = prom_inst.get_status_codes(version=version)
    #                 failed , cb = clean_prom_status_codes(statuses)
    #                 result[service+'-'+version]['failed'] = failed
    #                 result[service+'-'+version]['cb'] = cb

    #         # result[service] = {}
    #         # rt = prom_inst.get_response_time()
    #         # result[service]['rt'] = float(rt[0]['values'][0][1]) * 1000
    #         # statuses = prom_inst.get_status_codes()
    #         # failed , cb = clean_prom_status_codes(statuses)
    #         # result[service]['failed'] = failed
    #         # result[service]['cb'] = cb

    return result

        
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
    if len(success['data']) == 0:
        success = 0
    else:
        success = success['data'][0]
    if len(failed['data']) == 0:
        failed = 0
    else:
        failed = failed['data'][0]
    if len(circuit_broken['data']) == 0:
        circuit_broken = 0
    else:
        circuit_broken = circuit_broken['data'][0]
    return failed, circuit_broken
