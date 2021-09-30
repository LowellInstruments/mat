import glob
import boto3


def _ls_bucket(cli, buk_name) -> dict:
    """ returns a filled dict, an empty dict or None """

    assert cli
    dict_objects = {}
    try:
        rsp = cli.list_objects_v2(Bucket=buk_name)
        contents = rsp['Contents']
        for each in contents:
            dict_objects[each['Key']] = each['Size']
        return dict_objects
    except KeyError as ke:
        # empty bucket, no rsp['Contents']
        print('exc: {}'.format(ke))
        return None


def _put_to_bucket(cli, file_name, buk_name):
    cli.upload_file(file_name, buk_name, file_name)


def _get_from_bucket(cli, buk_name, file_name):
    cli.download_file(buk_name, file_name, file_name)


if __name__ == '__main__':

    # source bucket name, key, secret & client
    s_b = 'bkt-odn'
    s_k = 'AKIA2SU3QQX62ZQGS4GW'
    s_s = 'VRWbba+Wk2kaSmqHOoE6jev0576v4OZCBIuOCMi/'
    s_c = boto3.client('s3', region_name='us-east-1',
                       aws_access_key_id=s_k,
                       aws_secret_access_key=s_s)

    # destination bucket name, key, secret & client
    d_b = 'lowell-odn-emolt'
    d_k = 'AKIAY7KN2RML4FENJI7F'
    d_s = 'aSx4iJ2gogQ57JLrk8rNsfMEqTpp089P1Vfaxheg'
    d_c = boto3.client('s3', region_name='us-east-1',
                       aws_access_key_id=d_k,
                       aws_secret_access_key=d_s)

    # list files in source bucket
    s_f = _ls_bucket(s_c, s_b)
    print('files in source bucket: {}'.format(s_f))

    # download from source bucket
    for i in s_f.keys():
        _get_from_bucket(s_c, s_b, i)

    # see files in current directory
    l_f = [f for f in glob.glob("*.txt")]
    print('files in local folder: {}'.format(l_f))

    # put to destination bucket
    for i in l_f:
        _put_to_bucket(d_c, i, d_b)

    # list files in destination bucket
    d_f = _ls_bucket(d_c, d_b)
    print('files in destination bucket: {}'.format(d_f))

