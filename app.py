from flask import Flask, jsonify, render_template, redirect
from pprint import pprint as pp
import json
import os


# instantiate the app
app = Flask(__name__)


@app.route('/', methods=['GET'])
def home():
    return "Hello world"


if __name__ == '__main__':
    app.run(debug=True)
