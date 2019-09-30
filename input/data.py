from numpy import random


def read(input):
    return {'ticket': {'Class': random.choice(['support', 'trust', 'bug'], p=[0.6, 0.2, 0.2]), 'Value': int(input['ticket']['Value']) + random.randint(0, 100)}}
