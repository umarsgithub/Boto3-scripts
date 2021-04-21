import boto3
import os



regions = ['eu-west-1', 'eu-west-2']
accounts = ['111185111111', '222222222222']


def lambda_handler(event, context):
    is_test = context.function_name == 'test'  # this value is injected by SAM local
    
    for account in accounts:
        if account == '111185111111':
            account_name = "prd"
        elif account == '222222222222':
            account_name = "dev"

        role = boto3.client('sts').assume_role(
            RoleArn = f"arn:aws:iam::{account}:role/{account_name}-Roleforebsenitagger",
            RoleSessionName ="AssumedRole")
        
        # Get the temporary creds into a variable
        credentials = role['Credentials']
        session = boto3.session.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'])
        
        
        for region in regions:
            instances = session.resource('ec2', region_name=region).instances.all()

            
            print(instances)
            #copyable_tag_keys = ["TestSHNew1"]
            copyable_tag_keys = os.environ['copyable_tag_keys']
        
            for instance in instances:
                copyable_tags = [t for t in instance.tags
                                 if t["Key"] in copyable_tag_keys] if instance.tags else []
                if not copyable_tags:
                    continue
        
                # Tag the EBS Volumes
                print(f"{instance.instance_id}: {instance.tags}")
                for vol in instance.volumes.all():
                    print(f"{vol.attachments[0]['Device']}: {copyable_tags}")
                    if not is_test:
                        vol.create_tags(Tags=copyable_tags)
                        vol.create_tags(Tags=[{'Key': 'instance_id', 'Value': instance.instance_id}])
        
                # Tag the Elastic Network Interfaces
                for eni in instance.network_interfaces:
                    print(f"eth{str(eni.attachment['DeviceIndex'])}: {copyable_tags}")
                    if not is_test:
                        eni.create_tags(Tags=copyable_tags)
