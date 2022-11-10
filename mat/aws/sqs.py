import os
import random

from botocore.exceptions import ClientError
import uuid


def sqs_get_queue(q_name, session_sqs):
    try:
        if not q_name:
            print('error: q_name is empty')
            os._exit(1)
        queue = session_sqs.get_queue_by_name(QueueName=q_name)
        # print('[ MAT ] SQS | got queue {}'.format(queue.url))

    except ClientError as error:
        e = '[ MAT ] SQS | could not get queue {}'
        print(e.format(q_name))
        raise error
    else:
        return queue


def sqs_enqueue_msg(queue, message_body, message_attributes=None):
    if not message_attributes:
        message_attributes = {
            'my_rand': {
                'StringValue': str(uuid.uuid4()),
                'DataType': 'String'
            }
        }

    try:
        response = queue.send_message(
            MessageBody=message_body,
            MessageAttributes=message_attributes,
            MessageGroupId=str(uuid.uuid4()),
            MessageDeduplicationId=str(uuid.uuid4())
        )

    except ClientError as error:
        e = '[ MAT ] SQS | error enqueuing {}'
        print(e.format(message_body))
        raise error

    else:
        return response


def sqs_dequeue_msg(queue, max_number, wait_time):
    try:
        messages = queue.receive_messages(
            MessageAttributeNames=['All'],
            MaxNumberOfMessages=max_number,
            WaitTimeSeconds=wait_time
        )
        # if messages:
        #     s = '[ MAT ] SQS | de-queued {} messages'
        #     print(s.format(len(messages)))
    except ClientError as error:
        e = '[ MAT ] SQS | error de-queuing from {}'
        print(e.format(queue))
        raise error
    else:
        return messages


def sqs_rm_queue_msg(message):
    """
    Delete a message from a queue. Clients must delete messages after they
    are received and processed to remove them from the queue.

    :param message: The message to delete. The message's queue URL is contained in
                    the message's metadata.
    :return: None
    """
    try:
        message.delete()
    except ClientError as error:
        e = '[ MAT ] SQS | error deleting message {}'
        print(e.format(message.message_id))
        raise error
