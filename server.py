#!/usr/bin/python

import socket 
import signal
import time
from time import gmtime,strftime
import pymysql
import boto3

import argparse
import json
import pprint
import sys
import urllib
import urllib.error
from urllib.request import urlopen
# import oauth2

server_type = 1

cloudSearchClient = boto3.client('cloudsearch')

def getEndPoint():
    return cloudSearchClient.describe_domains()['DomainStatusList'][0]['SearchService']['Endpoint']

cloudSearchDomainClient = boto3.client("cloudsearchdomain", endpoint_url = "http://" + getEndPoint())
oldFileRequest = None
newCursor = None
class Server:

	

	def __init__(self,port = 8180):		

		if server_type==0:		
			self.host = 'ec2-52-20-8-20.compute-1.amazonaws.com'			
			self.databaseHost = 'localhost'
			self.user = 'root'
			self.password = '111314'
			self.database = "tweepy"

		else:
			self.host = '127.0.0.1'
			self.databaseHost ='localhost'		
			self.user = 'root'
			self.password = '111314'
			self.database = 'tweepy'

		self.port = port
		self.databasePort = 3306
		self.www_dir = 'www'


	def activate_server(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			print ("Launching HTTP server on ", self.host, ":", self.port)
			self.socket.bind((self.host, self.port))

		except Exception as e:
			success = 0;
			while success != 1:
				print("Warning: Could not acquite port:", self.port, "\n")
				print("I will try later")
				time.sleep(3)

				try:
					print("Launching HTTP server on ", self.host, ":", self.port)
					self.socket.bind((self.host, self.port))
					success = 1

				except Exception as e:
					success = 0
					
					# self.shutdown()
					# import sys
					# sys.exit(1)
		print ("Server successfully acquired the socket with port:", self.port)
		print ("Press Ctrl+C to shut down the server and exit.")
		self._wait_for_connections()

	def shutdown(self):
		try:
			print("Shutting down the server")
			s.socket.shutdown(socket.SHUT_RDWR)

		except Exception as e:
			print("Warning: could not shut down the socket. Maybe it was already closed?", e)

	def _gen_headers(self, code):
		h = ''
		if (code == 200):
			h = 'HTTP/1.1 200 OK\n'
		elif(code == 404):
			h = 'HTTP/1.1 404 Not Found\n'

		current_date = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
		h += 'Date: ' + current_date + '\n'
		h += 'Server: TaoDong-WebSite-Server\n'
		h += 'Connection: close\n\n'
		return h

	def _wait_for_connections(self):
		global cloudSearchClient
		global cloudSearchDomainClient
		global oldFileRequest
		global newCursor
		while True:
			print ("Awaiting New connection")
			self.socket.listen(20)
			conn, addr = self.socket.accept()

			print ("Got connection from: ", addr)

			data = conn.recv(1024)
			string = bytes.decode(data)

			request_method = string.split(' ')[0]
			print("Method: ", request_method)
			print("Request body: ", string)

			if (request_method == 'GET') | (request_method == 'HEAD'):
				file_requested = string.split(' ')
				file_requested = file_requested[1][1:]
				file_requested = file_requested.split('?')[0]

				if(file_requested == ''):
					file_requested = 'new.html'
				try:
					file_handler = open(file_requested,'rb')
					if (request_method == 'GET'):
						response_content = file_handler.read()
					file_handler.close()
					response_headers = self._gen_headers( 200)

				except Exception as e:
					print("Warning, file not found. Serving response code 404\n", e)
					response_headers = self._gen_headers( 404)
					if (request_method == 'GET'):
						response_content = b"<html><body><p>Error 404: File not found</p><p>TaoDong-WebSite-Server</p></body></html>"

				server_response = response_headers.encode()

				if (request_method == 'GET'):
					server_response += response_content

				conn.send(server_response)
				print ("File "+file_requested+" sent successfully!")
				print ("Closing connection with client")
				conn.close()
			else:
				file_requested = string.split(' ')
				if(len(file_requested)>1):
					file_requested = file_requested[1][1:]
					keyword = file_requested.split('?')[0]
					timeRange = file_requested.split('?')[1]
					startTime = timeRange.split(',')[0]
					endTime = timeRange.split(',')[1]
					print("keyword: "+keyword+" startTime: "+startTime+" endTime: "+endTime)
					if(startTime=="" or endTime==""):						
					# print("keyword: "+keyword+" time: "+timeRange)
						now_time = int(time.time())
						start_time = now_time - 30
						nowTime = strftime("%Y-%m-%d %H:%M:%S", time.localtime(now_time))
						searchStartTime = strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time))
					# timeToCloudSearch = strftime("%Y-%m-%dT%H:%M:%SZ",gmtime())
					# timeToMySQL = strftime("%Y-%m-%d %H:%M:%S",gmtime())
					# print(gmtime())
						conndb = pymysql.connect(host='localhost', port=3306, user='root', passwd='111314', db='tweepy',charset='utf8mb4')
						cur = conndb.cursor()
						cur.execute("select * from coordinates where time>=%s and time<=%s", (searchStartTime,nowTime))
						data = cur.fetchall()
					# print("data: ", data)
						cur.close()
						conndb.commit()
						conndb.close()
						length = len(data)
						string = ""
						if length>0:
							string = '[{"syn":"yes"},'
							# string = "["
							for i in range(0,length):
								text = str(data[i][1]);
								# print (text)
								if keyword!="":
									if keyword in text:
										string += '{"latitude":"'+str(data[i][2])+'", "longitude":"'+str(data[i][3])+'"},';
										
								else:
									string += '{"latitude":"'+str(data[i][2])+'", "longitude":"'+str(data[i][3])+'"},';
							if len(string)>1:
								string = string[:-1]
							string += "]"
						message = bytes(string, 'UTF-8')
					else:
						if file_requested==oldFileRequest:
							cursor = newCursor
							string = '[{"syn":"no"},'
						else:
							cursor = "initial"
							string = '[{"syn":"yes"},'

						
						startTime = startTime+"Z"
						endTime = endTime+"Z"
						query = ("(and \'" + keyword + "\' time:[\'" + startTime + "\',\'" + endTime + "\'])")
						
						searchResponse = cloudSearchDomainClient.search(
							cursor = cursor,
							queryParser = "structured",
							query = query,
							size = 10000)

						hitRecords = searchResponse['hits']['hit']
						newCursor = searchResponse['hits']['cursor']
						# Get only coordinate data
						if(len(hitRecords) != 0):
							for record in hitRecords:
								coordinate = record['fields']['coordinates'][0].split(",")
								string += '{"latitude":"'+str(coordinate[0])+'", "longitude":"'+str(coordinate[1])+'"},';
							
						if len(string)>1:
							string = string[:-1]
						string += "]"
						message = bytes(string, 'UTF-8')
						oldFileRequest = file_requested
						print (newCursor)
						print (cursor)

					response_headers = self._gen_headers( 200)
					server_response = response_headers.encode()
					server_response += message
					# print("server_response: " + server_response.decode("UTF-8"))
					conn.send(server_response)
					print("Closing connection with client")
				conn.close()


def graceful_shutdown(sig, dummy):
	s.shutdown()
	import sys
	sys.exit()

signal.signal(signal.SIGINT, graceful_shutdown)

while True:
	try:
		print ("Starting web server")
		s = Server()
		s.activate_server()
	except (KeyboardInterrupt, SystemExit):
		print("Server Terminated.")
		break
	except Exception:
		pass


