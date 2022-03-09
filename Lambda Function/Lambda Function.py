#!/usr/bin/env python3

import math
import json
import random
import time

def lambda_handler(event, context):
    t = time.time()
    S = int(event['key1'])
    Q = int(event['key2'])
    D = int(event['key3'])

    sumIncircles = 0
    incircles = []
    results = []

    for i in range(0, int(S/Q)):
        incircle = 0
        for j in range(0, Q):
            random1 = random.uniform(-1.0, 1.0)
            random2 = random.uniform(-1.0, 1.0)
            if( ( random1*random1 + random2*random2 ) < 1 ):
                incircle += 1
        incircles.append(incircle)
        results.append(int((4.0 * incircle/Q)*(10**D))/10**D)
        
    ti = time.time() - t
    return incircles, results, ti