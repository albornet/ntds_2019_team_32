# NTDS 2019 - Team 32

## Project description

Until recently, researchers have mostly relied on classical publication tools to share their work within their field. With the increased popularity of social media, however, researchers have been starting to use Twitter to further enhance their impact across the scientific community. However, it is not clear whether this increase in Twitter usage is just following a general trend in society or whether it represents a specific strategy that turned out to be useful for publication success. In the first part of this project, we conducted a basic assessment of this newly emerging network of scientists on Twitter – by means of similarity graph analyses and spectral clustering-based predictions of features concerning Twitter behavior reported for several thousands of computer scientists, in Hadgu & Jäschke (2014). In the second part, we tried to relate this Twitter activity to activity from outside of the Twitter network. Specifically, we probed whether time-series of how many Twitter posts are published every month by the computer scientists is a good predictor of either their h-index or of the number of citations they get every year on Google Scholar. To gain predictive power, we filtered the data using a network built from co-author relationships between the scientists, as the underlying structure of those time-series.

## Usage

In order to reproduce the results of part 1, please run the basic_twitter_analysis juypter notebook, which will read in the twitter feature stored in data matrix_reci_final_preprocessed.csv. The list of features utilized are given as follows: the number of tweets, number of followers, number of friends, retweet-tweet ratio, number of conference hashtags, number of overall hashtags, number of conference mentions, number of reciprocal researcher followers, number of publications, number of organic tweets, number of global followers, number of global followees, number of researcher followers, ratio of male and female researchers, rate of PhD and professor followers, ratio of reciprocal male and female researcher followers, and ratio of reciprocal phd and professor followers.

To scrape the twitter data, please go to tweet_dumper, it will crawl the twitter data from the list.

To scrape the scholar data, simply run scholar_scraper.py (however, if you don't have a VPN service, this will be almost impossible).

To generate the granger causality matrix, run granger_correlation.py, and analyse it with granger_explore.py. To generate the results with the classifier, first run co_authorship.py to have the graph filter network, and then run graph_filtering.py, which will compute the graph filter and train the classifier both with and without the filtering.
