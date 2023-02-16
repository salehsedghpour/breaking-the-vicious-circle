import experiments.libs.functions
from prometheus_api_client import PrometheusConnect
from datetime import datetime



class PromQuery:
    def __init__(self):
        # nodes = experiments.libs.functions.get_nodes()
        # if nodes[-1]['type'] == 'worker':
        #     self.prom_host = nodes[-1]['address']
        # else:
        #     self.prom_host = nodes[1]['address']
        self.prom_host = "labumu.se"
        self.prom_port = "30090"
        self.prom_address = "http://" + self.prom_host + ":" + self.prom_port + "/"
        self.warmup = 9000
        self.warmdown = 3000
        self.step = 5
        self.query = ""
        self.start = 0
        self.end = 0
        self.service = ""
        self.namespace = ""
        self.percentile = ""
        self.reporter = "source"
        self.response_code = ""

    def query_prometheus(self):
        """
            This function collects data in prometheus for a given query, in a given time interval, with a given
            warmup/warmdown time offset and a given step.
        :return:
        """
        prom = PrometheusConnect(url=self.prom_address, disable_ssl=True)
        start = datetime.fromtimestamp((self.start + self.warmup) / 1000)
        end = datetime.fromtimestamp((self.end - self.warmdown) / 1000)

        result = prom.custom_query_range(query=self.query, start_time=start, end_time=end, step=self.step)
        return result

    def get_response_time(self):
        """
        This function will get the response time for a given service in a given time interval and based on a given
        percentile
        :return:
        """
        if self.response_code == "":
            self.query = '(histogram_quantile(' + str(
                self.percentile) + ', sum(irate(istio_request_duration_milliseconds_bucket{reporter="'+ self.reporter +\
                '", destination_service=~"' + self.service + '.' + self.namespace + '.svc.cluster.local"}[1m])) ' \
                'by (le)) / 1000)'
        else:
            self.query = '(histogram_quantile(' + str(
                self.percentile) + ', sum(irate(istio_request_duration_milliseconds_bucket{reporter="' + self.reporter + \
                 '", destination_service=~"' + self.service + '.' + self.namespace + '.svc.cluster.local",' \
                 'response_code="'+ self.response_code +'"}[1m])) by (le)) / 1000)'
        result = self.query_prometheus()
        return result

    def get_status_codes(self):
        """
            This function will get the request status codes for agiven service, in agiven time interval with a given
            warmup/warmdown time offset and a given step

        """
        self.query = 'round(sum(irate(istio_requests_total{destination_service=~"' + self.service + '' \
                '.' + self.namespace + '.svc.cluster.local", reporter="source"}[1m])) by (response_code, response_flags), 0.001)'
        result = self.query_prometheus()
        return result

    def get_requests_in_queue(self):
        """
            This function will get the request in the queue for a given service
        """
        self.query = 'round(sum(irate(envoy_http_inbound_0_0_0_0_5000_downstream_rq_active{app=~"'+self.service+'"}[1m])) by (service_istio_io_canonical_name), 0.001)'
        result = self.query_prometheus()
        return result

    def get_current_queue_size(self, job="istio"):
        """
            This function will get the current queue size which is pushed in pushgateway (HTTP2MaxRequests)
        """
        self.query = 'destination_rule_http2_max_requests{exported_job="' + job + '"}'
        result = self.query_prometheus()
        return result
    
    def get_retry_attempt(self):
        """
            This function get the retry attempt which is pushed in pushgateway (attempts)
        """
        self.query = 'retry_attempts_'+self.service
        result = self.query_prometheus()
        return result
