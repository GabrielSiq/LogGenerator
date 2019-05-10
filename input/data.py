def verify(input):
    app = input['app']
    if app['ApplicationInfo'] is not None and app['HostChecklist'] is not None:
        return {'app': {'VerifiedChecklist': True}}


def application(input):
    return {'app': {'ApplicationInfo': True, 'HostChecklist': True}}


def inspection(input):
    return {'app': {'ApplicationInfo': True}}

def quality(input):
    return {'app': {'ApplicationInfo': True}}

def fixQuality(input):
    return {'app': {'ApplicationInfo': True}}

def photo(input):
    return {'app': {'ApplicationInfo': True}}

def review(input):
    return {'app': {'ApplicationInfo': True}}

