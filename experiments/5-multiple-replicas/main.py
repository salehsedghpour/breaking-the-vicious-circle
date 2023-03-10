from experiments.libs import functions, deployment_crud, service_crud
import logging.config
import csv, yaml, time



logging.config.fileConfig(functions.get_project_root()+'/experiments/logging.ini', disable_existing_loggers=False)
functions.k8s_authentication()

# output_log_file_name = functions.get_project_root()+'/logs/exp-5-1-.csv'

# # Create the log files
# with open(output_log_file_name, 'w') as csv_file:
#     fieldnames = ['traffic','cb', 'retry', 'start', 'end']
#     writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
#     writer.writeheader()
#     csv_file.close()




deployment_list = ['adservice-dep', 'cartservice-dep', 'checkoutservice-dep', 'currencyservice-dep', 'emailservice-dep',
                    'frontend-dep', 'paymentservice-dep', 'productcatalogservice-dep-v1', 'productcatalogservice-dep-v2', 'recommendationservice-dep',
                    'redis-cart-dep', 'shippingservice-dep']
services_list = ['adservice', 'cartservice', 'checkoutservice', 'currencyservice', 'emailservice',
                    'frontend', 'paymentservice', 'productcatalogservice', 'recommendationservice',
                    'redis-cart', 'shippingservice']


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