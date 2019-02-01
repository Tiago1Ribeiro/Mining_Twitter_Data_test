#!/usr/bin/env python
# encoding: utf-8

#--------------
# Future work #
#--------------
# C. 
# 	Engajamento 
# 		1) Seguidores (crescimento)
# 		2) # Respostas
# 		3) Likes/retweets
# 	Sentimento
# 		1) Polaridade das respostas e comentários
# 			exemplo: conta: @brumelianebrum => Quem matou Marielle? 
#----------------------

from tweepy import API 
from tweepy import Cursor
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream

from textblob import TextBlob                        # to analyse sentiment

from os import path
from PIL import Image
from wordcloud import WordCloud, ImageColorGenerator
from stop_words import get_stop_words
STOPWORDSpt = get_stop_words('portuguese')
STOPWORDSen = get_stop_words('english')
 
import twitter_credentials

import matplotlib.pyplot as plt
# from IPython import get_ipython
# get_ipython().run_line_magic('matplotlib', 'inline') 
import numpy as np
import pandas as pd
import re

# # # # TWITTER CLIENT # # # #
class TwitterClient():
    def __init__(self, twitter_user=None):
        self.auth = TwitterAuthenticator().authenticate_twitter_app()
        self.twitter_client = API(self.auth)

        self.twitter_user = twitter_user

    def get_twitter_client_api(self):
        return self.twitter_client

    def get_user_timeline_tweets(self, num_tweets):
        tweets = []
        for tweet in Cursor(self.twitter_client.user_timeline, id = self.twitter_user).items(num_tweets):
            tweets.append(tweet)
        return tweets

    def get_friend_list(self, num_friends):
        friend_list = []
        for friend in Cursor(self.twitter_client.friends, id = self.twitter_user).items(num_friends):
            friend_list.append(friend)
        return friend_list

    def get_home_timeline_tweets(self, num_tweets):
        home_timeline_tweets = []
        for tweet in Cursor(self.twitter_client.home_timeline, id=self.twitter_user).items(num_tweets):
            home_timeline_tweets.append(tweet)
        return home_timeline_tweets


# # # # TWITTER AUTHENTICATER # # # #
class TwitterAuthenticator():

    def authenticate_twitter_app(self):
        auth = OAuthHandler(twitter_credentials.consumer_key, twitter_credentials.consumer_secret)
        auth.set_access_token(twitter_credentials.access_token, twitter_credentials.access_secret)
        return auth

# # # # TWITTER STREAMER # # # #
class TwitterStreamer():
    """
    Class for streaming and processing live tweets.
    """
    def __init__(self):
        self.twitter_autenticator = TwitterAuthenticator()    

    def stream_tweets(self, fetched_tweets_filename, hash_tag_list):
        # This handles Twitter authetification and the connection to Twitter Streaming API
        listener = TwitterListener(fetched_tweets_filename)
        auth = self.twitter_autenticator.authenticate_twitter_app() 
        stream = Stream(auth, listener, tweet_mode='extended')

        # This line filter Twitter Streams to capture data by the keywords: 
        stream.filter(track=hash_tag_list)


# # # # TWITTER STREAM LISTENER # # # #
class TwitterListener(StreamListener):
    """
    This is a basic listener that just prints received tweets to stdout.
    """
    def __init__(self, fetched_tweets_filename):
        self.fetched_tweets_filename = fetched_tweets_filename

    def on_data(self, data):
        try:
            print(data)
            with open(self.fetched_tweets_filename, 'a', encoding='utf-8') as tf:
                tf.write(data)
            return True
        except BaseException as e:
            print("Error on_data %s" % str(e))
        return True
          
    def on_error(self, status):
        if status == 420:
            # Returning False on_data method in case rate limit occurs.
            return False
        print(status)

		

class TweetAnalyzer():
    """
    Functionality for analyzing and categorizing content from tweets.
    """

    def clean_tweet(self, tweet):
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

    def analyze_sentiment(self, tweet):
        analysis = TextBlob(self.clean_tweet(tweet))
        
        if analysis.sentiment.polarity > 0:
            return 1
        elif analysis.sentiment.polarity == 0:
            return 0
        else:
            return -1

    def tweets_to_data_frame(self, tweets):
		# Estrutura de dados 
        df = pd.DataFrame(data=[tweet.text for tweet in tweets], columns=['tweets'])
        
		# Adiciona colunas à dataFrame 'df' com id, tamanho, data, etc dos tweets
		# -----------------------------------------------------------------------
		# => Objecto tweet
		# => https://developer.twitter.com/en/docs/tweets/data-dictionary/overview/tweet-object.html
		
        df['id'] = np.array([tweet.id for tweet in tweets])
        df['tamanho'] = np.array([len(tweet.text) for tweet in tweets])
        df['data'] = np.array([tweet.created_at for tweet in tweets])
        df['fonte'] = np.array([tweet.source for tweet in tweets])
        df['likes'] = np.array([tweet.favorite_count for tweet in tweets])
        df['retweets'] = np.array([tweet.retweet_count for tweet in tweets])
		
        return df

# ------------------		
# Classes em Python
# https://www.learnpython.org/en/Classes_and_Objectsd
# ------------------
class TweetPlot():
    
    # Time Series e brincadeirita com matplotlib
	# Refs: http://pandas.pydata.org/pandas-docs/version/0.13/visualization.html
    def subplot(df,twitter_handle):
        fig1, axes = plt.subplots(nrows=2, ncols=1) 
        axes[0].set_title('@' + twitter_handle)
        likes = pd.Series(data=df['likes'].values, index=df['data'])
        likes.plot(ax=axes[0], marker = ".", alpha = 0.5, label='likes') 
        
        retweets = pd.Series(data=df['retweets'].values, index=df['data'])
        retweets.plot(ax=axes[0], marker = ".", alpha = 0.5, label = 'retweets')
        axes[0].legend()
	
        sentiment = pd.Series(data=df['sentimento'].values, index=df['data'])
        sentiment.plot(ax=axes[1], linestyle='None', marker=".")
        plt.title('sentimento')
        fig1.tight_layout()
        plt.show()
    
    # Apply word cloud 
	# https://www.datacamp.com/community/tutorials/wordcloud-python
    def wordcloud(df):
        # Start with one review:
        text = ' '.join(df['tweets']) # concatena texto
    
        # Set the stopwords list (portuguese)
        stopwords = set(STOPWORDSpt + STOPWORDSen)
        stopwords.update(['https','RT','co','aqui', 'of', 'and', 'têm', 'sido', 'with', 'queremo', 'sobre']) # adiciona elementos a um 'set'

        # Create and generate a word cloud image:
        wordcloud = WordCloud().generate(text)

        # Display the generated image:
        wordcloud = WordCloud(
        max_font_size=50, 
        max_words=100, 
        stopwords = stopwords, 
        background_color="black"
        ).generate(text)
	
        plt.figure()
        plt.imshow(wordcloud, interpolation="bilinear")
        plt.axis("off")
        plt.show()

 
if __name__ == '__main__':

    twitter_client = TwitterClient()
    tweet_analyzer = TweetAnalyzer()
    api = twitter_client.get_twitter_client_api()
    
    twitter_handle = input("Twitter handle (ignore the @): ")
    tweets = api.user_timeline(screen_name = twitter_handle, count=3000)
    
    df = tweet_analyzer.tweets_to_data_frame(tweets)

    df['sentimento'] = np.array([tweet_analyzer.analyze_sentiment(tweet) for tweet in df['tweets']])  # acrescenta coluna de sentimento 
    
    # Plots wordcloud and likes/retweets and sentiment charts
    TweetPlot.wordcloud(df)
    TweetPlot.subplot(df, twitter_handle)
	

	

	
	

	

