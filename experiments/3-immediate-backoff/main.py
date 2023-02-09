from experiments.libs import functions,deployment_crud,service_account_crud, service_crud,virtual_service_crud, configmap_crud, destination_rule_crud
import logging.config
import yaml, time, re, csv


# this file should be updated with the new app

logging.config.fileConfig(functions.get_project_root()+'/experiments/logging.ini', disable_existing_loggers=False)


functions.k8s_authentication()


output_log_file_name = functions.get_project_root()+'/logs/exp-3-immediate-controller.csv'
deployment_list = ['adservice-dep', 'cartservice-dep', 'checkoutservice-dep', 'currencyservice-dep', 'emailservice-dep',
                    'frontend-dep', 'paymentservice-dep', 'productcatalogservice-dep', 'recommendationservice-dep',
                    'redis-cart-dep', 'shippingservice-dep']
services_list = ['adservice', 'cartservice', 'checkoutservice', 'currencyservice', 'emailservice',
                    'frontend', 'paymentservice', 'productcatalogservice', 'recommendationservice',
                    'redis-cart', 'shippingservice']
svc_dep_list = deployment_list + services_list
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


# Perform the experiments without controller with static overload
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
            """.format("{110..111..1}", 300)

        yaml_object['spec']['template']['spec']['containers'][0]['env'][-1]['value'] = traffic_scenario
        yaml_object['spec']['template']['spec']['containers'][0]['env'][0]['value'] = lg_address
        deployment_crud.create_deployment(yaml_object)
    except yaml.YAMLError as e:
        logging.warning("There was a problem loading the yaml file in loadgenerator deployment")
        logging.warning(e)
    
    logging.info("Wait {wait_time} seconds for the experiments without controller and static overload to be done.".format(wait_time=str(experiment_duration)))
    time.sleep(experiment_duration)
    experiment_end = int(time.time() * 1000)

    with open(output_log_file_name, 'a') as csv_file:
        writer = csv.writer(csv_file, delimiter=",")
        writer.writerow([
            'static-110', # Traffic
            '-', #CB
            '-', # Retry
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


# Perform the experiments without controller with static overload and spikes
with open(functions.get_project_root()+'/experiments/yaml-files/loadgenerator.yaml', "r") as yaml_file:
    lg_address = "frontend/cart"
    yaml_object = None
    experiment_start = int(time.time() * 1000)
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
    time.sleep(experiment_duration)
    experiment_end = int(time.time() * 1000)

    with open(output_log_file_name, 'a') as csv_file:
        writer = csv.writer(csv_file, delimiter=",")
        writer.writerow([
            'spike-110-160', # Traffic
            '-', #CB
            '-', # Retry
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

