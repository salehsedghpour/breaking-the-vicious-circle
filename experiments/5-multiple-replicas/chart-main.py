import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from experiments.libs import  prom_client
from matplotlib.font_manager import FontProperties
import math


def plot_figure(data):
    fig, ax = plt.subplots(figsize=(16, 6))
    # Create an empty graph
    G = nx.DiGraph()

    # Define the edges between the nodes
    edges = [
        ("Load Generator", "Front End"),
        ("Front End", "Recommendation"),
        ("Front End", "Product Catalogue"),
        ("Recommendation", "Product Catalogue"),
        ("Product Catalogue", "v1"),
        ("Product Catalogue", "v2"),
        ("Product Catalogue", "v3")
    ]

    # Add the edges to the graph
    G.add_edges_from(edges)

    # Define the positions of the nodes in the graph
    pos = {
        "Load Generator": (-2, 0),
        "Front End": (0, 0),
        "Recommendation": (1, 1),
        "Product Catalogue": (2, 0),
        "v1": (3, 1.5),
        "v2": (3.5, 0),
        "v3": (3, -1.5)
    }

    # Define the node shapes
    node_shapes = {
        "Load Generator": "h",
        "Front End": "h",
        "Recommendation": "h",
        "Product Catalogue": "8",
        "v1": "h",
        "v2": "h",
        "v3": "h"
    }

    # Define the node colors
    node_colors = {
        "Load Generator": "rosybrown",
        "Front End": "whitesmoke",
        "Recommendation": "whitesmoke",
        "Product Catalogue": "tab:blue",
        "v1": "whitesmoke",
        "v2": "whitesmoke",
        "v3": "whitesmoke"
    }

    # Define the node labels
    node_labels = {
        "Load Generator": "Load\nGenerator",
        "Front End": "Frontend",
        "Recommendation": "Recomme\nndation",
        "Product Catalogue": "Product\nCatalogue",
        "v1": "v1",
        "v2": "v2",
        "v3": "v3"
    }

    # Draw the nodes and edges of the graph
    for node in G.nodes():
        if node in ['v1', 'v2', 'v3']:
            nx.draw_networkx_nodes(G, pos, nodelist=[node], node_size=800, node_shape=node_shapes[node], node_color=node_colors[node], edgecolors='#0072c6')
        else:
            nx.draw_networkx_nodes(G, pos, nodelist=[node], node_size=3500, node_shape=node_shapes[node], node_color=node_colors[node], edgecolors='#0072c6')

    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=8, font_family='sans-serif')
    nx.draw_networkx_edges(G, pos, width=2, alpha=0.8, edge_color="gray")

    labels = {
            ("Load Generator", "Front End"): "Succ: {succ}\nFail: {fail}\nRT: {rt}ms".format(succ=str(data['client-succ']), fail=str(data['client-fail']), rt=str(data['client-rt'])), 
            ("Front End", "Recommendation"): "Succ: {succ}\nFail: {fail}\nRT: {rt}ms".format(succ=str(data['fr-succ']), fail=str(data['fr-fail']), rt=str(data['fr-rt'])), 
            ("Product Catalogue", "v1"): "Succ: {succ}\nFail: {fail}\nCB: {cb}\nRT: {rt}ms".format(succ=str(data['v1-succ']), fail=str(data['v1-fail']),cb=str(data['v1-cb']), rt=str(data['v1-rt'])), 
            ("Product Catalogue", "v2"): "Succ: {succ}\nFail: {fail}\nCB: {cb}\nRT: {rt}ms".format(succ=str(data['v2-succ']), fail=str(data['v2-fail']),cb=str(data['v2-cb']), rt=str(data['v2-rt'])), 
            ("Product Catalogue", "v3"): "Succ: {succ}\nFail: {fail}\nCB: {cb}\nRT: {rt}ms".format(succ=str(data['v3-succ']), fail=str(data['v3-fail']),cb=str(data['v3-cb']), rt=str(data['v3-rt'])), 
        }
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels, font_size=8, ax=ax)


    node_positions = [pos[node] for node in G.nodes() if node != "Load Generator"]
    x_values = [position[0] for position in node_positions]
    y_values = [position[1] for position in node_positions]
    min_x = min(x_values) - 0.5
    max_x = max(x_values) + 0.5
    min_y = min(y_values) - 0.5
    max_y = max(y_values) + 0.5
    plt.gca().add_patch(plt.Rectangle((min_x, min_y), max_x - min_x, max_y - min_y, fill=False, linestyle='dashed',  edgecolor="#0072c6"))
    ax.text(x=1.75, y=2.1, s="Online Boutique", ha="center", va="center", fontsize=14)
    # ax.text(x=-2, y=-2, s="Configruations:", ha="left", va="center", fontsize=14)
    # ax.text(x=-2, y=-2.3,  s="Queue Size:       20", ha="left", va="center", fontsize=8)
    # ax.text(x=-2, y=-2.45, s="Retry Attempts:       20", ha="left", va="center", fontsize=8)
    # ax.text(x=-2, y=-2.6,  s="Retry Intervals:       20", ha="left", va="center", fontsize=8)
    # ax.text(x=-2, y=-2.75, s="Traffic:            20", ha="left", va="center", fontsize=8)


    
    data_2 = [
        ["Queue Size v1 (CB)", data['v1-queue']],
        ["Queue Size v2 (CB)", data['v2-queue']],
        ["Queue Size v3 (CB)", data['v3-queue']],
        ["Retry Attempts", data['retry-attempt']],
        ["Retry Intervals (ms)", data['retry-interval']],
        ["Traffic Ratio", data['traffic-ratio']],    
    ]

    data_1 = [
        ["Total Requests (req)", data['total-req']],
        ["Total Succsess (req)", data['total-succ-req']],
        ["Total Failed (req)", data['total-fail-req']],
        ["Total CB (req)", data['total-cb-req']],
        ["Total Retry (req)", data['total-retry-req']],
        ["Avg. Response Time (ms)", data['avg-rt']
    ]
    ]

    table_data_1 = ax.table(cellText=data_1,
                        # colWidths=[0.1]*2,
                        bbox=[0.55, -0.1, 0.35, 0.25],
                        cellLoc='center',
                        #  rowLabels=table_header_2
                        )

    table_data_2 = ax.table(cellText=data_2,
                        # colWidths=[0.1]*2,
                        bbox=[0.1, -0.1, 0.35, 0.25],
                        cellLoc='center',
                        #  rowLabels=table_header_2
                        )

    # for (row, col), cell in table_data_1.get_celld().items():
    #     if (col == 0):
    #         cell.set_text_props(fontproperties=FontProperties(weight='bold'))
    # for (row, col), cell in table_data_2.get_celld().items():
    #     if (col == 0):
    #         cell.set_text_props(fontproperties=FontProperties(weight='bold'))



    # for i in range(0, 5):
    #     table_data[(0,i)].set_facecolor("lightgray")
    #     table_data[(2,i)].set_facecolor("lightgray")
    #     table_data[(0,i)].set_height(1)



    # Set the axis limits and remove them
    plt.xlim(-2.5, 4.5)
    plt.ylim(-3, 2.1)
    plt.axis('off')

    # Show the graph
    plt.savefig("experiments/5-multiple-replicas/charts-main/traffic-{traffic}_attempt-{attempt}_interval-{interval}_cb1-{cb1}_cb2-{cb2}_cb3-{cb3}.pdf".format(
        traffic=data['traffic-ratio'],
        attempt=data['retry-attempt'],
        interval=data['retry-interval'],
        cb1=data['v1-queue'],
        cb2=data['v2-queue'],
        cb3=data['v3-queue'] ))
    plt.close('all')
    


def clean_prom_status_codes(status_code_prom_data):
    success = {
        "data": [],
        "timestamp": [],
    }
    failed = {
        "data": [],
        "timestamp": []
    }
    circuit_broken = {
        "data": [],
        "timestamp": [],
    }

    for item in status_code_prom_data:
        if item['metric']['response_code'] == "200" and item['metric']['response_flags'] == "-":
            for val in item['values']:
                success["data"].append(float(val[1]))
                success["timestamp"].append(float(val[0]) - item['values'][0][0])
        elif item['metric']['response_flags'] == "UO":
            for val in item['values']:
                circuit_broken["data"].append(float(val[1]))
                circuit_broken["timestamp"].append(float(val[0]) - item['values'][0][0])
        elif item['metric']['response_flags'] != "UO":
            for val in item['values']:
                cur_val = (float(val[0]) - float(item['values'][0][0]))
                if cur_val in failed["timestamp"]:
                    failed['data'][failed['timestamp'].index(cur_val)] = failed['data'][failed['timestamp'].index(
                        cur_val)] + float(val[1])
                else:
                    failed["data"].append(float(val[1]))
                    failed["timestamp"].append(float(val[0]) - float(item['values'][0][0]))
    lengths = [len(success["data"]), len(failed["data"]), len(circuit_broken["data"])]
    return int(sum(success["data"])), int(sum(failed["data"])), int(sum(circuit_broken["data"])), lengths

def clean_prom_rt(response_time_prom_data):
    response_time = {
        "data": [],
        "timestamp": []
    }
    if len(response_time_prom_data) > 0:
        for item in response_time_prom_data[0]['values']:
            if not math.isnan(float(item[1])):
                response_time['data'].append(float(item[1]))
                response_time['timestamp'].append(float(item[0]) - float(response_time_prom_data[0]['values'][0][0]))
    if len(response_time["data"]) != 0:
        return int((sum(response_time['data'])/len(response_time['data']))*1000)
    else:
        return 0

def clean_prom_retry(retries_prom_data):
    retries = {
        "data": [],
        "timestamp": []
    }
    if len(retries_prom_data) > 0:
        for item in retries_prom_data[0]['values']:
            retries['data'].append(float(item[1]))
            retries['timestamp'].append(float(item[0]) - float(retries_prom_data[0]['values'][0][0]))
    return int(sum(retries['data']))









df = pd.read_csv("logs/exp-5-1-static-cb-retry-3-rep.csv")

for index, row in df.iterrows():
    data = {
        'client-succ': 0,
        'client-fail': 0,
        'client-rt': 0,
        'fr-succ':0,
        'fr-fail':0,
        'fr-rt': 0,
        'v1-succ': 0,
        'v1-fail': 0,
        'v1-cb': 0,
        'v1-rt': 0,
        'v2-succ': 0,
        'v2-fail': 0,
        'v2-cb': 0,
        'v2-rt': 0,
        'v3-succ': 0,
        'v3-fail': 0,
        'v3-cb': 0,
        'v3-rt': 0,
        'v1-queue': 0,
        'v2-queue': 0,
        'v3-queue': 0,
        'retry-attempt': 0,
        'retry-interval': 0,
        'traffic-ratio': 0,
        'total-req': 0,
        'total-succ-req': 0,
        'total-fail-req': 0,
        'total-cb-req':0,
        'total-retry-req': 0,
        'avg-rt': 0

    }
    prom_inst = prom_client.PromQuery()
    prom_inst.prom_host = "labumu.se"
    prom_inst.start = int(row['start'])
    prom_inst.end = int(row['end'])
    prom_inst.response_code = "200"
    prom_inst.namespace = "default"
    prom_inst.percentile = "0.95"
    prom_inst.warmup = 10000
    prom_inst.warmdown = 0

    data["v1-queue"] = row['cb_v1']
    data["v2-queue"] = row['cv_v2']
    data["v3-queue"] = row['cv_v3']
    data["retry-attempt"] = row['retry']
    data["retry-interval"] = row['interval']
    data["traffic-ratio"] = int(row['traffic'])/70


    

    # get data for frontend
    prom_inst.service = 'frontend'
    status_f = prom_inst.get_status_codes()
    succ_f, fail_f, cb_f , lengths= clean_prom_status_codes(status_f)
    if lengths[0] != 0:
        data["client-succ"] = int(succ_f/lengths[0])
    else:
        data["client-succ"] = 0
    if lengths[1] != 0:
        data["client-fail"] = int(fail_f/lengths[1])
    else:
        data["client-fail"] = 0
    data["client-rt"] = clean_prom_rt(prom_inst.get_response_time())
    data["total-succ-req"] = int(succ_f)
    data["total-fail-req"] = int(fail_f)
    data["total-req"] = int(50*float(row['traffic']))
    data["avg-rt"] = clean_prom_rt(prom_inst.get_response_time())



    # get data for recommendation
    prom_inst.service = 'recommendationservice'
    status_f = prom_inst.get_status_codes()
    succ_r, fail_r, cb_r , lengths= clean_prom_status_codes(status_f)
    if lengths[0] != 0:
        data["fr-succ"] = int(succ_r/lengths[0])
    else:
        data["fr-succ"] = 0
    if lengths[1] != 0:
        data["fr-fail"] = int(fail_r/lengths[1])
    else:
        data["fr-fail"] = 0
    data["fr-rt"] = clean_prom_rt(prom_inst.get_response_time())

    # get data for v1
    prom_inst.service = 'productcatalogservice'
    retried_req = prom_inst.get_retried_requests(port="3550", version='v1')
    data["total-retry-req"] = data["total-retry-req"] + clean_prom_retry(retried_req)
    retried_req = prom_inst.get_retried_requests(port="3550")
    data["total-retry-req"] = data["total-retry-req"] + clean_prom_retry(retried_req)
    status_f = prom_inst.get_status_codes(version='v1')
    succ_v1, fail_v1, cb_v1 , lengths= clean_prom_status_codes(status_f)
    if lengths[0] != 0:
        data["v1-succ"] = int(succ_v1/lengths[0])
    else:
        data["v1-succ"] = 0
    if lengths[1] != 0:
        data["v1-fail"] = int(fail_v1/lengths[1])
    else:
        data["v1-fail"] = 0
    if lengths[2] != 0:
        data["v1-cb"] = int(cb_v1/lengths[2])
    else:
        data["v1-cb"] = 0
    data["total-cb-req"] = data["total-cb-req"] + cb_v1
    data["v1-rt"] = clean_prom_rt(prom_inst.get_response_time(version='v1'))


    # get data for v2
    prom_inst.service = 'productcatalogservice'
    retried_req = prom_inst.get_retried_requests(port="3550", version='v2')
    data["total-retry-req"] = data["total-retry-req"] + clean_prom_retry(retried_req)
    status_f = prom_inst.get_status_codes(version='v2')
    succ_v2, fail_v2, cb_v2 , lengths= clean_prom_status_codes(status_f)
    if lengths[0] != 0:
        data["v2-succ"] = int(succ_v2/lengths[0])
    else:
        data["v2-succ"] = 0
    if lengths[1] != 0:
        data["v2-fail"] = int(fail_v2/lengths[1])
    else:
        data["v2-fail"] = 0
    if lengths[2] != 0:
        data["v2-cb"] = int(cb_v2/lengths[2])
    else:
        data["v2-cb"] = 0
    data["total-cb-req"] = data["total-cb-req"] + cb_v2
    data["v2-rt"] = clean_prom_rt(prom_inst.get_response_time(version='v2'))

    # get data for v3
    prom_inst.service = 'productcatalogservice'
    retried_req = prom_inst.get_retried_requests(port="3550", version='v3')
    data["total-retry-req"] = data["total-retry-req"] + clean_prom_retry(retried_req)
    status_f = prom_inst.get_status_codes(version='v3')
    succ_v3, fail_v3, cb_v3 , lengths= clean_prom_status_codes(status_f)
    if lengths[0] != 0:
        data["v3-succ"] = int(succ_v3/lengths[0])
    else:
        data["v3-succ"] = 0
    if lengths[1] != 0:
        data["v3-fail"] = int(fail_v3/lengths[1])
    else:
        data["v3-fail"] = 0
    if lengths[2] != 0:
        data["v3-cb"] = int(cb_v3/lengths[2])
    else:
        data["v3-cb"] = 0
    data["total-cb-req"] = data["total-cb-req"] + cb_v3
    data["v3-rt"] = clean_prom_rt(prom_inst.get_response_time(version='v3'))

    plot_figure(data)









