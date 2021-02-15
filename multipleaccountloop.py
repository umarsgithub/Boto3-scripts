#If you need to run some python code across multiple AWS accounts this snippet of code is an effective way of doing so
#effectively you create a role in all of the accounts with all of the permissions you would need & then you create a policy which gives permissions either to another role or a user\group. For all of the accounts you would create a secret in secrets manager where the key is the Arn of the Role & the value is the name of the role.
import boto3, json
regions = ['eu-west-1', 'eu-west-2']
secretsManagerclient = boto3.client('secretsmanager')
secretresponse = secretsManagerclient.get_secret_value(
    SecretId='#YourSecretHere'
)
credsdict = json.loads(secretresponse['SecretString'])

for key, value in credsdict.items():
    RoleArn = key
    RoleSessionName = value
    role = boto3.client('sts').assume_role(RoleArn = RoleArn, RoleSessionName = RoleSessionName)
    credentials = role['Credentials']
    aws_access_key_id = credentials['AccessKeyId']
    aws_secret_access_key = credentials['SecretAccessKey']
    aws_session_token = credentials['SessionToken']
    session = boto3.session.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token)
