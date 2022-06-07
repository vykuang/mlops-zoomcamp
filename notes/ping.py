#!/usr/bin/env python
# coding: utf-8
from flask import Flask

app = Flask('ping')

@app.route('/ping', methods=['GET'])
def ping():
    return 'PONG'


if __name__  == '__main__':
#     # only run if called from CLI as a script
#     # or with python -m
    app.run(debug=True, host='0.0.0.0', port=9224)