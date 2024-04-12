'''
Code Written by: Vijay Shankar (vijay.shankar.2110@gmail.com)
---------------Event Sample Input---------------------------
{
    "Request_no": "Req_001",
    "account_no": "xxxxxxxxxxxx",
    "region_name": "us-east-1",
    "assume_role": "arn:aws:iam::account:role_name",
    "image_id": "ami-123456789",
    "instance_class": "t2.micro",
    "iam_instance_role_arn": "arn:aws:iam::account:role_name"
    "new_key": "yes/no",
    "key_name": "ssh_key",
    "key_type": "rsa/ed25519",
    "KeyFormat": "pem/ppk",
    "max_count": 5,
    "security_group_ids": ['sg-12345','sg-456789'],
    "subnet_id": "sub-123456",
    "tag_key": "Name",
    "tag_value": "Demo-EC2"
}
'''
#importing libraries
import boto3
import botocore

sts_client = boto3.client('sts')

# function to create Key-Pair for EC2
def create_key_pair(ec2_client,key_name,key_type,key_format):
    try:
        keyPair_response = ec2_client.create_key_pair(
            KeyName=key_name,
            KeyType=key_type,
            KeyFormat=key_format
        )
        return keyPair_response
    except botocore.exceptions.ClientError as error:
        print("error while creating Key-Pair")
        raise error

# function to create EC2
def create_instance(ec2_client,image_id,instance_class,key_name,max_count,subnet_group_ids,subnet_id,iam_instance_role_arn,tag_key,tag_value):
    try:
        instance = ec2_client.create_instances(
            ImageId=image_id,
            InstanceType= instance_class,
            KeyName=key_name,
            MaxCount=max_count,
            MinCount=1,
            Monitoring={
                'Enabled': True
            },
            SecurityGroupIds=subnet_group_ids,
            SubnetId=subnet_id,
            IamInstanceProfile={
                'Arn': iam_instance_role_arn,
                'Name': 'IAM_role_for_ec2'
            },
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': tag_key,
                            'Value': tag_value
                        },
                    ]
                },
            ]
        )
        return instance
    except botocore.exceptions.ClientError as error:
        print("error while creating EC2")
        raise error

# lambda function
def handler_name(event, context):
    image_id = event['image_id']
    instance_class = event['instance_class']
    key_name = event['key_name']
    max_count = event['max_count']
    subnet_group_ids = event['subnet_group_ids']
    subnet_id = event['subnet_id']
    iam_instance_role_arn = event['iam_instance_role_arn']
    tag_key = event['tag_key']
    tag_value = event['tag_value']
    account_no = event['account_no']
    # fetching current account number
    try:
        current_account_no = boto3.client('sts').get_caller_identity().get('Account')
    except botocore.exceptions.ClientError as error:
        print("error while fetching Current Account No.")
        raise error
    region_name = event['region_name']

    # checking current/other account and assuming role 
    if account_no != current_account_no:
        try:
            stsresponse = sts_client.assume_role(RoleArn="OtherAccountARNGoesHere",RoleSessionName='newsession')
            newsession_id = stsresponse["Credentials"]["AccessKeyId"]
            newsession_key = stsresponse["Credentials"]["SecretAccessKey"]
            newsession_token = stsresponse["Credentials"]["SessionToken"]
            ec2_client = boto3.client('ec2', region_name=region_name, aws_access_key_id=newsession_id, aws_secret_access_key=newsession_key, aws_session_token=newsession_token )
        except botocore.exceptions.ClientError as error:
            print("error while Assuming Role")
            raise error
    else:
        ec2_client = boto3.client('ec2', region_name=region_name)

    # creating new key pair if key not exist.
    if event['new_key'] == 'yes':
        key_type = event["key_type"]
        key_format = event["key_format"]
        create_key_pair(ec2_client,key_name,key_type,key_format)

    ec2_response = create_instance(ec2_client,image_id,instance_class,key_name,max_count,subnet_group_ids,subnet_id,iam_instance_role_arn,tag_key,tag_value)
      
    return ec2_response