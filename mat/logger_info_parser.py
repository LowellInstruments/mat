class LoggerInfoParser:
    def __init__(self, data):
        self.data = data

    def info(self):
        li_string = self.data
        logger_info = {}
        try:
            tag = li_string[0:2]
            while tag != '##' and tag != '\xff' * 2:
                length = ord(li_string[2])
                value = li_string[3:3 + length]
                if tag == 'CA':
                    value = value[2:4] + value[0:2]
                    value = int(value, 16)
                    if value > 32768:
                        value -= 65536
                    value /= float(256)  # float() is to avoid integer division
                elif tag == 'BA' or tag == 'DP':
                    if length == 4:
                        value = value[2:4] + value[0:2]
                        value = int(value, 16)
                    else:
                        value = 0
                logger_info[tag] = value
                li_string = li_string[3 + length:]
                tag = li_string[0:2]
        except (IndexError, ValueError):
            logger_info = {'error': True}
        return logger_info
