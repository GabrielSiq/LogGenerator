def bug(input):
    ticket = input['ticket']
    if ticket['Class'] == 'bug':
        return 'yes'
    else:
        return 'no'


def type(input):
    ticket = input['ticket']
    return ticket['Class']