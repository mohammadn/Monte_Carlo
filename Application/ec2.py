import os

os.environ['AWS_SHARED_CREDENTIALS_FILE']='./cred' 

import boto3
ec2 = boto3.client('ec2', region_name='us-east-1')
print( ec2.describe_availability_zones() )
