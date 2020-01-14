def reversed(list):
    for i in range(0, len(list), -1):
        yield list[i]