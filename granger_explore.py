import matplotlib.pyplot as plt
import numpy as np
import networkx as nx
import pandas as pd

# Load Granger matrix
data_m=np.load('granger_01month.npy')

# Thresholding
thres=40
data_m[data_m<thres]=0
data_m[data_m>=thres]=1
plt.spy(data_m)
plt.show()

# Making the graph, and also printed the properties
G = nx.Graph(data_m)
degrees_list=np.zeros((len(data_m),1))

for ii in range(len(degrees_list)):
    degrees_list[ii] = G.degree([ii])[ii]
plt.hist(degrees_list);    
plt.show()

cc = nx.number_connected_components(G)
ac = nx.average_clustering(G)

print(f"Number of connected components: {cc}")
print(f"Average clustering coefficient: {ac}")

# Loading the google citation data
data_goo=pd.read_csv('citations.txt',delimiter='\t')
researcher_idx = data_goo['id'].values
researcher_hidx = data_goo['h_index'].values

# Getting the data point of top 50 degrees
degree_high = np.argsort(degrees_list[:,0])[-50:]
c=np.load('granger_indexes.npy')

hidex=[]
for ii in degree_high:
    hidex.append(researcher_hidx[np.where(researcher_idx==c[ii])])

print(researcher_hidx.mean())
print(np.array(hidex).mean())

