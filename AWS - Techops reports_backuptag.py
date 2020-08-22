import boto3, time, csv, json
regions=['eu-west-1', 'eu-west-2']
key_to_find = 'Backup'
backupvalues = ['yes', 'no']

filename = time.strftime("%d%m%y" + "backuptag.csv")
oldfilepath = ("/home/umar.hussain/" + filename)
newfilepath = ("SAC/backuptag/" + filename)


with open(oldfilepath, "w", newline="") as csvfile:
  tagwriter = csv.writer(csvfile)
  tagwriter.writerow(["AWS Resource type","Backup Tag","AWS Resource", "Other1", "Other2"])

secretsManagerclient = boto3.client('secretsmanager')
secretresponse = secretsManagerclient.get_secret_value(
    SecretId = 'dev/test/sacreports'
)
credsdict = json.loads(secretresponse['SecretString'])

for key, value in credsdict.items():
    ACCESS_KEY = key
    SECRET_KEY = value
    #print(SECRET_KEY)
    session = boto3.Session(
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        #aws_session_token=SESSION_TOKEN,
    )
    regions=['eu-west-1', 'eu-west-2']
    for region in regions:
        dynamodbclient = session.client('dynamodb', region)
        dynamodbresponse = dynamodbclient.list_tables()
        #print(dynamodbresponse)
        for TableName in dynamodbresponse["TableNames"]:
            ddbresponse2 = dynamodbclient.describe_table(TableName=TableName)
            #print(dynamodbresponse2["Table"])
            Table = ddbresponse2["Table"]
            TableName = Table["TableName"]
            TableArn = Table["TableArn"]
            ddbresponse3 = dynamodbclient.list_tags_of_resource(ResourceArn=TableArn)
            ddbtags = ddbresponse3["Tags"]
            for tag in ddbtags:
                if tag["Key"] == "Backup":
                    Backuptag = str(tag["Value"])
                elif key_to_find not in [tag['Key'] for tag in ddbtags]:
                    Backuptag = "not found"
            try:
                if key_to_find not in [tag['Key'] for tag in ddbtags]:
                    #print(TableName, " ", Backuptag)
                    with open(oldfilepath, "a+", newline="") as csvfile:
                        tagwriter = csv.writer(csvfile)
                        tagwriter.writerow(["DynamoDB Table", "Backuptag not found", TableName])
            except KeyError:
                print("This is a key error")

    for region in regions:
        ec2client = session.client('ec2', region)
        ec2response = ec2client.describe_instances()
        for reservation in ec2response['Reservations']:
            for instance in reservation['Instances']:
                tags = instance["Tags"]
                for tag in tags:
                    if tag["Key"] == "Name":
                        thename = str(tag["Value"])
                    elif "Name" not in [tag['Key'] for tag in tags]:
                        thename = "not found"
                for tag in tags:
                    if tag["Key"] == "Hostname":
                        thehostname = str(tag["Value"])
                    elif "Hostname" not in [tag['Key'] for tag in tags]:
                        thehostname = "not found"
                if key_to_find not in [tag['Key'] for tag in instance['Tags']]:
                #print (key_to_find + ' tag not found for Instance ' + instance['InstanceId'])
                    with open(oldfilepath, "a+", newline="") as csvfile:
                        tagwriter = csv.writer(csvfile)
                        tagwriter.writerow(["EC2 instance", key_to_find + " tag not found", instance['InstanceId'], thename, thehostname])
        
        ec2resource = session.resource('ec2', region)
        #volumes = ec2resource.volumes.filter(Filters=[{'Name': 'tag:this is a test', 'Values': ['this is a test']}])
        volumes = ec2resource.volumes.all()
        for v in volumes:
            ebstags = v.tags
            try:
                if key_to_find not in [tag['Key'] for tag in ebstags]:
                    #print(v.id)
                    with open(oldfilepath, "a+", newline="") as csvfile:
                        tagwriter = csv.writer(csvfile)
                        tagwriter.writerow(["EBS Volume", key_to_find + "tag not found", v.id])
            except TypeError:
            #print(v.id, "Volume has no tags")
                with open(oldfilepath, "a+", newline="") as csvfile:
                    tagwriter = csv.writer(csvfile)
                    tagwriter.writerow(["EBS Volume", "Volume has no tags", v.id])

    for region in regions:
        rdsclient = session.client('rds', region)
        rdsresponse = rdsclient.describe_db_instances() 
        for DBInstance in rdsresponse['DBInstances']:
            db_Instance_ID = DBInstance['DBInstanceIdentifier']
            arn = DBInstance['DBInstanceArn']
            rdstags = rdsclient.list_tags_for_resource(ResourceName=arn)['TagList']
            for tag in rdstags:
            if tag["Key"] == "Backup":
                Backuptag = str(tag["Value"])
            elif key_to_find not in [tag['Key'] for tag in rdstags]:
                Backuptag = "not found"
            if key_to_find not in [tag['Key'] for tag in rdstags]:
            #print(db_Instance_ID, " ", Backuptag)
            with open(oldfilepath, "a+", newline="") as csvfile:
                tagwriter = csv.writer(csvfile)
                tagwriter.writerow(["RDS Instance", "Backuptag not found", db_Instance_ID])

s3 = boto3.client('s3')
with open(oldfilepath, "rb") as f:
    s3.upload_fileobj(f, "veotechops", newfilepath)   
