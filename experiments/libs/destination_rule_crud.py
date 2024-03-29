import logging.config
from kubernetes import client
from kubernetes.client.rest import ApiException
from .functions import push_to_prom_pg


def create_circuit_breaker(service_name, name_space, max_requests):
    """
    :param service_name:
    :param name_space:
    :param max_requests:
    :return:
    """
    try:
        api_instance = client.CustomObjectsApi()
        cb = {
            "apiVersion": "networking.istio.io/v1alpha3",
            "kind": "DestinationRule",
            "metadata": {"name": service_name+"-cb"},
            "spec": {
                "host": service_name,
                "trafficPolicy": {
                    "connectionPool":{
                        "http": {"http2MaxRequests": max_requests}
                    }
                }
            }
        }
        api_instance.create_namespaced_custom_object(
            namespace=name_space,
            body=cb,
            group="networking.istio.io",
            version="v1alpha3",
            plural="destinationrules"
        )
        data_for_pg = {
            "name": "destination_rule_http2_max_requests",
            "description": "Value of http2MaxRequest applied to Istio as DR",
            "value": max_requests,
            "job": "circuit_breaker",
            "service_name": service_name,
            "service_version": "latest"
        }
        push_to_prom_pg(data_for_pg)
        logging.info("Circuit breaker for service %s with value of %s is successfully created. " % (str(service_name), str(max_requests)))
        return True
    except ApiException as e:
        logging.warning("Circuit breaker creation for service %s is not completed. %s" % (str(service_name), str(e)))
        return False


def create_circuit_breaker_for_specific_version(service_name, service_version, max_requests, name_space):
    """
    :param  service_name:
    :param  service_version:
    :param  namespace:
    :return:
    """
    try:
        api_instance = client.CustomObjectsApi()
        cb = {
            "apiVersion": "networking.istio.io/v1alpha3",
            "kind": "DestinationRule",
            "metadata": {"name": service_name+"-"+service_version+"-cb"},
            "spec": {
                "host": service_name,
                "subsets": [
                    {
                        "name": service_version,
                        "labels": {
                            "version": service_version,
                        },
                        "trafficPolicy": {
                            "connectionPool":{
                                "http": {"http2MaxRequests": max_requests}
                            }
                        }
                    }
                ]
            }
        }
        api_instance.create_namespaced_custom_object(
            namespace=name_space,
            body=cb,
            group="networking.istio.io",
            version="v1alpha3",
            plural="destinationrules"
        )
        data_for_pg = {
            "name": "destination_rule_http2_max_requests",
            "description": "Value of http2MaxRequest applied to Istio as DR",
            "value": max_requests,
            "job": "circuit_breaker_"+service_name,
            "service_name": service_name,
             "service_version": service_version
        }
        push_to_prom_pg(data_for_pg)

        logging.info("Circuit breaker for service %s with value of %s is successfully created. " % (str(service_name), str(max_requests)))
        return True
    except ApiException as e:
        logging.warning("Circuit breaker creation for service %s is not completed. %s" % (str(service_name), str(e)))
        return False



def delete_circuit_breaker(service_name, name_space, version=None):
    """
    :param name_space:
    :param service_name:
    :return:
    """
    if version != None:
        service_name = service_name+"-"+version
    try:
        api_instance = client.CustomObjectsApi()
        api_instance.delete_namespaced_custom_object(
            namespace=name_space,
            group="networking.istio.io",
            version="v1alpha3",
            plural="destinationrules",
            name=service_name+"-cb"
        )
        logging.info("Circuit breaker for service %s is successfully deleted. " % str(service_name))
        return True
    except ApiException as e:
        logging.warning(
            "Circuit breaker deletion for service %s is not completed. %s" % (str(service_name), str(e)))
        return False


def patch_circuit_breaker(service_name, name_space, max_requests):
    """
    :param service_name:
    :param name_space:
    :param max_requests:
    :return:
    """
    try:
        api_instance = client.CustomObjectsApi()
        cb = {
            "apiVersion": "networking.istio.io/v1alpha3",
            "kind": "DestinationRule",
            "metadata": {"name": service_name+"-cb"},
            "spec": {
                "host": service_name,
                "trafficPolicy":{
                    "connectionPool":{
                        "http": {"http2MaxRequests": max_requests}
                    }
                }
            }
        }
        api_instance.patch_namespaced_custom_object(
            name=service_name+"-cb",
            namespace=name_space,
            body=cb,
            group="networking.istio.io",
            version="v1alpha3",
            plural="destinationrules"
        )
        data_for_pg = {
            "name": "destination_rule_http2_max_requests",
            "description": "Value of http2MaxRequest applied to Istio as DR",
            "value": max_requests,
            "job": "circuit_breaker_"+service_name,
            "service_name": service_name,
            "service_version": "latest"
        }
        push_to_prom_pg(data_for_pg)
        logging.info("Circuit breaker for service %s with value of %s is successfully updated. " % (str(service_name), str(max_requests)))
        return True
    except ApiException as e:
        logging.warning("Circuit breaker update for service %s is not completed. %s" % (str(service_name), str(e)))
        return False
    

def patch_circuit_breaker_for_specific_version(service_name, service_version, max_requests, name_space):
    """
    :param  service_name:
    :param  service_version:
    :param  namespace:
    :return:
    """
    try:
        api_instance = client.CustomObjectsApi()
        cb = {
            "apiVersion": "networking.istio.io/v1alpha3",
            "kind": "DestinationRule",
            "metadata": {"name": service_name+"-"+service_version+"-cb"},
            "spec": {
                "host": service_name,
                "subsets": [
                    {
                        "name": service_version,
                        "labels": {
                            "version": service_version,
                        },
                        "trafficPolicy": {
                            "connectionPool":{
                                "http": {"http2MaxRequests": max_requests}
                            }
                        }
                    }
                ]
            }
        }
        api_instance.patch_namespaced_custom_object(
            name=service_name+"-"+service_version+"-cb",
            namespace=name_space,
            body=cb,
            group="networking.istio.io",
            version="v1alpha3",
            plural="destinationrules"
        )
        data_for_pg = {
            "name": "destination_rule_http2_max_requests",
            "description": "Value of http2MaxRequest applied to Istio as DR",
            "value": max_requests,
            "job": "circuit_breaker_"+service_name+"-"+service_version+"-cb",
            "service_name": service_name,
            "service_version": service_version
        }
        push_to_prom_pg(data_for_pg)

        logging.info("Circuit breaker for service %s with value of %s is successfully created. " % (str(service_name), str(max_requests)))
        return True
    except ApiException as e:
        logging.warning("Circuit breaker creation for service %s is not completed. %s" % (str(service_name), str(e)))
        return False

