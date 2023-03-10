'''
In this script, we will run different values for CB, retry interval, retry attempt, traffic
'''
from experiments.libs import functions,deployment_crud, prom_client,service_account_crud, service_crud,virtual_service_crud, configmap_crud, destination_rule_crud, controllers
import logging.config
import yaml, time, csv, math

# Configurations
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
# experiment duration: 5 minutes = 60 Datapoints
experiment_duration = 300

sleep_between_experiments = 15
capacity = 33
namespace = "default"
enforcement_point = 3

# Output log file
output_log_file_name = functions.get_project_root()+'/logs/exp-4.2-capacity-2-' + str(capacity) + '.csv'

# 5 * 5 * 5 * 7 * 5.25

traffic_ratios = [0.8, 1.0, 1.2, 1.4] # 0.6
retry_attempts = [1, 2, 5, 10, 20]
retry_intervals = ['1ms', '5ms', '10ms', '50ms', '100ms']
cb_values = [1, 5, 10, 20, 50, 500, 1000]

logging.config.fileConfig(functions.get_project_root()+'/experiments/logging.ini', disable_existing_loggers=False)
functions.k8s_authentication()

# Create the log files
with open(output_log_file_name, 'w') as csv_file:
    fieldnames = ['capacity', 'traffic', 'retry_attempt', 'retry_interval', 'cb', 'enforcement_point', 'start', 'end']
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

def deploy_loadgenerator(traffic_ratio, sleep_time):
    load_lower_bound = int(traffic_ratio * capacity)
    load_upper_bound = load_lower_bound + 1 
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
                """.format("{" + str(load_lower_bound) + ".." + str(load_upper_bound) + "..1}", sleep_time)

            yaml_object['spec']['template']['spec']['containers'][0]['env'][-1]['value'] = traffic_scenario
            yaml_object['spec']['template']['spec']['containers'][0]['env'][0]['value'] = lg_address
            deployment_crud.create_deployment(yaml_object)
        except yaml.YAMLError as e:
            logging.warning("There was a problem loading the yaml file in loadgenerator deployment")
            logging.warning(e)
        
        logging.info("Loadgenerator is successfully deployed and this series (traffic ratio = {}) of experiments will take {} seconds.".format(str(traffic_ratio), str(sleep_time)))
    yaml_file.close()

def delete_loadgenerator():
    with open(functions.get_project_root()+'/experiments/yaml-files/loadgenerator.yaml', "r") as yaml_file:
        lg_address = "frontend/cart"
        yaml_object = None
        try:
            yaml_object = yaml.safe_load(yaml_file)
            deployment_crud.delete_deployment(yaml_object)
        except yaml.YAMLError as e:
            logging.warning("There was a problem loading the yaml file in loadgenerator deployment")
            logging.warning(e)
        
        logging.info("Load generator is successfully deleted.")
    yaml_file.close()

def create_retry(retry_attempt, retry_interval, namespace, service_name):
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
                        "perTryTimeout": retry_interval,
                        "retryOn": "connect-failure,refused-stream,unavailable,cancelled,retriable-status-codes,5xx,deadline-exceeded"
                    },
                }
            ]
        }
    } 
    virtual_service_crud.create_virtual_service(vs_retry)


def delete_retry(retry_attempt, retry_interval, namespace, service_name):
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
                        "perTryTimeout": retry_interval,
                        "retryOn": "connect-failure,refused-stream,unavailable,cancelled,retriable-status-codes,5xx,deadline-exceeded"
                    },
                }
            ]
        }
    } 
    virtual_service_crud.delete_virtual_service(vs_retry)



for traffic_ratio in traffic_ratios:
    # deploy loadgenerator
    loadgenerator_sleep_time = len(retry_attempts) * len(retry_intervals) * len(cb_values) * sleep_between_experiments
    deploy_loadgenerator(traffic_ratio=traffic_ratio, sleep_time=loadgenerator_sleep_time)
    for retry_attempt in retry_attempts:
        for retry_interval in retry_intervals:
            create_retry(retry_attempt=retry_attempt, retry_interval=retry_interval, namespace=namespace, service_name=layer_3_services[-1])
            for cb_value in cb_values:
                destination_rule_crud.create_circuit_breaker(service_name=layer_3_services[-1], name_space=namespace, max_requests=cb_value)
                logging.info("The running experiment has the following values: traffic={}, attempt={}, interval={}, cb={}".format(str(traffic_ratio), str(retry_attempt), str(retry_interval), str(cb_value)))
                start_time = int(time.time() * 1000)
                time.sleep(experiment_duration)
                end_time =  int(time.time() * 1000)
                #fieldnames = ['capacity', 'traffic', 'retry_attempt', 'retry_interval', 'cb', 'enforcement_point', 'start', 'end']
                with open(output_log_file_name, 'a') as csv_file:
                    writer = csv.writer(csv_file, delimiter=",")
                    writer.writerow([
                        capacity, # capacity
                        traffic_ratio, # traffic
                        retry_attempt, # retry_attempt
                        retry_interval, # retry_interval
                        cb_value, # cb
                        enforcement_point, # enforcement point
                        start_time, # start
                        end_time # end
                ])
                csv_file.close()
                destination_rule_crud.delete_circuit_breaker(service_name=layer_3_services[-1], name_space=namespace)
                time.sleep(sleep_between_experiments)

            # delete retry
            delete_retry(retry_attempt=retry_attempt, retry_interval=retry_interval, namespace=namespace, service_name=layer_3_services[-1])
    delete_loadgenerator()


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