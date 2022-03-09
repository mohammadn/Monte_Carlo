import os
import logging

from flask import Flask, request, render_template

app = Flask(__name__)

def doRender(tname, values={}):
	if not os.path.isfile( os.path.join(os.getcwd(), 'templates/'+tname) ):
		return render_template('index.htm')
	return render_template(tname, **values) 

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def mainPage(path):
	return doRender(path)
@app.route('/terminate')
def terminate():
	os.environ['AWS_SHARED_CREDENTIALS_FILE']='./cred' 
	
	import sys
	import boto3
	
	ids = []
	ec2 = boto3.resource('ec2', region_name='us-east-1')
	instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
	
	for instance in instances:
		ids.append(instance.id)

	if (ids != []):
		ec2.instances.filter(InstanceIds=ids).stop()
		ec2.instances.filter(InstanceIds=ids).terminate()
	return doRender( 'index.htm', {})

@app.route('/calculate', methods=['POST'])
def calculate():
	#!/usr/bin/env python3
	import queue
	import threading
	import math
	import json
	import http.client

	# Modified from: http://www.ibm.com/developerworks/aix/library/au-threadingpython/
	# and fixed with try-except around urllib call
	
	service = request.form.get('service')
	shots = int(request.form.get('shots'))
	rate = request.form.get('rate')
	digits = int(request.form.get('digits'))-1
	runs = int(request.form.get('resources'))
	eachInstanceShots = shots/runs
	count = 0
	queue = queue.Queue()
	if (service == 'lambda'):
		class ThreadUrl(threading.Thread):
			
			def __init__(self, queue, task_id):
				threading.Thread.__init__(self)
				self.queue = queue
				self.task_id = task_id
				self.incircles = []
				self.results = []
				self.resourceId = []
				self.runningTime = []

			def run(self):
				
				count = self.queue.get()
				host = "jy6u38g96k.execute-api.us-east-1.amazonaws.com"
				
				try:
					c = http.client.HTTPSConnection(host)
					jsons= '{ "key1": "'+str(int(eachInstanceShots))+'", "key2": "'+rate+'", "key3": "'+str(digits)+'"}'
					c.request("POST", "/default/test", jsons)

					response = c.getresponse()
					data = response.read().decode('utf-8')
					data = json.loads(data)
					self.incircles.extend(data[0])
					self.results.extend(data[1])
					self.runningTime.append(data[2])
					self.resourceId.append(self.task_id)
								
				except IOError:
					print( 'Failed to open ' , host ) 

				self.queue.task_done()

		def parallel_run():
			threads=[]
			
			for i in range(0, runs):
				t = ThreadUrl(queue, i)
				threads.append(t)
				t.setDaemon(True)
				t.start()		

			for x in range(0, runs):
				queue.put(count)

			queue.join()

			incircles = [t.incircles for t in threads]
			results = [t.results for t in threads]
			resourceId = [t.resourceId for t in threads]
			runningTime = [t.runningTime for t in threads]
			return incircles, results, resourceId, runningTime

		mergedIncircles = []
		mergedResults = []
		stringedResults = ''
		mergedResourceId = []
		pi = int(math.pi*(10**digits))/10**digits
		piValues = ''
		matched = 0
		roundNum = 9
		sumTime = 0

		for a in range(0,9):
			incircles, results, resourceId, runningTime = parallel_run()
			sumResults = 0
			
			# merging results arrays
			for i  in range(0, len(results)):
				for j in range(0,len(results[i])):
					mergedResults.append(results[i][j])

			# merging incircles arrays
			for i  in range(0, len(incircles)):
				mergedIncircles.append(incircles[i])

			for i  in range(0, len(resourceId)):
				mergedResourceId.append(resourceId[i])		

			# Adding up results
			for i in range(0, len(mergedResults)):
				sumResults = sumResults + mergedResults[i]

			# Adding up runningTime
			for i in range(0, len(runningTime)):
				for j in range(0,len(runningTime[i])):
					sumTime = sumTime + runningTime[i][j]
			
			# Final estimation
			finalResult = int(sumResults/len(mergedResults)*(10**digits))/10**digits
			if( pi == finalResult):
				matched = 1
				roundNum = a+1
				break
		# transform results to string 
		for i  in range(0,len(mergedResults)):
			stringedResults = stringedResults + str(mergedResults[i]) + ','
		stringedResults = stringedResults[:-1]

		
		for i in range(0,len(mergedResults)):
			piValues = piValues + str(pi) + ','
		
		comCost = sumTime*512/1024*0.0000000083
		reqCost = roundNum*runs*0.2/10**6
		finalCost = comCost + reqCost
		finalCost = f'{finalCost:.12f}'
		comCost = f'{comCost:.12f}'
		reqCost = f'{reqCost:.12f}'
		return doRender( 'result.htm', {'stringedResults': piValues + '|' + stringedResults, 'incircles': mergedIncircles, 'resourceId': mergedResourceId, 'rate': int(rate), 'roundNum': roundNum, 'matched': matched, 'finalResult': finalResult, 'pi': pi, 'finalCost': finalCost, 'shots': shots, 'rate': rate, 'resources': runs, 'digits': digits+1, 'reqCost': reqCost,'comCost': comCost})
	else:
		#running ec2 instances
		os.environ['AWS_SHARED_CREDENTIALS_FILE']='./cred' 
	
		import sys
		import boto3
		
		ec2 = boto3.resource('ec2', region_name='us-east-1')
		dnss = []
		instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
		for instance in instances:
			dnss.append(instance.public_dns_name)

		if (dnss == []):
			instances = ec2.create_instances(
				ImageId='ami-0147982d8de757491',
				MinCount=1,
				MaxCount=runs,
				InstanceType='t2.micro',)
		return doRender( 'result.htm', {})

@app.errorhandler(500)
def server_error(e):
	logging.exception('ERROR!')
	return """
	An  error occurred: <pre>{}</pre>
	""".format(e), 500

if __name__ == '__main__':
	app.run(host='127.0.0.1', port=8080, debug=True)
