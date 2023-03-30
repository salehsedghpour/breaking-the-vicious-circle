import logging.config
from kubernetes import client


def create_configmap(configmap):
    """
    This function will create a kubernetes configmap
    :param configmap:
    :return:
    """
    try:
        namespace = ''
        if 'namespace' in configmap['metadata']:
            namespace = configmap['metadata']['namespace']
        else:
            namespace = 'default'
        api = client.CoreV1Api()
        resp = api.create_namespaced_config_map(body=configmap, namespace=namespace)

        logging.info("Configmap {} is successfully created. \n"
                     "\t Name \t\t Namespace\n"
                     "\t {} \t {}"
                     "".format(configmap['metadata']['name'],
                               resp.metadata.name,
                               resp.metadata.namespace,
                               )
                     )
    except client.ApiException as e:
        logging.warning("Configmap creation of {} did not completed, look at the following for more details".format(str(configmap['metadata']['name'])))
        logging.warning(e)


def update_configmap(configmap):
    """
    This function will update a kubernetes configmap
    :param configmap:
    :return:
    """
    try:
        api = client.CoreV1Api()
        namespace = ''
        if 'namespace' in configmap['metadata']:
            namespace = configmap['metadata']['namespace']
        else:
            namespace = 'default'
        resp = api.patch_namespaced_config_map(body=configmap, namespace=namespace,
                                               name=configmap['metadata']['name'])

        logging.info("Configmap {} is successfully updated. \n"
                     "\t Name \t\t Namespace \n"
                     "\t {} \t {}"
                     "".format(configmap['metadata']['name'],
                               resp.metadata.name,
                               resp.metadata.namespace,
                               )
                     )
    except client.ApiException as e:
        logging.warning("Configmap update of {} did not completed, look at the following for more details".format(str(configmap['metadata']['name'])))
        logging.warning(e)


def delete_configmap(configmap):
    """
    This function will delete a kubernetes configmap
    :param configmap:
    :return:
    """
    try:
        api = client.CoreV1Api()
        namespace = ''
        if 'namespace' in configmap['metadata']:
            namespace = configmap['metadata']['namespace']
        else:
            namespace = 'default'
        api.delete_namespaced_config_map(namespace=namespace,
                                               name=configmap['metadata']['name'])

        logging.info("Configmap {} is successfully deleted.".format(configmap['metadata']['name']))
    except client.ApiException as e:
        logging.warning("Configmap deletion of {} did not completed, look at the following for more details".format(str(configmap['metadata']['name'])))
        logging.warning(e)