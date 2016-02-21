from __future__ import absolute_import, print_function
import datetime
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import json
import pymysql

# Go to http://apps.twitter.com and create an app.
# The consumer key and secret will be generated for you after
consumer_key="qS95rvZodUgn2g6FywsolBvhQ"
consumer_secret="2fclwgsOi8Sw1CgWESFq0RnF75gVEG6B3bGIyzibTjXviw8huM"

# After the step above, you will be redirected to your app's page.
# Create an access token under the the "Your access token" section
access_token="700767925737656321-rXt73ZjHzXM8k9EMM8CgI0c0CXCaYiL"
access_token_secret="RtggJpUh2ZVkdbskj08FiNqQfON7L51g9sXvCVuN2v3Cw"

class StdOutListener(StreamListener):
    """ A listener handles tweets that are received from the stream.
    This is a basic listener that just prints received tweets to stdout.

    """
    def on_data(self, status):
        data = json.loads(status)
        if data.get('coordinates'):
            latitude = data.get('coordinates').get('coordinates')[0]
            longitude = data.get('coordinates').get('coordinates')[1]
            time = int(int(data.get('timestamp_ms'))/1000)
            print ("time: ",time)
            print ("latitude: ",latitude)
            print ("longitude: ",longitude)
            conndb = pymysql.connect(host='localhost', port=3306, user='root', passwd='111314', db='tweepy')
            cur = conndb.cursor()
            cur.execute("insert into coordinates(latitude, longitude, time) values(%s,%s,%s)", (latitude, longitude, int(time)))
            cur.close()
            conndb.commit()
            conndb.close()
        return True

    def on_error(self, status):
        print("error")

if __name__ == '__main__':
    l = StdOutListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    stream = Stream(auth, l)
    # stream.filter(track=['basketball'])
    stream.filter(locations = [-180, -90, 180, 90])
