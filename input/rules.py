def checklistCompleted(input):
    app = input['app']
    if app['VerifiedChecklist'] is True:
        return 'yes'
    else:
        return 'no'