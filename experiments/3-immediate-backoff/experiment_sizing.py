"""
The experiment sizing is just a measurement of the capacity of system
The capacity is defined by the average throughput when the average 95th percentile response times reaches to 100ms
"""

from experiments.libs import functions,deployment_crud,service_account_crud, service_crud,virtual_service_crud, configmap_crud, destination_rule_crud
import logging.config
from kubernetes import client
from kubernetes.stream import stream
import yaml, time, re

logging.config.fileConfig(functions.get_project_root()+'/experiments/logging.ini', disable_existing_loggers=False)

functions.k8s_authentication()
deployment_list = ['adservice-dep', 'cartservice-dep', 'checkoutservice-dep', 'currencyservice-dep', 'emailservice-dep',
                    'frontend-dep', 'paymentservice-dep', 'productcatalogservice-dep', 'recommendationservice-dep',
                    'redis-cart-dep', 'shippingservice-dep']
services_list = ['adservice', 'cartservice', 'checkoutservice', 'currencyservice', 'emailservice',
                    'frontend', 'paymentservice', 'productcatalogservice', 'recommendationservice',
                    'redis-cart', 'shippingservice']
svc_dep_list = deployment_list + services_list

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
time.sleep(60)


# Deploy loadgenerator
with open(functions.get_project_root()+'/experiments/yaml-files/loadgenerator.yaml', "r") as yaml_file:
    lg_address = "frontend/cart"
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
            """.format("{100..500..10}", 15)

        yaml_object['spec']['template']['spec']['containers'][0]['env'][-1]['value'] = traffic_scenario
        yaml_object['spec']['template']['spec']['containers'][0]['env'][0]['value'] = lg_address
        deployment_crud.create_deployment(yaml_object)
    except yaml.YAMLError as e:
        logging.warning("There was a problem loading the yaml file in loadgenerator deployment")
        logging.warning(e)

logging.info("Wait {wait_time} seconds for experiment sizing to be done.".format(wait_time="650"))

time.sleep(650)

pod_name = ""
api_instance = client.CoreV1Api()

pods = api_instance.list_namespaced_pod("default").items
for pod in pods:
    if pod.metadata.labels['service.istio.io/canonical-name'] == "loadgenerator":
        pod_name = pod.metadata.name
exec_command = [
    '/bin/sh',
    '-c',
    'echo This message goes to stdout; cat httpmon.log'
]
api_response = stream(api_instance.connect_get_namespaced_pod_exec,
                      pod_name,
                      'default',
                      container='main',
                      command=exec_command,
                      stderr=True,
                      stdin=False,
                      stdout=True,
                      tty=False,
                      _preload_content=True)
response_times = re.findall(r"latency95=(\d+)", api_response)
print(response_times)

throughput = re.findall(r"throughput=(\d+)", api_response)
print(throughput)


occurance_num = 20
occurance_index = 0
for i in range(len(response_times)):
    if i > occurance_num:
        all_more_than_100 = 0
        for j in range(occurance_num):
            if int(response_times[i-j]) > 100:
                all_more_than_100 = all_more_than_100 + 1
        if all_more_than_100 == occurance_num:
            occurance_index = i
            break

capacity_sum = 0
for i in range(occurance_num-1):
    capacity_sum = capacity_sum + int(throughput[occurance_index-i])

logging.info("The capacity is calculated as follows")
print("Capacity is: ", int(capacity_sum/occurance_num))


with open(functions.get_project_root()+'/experiments/yaml-files/loadgenerator.yaml', "r") as yaml_file:
    try:
        yaml_object = yaml.safe_load(yaml_file)
        deployment_crud.delete_deployment(yaml_object)
    except yaml.YAMLError as e:
        logging.warning("There was a problem loading the yaml file in loadgenerator deleting")
        logging.warning(e)

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


'''
2023-02-07 17:17:44,705 [INFO]  Wait 650 seconds for experiment sizing to be done.
['82', '82', '93', '105', '83', '75', '117', '87', '116', '230', '315', '105', '115', '101', '122', '118', '93', '115', '176', '264', '369']
['0', '93', '95', '100', '102', '99', '88', '106', '83', '106', '75', '118', '100', '110', '108', '111', '112', '94', '105', '113', '101', '124']
2023-02-07 17:28:35,225 [INFO]  The capacity is calculated as follows
Capacity is:  92
'''