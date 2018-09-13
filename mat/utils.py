def obj_from_coefficients(coefficients, classes):
    coefficient_set = set(coefficients)
    for klass in classes:
        keys = klass.REQUIRED_KEYS
        if keys <= coefficient_set:
            return klass(coefficients)
    return None


def _trim_start(string, n_chars_to_trim):
    return string[n_chars_to_trim:]


def array_from_tags(data, *key_lists):
    return [[data[key] for key in key_list]
            for key_list in key_lists]
