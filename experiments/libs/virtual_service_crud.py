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


def create_versioned_retry(service_name, retry_attempt, interval, versions):
    vs = {
        "apiVersion": "networking.istio.io/v1alpha3",
        "kind": "VirtualService",
        "metadata": {
            "name": service_name+"-versioned-retry",
            "namespace": "default"
        },
        "spec": {
            "hosts": [
                service_name+".default.svc.cluster.local"
            ],
            "http": [
                {
                    "route": [
                    ],
                    "retries": {
                        "attempts": retry_attempt,
                        "perTryTimeout": interval,
                        "retryOn": "connect-failure,refused-stream,unavailable,cancelled,retriable-status-codes,5xx,deadline-exceeded"
                    },
                }
            ]
        }
    }


    for version in versions:
        weight = 0
        if 100/len(versions) % 1 == 0:
            weight = int(100/len(versions))
        elif version == versions[-1]:
            weight = int(100/len(versions)) + 1
        else:
            weight = int(100/len(versions))
        route = {
                    "destination": {
                        "host": service_name,
                        "subset": version
                    },
                    "weight": weight
                }
        vs["spec"]['http'][0]['route'].append(route)
    create_virtual_service(vs)


def delete_versioned_retry(service_name, retry_attempt, interval, versions):
    vs = {
        "apiVersion": "networking.istio.io/v1alpha3",
        "kind": "VirtualService",
        "metadata": {
            "name": service_name+"-versioned-retry",
            "namespace": "default"
        },
        "spec": {
            "hosts": [
                service_name+".default.svc.cluster.local"
            ],
            "http": [
                {
                    "route": [
                    ],
                    "retries": {
                        "attempts": retry_attempt,
                        "perTryTimeout": interval,
                        "retryOn": "connect-failure,refused-stream,unavailable,cancelled,retriable-status-codes,5xx,deadline-exceeded"
                    },
                }
            ]
        }
    }
    for version in versions:
        route = {
                    "destination": {
                        "host": service_name,
                        "subset": version
                    },
                    "weight": 10
                }
        vs["spec"]['http'][0]['route'].append(route)
    delete_virtual_service(vs)


def create_versions(service_name, versions):
    vs = {
        "apiVersion": "networking.istio.io/v1alpha3",
        "kind": "VirtualService",
        "metadata": {
            "name": service_name+"-versions",
            "namespace": "default"
        },
        "spec": {
            "hosts": [
                service_name+".default.svc.cluster.local"
            ],
            "http": [
                {
                    "route": [
                       
                    ]
                }
            ]
        }
    }
    for version in versions:
        route = {
                    "destination": {
                        "host": service_name,
                        "subset": version
                    },
                    "weight": 10
                }
        vs["spec"]['http'][0]['route'].append(route)
    create_virtual_service(vs)


def delete_versions(service_name, versions):
    vs = {
        "apiVersion": "networking.istio.io/v1alpha3",
        "kind": "VirtualService",
        "metadata": {
            "name": service_name+"-versions",
            "namespace": "default"
        },
        "spec": {
            "hosts": [
                service_name+".default.svc.cluster.local"
            ],
            "http": [
                {
                    "route": [
                       
                    ]
                }
            ]
        }
    }
    for version in versions:
        route = {
                    "destination": {
                        "host": service_name,
                        "subset": version
                    },
                    "weight": 10
                }
        vs["spec"]['http'][0]['route'].append(route)
    delete_virtual_service(vs)