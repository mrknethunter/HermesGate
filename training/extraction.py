import numpy as np
import re

def getLength(x):
    return np.array([len(str(t)) for t in x]).reshape(-1, 1)

def specialChars(x):
    return np.array([str(t).count('!') + str(t).count('$') for t in x]).reshape(-1, 1)

def countDigits(x):
    return np.array([sum(c.isdigit() for c in str(t)) for t in x]).reshape(-1, 1)

def ipAddress(x):
    ip_pattern = r'http[s]?://(?:[0-9]{1,3}\.){3}[0-9]{1,3}'
    return np.array([1 if re.search(ip_pattern, str(t)) else 0 for t in x]).reshape(-1, 1)

def truncText(text):
    return str(text)[:1000]