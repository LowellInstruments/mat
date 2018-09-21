from numpy import array


def obj_from_coefficients(coefficients, classes):
    coefficient_set = set(coefficients)
    for klass in classes:
        keys = klass.REQUIRED_KEYS
        if keys <= coefficient_set:
            return klass(coefficients)
    return None


def trim_start(string, n_chars_to_trim):
    return string[n_chars_to_trim:]


def array_from_tags(data, *key_lists):
    return array([[data[key] for key in key_list]
                  for key_list in key_lists])


def four_byte_int(bytes, signed=False):
    if len(bytes) != 4:
        return 0
    result = int(bytes[2:4] + bytes[0:2], 16)
    if signed and result > 32768:
        return result - 65536
    return result
