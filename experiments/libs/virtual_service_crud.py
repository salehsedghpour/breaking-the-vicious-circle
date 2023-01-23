import logging.config
from kubernetes import client
from kubernetes.client.rest import ApiException


def create_virtual_service(virtual_service):
    """
    :param virtual_service:
    :return:
    """
    try:
        api_instance = client.CustomObjectsApi()

        api_instance.create_namespaced_custom_object(
            namespace=virtual_service['metadata']['namespace'],
            body=virtual_service,
            group="networking.istio.io",
            version="v1alpha3",
            plural="virtualservices"
        )
        logging.info("Virtual Service for service %s is successfully created. " % (str(virtual_service['metadata']['name'])))
        return True
    except ApiException as e:
        logging.warning("Virtual Service creation for service %s is not completed. %s" % (str(virtual_service['metadata']['name']), str(e)))
        return False


def delete_virtual_service(virtual_service):
    """
    :param virtual_service:
    :return:
    """
    try:
        api_instance = client.CustomObjectsApi()
        api_instance.delete_namespaced_custom_object(
            namespace=virtual_service['metadata']['namespace'],
            group="networking.istio.io",
            version="v1alpha3",
            plural="virtualservices",
            name=virtual_service['metadata']['name']
        )
        logging.info("Virtual service %s is successfully deleted. " % str(virtual_service['metadata']['name']))
        return True
    except ApiException as e:
        logging.warning(
            "Virtual service deletion %s is not completed. %s" % (str(virtual_service['metadata']['name']), str(e)))
        return False