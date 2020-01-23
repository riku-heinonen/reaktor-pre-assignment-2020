from flask import Flask, jsonify, render_template, redirect
from pprint import pprint as pp
import json
import os


# instantiate the app
app = Flask(__name__)
STATUS_FILE_PATH = os.path.abspath('/var/lib/dpkg/status') or 'static/status'


class Package():
    def __init__(self, name, version, description):
        self.name = name
        self.version = version
        self.description = description

    def serialize(self):
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description
        }

    def __repr__(self):
        return '<Package {}, version {}>'.format(self.name, self.version)


def parse_package_data(package_string):
    '''
        Parses one entry of the status file (separated by a double newline). 
        Gets the name, version and description of the package and returns
        them as a Package object. 
    '''
    lines = package_string.splitlines(keepends=True)
    line_index = 0
    while line_index < len(lines):
        line = lines[line_index]
        if line.startswith('Package'):
            name = line.split(': ', 1)[1].strip()

        elif line.startswith('Version'):
            version = line.split(': ', 1)[1].strip()

        elif line.startswith('Description'):
            description = line.split(': ', 1)[1]
            # check for a multiline description, a multiline field is determined
            # to begin every continuation line with a space ' ' or a tab '\t'
            line_index += 1
            next_line = lines[line_index]
            while next_line[0] == ' ' or next_line[0] == '\t':
                description += next_line
                line_index += 1
                if line_index >= len(lines):
                    break
                next_line = lines[line_index]

            # get rid of the last newline
            description = description.rstrip()

        line_index += 1

    return Package(name, version, description)


def parse_packages(filename):
    '''
        Parses a dpkg status file and returns a dictionary of Package objects that contain
        the name, version, description, dependencies and reverse dependencies of a package.
    '''
    packages = {}
    with open(filename, 'r') as status_file:
        raw_data = status_file.read()
        # package entries are separated by a double new-line
        data = raw_data.split('\n\n')
        for package_string in data[:-2]:
            package = parse_package_data(package_string)
            packages[package.name] = package

    return packages


packages = parse_packages(STATUS_FILE_PATH)


@app.route('/', methods=['GET'])
def home():
    return jsonify([package.serialize() for package in packages.values()])


if __name__ == '__main__':
    app.run(debug=True)
