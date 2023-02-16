'''
Static CB       1       50
Static retry    2       10
Traffic         static  spike
CB controller   0       1
Retry cont.     0       1    
'''
from experiments.libs import functions,deployment_crud, prom_client,service_account_crud, service_crud,virtual_service_crud, configmap_crud, destination_rule_crud, controllers
import logging.config
import yaml, time, csv, math



logging.config.fileConfig(functions.get_project_root()+'/experiments/logging.ini', disable_existing_loggers=False)


functions.k8s_authentication()

CB_values =[[1]]#'dynamic', 1, 50, None]
retry_values = ['dynamic', [2, 10], None]
traffic_patterns = ['static', ]#'spike']
output_log_file_name = functions.get_project_root()+'/logs/exp-3-cb-1-interval-1ms.csv'
deployment_list = ['adservice-dep', 'cartservice-dep', 'checkoutservice-dep', 'currencyservice-dep', 'emailservice-dep',
                    'frontend-dep', 'paymentservice-dep', 'productcatalogservice-dep', 'recommendationservice-dep',
                    'redis-cart-dep', 'shippingservice-dep']
services_list = ['adservice', 'cartservice', 'checkoutservice', 'currencyservice', 'emailservice',
                    'frontend', 'paymentservice', 'productcatalogservice', 'recommendationservice',
                    'redis-cart', 'shippingservice']
svc_dep_list = deployment_list + services_list
layer_3_services = ["cartservice", "shippingservice", "emailservice", "paymentservice", "currencyservice",
                    "productcatalogservice"]
prometheus_host = 'labumu.se'
# experiment duration: 5 minutes
experiment_duration = 300


# Create the log files
with open(output_log_file_name, 'w') as csv_file:
    fieldnames = ['traffic','cb', 'retry', 'start', 'end']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    csv_file.close()


# deploy the online-boutique
for service in svc_dep_list:
    with open(functions.get_project_root()+'/experiments/yaml-files/online-boutique/'+ service +'.yaml', "r") as yaml_file:
        try:
            yaml_object = yaml.safe_load_all(yaml_file)
            for part in yaml_object:
                if part["kind"] == "Deployment":
                    deployment_crud.create_deployment(part)
                elif part["kind"] == "ServiceAccount":
                    service_account_crud.create_service_account(part)
                elif part["kind"] == "Service":
                    service_crud.create_service(part)
                elif part["kind"] == "VirtualService":
                    virtual_service_crud.create_virtual_service(part)
                elif part["kind"] == "ConfigMap":
                    configmap_crud.create_configmap(part)
        except yaml.YAMLError as e:
            logging.warning("There was a problem loading the yaml file in deploying emulatade app")
            logging.warning(e)
logging.info("Please wait for some time that all pods are readly...")
time.sleep(120)

def loadgenerator_static():
    with open(functions.get_project_root()+'/experiments/yaml-files/loadgenerator.yaml', "r") as yaml_file:
        lg_address = "frontend/cart"
        yaml_object = None
        try:
            yaml_object = yaml.safe_load(yaml_file)
            traffic_scenario = """
                for j in {};
                    do
                    setConcurrency $j;
                    sleep {};
                    done;
                echo "done";
                pkill -15 httpmon;
                """.format("{110..111..1}", 300)

            yaml_object['spec']['template']['spec']['containers'][0]['env'][-1]['value'] = traffic_scenario
            yaml_object['spec']['template']['spec']['containers'][0]['env'][0]['value'] = lg_address
            deployment_crud.create_deployment(yaml_object)
        except yaml.YAMLError as e:
            logging.warning("There was a problem loading the yaml file in loadgenerator deployment")
            logging.warning(e)
        
        logging.info("Wait {wait_time} seconds for the experiments without controller and static overload to be done.".format(wait_time=str(experiment_duration)))
    yaml_file.close()  

def loadgenerator_spike():
    with open(functions.get_project_root()+'/experiments/yaml-files/loadgenerator.yaml', "r") as yaml_file:
        lg_address = "frontend/cart"
        yaml_object = None
        try:
            yaml_object = yaml.safe_load(yaml_file)
            traffic_scenario = """
                for j in {};
                    do
                    setConcurrency {};
                    sleep {};
                    setConcurrency {};
                    sleep {}
                    done;
                echo "done";
                pkill -15 httpmon;
                """.format("{1..12..1}", 110, 30, 160, 5)

            yaml_object['spec']['template']['spec']['containers'][0]['env'][-1]['value'] = traffic_scenario
            yaml_object['spec']['template']['spec']['containers'][0]['env'][0]['value'] = lg_address
            deployment_crud.create_deployment(yaml_object)
        except yaml.YAMLError as e:
            logging.warning("There was a problem loading the yaml file in loadgenerator deployment")
            logging.warning(e)
        
        logging.info("Wait {wait_time} seconds for the experiments without controller and static overload to be done.".format(wait_time=str(experiment_duration)))
    yaml_file.close()

def delete_loadgenerator(traffic_log, cb_log, retry_log, experiment_start, experiment_end):    
    with open(output_log_file_name, 'a') as csv_file:
        writer = csv.writer(csv_file, delimiter=",")
        writer.writerow([
            traffic_log, # Traffic
            cb_log, #CB
            retry_log, # Retry
            experiment_start, # Start
            experiment_end, # end
        ])
    csv_file.close()
    
    with open(functions.get_project_root()+'/experiments/yaml-files/loadgenerator.yaml', "r") as yaml_file:
        yaml_object = None
        try:
            yaml_object = yaml.safe_load(yaml_file)
            deployment_crud.delete_deployment(yaml_object)
        except yaml.YAMLError as e:
            logging.warning("There was a problem loading the yaml file")
            logging.warning(e)
    yaml_file.close

def create_retry(service_name, namespace, retry_attempt ):
    vs_retry = {
        "apiVersion": "networking.istio.io/v1alpha3",
        "kind": "VirtualService",
        "metadata": {
            "name": service_name+"-retry",
            "namespace": namespace
        },
        "spec": {
            "hosts": [
                service_name+".default.svc.cluster.local"
            ],
            "http": [
                {
                    "route": [
                        {
                            "destination": {
                                "host": service_name+".default.svc.cluster.local",
                            },
                        }
                    ],
                    "retries": {
                        "attempts": retry_attempt,
                        "perTryTimeout": "1ms",
                        "retryOn": "connect-failure,refused-stream,unavailable,cancelled,retriable-status-codes,5xx,deadline-exceeded"
                    },
                }
            ]
        }
    } 
    virtual_service_crud.create_virtual_service(vs_retry)

def delete_retry(service_name, namespace, retry_attempt ):
    vs_retry = {
        "apiVersion": "networking.istio.io/v1alpha3",
        "kind": "VirtualService",
        "metadata": {
            "name": service_name+"-retry",
            "namespace": namespace
        },
        "spec": {
            "hosts": [
                service_name+".default.svc.cluster.local"
            ],
            "http": [
                {
                    "route": [
                        {
                            "destination": {
                                "host": service_name+".default.svc.cluster.local",
                            },
                        }
                    ],
                    "retries": {
                        "attempts": retry_attempt,
                        "perTryTimeout": "1ms",
                        "retryOn": "connect-failure,refused-stream,unavailable,cancelled,retriable-status-codes,5xx,deadline-exceeded"
                    },
                }
            ]
        }
    } 
    virtual_service_crud.delete_virtual_service(vs_retry)
    
# initialize prometheus client
prom_inst = prom_client.PromQuery()
# prom_inst.response_code = "200"
prom_inst.namespace = "default"
prom_inst.percentile = "0.95"
prom_inst.service = layer_3_services[-1]


# Initialize the CB controller
cb_controller = controllers.CB_Controller()

cb_controller.trgt_rsp_time_95 = 0.1
cb_controller.p = 0.9
cb_controller.cur_rsp_time_95 = 0.01
cb_controller.cur_que_len = 1024

# Initializer the immediate backoff controller for retry attempts
retry_controller = controllers.Immediate_Backoff_Controller()


def re_initialize():
    logging.info("Re-Initialize in progress!  If there is any warning, simply ignore it!")
    cb_controller.__init__()
    retry_controller.__init__()
    vs_retry = {
        "apiVersion": "networking.istio.io/v1alpha3",
        "kind": "VirtualService",
        "metadata": {
            "name": layer_3_services[-1]+"-retry",
            "namespace": 'default'
        },
        "spec": {
            "hosts": [
                layer_3_services[-1]+".default.svc.cluster.local"
            ],
            "http": [
                {
                    "route": [
                        {
                            "destination": {
                                "host": layer_3_services[-1]+".default.svc.cluster.local",
                            },
                        }
                    ],
                    "retries": {
                        "attempts": 1,
                        "retryOn": "connect-failure,refused-stream,unavailable,cancelled,retriable-status-codes,5xx,deadline-exceeded"
                    },
                }
            ]
        }
    } 
    virtual_service_crud.delete_virtual_service(vs_retry)
    destination_rule_crud.delete_circuit_breaker(layer_3_services[-1], 'default')


def enforce_cb_controller(start_time):
    prom_inst.start = int(time.time() * 1000)
    prom_inst.end = prom_inst.start
    prom_inst.warmup = 0
    prom_inst.warmdown = 0

    prom_inst.service = layer_3_services[-1]
    pcs_rt = prom_inst.get_response_time()
    if len(pcs_rt) > 0:
        cb_controller.cur_rsp_time_95 = float(pcs_rt[0]['values'][0][1]) * 1000
        if math.isnan(cb_controller.cur_rsp_time_95):
            cb_controller.cur_rsp_time_95 = 0.0
    else:
        cb_controller.cur_rsp_time_95 = 0.0
    queue_size_tier_1 = prom_inst.get_current_queue_size(job="onetier1")
    if len(queue_size_tier_1) > 0:
        cb_controller.cur_que_len = int(queue_size_tier_1[0]['values'][0][1])
    else:
        cb_controller.cur_que_len = 1024

    new_queue_size_tier_1 = cb_controller.exec()

    data_for_pg_tier_1 = {
        "name": "destination_rule_http2_max_requests",
        "description": "Value of http2MaxRequest applied to Istio as DR",
        "value": new_queue_size_tier_1,
        "job": "onetier1"
    }

    functions.push_to_prom_pg(data_for_pg_tier_1)
    for affected_service in layer_3_services: 
        ret = destination_rule_crud.patch_circuit_breaker(service_name=affected_service, name_space="default",
                                            max_requests=new_queue_size_tier_1)
        if not ret:
            logging.info("As the destination-rule didn't exist, we are creating it now ...")
            ret = destination_rule_crud.create_circuit_breaker(service_name=affected_service, name_space="default",
                                                            max_requests=new_queue_size_tier_1)


def enforce_retry_controller():
    
    prom_inst.start = int(time.time() * 1000 - 15000)
    prom_inst.end =  int(time.time() * 1000 - 10000)
    prom_inst.warmup = 0
    prom_inst.warmdown = 0
    prom_inst.service = layer_3_services[-1]
    # {"status":"success","data":{"resultType":"vector","result":[{"metric":{"response_code":"0","response_flags":"unknown"},"value":[1675787029,"0"]},{"metric":{"response_code":"200","response_flags":"-"},"value":[1675787029,"163.6"]},{"metric":{"response_code":"500","response_flags":"-"},"value":[1675787029,"0"]},{"metric":{"response_code":"500","response_flags":"DC"},"value":[1675787029,"0"]}]}}
    status_codes = prom_inst.get_status_codes()
    failed_requests_list = []
    failed_requests = 0
    for item in status_codes:
        if (item['metric']['response_code'] != "200") or (item['metric']['response_code'] == "200" and item['metric']['response_flags'] != '-'):

            avg = 0
            for i in item['values']:
                print("i")
                print(i)
                avg = int(float(i[1])) + avg
            print("avg")
            print(avg)
            avg = avg/len(item['values'])
            failed_requests = failed_requests + int(avg)
    print("failed_requests 1:")
    print(failed_requests)
    failed_requests_list.append(failed_requests)
    prom_inst.start = int(time.time() * 1000 - 10000)
    prom_inst.end =  int(time.time() * 1000 - 5000)
    failed_requests = 0
    for item in status_codes:
        if (item['metric']['response_code'] != "200") or (item['metric']['response_code'] == "200" and item['metric']['response_flags'] != '-'):
            avg = 0
            for i in item['values']:
                avg = int(float(i[1]))
            avg = avg/len(item['values'])
            failed_requests = failed_requests + int(avg)
    failed_requests_list.append(failed_requests)
    print("failed_requests 2:")
    print(failed_requests)
    prom_inst.start = int(time.time() * 1000 - 5000)
    prom_inst.end =  int(time.time() * 1000 )
    failed_requests = 0
    for item in status_codes:
        if (item['metric']['response_code'] != "200") or (item['metric']['response_code'] == "200" and item['metric']['response_flags'] != '-'):
            avg = 0
            for i in item['values']:
                avg = int(float(i[1]))
            avg = avg/len(item['values'])
            failed_requests = failed_requests + int(avg)
    failed_requests_list.append(failed_requests)
    print("failed_requests 3:")
    print(failed_requests)
    print("The failed request list:")
    print(failed_requests_list)
    retry_controller.failed_requests = failed_requests_list
    retry_controller.specify_retry_threshold()
    failed_requests_list = []
    vs_retry = {
        "apiVersion": "networking.istio.io/v1alpha3",
        "kind": "VirtualService",
        "metadata": {
            "name": layer_3_services[-1]+"-retry",
            "namespace": 'default'
        },
        "spec": {
            "hosts": [
                layer_3_services[-1]+".default.svc.cluster.local"
            ],
            "http": [
                {
                    "route": [
                        {
                            "destination": {
                                "host": layer_3_services[-1]+".default.svc.cluster.local",
                            },
                        }
                    ],
                    "retries": {
                        "attempts": retry_controller.retry_attempt,
                        "perTryTimeout": "1ms",
                        "retryOn": "connect-failure,refused-stream,unavailable,cancelled,retriable-status-codes,5xx,deadline-exceeded"
                    },
                }
            ]
        }
    }

    data_for_pg_tier_1 = {
        "name": "retry_attempts_"+layer_3_services[-1],
        "description": "Value of retry attempt applied to Istio as DR",
        "value":  retry_controller.retry_attempt,
        "job": "onetier1"
    }

    functions.push_to_prom_pg(data_for_pg_tier_1)
    # delete previous one
    virtual_service_crud.delete_virtual_service(vs_retry)
    # create new one
    virtual_service_crud.create_virtual_service(vs_retry)



# performing the experiments
for CB_value in CB_values:
    for retry_value in retry_values:
        for traffic_pattern in traffic_patterns:
            time.sleep(30)
            if CB_value == 'dynamic':
                if retry_value == 'dynamic':
                    if traffic_pattern == 'static':
                        start_time = int(time.time() * 1000)
                        loadgenerator_static()
                        while int(time.time() * 1000) < start_time + (experiment_duration * 1000):
                            enforce_cb_controller(start_time=start_time)
                            enforce_retry_controller()
                            time.sleep(5)
                            pass
                        end_time =  int(time.time() * 1000)
                        delete_loadgenerator(traffic_log='static-110',cb_log='dynamic', retry_log='dynamic', experiment_start=start_time, experiment_end=end_time)
                        re_initialize()
                    else:
                        start_time = int(time.time() * 1000)
                        loadgenerator_spike()
                        while int(time.time() * 1000) < start_time + (experiment_duration * 1000):
                            enforce_cb_controller(start_time=start_time)
                            enforce_retry_controller()
                            time.sleep(5)
                            pass
                        end_time =  int(time.time() * 1000)
                        delete_loadgenerator(traffic_log='spike-110-160',cb_log='dynamic', retry_log='dynamic', experiment_start=start_time, experiment_end=end_time)
                        re_initialize()
                elif retry_value == None:
                    if traffic_pattern == 'static':
                        start_time = int(time.time() * 1000)
                        loadgenerator_static()
                        while int(time.time() * 1000) < start_time + (experiment_duration * 1000):
                            enforce_cb_controller(start_time=start_time)
                            time.sleep(5)
                            pass
                        end_time =  int(time.time() * 1000)
                        delete_loadgenerator(traffic_log='static-110',cb_log='dynamic', retry_log='none', experiment_start=start_time, experiment_end=end_time)
                        re_initialize()
                    else:
                        start_time = int(time.time() * 1000)
                        loadgenerator_spike()
                        while int(time.time() * 1000) < start_time + (experiment_duration * 1000):
                            enforce_cb_controller(start_time=start_time)
                            time.sleep(5)
                            pass                        
                        end_time =  int(time.time() * 1000)
                        delete_loadgenerator(traffic_log='spike-110-160',cb_log='dynamic', retry_log='none', experiment_start=start_time, experiment_end=end_time)
                        re_initialize()
                else:
                    if traffic_pattern == 'static':
                        for retry in retry_value:
                            for affected_service in layer_3_services:
                                create_retry(affected_service,'default', retry)
                            loadgenerator_static()
                            start_time = int(time.time() * 1000)
                            while int(time.time() * 1000) < start_time + (experiment_duration * 1000):
                                enforce_cb_controller(start_time=start_time)
                                time.sleep(5)
                                pass                                       
                            end_time =  int(time.time() * 1000)
                            delete_loadgenerator(traffic_log='static-110',cb_log='dynamic', retry_log=retry, experiment_start=start_time, experiment_end=end_time)
                            for affected_service in layer_3_services:
                                delete_retry(affected_service,'default', retry)
                            re_initialize()
                    else:
                        for retry in retry_value:
                            for affected_service in layer_3_services:
                                create_retry(affected_service,'default', retry)
                            loadgenerator_spike()
                            start_time = int(time.time() * 1000)
                            while int(time.time() * 1000) < start_time + (experiment_duration * 1000):
                                enforce_cb_controller(start_time=start_time)
                                time.sleep(5)
                                pass           
                            end_time =  int(time.time() * 1000)
                            delete_loadgenerator(traffic_log='spike-110-160',cb_log='dynamic', retry_log=retry, experiment_start=start_time, experiment_end=end_time)
                            for affected_service in layer_3_services:
                                delete_retry(affected_service,'default', retry)
                            re_initialize()
            elif CB_value == None:
                if retry_value == 'dynamic':
                    if traffic_pattern == 'static':
                        start_time = int(time.time() * 1000)
                        loadgenerator_static()
                        while int(time.time() * 1000) < start_time + (experiment_duration * 1000):
                            enforce_retry_controller()
                            time.sleep(5)
                            pass
                        end_time =  int(time.time() * 1000)
                        delete_loadgenerator(traffic_log='static-110',cb_log='none', retry_log='dynamic', experiment_start=start_time, experiment_end=end_time)
                        re_initialize()
                    else:
                        start_time = int(time.time() * 1000)
                        loadgenerator_spike()
                        while int(time.time() * 1000) < start_time + (experiment_duration * 1000):
                            enforce_cb_controller(start_time=start_time)
                            enforce_retry_controller()
                            time.sleep(5)
                            pass
                        end_time =  int(time.time() * 1000)
                        delete_loadgenerator(traffic_log='spike-110-160',cb_log='none', retry_log='dynamic', experiment_start=start_time, experiment_end=end_time)
                        re_initialize()
                elif retry_value == None:
                    if traffic_pattern == 'static':
                        start_time = int(time.time() * 1000)
                        loadgenerator_static()
                        while int(time.time() * 1000) < start_time + (experiment_duration * 1000):
                            pass           
                        end_time =  int(time.time() * 1000)
                        delete_loadgenerator(traffic_log='static-110',cb_log='none', retry_log='none', experiment_start=start_time, experiment_end=end_time)
                        re_initialize()
                    else:
                        start_time = int(time.time() * 1000)
                        loadgenerator_spike()
                        while int(time.time() * 1000) < start_time + (experiment_duration * 1000):
                            pass           
                        end_time =  int(time.time() * 1000)
                        delete_loadgenerator(traffic_log='spike-110-160',cb_log='none', retry_log='none', experiment_start=start_time, experiment_end=end_time)
                        re_initialize()
                else:
                    if traffic_pattern == 'static':
                        for retry in retry_value:
                            for affected_service in layer_3_services:
                                create_retry(affected_service,'default', retry)
                            start_time = int(time.time() * 1000)
                            loadgenerator_static()
                            while int(time.time() * 1000) < start_time + (experiment_duration * 1000):
                                pass
                            end_time =  int(time.time() * 1000)
                            delete_loadgenerator(traffic_log='static-110',cb_log='none', retry_log=retry, experiment_start=start_time, experiment_end=end_time)
                            for affected_service in layer_3_services:
                                delete_retry(affected_service,'default', retry)
                            re_initialize()
                    else:
                        for retry in retry_value:
                            for affected_service in layer_3_services:
                                create_retry(affected_service,'default', retry)
                            start_time = int(time.time() * 1000)
                            loadgenerator_spike()
                            while int(time.time() * 1000) < start_time + (experiment_duration * 1000):
                                pass
                            end_time =  int(time.time() * 1000)
                            delete_loadgenerator(traffic_log='spike-110-160',cb_log='none', retry_log=retry, experiment_start=start_time, experiment_end=end_time)
                            for affected_service in layer_3_services:
                                delete_retry(affected_service,'default', retry)
                            re_initialize()
            else:
                if retry_value == 'dynamic':
                    if traffic_pattern == 'static':
                        for cb in CB_value:
                            for cb_service in layer_3_services:
                                destination_rule_crud.create_circuit_breaker(cb_service, 'default', cb)
                            start_time = int(time.time() * 1000)
                            loadgenerator_static()
                            while int(time.time() * 1000) < start_time + (experiment_duration * 1000):
                                enforce_retry_controller()
                                time.sleep(5)
                                pass
                            end_time =  int(time.time() * 1000)
                            delete_loadgenerator(traffic_log='static-110',cb_log=cb, retry_log='dynamic', experiment_start=start_time, experiment_end=end_time)
                            for cb_service in layer_3_services:
                                destination_rule_crud.delete_circuit_breaker(cb_service, 'default',)
                            re_initialize()
                    else:
                        for cb in CB_value:
                            for cb_service in layer_3_services:
                                destination_rule_crud.create_circuit_breaker(cb_service, 'default', cb)
                            start_time = int(time.time() * 1000)
                            loadgenerator_spike()
                            while int(time.time() * 1000) < start_time + (experiment_duration * 1000):
                                enforce_retry_controller()
                                time.sleep(5)
                                pass
                            end_time =  int(time.time() * 1000)
                            delete_loadgenerator(traffic_log='spike-110-160',cb_log=cb, retry_log='dynamic', experiment_start=start_time, experiment_end=end_time)
                            for cb_service in layer_3_services:
                                destination_rule_crud.delete_circuit_breaker(cb_service, 'default',)
                            re_initialize()
                        
                elif retry_value == None:
                    if traffic_pattern == 'static':
                        for cb in CB_value:
                            for cb_service in layer_3_services:
                                destination_rule_crud.create_circuit_breaker(cb_service, 'default', cb)
                            start_time = int(time.time() * 1000)
                            loadgenerator_static()
                            while int(time.time() * 1000) < start_time + (experiment_duration * 1000):
                                pass
                            end_time =  int(time.time() * 1000)
                            delete_loadgenerator(traffic_log='static-110',cb_log=cb, retry_log='none', experiment_start=start_time, experiment_end=end_time)
                            for cb_service in layer_3_services:
                                destination_rule_crud.delete_circuit_breaker(cb_service, 'default',)
                            re_initialize()
                    else:
                        for cb in CB_value:
                            for cb_service in layer_3_services:
                                destination_rule_crud.create_circuit_breaker(cb_service, 'default', cb)
                            start_time = int(time.time() * 1000)
                            loadgenerator_spike()
                            while int(time.time() * 1000) < start_time + (experiment_duration * 1000):
                                pass
                            end_time =  int(time.time() * 1000)
                            delete_loadgenerator(traffic_log='spike-110-160',cb_log=cb, retry_log='none', experiment_start=start_time, experiment_end=end_time)
                            for cb_service in layer_3_services:
                                destination_rule_crud.delete_circuit_breaker(cb_service, 'default',)
                            re_initialize()                 
                else:
                    if traffic_pattern == 'static':
                        for cb in CB_value:
                            for retry in retry_value:
                                for affected_service in layer_3_services:
                                    destination_rule_crud.create_circuit_breaker(affected_service, 'default', cb)
                                    create_retry(affected_service,'default', retry)
                                start_time = int(time.time() * 1000)
                                loadgenerator_static()
                                while int(time.time() * 1000) < start_time + (experiment_duration * 1000):
                                    pass
                                end_time =  int(time.time() * 1000)
                                delete_loadgenerator(traffic_log='static-110',cb_log=cb, retry_log=retry, experiment_start=start_time, experiment_end=end_time)
                                for affected_service in layer_3_services:
                                    destination_rule_crud.delete_circuit_breaker(affected_service, 'default')
                                    delete_retry(affected_service,'default', retry)
                                re_initialize()
                    else:
                        for cb in CB_value:
                            for retry in retry_value:
                                for affected_service in layer_3_services:
                                    destination_rule_crud.create_circuit_breaker(affected_service, 'default', cb)
                                    create_retry(affected_service,'default', retry)
                                start_time = int(time.time() * 1000)
                                loadgenerator_spike()
                                while int(time.time() * 1000) < start_time + (experiment_duration * 1000):
                                    pass
                                end_time =  int(time.time() * 1000)
                                delete_loadgenerator(traffic_log='spike-110-160',cb_log=cb, retry_log=retry, experiment_start=start_time, experiment_end=end_time)
                                for affected_service in layer_3_services:
                                    destination_rule_crud.delete_circuit_breaker(affected_service, 'default')
                                    delete_retry(affected_service,'default', retry)
                                re_initialize()    

# Delete Tthe online-boutique
for service in svc_dep_list:
    with open(functions.get_project_root()+'/experiments/yaml-files/online-boutique//'+ service +'.yaml', "r") as yaml_file:
        try:
            yaml_object = yaml.safe_load_all(yaml_file)
            for part in yaml_object:
                if part["kind"] == "Deployment":
                    deployment_crud.delete_deployment(part)
                elif part["kind"] == "ServiceAccount":
                    service_account_crud.delete_service_account(part)
                elif part["kind"] == "Service":
                    service_crud.delete_service(part)
                elif part["kind"] == "VirtualService":
                    virtual_service_crud.delete_virtual_service(part)
                elif part["kind"] == "ConfigMap":
                    configmap_crud.delete_configmap(part)
        except yaml.YAMLError as e:
            logging.warning("There was a problem loading the yaml file for deleting emulated app")
            logging.warning(e)

