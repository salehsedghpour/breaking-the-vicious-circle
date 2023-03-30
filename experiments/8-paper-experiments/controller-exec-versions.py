from experiments.libs import functions, deployment_crud, service_crud, destination_rule_crud, virtual_service_crud
import logging.config
import csv, yaml, time
from . import fung_7 as func

logging.config.fileConfig(functions.get_project_root()+'/experiments/logging.ini', disable_existing_loggers=False)
functions.k8s_authentication()

output_log_file_name = functions.get_project_root()+'/logs/exp-8-3-controller-exec-versions.csv'

# Create the log files
with open(output_log_file_name, 'w') as csv_file:
    fieldnames = ['traffic', 'capacity', 'cb_controller', 'retry_controller','retry_attempt', 'retry_interval', 'start', 'end']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    csv_file.close()


def add_new_experiment_to_csv(values):
    with open(output_log_file_name, 'a') as csv_file:
        writer = csv.writer(csv_file, delimiter=",")
        writer.writerow([
            values['traffic'],
            capacity,
            values['cb_controller'],
            values['retry_controller'],
            values['retry_attempt'],
            values['retry_interval'],
            values['start'],
            values['end']
        ])
    csv_file.close()


deployment_list = ['adservice-dep', 'cartservice-dep', 'checkoutservice-dep', 'currencyservice-dep', 'emailservice-dep',
                    'frontend-dep', 'paymentservice-dep', 'productcatalogservice-dep-v1', 'productcatalogservice-dep-v2',
                    'productcatalogservice-dep-v3', 'recommendationservice-dep','redis-cart-dep', 'shippingservice-dep']
services_list = ['adservice', 'cartservice', 'checkoutservice', 'currencyservice', 'emailservice',
                    'frontend', 'paymentservice', 'productcatalogservice', 'recommendationservice',
                    'redis-cart', 'shippingservice']

pc_versions = ['v1', 'v2', 'v3']
retry_intervals = ['1ms','25ms', '50ms']
retry_attempts = [1, 2, 5]
cb_controller = [1]
retry_controller = [1, 0]
traffics = [70]# 'spike']
traffic_spike = 75
# 5 minutes for each experiment
experiment_duration = 300
sleep_between_each_experiment = 15

capacity = 70

svc_dep_list = deployment_list + services_list
prometheus_host = 'labumu.se'




# Deploy services
for service in svc_dep_list:
    with open(functions.get_project_root()+'/experiments/yaml-files/online-boutique-replicas/'+ service +'.yaml', "r") as yaml_file:
        try:
            yaml_object = yaml.safe_load_all(yaml_file)
            for part in yaml_object:
                if part["kind"] == "Deployment":
                    deployment_crud.create_deployment(part)
                elif part["kind"] == "Service":
                    service_crud.create_service(part)
                else:
                    logging.warning("There is a new kind in the yaml object that is not implemented.")
        except yaml.YAMLError as e:
            logging.warning("There was a problem loading the yaml file in deploying emulatade app")
            logging.warning(e)
logging.info("Please wait for some time that all pods are ready...")
time.sleep(120)

for traffic in traffics:
    for cb_cont in cb_controller:
        for retry_cont in retry_controller:
            if traffic != 'spike':
                loadgenerator_sleep_time = len(retry_attempts) * len(retry_intervals) * len(retry_controller) * len(cb_controller) * (sleep_between_each_experiment+ experiment_duration)
                functions.deploy_static_loadgenerator(traffic, traffic+1, loadgenerator_sleep_time)
                if cb_cont == 0:
                    # deploy 1024 (default value for queue size)
                    func.deploy_same_cbs(services_list, pc_versions, 1024)
                    if retry_cont == 0:
                        # I guess it is done now 16:38 March 16th
                        for retry_attempt in retry_attempts:
                            for retry_interval in retry_intervals:
                                log_start_time = int(time.time() * 1000)
                                func.deploy_same_retrys(services_list,pc_versions,retry_attempt,retry_interval)
                                while int(time.time() * 1000) < log_start_time + (experiment_duration * 1000):
                                    pass
                                log_end_time = int(time.time() * 1000)
                                log_dict = {
                                    "traffic": traffic,
                                    "cb_controller": cb_cont,
                                    "retry_controller": retry_cont,
                                    "retry_attempt": retry_attempt,
                                    "retry_interval": retry_interval,
                                    "start": log_start_time,
                                    "end": log_end_time
                                }
                                add_new_experiment_to_csv(log_dict)
                                
                    else:
                        # I guess it is done now 16:39 March 16th
                        retry_controllers = func.initialize_retry_controller(service_list=services_list)
                        log_start_time = int(time.time() * 1000)
                        while int(time.time() * 1000) < log_start_time + (experiment_duration * 1000):
                            monitoring_data = func.monitor_services(services_list, pc_versions)
                            for service in services_list:
                                if service == 'productcatalogservice':
                                    retry_controllers[service+'-retry'].cur_rsp_time_95 = monitoring_data[service+'-v1']['rt']
                                    retry_controllers[service+'-retry'].curr_failed = monitoring_data[service+'-v1']['failed']
                                    retry_controllers[service+'-retry'].curr_cb = monitoring_data[service+'-v1']['cb']
                                    retry_attempt, retry_interval = retry_controllers[service+'-retry'].exec()
                                    virtual_service_crud.create_retry(service_name=service,versions=pc_versions, retry_attempt=retry_attempt, interval=retry_interval)
                                else:
                                    retry_controllers[service+'-retry'].cur_rsp_time_95 = monitoring_data[service]['rt']
                                    retry_controllers[service+'-retry'].curr_failed = monitoring_data[service]['failed']
                                    retry_controllers[service+'-retry'].curr_cb = monitoring_data[service]['cb']
                                    retry_attempt, retry_interval = retry_controllers[service+'-retry'].exec()
                                    virtual_service_crud.create_retry(service_name=service, retry_attempt=retry_attempt, interval=retry_interval)
                            time.sleep(5)
                            func.delete_retrys(services_list, pc_versions, 2, '25ms')
                        log_end_time = int(time.time()* 1000)
                        log_dict = {
                            "traffic": traffic,
                            "cb_controller": cb_cont,
                            "retry_controller": retry_cont,
                            "retry_attempt": 0,
                            "retry_interval": 0,
                            "start": log_start_time,
                            "end": log_end_time
                        }
                        add_new_experiment_to_csv(log_dict)


                    func.delete_same_cbs(services_list,pc_versions)
                        
                        
                else:
                    if retry_cont == 0:
                        # I guess it is done 16:40 March 16th
                        for retry_attempt in retry_attempts:
                            for retry_interval in retry_intervals:
                                cb_controllers = func.initialize_cb_controllers(service_list=services_list, pc_ver_list=pc_versions)
                                log_start_time = int(time.time() * 1000)
                                func.deploy_same_retrys(services_list,pc_versions,retry_attempt,retry_interval)
                                while int(time.time() * 1000) < log_start_time + (experiment_duration * 1000):
                                    monitoring_data = func.monitor_services(services_list, pc_versions)
                                    for service in services_list:
                                        if service == 'productcatalogservice':
                                            for version in pc_versions:
                                                cb_controllers[service+"-"+version+"-cb"].cur_rsp_time_95 = monitoring_data[service+"-"+version]['rt']
                                                cb_val = cb_controllers[service+"-"+version+"-cb"].exec()
                                                create = destination_rule_crud.patch_circuit_breaker_for_specific_version(service_name=service, service_version=version, max_requests=cb_val, name_space="default")
                                                if not create:
                                                    destination_rule_crud.create_circuit_breaker_for_specific_version(service_name=service, service_version=version, max_requests=cb_val, name_space="default")
                                        else:
                                            cb_controllers[service+'-cb'].cur_rsp_time_95 =  monitoring_data[service]['rt']
                                            cb_val = cb_controllers[service+"-cb"].exec()
                                            create = destination_rule_crud.patch_circuit_breaker(service_name=service, max_requests=cb_val, name_space="default")
                                            if not create:
                                                destination_rule_crud.create_circuit_breaker(service_name=service, max_requests=cb_val, name_space="default")
                                    time.sleep(5)
                                func.delete_retrys(service_list=services_list, pc_ver_list=pc_versions, retry_attempt=retry_attempt, retry_interval=retry_interval)
                                log_end_time = int(time.time() * 1000)
                                log_dict = {
                                    "traffic": traffic,
                                    "cb_controller": cb_cont,
                                    "retry_controller": retry_cont,
                                    "retry_attempt": retry_attempt,
                                    "retry_interval": retry_interval,
                                    "start": log_start_time,
                                    "end": log_end_time
                                }
                                add_new_experiment_to_csv(log_dict)
                                
                    else:
                        # I guess it is not done now 15:57 March 16th
                        retry_controllers = func.initialize_retry_controller(service_list=services_list)
                        cb_controllers = func.initialize_cb_controllers(service_list=services_list, pc_ver_list=pc_versions)
                        log_start_time = int(time.time() * 1000)
                        while int(time.time() * 1000) < log_start_time + (experiment_duration * 1000):
                            monitoring_data = func.monitor_services(services_list, pc_versions)
                            for service in services_list:
                                if service == 'productcatalogservice':
                                    retry_controllers[service+'-retry'].cur_rsp_time_95 = monitoring_data[service+"-v1"]['rt']
                                    retry_controllers[service+'-retry'].curr_failed = monitoring_data[service+"-v1"]['failed']
                                    retry_controllers[service+'-retry'].curr_cb = monitoring_data[service+"-v1"]['cb']
                                    retry_attempt, retry_interval = retry_controllers[service+'-retry'].exec()
                                    create = virtual_service_crud.patch_retry(service_name=service,versions=pc_versions, retry_attempt=retry_attempt,interval=retry_interval)
                                    if not create:
                                        virtual_service_crud.create_retry(service_name=service,versions=pc_versions, retry_attempt=retry_attempt,interval=retry_interval)
                                    for version in pc_versions:
                                        cb_controllers[service+"-"+version+"-cb"].cur_rsp_time_95 = monitoring_data[service+"-"+version]['rt']
                                        cb_val = cb_controllers[service+"-"+version+"-cb"].exec()
                                        create = destination_rule_crud.patch_circuit_breaker_for_specific_version(service_name=service, service_version=version, max_requests=cb_val, name_space="default")
                                        if not create:
                                            destination_rule_crud.create_circuit_breaker_for_specific_version(service_name=service, service_version=version, max_requests=cb_val, name_space="default")
                                else:
                                    retry_controllers[service+'-retry'].cur_rsp_time_95 = monitoring_data[service]['rt']
                                    retry_controllers[service+'-retry'].curr_failed = monitoring_data[service]['failed']
                                    retry_controllers[service+'-retry'].curr_cb = monitoring_data[service]['cb']
                                    retry_attempt, retry_interval = retry_controllers[service+'-retry'].exec()
                                    cb_controllers[service+'-cb'].cur_rsp_time_95 =  monitoring_data[service]['rt']
                                    cb_val = cb_controllers[service+"-cb"].exec()
                                    create = destination_rule_crud.patch_circuit_breaker(service_name=service, max_requests=cb_val, name_space="default")
                                    if not create:
                                        destination_rule_crud.create_circuit_breaker(service_name=service, max_requests=cb_val, name_space="default")
                                    create = virtual_service_crud.patch_retry(service_name=service, retry_attempt=retry_attempt, interval=retry_interval)
                                    if not create:
                                        virtual_service_crud.create_retry(service_name=service, retry_attempt=retry_attempt, interval=retry_interval)

                            time.sleep(5)

                        log_end_time = int(time.time()* 1000)
                        log_dict = {
                            "traffic": traffic,
                            "cb_controller": cb_cont,
                            "retry_controller": retry_cont,
                            "retry_attempt": 0,
                            "retry_interval": 0,
                            "start": log_start_time,
                            "end": log_end_time
                        }
                        add_new_experiment_to_csv(log_dict)

            else:
                test = 'spike traffic'
                if cb_cont == 0:
                    test = "no cb controller"
                    if retry_cont == 0:
                        for retry_attempt in retry_attempts:
                            for retry_interval in retry_intervals:
                                test = "deploy static retry"
                    else:
                        test = "deploy dynamic retry"
                else:
                    test = " initialize cb controllers"
            
            log_end_time = int(time.time() * 1000)

            functions.delete_loadgenerator()





# Delete services
for service in svc_dep_list:
    with open(functions.get_project_root()+'/experiments/yaml-files/online-boutique-replicas/'+ service +'.yaml', "r") as yaml_file:
        try:
            yaml_object = yaml.safe_load_all(yaml_file)
            for part in yaml_object:
                if part["kind"] == "Deployment":
                    deployment_crud.delete_deployment(part)
                elif part["kind"] == "Service":
                    service_crud.delete_service(part)
                else:
                    logging.warning("There is a new kind in the yaml object that is not implemented.")
        except yaml.YAMLError as e:
            logging.warning("There was a problem loading the yaml file in deploying emulatade app")
            logging.warning(e)