import logging.config
from kubernetes import client


def create_deployment(deployment):
    """
    This function will create a kubernetes deployment
    :param deployment:
    :return:
    """
    try:
        api = client.AppsV1Api()
        namespace = ''
        if 'namespace' in deployment['metadata']:
            namespace = deployment['metadata']['namespace']
        else:
            namespace = 'default'
        resp = api.create_namespaced_deployment(body=deployment, namespace=namespace)

        logging.info("Deployment {} is successfully created. \n"
                     "\t Name \t\t Namespace \t Image \n"
                     "\t {} \t {} \t {}"
                     "".format(deployment['metadata']['name'],
                               resp.metadata.name,
                               resp.metadata.namespace,
                               resp.spec.template.spec.containers[0].image
                               )
                     )
    except client.ApiException as e:
        logging.warning("Deployment creation of {} did not completed, look at the following for more details".format(str(deployment['metadata']['name'])))
        logging.warning(e)


def update_deployment(deployment):
    """
    This function will update a kubernetes deployment
    :param deployment:
    :return:
    """
    try:
        api = client.AppsV1Api()
        namespace = ''
        if 'namespace' in deployment['metadata']:
            namespace = deployment['metadata']['namespace']
        else:
            namespace = 'default'
        resp = api.patch_namespaced_deployment(body=deployment, namespace=namespace,
                                               name=deployment['metadata']['name'])

        logging.info("Deployment {} is successfully updated. \n"
                     "\t Name \t\t Namespace \t Image \n"
                     "\t {} \t {} \t {}"
                     "".format(deployment['metadata']['name'],
                               resp.metadata.name,
                               resp.metadata.namespace,
                               resp.spec.template.spec.containers[0].image
                               )
                     )
    except client.ApiException as e:
        logging.warning("Deployment update of {} did not completed, look at the following for more details".format(str(deployment['metadata']['name'])))
        logging.warning(e)


def delete_deployment(deployment):
    """
    This function will delete a kubernetes deployment
    :param deployment:
    :return:
    """
    try:
        api = client.AppsV1Api()
        namespace = ''
        if 'namespace' in deployment['metadata']:
            namespace = deployment['metadata']['namespace']
        else:
            namespace = 'default'
        api.delete_namespaced_deployment(namespace=namespace,
                                               name=deployment['metadata']['name'])

        logging.info("Deployment {} is successfully deleted.".format(deployment['metadata']['name']))
    except client.ApiException as e:
        logging.warning("Deployment deletion of {} did not completed, look at the following for more details".format(str(deployment['metadata']['name'])))
        logging.warning(e)