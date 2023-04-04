from experiments.libs import functions, deployment_crud, service_crud, destination_rule_crud, virtual_service_crud, configmap_crud
import logging.config
import csv, yaml, time, os
from kubernetes import client
from . import utils
# from . import func

logging.config.fileConfig(functions.get_project_root()+'/experiments/logging.ini', disable_existing_loggers=False)
functions.k8s_authentication()
api_instance = client.CoreV1Api()


output_log_file_name = functions.get_project_root()+'/logs/exp-9-controller-overload.csv'


# Create the log files
with open(output_log_file_name, 'w') as csv_file:
    fieldnames = ['app', 'spike_duration', 'capacity', 'cb_controller', 'retry_controller','retry_attempt', 'retry_interval', 'start', 'end']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    csv_file.close()

def add_new_experiment_to_csv(values):
    with open(output_log_file_name, 'a') as csv_file:
        writer = csv.writer(csv_file, delimiter=",")
        writer.writerow([
            values['app'],
            values['spike_duration'],
            values['capacity'],
            values['cb_controller'],
            values['retry_controller'],
            values['retry_attempt'],
            values['retry_interval'],
            values['start'],
            values['end']
        ])
    csv_file.close()


apps = ["online-boutique", "DeathStarBench"]

capacity = {
    "online-boutique": 33,
    "DeathStarBench": 3300
}
frontend_addresses = {
    "online-boutique": 'frontend/cart',
    "DeathStarBench": 'frontend:5000/'
}

experiment_duration = 600
sleep_between_each_experiment = 60

retry_intervals = ['1ms','25ms', '50ms']
retry_attempts = [1, 2, 5]

adaptive_retry = [1, 0]
spike_durations = [1, 5, 10, 15, 30]


for app in apps:
    # deploy services
    for resource in os.listdir(functions.get_project_root()+'/experiments/yaml-files/' +app+"/"):
        with open(functions.get_project_root()+'/experiments/yaml-files/'+app+'/'+resource, 'r') as yaml_file:
            try:
                yaml_object = yaml.safe_load_all(yaml_file)
                for part in yaml_object:
                    if part["kind"] == "Deployment":
                        deployment_crud.create_deployment(part)
                    elif part["kind"] == "Service":
                        service_crud.create_service(part)
                    elif part["kin  d"] == "ConfigMap":
                        configmap_crud.create_configmap(part)
                    else:
                        logging.warning("There is a new kind in the yaml object that is not implemented.")
            except yaml.YAMLError as e:
                logging.warning("There was a problem loading the yaml file in deploying emulatade app")
                logging.warning(e)
    logging.info("Please wait for some time that all pods are ready...")
    time.sleep(180)

    # extract a list including the name of all services
    api_response = api_instance.list_namespaced_service(namespace="default")
    services_list = []
    for item in api_response.items:
        services_list.append(item.metadata.name)
    
    for spike_duration in spike_durations:

        # Deploy loadgenerator
        loadgenerator_sleep_time = len(retry_attempts) * len(retry_intervals) * len(adaptive_retry) * (experiment_duration + sleep_between_each_experiment)
        functions.deploy_dynamic_loadgenerator(capacity=int(capacity[app]*0.6), spikes=int(capacity[app]*1.4), duration=loadgenerator_sleep_time, spike_duration=spike_duration, capacity_duration=60 - spike_duration, lg_address=frontend_addresses[app])
        
        # Configuration of resiliency patterns
        for adaptive in adaptive_retry:
            if adaptive == 1:
                # initialize controllers
                retry_controllers = utils.initialize_retry_controller(service_list=services_list)
                cb_controllers = utils.initialize_cb_controllers(service_list=services_list)
                log_start_time = int(time.time() * 1000)
                while int(time.time() * 1000) < log_start_time + (experiment_duration * 1000):
                    monitoring_data = utils.monitor_services(services_list)
                    for service in services_list:
                        # Feedback to retry controller
                        retry_controllers[service+'-retry'].cur_rsp_time_95 = monitoring_data[service]['rt']
                        retry_controllers[service+'-retry'].curr_failed = monitoring_data[service]['failed']
                        retry_controllers[service+'-retry'].curr_cb = monitoring_data[service]['cb']
                        retry_attempt, retry_interval = retry_controllers[service+'-retry'].exec()

                        # Feedback to cb controller
                        cb_controllers[service+'-cb'].cur_rsp_time_95 =  monitoring_data[service]['rt']
                        cb_val = cb_controllers[service+"-cb"].exec()

                        # Enforce output of controllers
                        created = destination_rule_crud.patch_circuit_breaker(service_name=service, max_requests=cb_val, name_space="default")
                        if not created:
                            destination_rule_crud.create_circuit_breaker(service_name=service, max_requests=cb_val, name_space="default")
                        created = virtual_service_crud.patch_retry(service_name=service, retry_attempt=retry_attempt, interval=retry_interval)
                        if not created:
                            virtual_service_crud.create_retry(service_name=service, retry_attempt=retry_attempt, interval=retry_interval)

                    time.sleep(5)
                # The experiment is done    
                log_end_time = int(time.time()* 1000)
                log_dict = {
                            "app": app,
                            "spike_duration": spike_duration,
                            "capacity": capacity[app],
                            "cb_controller": 1,
                            "retry_controller": adaptive,
                            "retry_attempt": 0,
                            "retry_interval": 0,
                            "start": log_start_time,
                            "end": log_end_time
                        }
                add_new_experiment_to_csv(log_dict)
            else:
                for retry_attempt in retry_attempts:
                    for retry_interval in retry_intervals:
                        # Initialize controllers
                        cb_controllers = utils.initialize_cb_controllers(service_list=services_list)
                        log_start_time = int(time.time() * 1000)    

                        utils.deploy_same_retrys(service_list=services_list, retry_attempt=retry_attempt, retry_interval=retry_interval)
                        while int(time.time() * 1000) < log_start_time + (experiment_duration * 1000):
                            monitoring_data = utils.monitor_services(services_list)
                            for service in services_list:
                                # Feedback to cb controller
                                cb_controllers[service+'-cb'].cur_rsp_time_95 =  monitoring_data[service]['rt']
                                cb_val = cb_controllers[service+"-cb"].exec()
                                
                                # Enforce output of controllers
                                created = destination_rule_crud.patch_circuit_breaker(service_name=service, max_requests=cb_val, name_space="default")
                                if not created:
                                    destination_rule_crud.create_circuit_breaker(service_name=service, max_requests=cb_val, name_space="default")
                            
                            time.sleep(5)
                        
                        utils.delete_retrys(service_list=services_list, retry_attempt=retry_attempt, retry_interval=retry_interval)

                        # The experiment is done    
                        log_end_time = int(time.time()* 1000)
                        log_dict = {
                                    "app": app,
                                "spike_duration": spike_duration,
                                "capacity": capacity[app],
                                    "cb_controller": 1,
                                    "retry_controller": adaptive,
                                    "retry_attempt": retry_attempt,
                                    "retry_interval": retry_interval,
                                    "start": log_start_time,
                                    "end": log_end_time
                                }
                        add_new_experiment_to_csv(log_dict)

    

    
        functions.delete_loadgenerator()


    # delete services
    for resource in os.listdir(functions.get_project_root()+'/experiments/yaml-files/' +app+"/"):
        with open(functions.get_project_root()+'/experiments/yaml-files/'+app+'/'+resource, 'r') as yaml_file:
            try:
                yaml_object = yaml.safe_load_all(yaml_file)
                for part in yaml_object:
                    if part["kind"] == "Deployment":
                        deployment_crud.delete_deployment(part)
                    elif part["kind"] == "Service":
                        service_crud.delete_service(part)
                    elif part["kind"] == "ConfigMap":
                        configmap_crud.delete_configmap(part)
                    else:
                        logging.warning("There is a new kind in the yaml object that is not implemented.")
            except yaml.YAMLError as e:
                logging.warning("There was a problem loading the yaml file in deleting ")
                logging.warning(e)
