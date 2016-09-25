import pandas as pd
from collections import defaultdict
import pygraphviz as pgv
from datetime import datetime

import networkx as nx
from networkx.drawing.nx_pydot import write_dot
from networkx.drawing.nx_agraph import to_agraph

prefix = "w1"
roster_file = "wave1/HouseholdRoster_W1_Anon_V6.1.csv"
indderived_file = "wave1/indderived_W1_Anon_V6.1.csv"

def load_data():
    w1_roster = pd.read_csv(roster_file)
    w1_indderived = pd.read_csv(indderived_file)

    prefix = "w1"
    roster = w1_roster
    indderived = w1_indderived
    data = roster.merge(indderived, how="outer", left_on="pid", right_on="pid")
    return data

def is_valid(val):
    try:
        return int(val) and int(val) > 0
    except ValueError:
        return None
    
def shape(person):
    gender = str(person["%s_r_gen" % prefix]).lower()
    if gender == "female":
        return "oval"
    elif gender == "male":
        return "oval"
    else:
        return "square"

def gender_partner_label(person):
    gender = str(person["%s_best_gen" % prefix]).lower()
    if gender == "female":
        return "husband"
    elif gender == "male":
        return "wife"
    else:
        return "other"
    
def color(person):
    gender = str(person["%s_best_gen" % prefix]).lower()
        
    if gender == "female":
        return "purple"
    elif gender == "male":
        return "darkorange1"
    else:
        return "black"
    
def age_label(person):
    try:
        return int(person["%s_best_age_yrs" % prefix])
    except (IndexError, ValueError):
        try:
            return 2008 - int(person["age"])
        except ValueError:
            return "N/A"

def description_label(person):
    values = [
        "HHID: %s" % person["%s_hhid_x" % prefix],
        "Age: %s" % age_label(person),
        "PID: %s" % person["pid"],
        "Edu: %s" % edu_label(person),
        "Race: %s" % person["%s_best_race" % prefix],
        "Wage: %s" % person["%s_fwag" % prefix],
        "Employment: %s" % person["%s_empl_stat" % prefix]
    ]
    return "\n".join(values) 
    
def edu_label(row):
    education = row["%s_r_edu" % prefix]
    if education == "Grade 1/Sub A/Class 1":
        return "Grade 1"
    elif education == "Grade 2/Sub B/Class 2":
        return "Grade 2"
    elif education == "Grade 8/ Std. 6/Form 1":
        return "Grade 8"
    elif education == "Grade 9/Std. 7/Form 2":
        return "Grade 9"
    elif education == "Grade 10/ Std. 8/Form 3":
        return "Grade 10"
    elif education == "Grade 11/ Std. 9/Form 4":
        return "Grade 11"
    elif education == "Grade 12/Std. 10/Form 5/Matric/Senior Certificate":
        return "Grade 12"
    elif education == "Grade 12/Std. 10/Form 5/Matric/Senior Certificate":
        return "Matric"
    
    return education

def generate_graph(data):
    G = nx.DiGraph()

    for index, row in data.iterrows():
        pid = row["pid"]
        hhid = int(row["%s_hhid_x" % prefix])
        
        style = "bold" if row["%s_r_pres" % prefix] == "Resident" else "dashed"
        G.add_node(
            pid, hhid=hhid,
            color=color(row),
            style=style,
            shape=shape(row),
            label=description_label(row)
        )
        if is_valid(row["%s_r_mthpid" % prefix]):
            G.add_edge(int(row["%s_r_mthpid" % prefix]), pid, label="")
            
        if is_valid(row["%s_r_fthpid" % prefix]):
            G.add_edge(int(row["%s_r_fthpid" % prefix]), pid, label="")
            
        if is_valid(row["%s_r_parhpid" % prefix]):
            G.add_edge(int(row["%s_r_parhpid" % prefix]), pid, type="partner", label=gender_partner_label(row))

    return G

def extract_household_graphs(G):
    networks = []

    for i, l in enumerate(nx.weakly_connected_component_subgraphs(G)):
        networks.append(l)
    networks = sorted(networks, key=lambda x: len(x), reverse=True)
    return networks

def draw_graph(network, name):
    households = defaultdict(list)
    A = to_agraph(network)

    for node in network.nodes(data=True):
        hhid = node[1]["hhid"]
        households[hhid].append(node[0])
        
        # Put each household in a different cluster - messes with the partner rank
        #for idx2, household in enumerate(households.values()):
        #    cluster = A.add_subgraph(household, name="cluster%d" % idx2, color="red")
       
        
        # Place married couples on the same rank
        for edge in network.edges(data=True):
            attr = edge[2]
            if attr.get("type", "") == "partner":
                A.add_subgraph(edge[0:2], rank='same')
            
        A.draw("graphs/%s.png" % name, prog="dot")
        A.write("dot/%s.dot" % name)
 
   
now = datetime.now()
data = load_data()
print "Loading data: %ss" % (datetime.now() - now).seconds


data["age"] = pd.to_numeric(data["%s_r_dob_y" % prefix], errors="coerce")

now = datetime.now()
G = generate_graph(data)
print "Generating graph: %ss" % (datetime.now() - now).seconds

now = datetime.now()
networks = extract_household_graphs(G)
print "Extracting data: %ss" % (datetime.now() - now).seconds

now = datetime.now()
for idx in range(0, 100):
    network = networks[idx]
    draw_graph(network, idx)
print "Drawing graphs: %ss" % (datetime.now() - now).seconds
