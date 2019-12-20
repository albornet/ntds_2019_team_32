import pandas
import csv
from scholar_crawler import get_citation_statistics
from tweet_dumper import get_all_tweets


# Check whether the generated files already exist
try:
    output_file     = open('./citations.tsv', 'r')
    len_output_file = len([1 for row in output_file])
except FileNotFoundError:
    len_output_file = 1  # code for 'no existing output file'

# Read data containing a list of scientists using twitter
path  = '../twitter-researcher/data/candidates_matched.tsv'
data  = pandas.read_csv(path, sep='\t')[len_output_file-1:]

# Write scholar information in tsv files ('at' is append text, i.e. start form the end of the file)
with open('./citations.tsv', 'at') as cites_file, open('./coauthors.tsv', 'at') as coaut_file:

    # Start writing in the files
    cites_writer = csv.writer(cites_file, delimiter='\t')
    coaut_writer = csv.writer(coaut_file, delimiter='\t')

    # Write headers if the files are new
    if len_output_file == 1:
        cites_writer.writerow(['name'] + list(range(1980, 2020)))
        coaut_writer.writerow(['name'] + list(range(   1,  100)))

    # Compute and write citation statistics form the scientists names and from their dblp / scholar webpages
    for (real_name, twitter_name, dblp_url) in zip(data['real name'], data['screen name'], data['dblp url']):
        print('\nProcessing ' + real_name)
        citations, coauthors = get_citation_statistics(real_name, dblp_url)
        # months, something = get_all_tweets(twitter_name)
        cites_writer.writerow([real_name] + citations)
        coaut_writer.writerow([real_name] + coauthors)
