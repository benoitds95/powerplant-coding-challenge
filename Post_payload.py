#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 18 18:21:37 2021

@author: benoitdeschrynmakers
"""

import requests

url = 'http://127.0.0.1:8888/productionplan'

if __name__ == "__main__":
    filename = "example_payloads/payload1.json"

    data = open(filename, 'rb').read()
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    response = requests.post(url, data=data, headers=headers)

    if response.ok:
        print(response.json())
    else:
        print("error!")
        
        
        