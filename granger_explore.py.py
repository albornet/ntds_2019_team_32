import matplotlib.pyplot as plt
import numpy as np
import networkx as nx
import pandas as pd


#data_m=np.load('pearson_01.npy')
data_m=np.load('granger_01month.npy')

# Make the adjacency matrix symmetric (because it has to) save it
#n_non_symmetric_values = np.count_nonzero(data_m - data_m.transpose())
#if n_non_symmetric_values > 0:
    #percent_non_symmetric = 100.0*n_non_symmetric_values/data_m.sum()
    #print('Completing the coauthor matrix (%2i%% non symmetric values).' % (percent_non_symmetric))
#    data_m = (data_m + data_m.transpose())/2


thres=40
data_m[data_m<thres]=0
data_m[data_m>=thres]=1
plt.spy(data_m)
plt.show()

G = nx.Graph(data_m)
#print(nx.degree(G))
print(nx.number_connected_components(G))
#print(nx.average_clustering(G))

degrees_list=np.zeros((len(data_m),1))

for ii in range(len(degrees_list)):
    degrees_list[ii] = G.degree([ii])[ii]
plt.hist(degrees_list);    
plt.show()

cc = nx.number_connected_components(G)
ca = nx.average_clustering(G)

print(f"Number of connected components: {cc}")
print(f"Average clustering coefficient: {ca}")

data_goo=pd.read_csv('citations.txt',delimiter='\t')

researcher_idx = data_goo['id'].values
researcher_hidx = data_goo['h_index'].values

degree_high = np.argsort(degrees_list[:,0])[-50:]
c=np.load('granger_indexes.npy')

hidex=[]
for ii in degree_high:
    hidex.append(researcher_hidx[np.where(researcher_idx==c[ii])])

print(researcher_hidx.mean())
print(np.array(hidex).mean())

