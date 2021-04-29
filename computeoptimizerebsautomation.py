import os 
import boto3 
import json

regions = ['eu-west-2', 'eu-west-1', 'us-east-1']
accounts = ['111111111111', '222222222222']
excludedVolumeids = ['vol-00xxxx4x35xxx06x7', 'vol-00z07zz9zz8z716z1']

def lambda_handler(event, context):
    is_test = context.function_name == 'test'  # this value is injected by SAM local
    
    for account in accounts:
        if account == '111111111111':
            account_name = "dev"
        elif account == '222222222222':
            account_name = "pre"       

#an assume role has to be created in each account you want to loop through with same naming convention            
        role = boto3.client('sts').assume_role(
            RoleArn = f"arn:aws:iam::{account}:role/{account_name}-ComputeOptimizerRole",
            RoleSessionName ="AssumedRole")
        
        # Get the temporary creds into a variable
        credentials = role['Credentials']
        session = boto3.session.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'])
        
        
        for region in regions:
            client = session.client('compute-optimizer', region)
            ec2client = session.client('ec2', region)
            response = client.get_ebs_volume_recommendations()
            #alias = boto3.client('iam').list_account_aliases()['AccountAliases'][0]

            vrs = response['volumeRecommendations']
            #Variable vrs will list all volumes which are showing in computer optimiser with their current configuration

            for vr in vrs:
            #The below if loop filters the above to show the volumes that are not currently optimised 
                if vr['finding'] == "NotOptimized":
                    print(vr['volumeArn'], vr['finding'])
                    print("currentvolumetype:", vr['currentConfiguration']['volumeType'],
                    "currentiops:", vr['currentConfiguration']['volumeBaselineIOPS'],
                    "volumeSize:", vr['currentConfiguration']['volumeSize'],
                    "Throughput:", vr['currentConfiguration']['volumeBaselineThroughput'])
                    vroptions = vr['volumeRecommendationOptions']
            #Each recomendaton can have multiple options
            #These have been filtered to only apply the computeoptimizer recomendation that is ranked first
            #An exclusion has been created for any volumes set as type st1
                    for vroption in vroptions:
                        if vroption['rank'] == 1:
                            if vroption['performanceRisk'] <= 2.0 and vroption['configuration']['volumeType'] != "st1":
            #vid is a variable which shows the volume id that has been extracted from the volumeArn
                                varn = vr['volumeArn']
                                varnsplit = varn.split("/", 1)
                                vid = varnsplit[1]
                                if vid not in excludedVolumeids:
                                    print(vid, vroption['rank'], vroption['performanceRisk'], vr['currentConfiguration']['volumeType'])
                                    if vroption['configuration']['volumeType'] == "gp3":
                                        try:
                                            print(f"Modified {vid} Settings",
                                            f"size: {vroption['configuration']['volumeSize']}",
                                            f"Throughput: {vroption['configuration']['volumeBaselineThroughput']}",
                                            f"Iops: {vroption['configuration']['volumeBaselineIOPS']}",
                                            f"VolumeType: {vroption['configuration']['volumeType']}")
                                            ec2client.modify_volume(VolumeId=vid,
                                                VolumeType= vroption['configuration']['volumeType'], 
                                                Iops= vroption['configuration']['volumeBaselineIOPS'],
                                                Throughput= vroption['configuration']['volumeBaselineThroughput'],
                                                Size= vroption['configuration']['volumeSize'],
                                                DryRun=True)
                                        except Exception as error:
                                            print(f'Error: {error}')
                                    elif vroption['configuration']['volumeType'] == "io1" or "io2":
                                        try:
                                            ec2client.modify_volume(VolumeId=vid,
                                                VolumeType= vroption['configuration']['volumeType'], 
                                                Iops= vroption['configuration']['volumeBaselineIOPS'],
                                                Size= vroption['configuration']['volumeSize'],
                                                DryRun=False)
                                        except Exception as error:
                                            print(f'Error: {error}')
                                else:
                                    print(f"Volume {vid} currently in excluded list")
