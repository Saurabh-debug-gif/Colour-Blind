def detect_colorblindness(responses):
    errors = {}
    for user, correct, ctype in responses:
        if user and user.strip() != correct:
            errors[ctype] = errors.get(ctype, 0) + 1
    if not errors:
        return "Normal Vision"
    return max(errors, key=errors.get)  # return most frequently missed type    