from experiments.libs import functions, deployment_crud, service_crud, destination_rule_crud, virtual_service_crud
import logging.config
import csv, yaml, time, re
from kubernetes import client
from kubernetes.stream import stream

# For being able to disable retry check the following link
# https://github.com/istio/istio/issues/40091#issuecomment-1198075161


logging.config.fileConfig(functions.get_project_root()+'/experiments/logging.ini', disable_existing_loggers=False)
functions.k8s_authentication()

output_log_file_name = functions.get_project_root()+'/logs/exp-5-1-static-cb-retry-3-rep.csv'

# Create the log files
with open(output_log_file_name, 'w') as csv_file:
    fieldnames = ['traffic','cb_v1','cv_v2','cv_v3', 'retry', 'interval', 'start', 'end']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    csv_file.close()




deployment_list = ['adservice-dep', 'cartservice-dep', 'checkoutservice-dep', 'currencyservice-dep', 'emailservice-dep',
                    'frontend-dep', 'paymentservice-dep', 'productcatalogservice-dep-v1', 'productcatalogservice-dep-v2',
                    'productcatalogservice-dep-v3', 'recommendationservice-dep','redis-cart-dep', 'shippingservice-dep']
services_list = ['adservice', 'cartservice', 'checkoutservice', 'currencyservice', 'emailservice',
                    'frontend', 'paymentservice', 'productcatalogservice', 'recommendationservice',
                    'redis-cart', 'shippingservice']

pc_versions = ['v1', 'v2', 'v3']
cbs= [1, 50, 1000]
retrys = [1, 2, 5]
retry_intervals = ['1ms', '25ms', '50ms']
traffics = [40, 70, 100]
experiment_duration = 60


svc_dep_list = deployment_list + services_list
prometheus_host = 'labumu.se'

    


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
    combinations = len(cbs)*len(cbs)*len(cbs)*len(retrys)*len(retry_intervals)*(experiment_duration)
    functions.deploy_static_loadgenerator(traffic, traffic + 1, combinations)
    for cb_v1 in cbs:
        destination_rule_crud.create_circuit_breaker_for_specific_version("productcatalogservice", 'v1', cb_v1, "default")
        for cb_v2 in cbs:
            destination_rule_crud.create_circuit_breaker_for_specific_version("productcatalogservice", 'v2', cb_v2, "default")
            for cb_v3 in cbs:
                destination_rule_crud.create_circuit_breaker_for_specific_version("productcatalogservice", 'v3', cb_v3, "default")
                for retry in retrys:
                    for retry_interval in retry_intervals:
                        virtual_service_crud.create_versioned_retry('productcatalogservice', retry, retry_interval, pc_versions)
                        start_time = int(time.time() * 1000)
                        time.sleep(experiment_duration)
                        end_time =  int(time.time() * 1000)
                        with open(output_log_file_name, 'a') as csv_file:
                            writer = csv.writer(csv_file, delimiter=",")
                            # ['traffic','cb_v1','cv_v2','cv_v3', 'retry', 'interval', 'start', 'end']
                            writer.writerow([
                                traffic, # traffic
                                cb_v1, # cb_v1
                                cb_v2, # cb_v2
                                cb_v3, # cb_v3
                                retry, # retry
                                retry_interval, # interval
                                start_time, # start
                                end_time # end
                        ])
                        csv_file.close()
                        virtual_service_crud.delete_versioned_retry('productcatalogservice', retry, retry_interval, pc_versions)
                destination_rule_crud.delete_circuit_breaker('productcatalogservice','default', 'v3')
            destination_rule_crud.delete_circuit_breaker('productcatalogservice','default', 'v2')
        destination_rule_crud.delete_circuit_breaker('productcatalogservice','default', 'v1')
    functions.delete_loadgenerator()



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