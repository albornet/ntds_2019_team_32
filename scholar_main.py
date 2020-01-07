import pandas
import time
import csv
from scholar_scraper import get_citation_statistics
from http.client import RemoteDisconnected, IncompleteRead
from urllib.error import URLError

# Check whether the generated files already exist
try:
    output_file     = open('./citations.tsv', 'r')
    len_output_file = len([1 for row in output_file])
except FileNotFoundError:
    len_output_file = 1  # code for 'no existing output file'

# Read data containing a list of scientists using twitter
path = '../twitter-researcher/data/candidates_matched.tsv'
data = pandas.read_csv(path, sep='\t')[len_output_file-1:]

# Write scholar information in tsv files ('at' is append text, i.e. start form the end of the file)
with open('./citations.tsv', 'at') as cites_file, open('./coauthors.tsv', 'at') as coaut_file:

    # Start writing in the files
    cites_writer = csv.writer(cites_file, delimiter='\t')
    coaut_writer = csv.writer(coaut_file, delimiter='\t')

    # Write headers if the files are new
    if len_output_file == 1:
        cites_writer.writerow(['id', 'twitter', 'name', 'h_index', 'h_2014', 'i10_index', 'i10_2014'] + list(range(1980, 2020)))
        coaut_writer.writerow(['id', 'twitter', 'name'                                              ] + list(range(   1,  100)))

    # Compute and write citation statistics form the scientists names and from their dblp / scholar webpages
    for i, (idx, real_name, twitter_name, dblp_url) in enumerate(zip(data['id'], data['real name'], data['screen name'], data['dblp url'])):
            print('\nProcessing ' + real_name)

            # Make sure the internet connection did not break during this scientist processing
            successful_read = False
            while not successful_read:
                try:
                    h, h_2014, i10, i10_2014, citations, coauthors = get_citation_statistics(real_name, dblp_url)
                except (RemoteDisconnected, IncompleteRead, URLError):
                    print('The internet connection broke down. Trying again in 10 seconds...')
                    time.sleep(10)
                    continue
                successful_read = True

            # Write all the data for this scientist in the tsv file
            cites_writer.writerow([idx, twitter_name, real_name, h, h_2014, i10, i10_2014] + citations)
            coaut_writer.writerow([idx, twitter_name, real_name                          ] + coauthors)
