import boto3

# create VPC
def create_vpc():
    vpc = ec2.create_vpc(CidrBlock='192.168.0.0/16')
    # we can assign a name to vpc, or any resource, by using tag
    vpc.create_tags(Tags=[{"Key": "Name", "Value": "default_vpc"}])
    vpc.wait_until_available()
    print(vpc.id)

# create then attach internet gateway
def internet_gateway():
    ig = ec2.create_internet_gateway()
    vpc.attach_internet_gateway(InternetGatewayId=ig.id)
    print(ig.id)

# create a route table and a public route
def create_route_table():
    route_table = vpc.create_route_table()
    route = route_table.create_route(
        DestinationCidrBlock='0.0.0.0/0',
        GatewayId=ig.id
    )
    print(route_table.id)

# create subnet
def create_subnet():
    subnet = ec2.create_subnet(CidrBlock='192.168.1.0/24', VpcId=vpc.id)
    print(subnet.id)

    # associate the route table with the subnet
    route_table.associate_with_subnet(SubnetId=subnet.id)

# Create sec group
def create_security_group():
    sec_group = ec2.create_security_group(
        GroupName='slice_0', Description='slice_0 sec group', VpcId=vpc.id)
    sec_group.authorize_ingress(
        CidrIp='0.0.0.0/0',
        IpProtocol='icmp',
        FromPort=-1,
        ToPort=-1
    )
    print(sec_group.id)

# Create instance
def create_ec2_instance():
    instances = ec2.create_instances(
        ImageId='ami-835b4efa', InstanceType='t2.micro', MaxCount=1, MinCount=1,
        NetworkInterfaces=[{'SubnetId': subnet.id, 'DeviceIndex': 0, 'AssociatePublicIpAddress': True, 'Groups': [sec_group.group_id]}])
    instances[0].wait_until_running()
    print(instances[0].id)

# lambda function
def handler_name(event, context):

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
            ec2_client = boto3.resource('ec2', region_name=region_name, aws_access_key_id=newsession_id, aws_secret_access_key=newsession_key, aws_session_token=newsession_token )
        except botocore.exceptions.ClientError as error:
            print("error while Assuming Role")
            raise error
    else:
        ec2_client = boto3.resource('ec2', region_name=region_name)

