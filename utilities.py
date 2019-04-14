import os
import importlib
import argparse
import pkgutil
import sys
from pwn import *
import magic
import json
import re
import html
import threading

# This subclass of argparse will print the help whenever there
# is a syntactic error in the options parsing
class ArgumentParserWithHelp(argparse.ArgumentParser):
	def error(self, message):
		print('{0}: error: {1}'.format(self.prog, message))
		self.print_help()
		sys.exit(2)

# argparse type to automatically verify that the specified path
# exists and is a directory
def DirectoryArgument(name):
	fullpath = os.path.abspath(os.path.expanduser(name))
	if not os.path.isdir(fullpath):
		raise argparse.ArgumentTypeError('{0} is not a directory'.format(name))
	return fullpath

# argparse type to automatically verify module existence and load it
def PythonModule(name):
	try:
		log.info('loading unit: {0}'.format(name))
		module = importlib.import_module(name)
	except Exception as e:
		print(e)
		raise argparse.ArgumentTypeError('{0} is not a valid module name'.format(name))
	return module

# This is dumb, but it makes the code more expressive...
def GetUnitName(unit):
	return unit.__module__

# Gets a fully qualified class name
def GetFullyQualifiedClassName(o):
	module = o.__class__.__module__
	if module is None or module == str.__class__.__module__:
		return o.__class__.__name__  # Avoid reporting __builtin__
	else:
		return module + '.' + o.__class__.__name__

def find_modules_recursively(path, prefix):
	""" Locate all modules under a path """
	log.warning('calling pkgutil.iter_modules({0},\'{1}\')'.format([path], prefix))
	for importer, name, ispkg in pkgutil.iter_modules([path], prefix):
		log.failure('looking at {0}'.format(name))
		module_path = os.path.join(path, name.replace('.','/'))
		if ispkg:
			
			for s in find_modules_recursively(module_path, name + '.'):
				yield s
		else:
			
			yield name

def element(tag, data, sub_level = 0, padding_level = None):
	if padding_level is None:
		padding_level = sub_level 
	return '<%s style="padding-left: %dpx">%s</%s>' % ( tag, padding_level*20,html.escape(data), tag )

def header(string, sub_level = 1, padding_level = None):
	return element('h%d' % (sub_level+1), string, sub_level, padding_level)

def pre(string, sub_level = 1, padding_level = None):
	return element('pre', string, sub_level, padding_level)

# This should happen FIRST in the HTML output generation...
def process_unit_output(output,content):

	anchors = []
	number_of_lines_for_each_anchor = []

	line_number_counter = 0
	anchor_name = ""

	for line in content:
		
		# Determine the level of indentation by examining the whitespace
		level = re.findall('^ +', line)
		if level:
			level = len(level[0])/4-1
		# If we are starting a new section, keep track of the anchor tag
		if line.endswith('": {') or line.endswith('": ['):
			string = line.split('"')[1]
			anchor_name = string
			if ( line.endswith('": {') and level == 0) or (line.endswith('": [') and level == 0): 

				anchors.append(anchor_name)

				if len(number_of_lines_for_each_anchor) == 0:
					number_of_lines_for_each_anchor.append(line_number_counter)
				else:
					number_of_lines_for_each_anchor[-1] = line_number_counter
				line_number_counter = 0
				number_of_lines_for_each_anchor.append(0)

				output.append('<hr style="opacity:0.3;">')

			output.append( '<a name="%s">%s</a>' % ( anchor_name, header(string, level+1, padding_level =level -1)) )
			line_number_counter -= 1

		else:
			
			# Clean up block lines
			if (line.endswith(']') and re.findall('^\s*\]', line)) \
			or (line.endswith('}') and re.findall('^\s*\}', line)) \
			or (line.endswith('{') and re.findall('^\s*\{', line)): continue

			# Add the line as preformated text!
			output.append(pre(line))

		# Keep adding to the line number so we know how much a unit takes up
		line_number_counter += 1

	# Don't forget to handle the last unit's line count!
	number_of_lines_for_each_anchor[-1] = line_number_counter

	# Remove the first number of lines because it is 0 and unneeded
	number_of_lines_for_each_anchor.pop(0)

	return output, anchors, number_of_lines_for_each_anchor 


def generate_table_of_contents(output, anchors, number_of_lines_for_each_anchor):

	table_of_contents = ['<h1>Katana Results</h1>',
							'<table>',
								'<th>Unit</th>', '<th>Number of Lines</th>']

	for i in range(len(number_of_lines_for_each_anchor)):
		
		anchor = anchors[i]
		num_lines = number_of_lines_for_each_anchor[i]

		# Add the anchor to the page...
		table_of_contents.append(f'''
		<tr>
			<td>
				<a href="#{anchor}">{anchor}</a>
			</td>
			<td>{num_lines}</td>
		</tr>''')
	
	table_of_contents.append('</table><br>')
	output.insert(0, '\n'.join(table_of_contents))

	return output

def add_flags_to_output(output, json_data):

	if 'flags' in json_data:
		
		potential_flags = ['<h2>Potential Flags</h2>', '<ul>']
		
		for flag in json_data['flags']:
			potential_flags.append(f'''
				<li>
					<span class='flag'>{flag}</span>
				</li>''')

		potential_flags.append('</ul><br>')

		output.insert(1, '\n'.join(potential_flags))
		return output
	else:
		return output

def add_images_to_output(output, json_data):
	if 'images' in json_data:
		
		found_images = ['<h2>Found Images</h2>', '<ul>',]
		
		for image in json_data['images']:
			if image.startswith('./results'):
				image = image.replace('./results','../results')
			
			found_images.append('<img src="%s">' % image)
		found_images.append('</ul><br>')

		output.insert(1, '\n'.join(found_images))
		return output
	else:
		return output


def render_html_to_file(json_data, file):

	html_output = []
	raw_content = [ x.rstrip() for x in json.dumps(json_data, indent=4).split('\n') ] 

	html_output, anchors, number_of_lines_for_each_anchor = process_unit_output(html_output, raw_content)
	html_output = generate_table_of_contents(html_output, anchors, number_of_lines_for_each_anchor)
	html_output = add_flags_to_output(html_output, json_data)
	html_output = add_images_to_output(html_output, json_data)

	html_output = '\n'.join(html_output)
	open(file,'w').write(html_output)

# -------------------------------------------------------------------

# These are utility functions that may be used in more than one module.

def process_output(popen_object):

	result = {
		"stdout": [],
		"stderr": [],
	}

	output = bytes.decode(popen_object.stdout.read(),'latin-1')
	error = bytes.decode(popen_object.stderr.read(),'latin-1')
	
	for line in [ l.strip() for l in error.split('\n') if l ]:
		result["stderr"].append(line)
	for line in [ l.strip() for l in output.split('\n') if l ]:
		result["stdout"].append(line)

	if not len(result['stderr']):
		result.pop('stderr')
	if not len(result['stdout']):
		result.pop('stdout')
	
	if result != {}:
		return result

def is_image(filename):
	# Ensure it's a file, and get it's mime type
	try:
		t = magic.from_file(filename).lower()
	except (FileNotFoundError, IsADirectoryError, ValueError, OSError):
		return False
	
	return bool( ' image ' in t )