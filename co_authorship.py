import pandas
import numpy
import html
import csv
import os
import matplotlib.pyplot as plt
rebuild_from_raw = 0

# Build the matrix from raw data
if rebuild_from_raw:

    # Deal with html escaped characters and errors during the data collection in the coauthors file
    with open('scholar_data/coauthors.tsv', 'r') as f, open('scholar_data/coauthors_2.tsv', 'w') as g:
        g.write(''.join(html.unescape(f.read()).split(' <span class=""homonym-nr')))
    os.remove('scholar_data/coauthors.tsv')
    os.rename('scholar_data/coauthors_2.tsv', 'scholar_data/coauthors.tsv')

    # Initialize scholar and twitter processed time-series
    twitter_data = pandas.read_csv('twitter_data/twitter_stats_month.csv',         sep=',' ).sort_values(by='id')
    scholar_data = pandas.read_csv('scholar_data/citations.tsv',                   sep='\t').sort_values(by='id')
    coauths_list = pandas.read_csv('scholar_data/coauthors.tsv', low_memory=False, sep='\t').sort_values(by='id')

    # Remove the people that are not in the twitter_data list (no active twitter account anymore)
    twitter_ids  = list(twitter_data['id'])
    drop_indexes = []
    for i, idx in enumerate(scholar_data['id']):
        if idx not in twitter_ids:
            drop_indexes.append(i)
    scholar_data = scholar_data.drop(drop_indexes)
    coauths_list = coauths_list.drop(drop_indexes)

    # Remove the scientists that have no publications
    cited_authors = list(scholar_data.loc[:,'2006':'2019'].sum(axis=1) > 0)
    cited_authors = list(scholar_data.loc[:,'2006':'2019'].sum(axis=1) > 0)

    twitter_data = twitter_data[cited_authors].reset_index(drop=True)
    coauths_list = coauths_list[cited_authors].reset_index(drop=True)
    scholar_data = scholar_data[cited_authors].reset_index(drop=True)

    # Build the graph from coauthors
    scientist_names = list(scholar_data['name'])
    n_scientists    = len(scholar_data)
    A_coauthors     = numpy.zeros((n_scientists, n_scientists), dtype=int)
    print('Building the coauthors adjajency matrix:')
    for i, row in coauths_list.iterrows():
        if i%1000 == 0:
            print('\t%4i scientists over %4i done...' % (i, n_scientists))
        for coauthor_name in row['1':'1021'].dropna():
            if coauthor_name in scientist_names:
                A_coauthors[i, scientist_names.index(coauthor_name)] = 1

    # Save the re-ordered data and the raw matrix
    numpy.save('twitter_data/twitter_signals', twitter_data)
    numpy.save('scholar_data/scholar_signals', scholar_data)
    numpy.save('scholar_data/A_coauthors_raw', A_coauthors)

# Load the raw matrix
else:
    A_coauthors = numpy.load('scholar_data/A_coauthors_raw.npy')

# Make the adjacency matrix symmetric (because it has to) save it
n_non_symmetric_values = numpy.count_nonzero(A_coauthors - A_coauthors.transpose())
if n_non_symmetric_values > 0:
    percent_non_symmetric = 100.0*n_non_symmetric_values/A_coauthors.sum()
    print('Completing the coauthor matrix (%2i%% non symmetric values).' % (percent_non_symmetric))
    A_coauthors = (A_coauthors + A_coauthors.transpose()).clip(max=1)
numpy.save('scholar_data/A_coauthors', A_coauthors)

# Build the degree distribution
D_coauthors = A_coauthors.sum(axis=0)
hist_normal = numpy.ones(D_coauthors.shape[0])/D_coauthors.shape[0]

# Plot everything
print(D_coauthors.max())
fig, axes = plt.subplots(1, 2, figsize=(16, 4))
axes[0].set_title('Coauthors graph adjacency matrix')
axes[0].imshow(A_coauthors)
axes[1].set_title('Coauthor graph degree distribution')
axes[1].hist(D_coauthors, bins=range(0, D_coauthors.max()+1), weights=hist_normal)
plt.show()