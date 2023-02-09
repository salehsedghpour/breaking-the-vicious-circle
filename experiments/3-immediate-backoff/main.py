from experiments.libs import functions,deployment_crud,service_account_crud, service_crud,virtual_service_crud, configmap_crud, destination_rule_crud
import logging.config
import yaml, time, re, csv


# this file should be updated with the new app

logging.config.fileConfig(functions.get_project_root()+'/experiments/logging.ini', disable_existing_loggers=False)


functions.k8s_authentication()


output_log_file_name = functions.get_project_root()+'/logs/exp-2-retry-intuition.csv'
deployment_list = ['adservice-dep', 'cartservice-dep', 'checkoutservice-dep', 'currencyservice-dep', 'emailservice-dep',
                    'frontend-dep', 'paymentservice-dep', 'productcatalogservice-dep', 'recommendationservice-dep',
                    'redis-cart-dep', 'shippingservice-dep']
services_list = ['adservice', 'cartservice', 'checkoutservice', 'currencyservice', 'emailservice',
                    'frontend', 'paymentservice', 'productcatalogservice', 'recommendationservice',
                    'redis-cart', 'shippingservice']
svc_dep_list = deployment_list + services_list


# Create the log files
with open(output_log_file_name, 'w') as csv_file:
    fieldnames = ['app', 'start', 'end', 'attempt']
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
time.sleep(60)




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

