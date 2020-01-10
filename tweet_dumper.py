# !/usr/bin/env python
# encoding: utf-8

import tweepy  # https://github.com/tweepy/tweepy
import csv
import pandas as pd
from pathlib import Path
import time

# Twitter API credentials
consumer_key    = 'nnOPnOSoOx9jrZl2OxxASZr16'
consumer_secret = 'bhgjX8S7LDOOHe51qM7qiZ3xKcx4qYRQgko7kgdQ9dR9BMhS2e'
access_key      = '1201474741250473985-gQWoxus4p40LMao3OH7ZBb7axazojV'
access_secret   = 'AOfvTfPS1Ailarqnejxxr1GaIePRM5ELoD1m9g7nTk2ig'

account = pd.read_csv('matrix_try.csv',usecols=["screen_name"])


# Twitter only allows access to a users most recent 3240 tweets with this method
def get_all_tweets(screen_name):

    # Authorize twitter, initialize tweepy
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    api = tweepy.API(auth)
    
    # Initialize a list to hold all the tweepy Tweets
    alltweets = []    
    
    # Make initial request for most recent tweets (200 is the maximum allowed count)
    try:
        new_tweets = api.user_timeline(screen_name=screen_name, count=200)
    except tweepy.TweepError:
        new_tweets = []  # if 'tweepy.error.TweepError: Not authorized.'

    # Save most recent tweets
    alltweets.extend(new_tweets)
    
    # Save the id of the oldest tweet less one
    if len(new_tweets) > 0:
        oldest = alltweets[-1].id - 1
    
    # Keep grabbing tweets until there are no tweets left to grab
    while len(new_tweets) > 0:
        
        # All subsiquent requests use the max_id param to prevent duplicates
        new_tweets = api.user_timeline(screen_name=screen_name, count=200, max_id=oldest)
        
        # Save most recent tweets
        alltweets.extend(new_tweets)
        
        # Update the id of the oldest tweet less one
        oldest = alltweets[-1].id - 1
            
    # Transform the tweepy tweets into a 2D array that will populate the csv    
    outtweets = [[tweet.id_str, tweet.created_at, tweet.text.encode('utf-8'),tweet.user] for tweet in alltweets]
    #print(alltweets[0].created_at.year)
    # Write the csv    
    file_name = Path('csv_all/%s_tweets.csv' % screen_name)
    with open(file_name, 'w', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id','created_at','text','user'])
        writer.writerows(outtweets)
    
    # Return something to the program
    print('%s tweets downloaded for %s' % (len(alltweets), screen_name))
    time.sleep(8)
    return 'a', len(alltweets)


# Pass in the username of the account you want to download
if __name__ == '__main__':
    
    account_name = account.screen_name
    [get_all_tweets(aa)  for aa in account_name[4868:]]
    
    
