'''
Code Written by: Vijay Shankar (vijay.shankar.2110@gmail.com)
---------------Event Sample Input---------------------------
{
    "Request_no": "Req_001",
    "account_no": "xxxxxxxxxxxx",
    "region_name": "us-east-1",
    "assume_role": "arn:aws:iam::account:role_name",
    "key_name": "ssh_key",
    "key_type": "rsa/ed25519",
    "KeyFormat": "pem/ppk",
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
            KeyFormat=key_format,
            TagSpecifications=[
                {
                    'ResourceType': 'key-pair',
                    'Tags': [
                        {
                            'Key': tag_key,
                            'Value': tag_value
                        },
                    ]
                },
            ]
        )
        return keyPair_response
    except botocore.exceptions.ClientError as error:
        print("error while creating Key-Pair")
        raise error

# lambda function
def handler_name(event, context):
    key_name = event['key_name']
    tag_key = event['tag_key']
    tag_value = event['tag_value']
    account_no = event['account_no']
    key_type = event["key_type"]
    key_format = event["key_format"]
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
    key_pair_response = create_key_pair(ec2_client,key_name,key_type,key_format)
    
    return key_pair_response


