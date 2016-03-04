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
		data = json.loads(status)
		if data.get('coordinates'):
			database_store(data)
			file_store(data)
		return True



def file_store(data):
	longitude = '{:f}'.format(data.get('coordinates').get('coordinates')[0])
	latitude = '{:f}'.format(data.get('coordinates').get('coordinates')[1])
	latlon = ""
	latlon = latlon + str(latitude) + ',' + str(longitude);
	times = int(int(data.get('timestamp_ms'))/1000)
	tweetid = data.get('id_str')
	timeToCloudSearch = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.localtime(times))
	text = data.get('text')
	tweetJSON = JSON_parse(latlon, timeToCloudSearch, text, tweetid)
	file_write(tweetJSON[1:-1])
	return True


def file_write(data):
	global count, file
	file.write(data)
	if os.path.getsize(getCurrentFilename())/1024/1024>2:
		file.write("]")
		file_close(file)
		count += 1
		new_file_open()
	else:
		file.write(",")

def new_file_open():																						
	global file
	global count
	while os.path.isfile(getCurrentFilename()):
		count += 1
	file = open(getCurrentFilename(),"a")
	file.write("[")

def file_close(file):
	file.close()
	f = open(getCurrentFilename(), 'rb+')
	f.seek(-1,2)
	if(f.read==b','):
		f.seek(-1,2)
		f.truncate()
		f.close()
	f = open(getCurrentFilename(), 'a')
	f.write("]")
	f.close()

def getCurrentFilename():
	return path + str(count) + ".json"


def JSON_parse(latlon, time, text, tweetid):
	tweetJSON = [
		{
			"type": "add",
			"id": tweetid,
			"fields": {
				"coordinates": latlon,
				"time": time,
				"tweet": text
			}
		}
	]
	return json.dumps(tweetJSON)

def database_store(data):
	longitude = '{:f}'.format(data.get('coordinates').get('coordinates')[0])
	latitude = '{:f}'.format(data.get('coordinates').get('coordinates')[1])
	times = int(int(data.get('timestamp_ms'))/1000)
	timeToMySQL = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(times))
	text = data.get('text')
	conndb = pymysql.connect(host='localhost', port=3306, user='root', passwd='111314', db='tweepy', charset='utf8mb4')
	cur = conndb.cursor()
	cur.execute("insert into coordinates(latitude, longitude, time, text) values(%s,%s,%s,%s)", (latitude, longitude, timeToMySQL, text))
	cur.close()
	conndb.commit()
	conndb.close()
	return True

if __name__ == '__main__':
	new_file_open()
	l = StdOutListener()
	auth = OAuthHandler(consumer_key, consumer_secret)
	auth.set_access_token(access_token, access_token_secret)

	stream = Stream(auth, l)
	# stream.filter(track=['basketball'])
stream.filter(locations = [-180, -90, 180, 90])
