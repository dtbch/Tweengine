from __future__ import absolute_import, print_function
import datetime
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import json
import pymysql
import time
import os
import boto3

# Go to http://apps.twitter.com and create an app.
# The consumer key and secret will be generated for you after
consumer_key="qS95rvZodUgn2g6FywsolBvhQ"
consumer_secret="2fclwgsOi8Sw1CgWESFq0RnF75gVEG6B3bGIyzibTjXviw8huM"

# After the step above, you will be redirected to your app's page.
# Create an access token under the the "Your access token" section
access_token="700767925737656321-rXt73ZjHzXM8k9EMM8CgI0c0CXCaYiL"
access_token_secret="RtggJpUh2ZVkdbskj08FiNqQfON7L51g9sXvCVuN2v3Cw"

path = "file/tweet_"
count = 0
file = None

class StdOutListener(StreamListener):
	""" A listener handles tweets that are received from the stream.
	This is a basic listener that just prints received tweets to stdout.

	"""
	def on_data(self, status):
		try:
			data = json.loads(status)
			if data.get('coordinates'):
				database_store(data)
			return True
		except (KeyboardInterrupt, SystemExit):
			print("Server Terminated.")
		except Exception as e:
			print(e)
		

def database_store(data):
	# print(data)
	longitude = '{:f}'.format(data.get('coordinates').get('coordinates')[0])
	print("lon: " + longitude)
	latitude = '{:f}'.format(data.get('coordinates').get('coordinates')[1])
	print("lat: " + latitude)
	times = int(int(data.get('timestamp_ms'))/1000)
	timeToMySQL = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(times))
	text = data.get('text')
	conndb = pymysql.connect(host='localhost', port=3306, user='root', passwd='111314', db='tweepy', charset='utf8mb4')
	cur = conndb.cursor()
	cur.execute("insert into coordinates(latitude, longitude, time, text) values(%s,%s,%s,%s)", (latitude, longitude, timeToMySQL, text))
	cur.close()
	conndb.commit()
	conndb.close()
	print (" content: " + latitude + longitude + timeToMySQL)
	return True

if __name__ == '__main__':
	# new_file_open()
	l = StdOutListener()
	auth = OAuthHandler(consumer_key, consumer_secret)
	auth.set_access_token(access_token, access_token_secret)

	stream = Stream(auth, l)
	# stream.filter(track=['basketball'])
try:
	stream.filter(locations = [-180, -90, 180, 90])
except (KeyboardInterrupt, SystemExit):
	print("Server Terminated.")
except Exception as e:
	print(e)
