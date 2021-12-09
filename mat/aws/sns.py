import json
import os
import boto3
import botocore


def get_aws_client():
    _k_ = os.getenv('DDH_AWS_KEY_ID')
    _s_ = os.getenv('DDH_AWS_SECRET')

    return boto3.client('sns',
                        aws_access_key_id=_k_,
                        aws_secret_access_key=_s_,
                        region_name='us-east-1')


def get_list_of_topics():
    cli = get_aws_client()
    try:
        list_of_topics = cli.list_topics()
        for each in list_of_topics['Topics']:
            print(each['TopicArn'])
    except botocore.exceptions.ClientError as e:
        print(e)
        return 1


def get_list_of_subscription_of_one_topic(s: str):
    cli = get_aws_client()
    try:
        list_of_subs = cli.list_subscriptions_by_topic(TopicArn=s)
        for each in list_of_subs['Subscriptions']:
            # each: {'SubscriptionArn': <subs_arn>',
            # 'Owner': '...',
            # 'Protocol': 'email',
            # 'Endpoint': 'destination@gmail.com',
            # 'TopicArn': '<topic_arn>'}
            print(each['Endpoint'])
    except botocore.exceptions.ClientError as e:
        print(e)
        return 1


def publish_example(topic_arn):
    cli = get_aws_client()
    try:
        msg_not_email_or_sms = {"foo": "bar"}
        response = cli.publish(
            TargetArn=topic_arn,
            Message=json.dumps({'default': json.dumps(msg_not_email_or_sms),
                                'sms': 'text -> short',
                                'email': 'this is a longer TEXT'}),
            Subject='SUBJECT: logger error',
            MessageStructure='json'
        )
        # response format very complicated, only use:
        if int(response['ResponseMetadata']['HTTPStatusCode']) == 200:
            print('message pub OK')
            return 0

    except botocore.exceptions.ClientError as e:
        print(e)
        return 1
