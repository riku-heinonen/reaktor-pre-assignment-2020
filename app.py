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
        self.dependencies = []
        self.required_by = []

    def serialize(self):
        '''
            Returns the contents of the package as a dictionary.
        '''
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'dependencies': [dep.name for dep in self.dependencies],
            'required_by': [req.name for req in self.required_by]
        }

    def __repr__(self):
        return '<Package {}, version {}>'.format(self.name, self.version)


def parse_package_data(package_string):
    '''
        Parses one entry of the status file (separated by a double newline). 
        Gets the name, version, description and dependencies of the package and returns
        them as a Package object. 
    '''
    dependency_names = None
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

        elif line.startswith('Depends'):
            dependency_names = []
            dependencies = line.split(': ', 1)[1].strip().split(', ')
            for dependency in dependencies:
                dependency_names.append(dependency)

        line_index += 1

    package = Package(name, version, description)

    # some packages don't have dependencies
    if dependency_names:
        package.dependencies = dependency_names

    return package


def update_dependency(packages, package, dependency_name):
    '''
        For the packages that have alternatives, finds the first alternative
        dependency that exists in the dataset and discards the other alternatives.
        Replaces the dependency names (strings) of a Package object with
        objects that represent those dependencies.
    '''
    dependency = None
    if '|' in dependency_name:
        # alternatives for a dependency found
        alternatives = dependency_name.split(' | ')
        for alternative in alternatives:
            alternative_name = alternative.split(':', 1)[0].split(' ', 1)[0]
            # get the first package that exists in the dataset
            if alternative_name in packages:
                dependency = packages[alternative_name]
                break
    else:
        dependency_name = dependency_name.split(':', 1)[0].split(' ', 1)[0]
        if dependency_name in packages:
        dependency = packages[dependency_name]

        # index = package.dependencies.index(dependency_name)
        # package.dependencies[index] = dependency
    return dependency


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
        for package_string in data[:-1]:
            package = parse_package_data(package_string)
            packages[package.name] = package

    # update dependencies and reverse dependencies
    for package in packages.values():
        if package.dependencies:
            updated_dependencies = []
            for dependency_name in package.dependencies:
                if dependency_name in packages:
                    dependency = update_dependency(packages,
                                                   package,
                                                   dependency_name)
                    updated_dependencies.append(dependency)
                    packages[dependency_name].required_by.append(package)
                package.dependencies = updated_dependencies
    return packages


packages = parse_packages(STATUS_FILE_PATH)


@app.route('/', methods=['GET'])
def redirect_home():
    return redirect('/packages/')


@app.route('/packages/', methods=['GET'])
def get_packages():
    return render_template('landing_page.html', packages=packages.values())


# for debugging purposes
@app.route('/packages/json', methods=['GET'])
def get_packages_as_json():
    return jsonify([package.serialize() for package in packages.values()])


@app.route('/packages/<package_name>', methods=['GET'])
def get_package(package_name):
    return render_template('package.html', package=packages[package_name])

# for debugging purposes
@app.route('/packages/<package_name>/json', methods=['GET'])
def get_package_as_json(package_name):
    return jsonify(packages[package_name].serialize())


if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug=True)
