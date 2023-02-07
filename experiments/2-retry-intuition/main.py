from experiments.libs import functions,deployment_crud,service_account_crud, service_crud,virtual_service_crud, configmap_crud, destination_rule_crud
import logging.config
import yaml, time, csv


# this file should be updated with the new app

logging.config.fileConfig(functions.get_project_root()+'/experiments/logging.ini', disable_existing_loggers=False)


functions.k8s_authentication()

# Experiment configuration
experiment_duration = 300
experiment_scenario = "{50..51..1}"
experiment_traffic_step_duration = 300
services_list = ['service1', 'service2','service3','service4','service5']
output_log_file_name = functions.get_project_root()+'/logs/exp-2-retry-intuition.csv'
cbs = [1, 10]
retry_attempts = [1, 2, 50]
retry_intervals = ["5ms", "1s"]
# Create the log files
with open(output_log_file_name, 'w') as csv_file:
    fieldnames = ['app', 'start', 'end', 'attempt']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    csv_file.close()

# Deploy Two-tier app
for service in services_list:
    with open(functions.get_project_root()+'/experiments/yaml-files/diamond-app/'+ service +'.yaml', "r") as yaml_file:
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
time.sleep(30)

for attempt in range(0,1):
    for cb in cbs:
        for retry_attempt in retry_attempts:
            for retry_interval in retry_intervals:
                destination_rule_crud.create_circuit_breaker('service5', 'default', cb)
                vs_retry = {
                    "apiVersion": "networking.istio.io/v1alpha3",
                    "kind": "VirtualService",
                    "metadata": {
                        "name": "service5-retry",
                        "namespace": "default"
                    },
                    "spec": {
                        "hosts": [
                            "service5.default.svc.cluster.local"
                        ],
                        "http": [
                            {
                                "route": [
                                    {
                                        "destination": {
                                            "host": "service5.default.svc.cluster.local",
                                        },
                                    }
                                ],
                                "retries": {
                                    "attempts": retry_attempt,
                                    "perTryTimeout": retry_interval,
                                    "retryOn": "connect-failure,refused-stream,unavailable,cancelled,retriable-status-codes,5xx,deadline-exceeded"
                                },
                            }
                        ]
                    }
                } 
                virtual_service_crud.create_virtual_service(vs_retry)

                with open(functions.get_project_root()+'/experiments/yaml-files/loadgenerator.yaml', "r") as yaml_file:
                    lg_address = "service1/end1"
                    yaml_object = None
                    experiment_start = int(time.time() * 1000)
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
                            """.format(experiment_scenario, experiment_traffic_step_duration)

                        yaml_object['spec']['template']['spec']['containers'][0]['env'][-1]['value'] = traffic_scenario
                        yaml_object['spec']['template']['spec']['containers'][0]['env'][0]['value'] = lg_address
                        deployment_crud.create_deployment(yaml_object)
                    except yaml.YAMLError as e:
                        logging.warning("There was a problem loading the yaml file in tuning experiments")
                        logging.warning(e)
                    
                    while int(time.time() * 1000) < experiment_start + (experiment_duration*1000):
                        time.sleep(5)

                    experiment_end = int(time.time() * 1000)

                    with open(output_log_file_name, 'a') as csv_file:
                        writer = csv.writer(csv_file, delimiter=",")
                        writer.writerow([
                            'emulated-app',
                            experiment_start,
                            experiment_end,
                            attempt
                        ])
                        csv_file.close()
                    destination_rule_crud.delete_circuit_breaker('service5', 'default')
                    virtual_service_crud.delete_virtual_service(vs_retry)
                with open(functions.get_project_root()+'/experiments/yaml-files/loadgenerator.yaml', "r") as yaml_file:
                    yaml_object = None
                    try:
                        yaml_object = yaml.safe_load(yaml_file)
                        deployment_crud.delete_deployment(yaml_object)
                    except yaml.YAMLError as e:
                        logging.warning("There was a problem loading the yaml file in tuning experiments")
                        logging.warning(e)


# functions.calculate_capacity('service1/end1',"{50..70..1}", 60, 120, 'logs/exp-2-capacity.log', ['capacity from 50 to 500 with step of 10', ''])


# Delete Two-tier application
for service in services_list:
    with open(functions.get_project_root()+'/experiments/yaml-files/diamond-app/'+ service +'.yaml', "r") as yaml_file:
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