import tweepy
import configparser
import pandas as pd
import numpy as np
import re
from textblob import TextBlob
import matplotlib.pyplot as plt

GREEN = '#2ca02c'
ORANGE = '#ff7f0e'
RED = '#d62728'

class TwitterSentimentChart:

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('my_config.ini')

        self.api_key = self.config['twitter']['api_key']
        self.api_key_secret = self.config['twitter']['api_key_secret']

        self.access_token = self.config['twitter']['access_token']
        self.access_token_secret = self.config['twitter']['access_token_secret']

        self.auth = tweepy.OAuthHandler(self.api_key, self.api_key_secret)
        self.auth.set_access_token(self.access_token, self.access_token_secret)

        self.api = tweepy.API(self.auth)

    def main(self):
        TSC.menu()
        TSC.extend_dataframe()
        TSC.create_pie_chart()

    def get_tweets(self, query, user, number_of_tweets):
        self.tweets_data = []
        self.columns = ['Time', 'User', 'Tweet']
        if self.option == '1':
            self.query = query + " -filter:retweets"
            self.tweets = tweepy.Cursor(self.api.search_tweets, q=self.query, lang="en").items(number_of_tweets)
            for tweet in self.tweets:
                self.tweets_data.append([str(tweet.created_at), tweet.user.screen_name, TSC.clean_text(tweet.text)])
            if len(self.tweets_data) == 0:
                print(f"No tweets with given topic: {query}")
                TSC.menu()
        else:
            self.tweets = tweepy.Cursor(self.api.user_timeline, screen_name=user, include_rts=False, tweet_mode='extended').items(number_of_tweets)
            for tweet in self.tweets:
                self.tweets_data.append([str(tweet.created_at), tweet.user.screen_name, TSC.clean_text(tweet.full_text)])
            if len(self.tweets_data) == 0:
                print(f"User: {user} doesnt tweet anything")
                TSC.menu()
        self.data_frame = pd.DataFrame(self.tweets_data, columns=self.columns)

    def clean_text(self, tweet):
        if type(tweet) == np.float64:
            return ""
        self.clean_tweet = tweet.lower()
        self.clean_tweet = re.sub("'", "", self.clean_tweet)
        self.clean_tweet = re.sub("@[A-Za-z0-9_]+","", self.clean_tweet)
        self.clean_tweet = re.sub("#[A-Za-z0-9_]+","", self.clean_tweet)
        self.clean_tweet = re.sub(r'http\S+', '', self.clean_tweet)
        self.clean_tweet = re.sub('[()!?]', ' ', self.clean_tweet)
        self.clean_tweet = re.sub('\[.*?\]',' ', self.clean_tweet)
        self.clean_tweet = re.sub("[^a-z0-9]"," ", self.clean_tweet)

        return self.clean_tweet

    def menu(self):
        self.tweets_topic = ''
        self.twitter_user = ''
        while True:
            print('Search tweets by keyword[1]\nGet user tweets[2]')
            self.option = input('Choose option: ')
            if self.option == '1':
                self.tweets_topic = input('Tweets topic: ')
                break
            elif self.option == '2':
                self.twitter_user = input('User: ').strip()
                try:
                    self.api.get_user(screen_name=self.twitter_user)
                    break
                except:
                    print('User does not exist. Try again.')
            else:
                print('Wrong option. Try again.')

        while True:
            self.number_of_tweets = input('Number of tweets: ')
            try:
                self.number_of_tweets = int(self.number_of_tweets)
                break
            except:
                pass
                
        if self.option == '1':
            self.chart_title = f"Tweets topic: {self.tweets_topic}\nNumber of tweets: {self.number_of_tweets}"
        else:
            self.chart_title = f"Twitter user: {self.api.get_user(screen_name=self.twitter_user).name}\nNumber of tweets: {self.number_of_tweets}"

        TSC.get_tweets(self.tweets_topic, self.twitter_user, self.number_of_tweets)

    def tweet_sentiment(self, polarity):
        if polarity < 0:
            self.sentiment = 'Negative'
        elif polarity > 0:
            self.sentiment = 'Positive'
        else:
            self.sentiment = 'Neutral'
        return self.sentiment

    def extend_dataframe(self):
        self.list_of_tweets = self.data_frame.Tweet.to_list()
        self.columns = ['Polarity', 'Sentiment']
        self.sentiment_data = []
        for tweet in self.list_of_tweets:
            self.tweet = TextBlob(tweet)
            self.polarity = self.tweet.sentiment.polarity
            self.sentiment = TSC.tweet_sentiment(self.polarity)
            self.sentiment_data.append([self.polarity, self.sentiment])
        self.sentiment_data_frame = pd.DataFrame(self.sentiment_data, columns=self.columns)

        self.data_frame = pd.concat([self.data_frame, self.sentiment_data_frame], axis=1)

    def calculate_chart_sizes(self):
        self.df_sentiment = self.data_frame.Sentiment.str.split(expand=True).stack().value_counts()
        self.all_sentiments = self.df_sentiment['Positive'] + self.df_sentiment['Neutral'] + self.df_sentiment['Negative']
        self.chart_sizes = [self.df_sentiment['Positive']/self.all_sentiments, self.df_sentiment['Neutral']/self.all_sentiments, self.df_sentiment['Negative']/self.all_sentiments]

    def create_pie_chart(self):
        self.chart_labels = 'Positive', 'Neutral', 'Negative'
        TSC.calculate_chart_sizes()
        self.colors = [GREEN, ORANGE, RED]
        
        self.fig1, self.ax1 = plt.subplots()
        self.fig1.canvas.manager.set_window_title('Sentiment Pie Chart')
        self.ax1.set_title(self.chart_title)
        self.ax1.pie(self.chart_sizes, labels=self.chart_labels, autopct='%1.1f%%',
                startangle=90, colors=self.colors, wedgeprops = { 'linewidth' : 3, 'edgecolor' : 'white' },
                textprops={'fontsize': 14})
        self.ax1.axis('equal')
        plt.show()

TSC = TwitterSentimentChart()
TSC.main()