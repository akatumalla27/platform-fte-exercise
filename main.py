import boto3

cfn = boto3.client('cloudformation')
cloudfront = boto3.client('cloudfront')

def list_stack_resources(stackName):
    # Generates a list of lists
    finalReponse = []
    response = cfn.list_stack_resources(
        StackName=stackName
    )
    finalReponse.append(response['StackResourceSummaries'])
    if 'NextToken' in response:
        list_stack_resources(stackName)
    return finalReponse

stack_summary_list = list_stack_resources('spa')
for summary in stack_summary_list:
    for resource in summary:
        if resource['ResourceType'] == 'AWS::CloudFront::Distribution':
            response = cloudfront.get_distribution(
                Id=resource['PhysicalResourceId']
            )
            print('Webpage hosted at: https://{}'.format(response['Distribution']['DomainName']))
