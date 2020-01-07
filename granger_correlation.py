import pandas
import numpy
import csv
import os
import matplotlib.pyplot as plt
import warnings
from scipy.stats               import pearsonr
from statsmodels.tsa.stattools import grangercausalitytests
from multiprocessing           import Pool, cpu_count


# Using multi-threading to gain time
def build_one_part_of_the_full_matrix(start_index):

    # Take only the needed part of the data matrices
    try:
        twitter_time_series_local = twitter_time_series[start_index:start_index + batch_size]
        scholar_time_series_local = scholar_time_series[           :n_scientists            ]
    except:
        twitter_time_series_local = twitter_time_series[start_index:n_scientists]
        scholar_time_series_local = scholar_time_series[           :n_scientists]

    # Build the granger causality matrix
    pearson = numpy.zeros((len(twitter_time_series_local), len(scholar_time_series_local)))
    granger = numpy.zeros((len(twitter_time_series_local), len(scholar_time_series_local)))
    for t, twitter_time in enumerate(twitter_time_series_local):
        print('Processing scientist number %4i...' % (start_index+t))
        for s, scholar_time in enumerate(scholar_time_series_local):
            time_array = numpy.vstack((scholar_time, twitter_time)).T
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                r, p_value_r = pearsonr(twitter_time, scholar_time)
                g_results    = grangercausalitytests(time_array, max_lag, verbose=False)
            p_values_g     = [g_results[i+1][0][g_test][1] for i in range(max_lag)]
            g_values_g     = [g_results[i+1][0][g_test][1] for i in range(max_lag)]
            p_value_g, idx = min((val, idx) for (idx, val) in enumerate(p_values_g))
            if p_value_r < 0.05:
                pearson[t,s] = r
            if p_value_g < 0.05:
                granger[t,s] = g_values_g[idx]

    # Save the matrices to build them afterwards
    numpy.save('pearson_' + str(start_index) + '.npy', pearson)
    numpy.save('granger_' + str(start_index) + '.npy', granger)


# Main code
if __name__ == '__main__':

    # Initialize scholar and twitter processed time-series
    twitter_data = pandas.read_csv('twitter_data/twitter_stats.csv', sep=',' )
    scholar_data = pandas.read_csv('scholar_data/citations.tsv',     sep='\t')

    # Initialize the time-series from the csv (tsv) datasets
    twitter_time_series = []
    scholar_time_series = []
    for i, idx in enumerate(twitter_data['id']):
        scholar_t = numpy.array(scholar_data.loc[scholar_data['id'] == idx])[0,-14:]
        if sum(scholar_t) > 0:
            twitter_t = numpy.array(twitter_data.loc[twitter_data['id'] == idx])[0,-14:]
            twitter_time_series.append(twitter_t)
            scholar_time_series.append(scholar_t)

    # Initialize some numbers for the statistical tests
    n_time_points = len(twitter_time_series[0])
    max_lag       = n_time_points//3
    g_test        = 'ssr_chi2test'

    # Initialize some numbers for the multi-threading
    n_cores_to_use = 7  # define here how many cores you want to use
    if n_cores_to_use >= cpu_count():
        print('You do not have enough cores! Number of used cores set to number of cores minus 1.')
        n_cores_to_use = cpu_count()-1
    n_scientists  = len(twitter_time_series)  # computed before
    batch_size    = n_scientists//n_cores_to_use + 1
    start_indexes = list(range(0, n_scientists, batch_size))

    # Run the function by parts
    if n_cores_to_use > 1:
        pool = Pool(n_cores_to_use)                                 # Pool(n) to use n cores
        pool.map(build_one_part_of_the_full_matrix, start_indexes)  # Process the iterable using multiple cores
    else:
        for start_index in start_indexes:
            build_one_part_of_the_full_matrix(start_index)

    # Re-build the complete matrices
    pearson = numpy.concatenate([numpy.load('pearson_' + str(s) + '.npy') for s in start_indexes], axis=0)
    granger = numpy.concatenate([numpy.load('granger_' + str(s) + '.npy') for s in start_indexes], axis=0)
    numpy.save('pearson', pearson)
    numpy.save('granger', granger)

    # Delete the partial matrices
    for start_index in start_indexes:
        os.remove('pearson_' + str(start_index) + '.npy')

    # Plot the thing
    plt.figure(0)
    plt.imshow(pearson)
    plt.figure(1)
    plt.imshow(granger)
    plt.show()
