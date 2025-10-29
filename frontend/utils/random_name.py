import random

def generate_random_name():
    return "user " + ''.join([str(random.randint(0, 9)) for _ in range(12)])

