#!/usr/bin/env python
""" This is an example of a more complex build script. This is probably useless to you, but makes for an OK skeleton/example
For simple cases, you can just run: python -m builder --run
For this, you could: ./example.py --run to build and run the app. """

import builder
import argparse
import sys

parser = argparse.ArgumentParser(description='Build this')
parser.add_argument('--debug', help='Build for debugging', action='store_true')
parser.add_argument('--run', help='Run the built executable after a succesful compilation', action='store_true')
parser.add_argument('--rebuild', help='Force a full rebuild', action='store_true')
args = parser.parse_args()

debug_args = ['-g', '--std=gnu++0x']
release_args = ['-fopenmp', '--std=gnu++0x', '-static-libgcc', '-O3', '-march=corei7', '-mtune=corei7', '-msse3', '-mssse3', '-msse4.1', '-msse4.2', '-msse4', '-maccumulate-outgoing-args', '-minline-all-stringops']
include_paths = ['/Developer/boost/', '-I/Developer/gnucompiler/include/']
library_paths = ['/Developer/boost/libs/', '-L/Developer/gnucompiler/lib/']
binary = './binaries/thisapp' + ('d' if args.debug else '')

if not builder.build_project(builder.all_files_of_ext('.cpp', exclude=['test']) + ['/Developer/boost/boost/bind.hpp'],
	output_file = binary,
	compile_args = debug_args if args.debug else release_args,
	compiler = 'g++-4.6.1',
	include_paths = include_paths,
	library_paths = library_paths,
	force_rebuild = args.rebuild,
	execute = args.run):
	sys.exit(1)