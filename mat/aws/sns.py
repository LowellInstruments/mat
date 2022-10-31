import boto3
from botocore.config import Config
from botocore.exceptions import EndpointConnectionError, ClientError
import json


def _get_sns_client(_s, _ls, _ta, key, secret):
    if not _ta:
        print('[ MAT ] SNS | missing topic ARN')
        return 1
    if ':' not in _ta:
        print('[ MAT ] SNS | topic ARN malformed')
        return 1

    rg = _ta.split(':')[3]
    _cnf = Config(connect_timeout=5, retries={'max_attempts': 0})
    return boto3.client('sns',
                        aws_access_key_id=key,
                        aws_secret_access_key=secret,
                        region_name=rg,
                        config=_cnf)


def sns_notify(short_s, long_s, topic_arn, key, secret):
    try:

        # --------------------
        # get the SNS client
        # --------------------
        cli = _get_sns_client(short_s, long_s, topic_arn, key, secret)
        response = cli.publish(
            TargetArn=topic_arn,
            Message=json.dumps({'default': short_s,
                                'sms': short_s,
                                'email': long_s}),
            Subject=short_s,
            MessageStructure='json'
        )

        # response format very complicated, only use one field:
        if int(response['ResponseMetadata']['HTTPStatusCode']) == 200:
            # print('[ MAT ] SNS | message published OK -> {}'.format(short_s))
            return 0

    except (ClientError, EndpointConnectionError, Exception) as e:
        print('[ MAT ] SNS | exception {}'.format(e))
        return 1
