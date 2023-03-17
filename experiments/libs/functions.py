from kubernetes import config, client
from kubernetes.client import ApiClient
# from experiments.libs.prom_client import PromQuery
from experiments.libs import functions, deployment_crud
import logging, yaml, os, time, csv
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway


def get_project_root():
    """
    This function will return the root of the project to solve path issues
    :return:
    """
    return os.getcwd()


def load_config_file():
    """
    This function just loads the config file in the home directory
    :return:
    """
    try:
        root = get_project_root()
        with open(str(root)+'/config.yaml', 'r') as config_file:
            config_object = yaml.safe_load(config_file)
            return config_object
    except IOError:
        logging.warning("Something went wrong with opening config.yaml")
    except yaml.YAMLError:
        logging.warning("Something went wrong with loading config.yaml as a proper yaml file")


def k8s_authentication():
    """
    This function will perform the authentication for k8s based on selected context
    :return:
    """
    try:
        config_file = load_config_file()
        if config_file['other_clusters']:
            config.load_kube_config(context=config_file["target_cluster_name"])
            logging.info("Successfully authenticated with the context {}".format(config_file["target_cluster_name"]))
        else:
            config.load_kube_config()
            logging.info("Successfully authenticated with default context")
    except config.ConfigException:
        logging.warning("Something went wrong with the K8s authentication!")


def __format_data_for_nodes(client_output):
    temp_dict = {}
    temp_list = []

    json_data = ApiClient().sanitize_for_serialization(client_output)
    if len(json_data["items"]) != 0:
        for node in json_data["items"]:
            type = "worker"
            address = ""
            if 'node-role.kubernetes.io/master' in node['metadata']['labels'].keys():
                type = "master"
            else:
                type = "worker"
            for host in node['status']['addresses']:
                if host['type'] == "InternalIP":
                    address = host['address']
            temp_dict = {
                "node": node["metadata"]["name"],
                "type": type,
                "address": address
            }
            temp_list.append(temp_dict)
    return temp_list


def get_nodes():
    """
    This function will return a list containing all nodes
    :return:
    """
    try:
        api = client.CoreV1Api()
        resp = api.list_node()
        data = __format_data_for_nodes(resp)
        logging.info("List of K8s nodes successfully fetched.")
        return data
    except client.ApiException as e:
        logging.warning("Fetching the K8s nodes has some errors.")
        logging.warning(e)


def calculate_capacity(lg_address, experiment_scenario, experiment_traffic_step_duration, experiment_duration, output_log_file_name, extra_data):
    """
    This function will perform the experiment sizing for the specific address
    :return:
    """

    prom_inst = PromQuery()
    prom_inst.start = int(time.time() * 1000)
    with open(functions.get_project_root()+'/experiments/yaml-files/loadgenerator.yaml', "r") as yaml_file:
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
                """.format(experiment_scenario, experiment_traffic_step_duration)

            yaml_object['spec']['template']['spec']['containers'][0]['env'][-1]['value'] = traffic_scenario
            yaml_object['spec']['template']['spec']['containers'][0]['env'][0]['value'] = lg_address
            deployment_crud.create_deployment(yaml_object)
        except yaml.YAMLError as e:
            logging.warning("There was a problem loading the yaml file in tuning experiments")
            logging.warning(e)
        
        time.sleep(experiment_duration)
        experiment_end = int(time.time() * 1000)

        with open(output_log_file_name, 'a') as csv_file:
            writer = csv.writer(csv_file, delimiter=",")
            writer.writerow([
                extra_data[0],
                prom_inst.start,
                experiment_end,
                extra_data[1]
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

def push_to_prom_pg(data):
    registry = CollectorRegistry()
    address = 'labumu.se'
    pg_port = "30091"
    pg_address = "http://" + address + ":" + pg_port + "/"

    g = Gauge(data['name']+"_"+data['service_name'].replace("-","_")+"_"+ data['service_version'], data['description'], registry=registry)
    g.set(data['value'])
    # g.labels([data['service_name'], data['service_version']])
    push_to_gateway(pg_address, job=data['job'], registry=registry)

    logging.info("The value {} successfully pushed to pushgateway for {}".format(str(data['value']), data['name']))


def deploy_static_loadgenerator(load_lower_bound, load_upper_bound, sleep_time=300, lg_address="frontend/cart" ):
    with open(get_project_root()+'/experiments/yaml-files/loadgenerator.yaml', "r") as yaml_file:
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
        
    yaml_file.close()  



def delete_loadgenerator():
    with open(get_project_root()+'/experiments/yaml-files/loadgenerator.yaml', "r") as yaml_file:
        yaml_object = None
        try:
            yaml_object = yaml.safe_load(yaml_file)
            deployment_crud.delete_deployment(yaml_object)
        except yaml.YAMLError as e:
            logging.warning("There was a problem loading the yaml file in loadgenerator deployment")
            logging.warning(e)
        
        logging.info("Load generator is successfully deleted.")
    yaml_file.close()


def deploy_dynamic_loadgenerator(capacity, spikes, duration, spike_duration=5, capacity_duration=45, lg_address="frontend/cart" ):
    with open(get_project_root()+'/experiments/yaml-files/loadgenerator.yaml', "r") as yaml_file:
        for_scanior = int(duration / (spike_duration+capacity_duration))       
        yaml_object = None
        try:
            yaml_object = yaml.safe_load(yaml_file)
            traffic_scenario = """
                for j in {};
                    do
                    setConcurrency {};
                    sleep {};
                    setConcurrency {};
                    sleep {};
                    done;
                echo "done";
                pkill -15 httpmon;
                """.format("{1.."+str(for_scanior)+"..1}", str(capacity), str(capacity_duration), str(spikes), str(capacity_duration))
            yaml_object['spec']['template']['spec']['containers'][0]['env'][-1]['value'] = traffic_scenario
            yaml_object['spec']['template']['spec']['containers'][0]['env'][0]['value'] = lg_address
            deployment_crud.create_deployment(yaml_object)
        except yaml.YAMLError as e:
            logging.warning("There was a problem loading the yaml file in loadgenerator deployment")
            logging.warning(e)
        
    yaml_file.close()  
