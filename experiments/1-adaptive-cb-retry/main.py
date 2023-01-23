from experiments.libs import functions,deployment_crud,service_account_crud, service_crud,virtual_service_crud, configmap_crud
import logging.config
import yaml, time, csv


# this file should be updated with the new app

logging.config.fileConfig(functions.get_project_root()+'/experiments/logging.ini', disable_existing_loggers=False)


functions.k8s_authentication()



# Experiment configuration
experiment_duration = 1500
experiment_scenario = "{50..90..10}"
experiment_traffic_step_duration = 300
services_list = ['ratings', 'reviews', 'details', 'productpage']
output_log_file_name = functions.get_project_root()+'/logs/exp-1.csv'

# Create the log files
with open(output_log_file_name, 'w') as csv_file:
    fieldnames = ['app', 'start', 'end', 'attempt']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    csv_file.close()


# Deploy Real App
for service in services_list:
    with open(functions.get_project_root()+'/experiments/yaml-files/bookinfo/real-app/'+ service +'.yaml', "r") as yaml_file:
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
        except yaml.YAMLError as e:
            logging.warning("There was a problem loading the yaml file in deploying real app experiments")
            logging.warning(e)
logging.info("Please wait for some time that all pods are readly...")
time.sleep(30)
logging.info("The experiments are just started, it takes {} minutes!".format(str(experiment_duration/60)))

for attempt in range(0,1):
    with open(functions.get_project_root()+'/experiments/yaml-files/loadgenerator.yaml', "r") as yaml_file:
        lg_address = "productpage:9080/productpage"
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
                'real-app',
                experiment_start,
                experiment_end,
                attempt
            ])
            csv_file.close()
    with open(functions.get_project_root()+'/experiments/yaml-files/loadgenerator.yaml', "r") as yaml_file:
        yaml_object = None
        try:
            yaml_object = yaml.safe_load(yaml_file)
            deployment_crud.delete_deployment(yaml_object)
        except yaml.YAMLError as e:
            logging.warning("There was a problem loading the yaml file in tuning experiments")
            logging.warning(e)

# Delete Real App
for service in services_list:
    with open(functions.get_project_root()+'/experiments/yaml-files/bookinfo/real-app/'+ service +'.yaml', "r") as yaml_file:
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
        except yaml.YAMLError as e:
            logging.warning("There was a problem loading the yaml file in deleting real-app experiments")
            logging.warning(e)
