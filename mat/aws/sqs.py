from botocore.exceptions import ClientError


def sqs_get_queue(q_name, session_sqs):
    try:
        queue = session_sqs.get_queue_by_name(QueueName=q_name)
        print("Got queue '%s' with URL=%s", q_name, queue.url)
    except ClientError as error:
        print("Couldn't get queue named %s.", q_name)
        raise error
    else:
        return queue


def sqs_enqueue_msg(queue, message_body, message_attributes=None):
    if not message_attributes:
        message_attributes = {}

    try:
        response = queue.send_message(
            MessageBody=message_body,
            MessageAttributes=message_attributes
        )
    except ClientError as error:
        print("Send message failed: %s", message_body)
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
        for msg in messages:
            print("Received message: %s: %s", msg.message_id, msg.body)
    except ClientError as error:
        print("Couldn't receive messages from queue: %s", queue)
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
        print("Deleted message: %s", message.message_id)
    except ClientError as error:
        print("Couldn't delete message: %s", message.message_id)
        raise error
