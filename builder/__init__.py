#!/usr/bin/env python
import subprocess
import pipes
import os
import sys
import argparse
from multiprocessing import Pool, cpu_count
from time import time

def run_cmd(cmd, args = [], print_output = False):
	""" Run a shell command. Pass a list of args if needed. print_output will print output as the program spits it to stdout.
	Returns a tuple of (program_output, exit_code) """
	if not cmd:
		return '', 0

	full_cmd = cmd
	if args:
		full_cmd += ' '
		full_cmd += ' '.join([pipes.quote(a) for a in args])

	output = ''
	p = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	for line in p.stdout.readlines():
		output += line
		if print_output:
			print line[:-1]
	retval = p.wait()
	return output, retval

def build_file(src_file, compile_args = [], build_dir = 'build', force_rebuild = False, compiler = 'g++', include_paths = [], library_paths = []):
	""" build a single source file with the given compile arguments. Only rebuilds if file changed from output (force_rebuild disables this.) """
	build_start = time()

	# If the build directory isn't an absolute path, try to make it one
	if build_dir.strip()[0] != '/':
		build_dir = os.getcwd() + '/' + build_dir

	is_header = True if (src_file.endswith('.h') or src_file.endswith('.hpp')) else False
	output_file = ''
	if is_header:
		# Precompiled headers for GCC just make a .gch file next to the header
		output_file += src_file + '.gch'
	else:
		output_file = build_dir + '/' + src_file[:src_file.rfind('.')] + '.o'

	# Get file modification time for cache checks. Do this always to make sure the src file exists.
	try:
		src_mod_time = os.stat(src_file).st_mtime
	except OSError:
		print '\033[1;31mFile not found:\033[0m', src_file
		return False

	if not force_rebuild:
		try:
			# If we aren't forcing a rebuild, check mod time on the output, if it exists.
			# If the output file is newer than the src file, don't rebuild it.
			output_mod_time = os.stat(output_file).st_mtime

			if output_mod_time >= src_mod_time:
				return output_file, False
		except OSError:
			pass

	# Building final extra arguments for compiler, including include and library paths
	extra_args = [src_file,] + ['-I' + p for p in include_paths] + ['-L' + p for p in library_paths]
	if not is_header:
		extra_args += ['-c', '-o', output_file]

	# Actually execute the compiler
	build_result = run_cmd(compiler, compile_args + extra_args)

	if build_result[1] != 0:
		print '\033[1;31mBuild Failed\033[0m for', src_file, '(exit code:', str(build_result[1]) + '):'
		print build_result[0]
		return False
	else:
		print '\033[1;32mBuild Succeeded\033[0m for', src_file
		return output_file, True

def _build_file_tuple(t):
	return build_file(*t)

def build_project(files, output_file, compile_args, build_dir = 'build', force_rebuild = False, compiler = 'g++', linker = None, include_paths = [], library_paths = [], concurrency = cpu_count(), execute = False):
	""" Build a buncha files at once with concurrency, linking at the end. Uses build_file in parallel. """
	build_start = time()

	# Make lists of source and header files. They are treated differently. Headers are optional!
	header_files = []
	src_files = []
	for f in files:
		if f.endswith('.h') or f.endswith('.hpp'):
			header_files.append(f)
		elif f.endswith('.c') or f.endswith('.cpp'):
			src_files.append(f)
		else:
			print 'Unknown file type:', f

	# At present we don't build headers-only.
	if not src_files:
		print 'No source files found. Nothing to do.'
		return False

	needs_linking = False

	# Compile headers first, if any
	if header_files:
		return_vals = Pool(concurrency).map(_build_file_tuple, [(f, compile_args, build_dir, force_rebuild, compiler, include_paths, library_paths) for f in header_files])
		for r in return_vals:
			if not r:
				print 'Project build failed at headers :('
				return False
			if r[1]:
				# If any files actually were built, we need to link again
				needs_linking = True

	# Compile source files. Uses Pool.map for concurrency
	return_vals = Pool(concurrency).map(_build_file_tuple, [(f, compile_args + ['-H',], build_dir, force_rebuild, compiler, include_paths, library_paths) for f in src_files])
	for r in return_vals:
		if not r:
			print 'Project build failed :('
			return False
		if r[1]:
			# If any files actually were built, we need to link again
			needs_linking = True

	if not needs_linking:
		print 'Nothing modified. No build required.'
		if not execute:
			return True
	else:
		if not linker:
			linker = compiler

		# Filenames that need linking. These were returned by the compiler. Need to link all, not just those that were recompiled!
		link_files = [a[0] for a in return_vals]

		# Execute the linker
		link_result = run_cmd(linker, compile_args + ['-o', output_file] + link_files)

		if link_result[1] != 0:
			print '\033[1;31mLinking Failed\033[0m (exit code:', str(link_result[1]) + '):'
			print link_result[0]
			return False
		print '\033[1;32mLinking Succeeded\033[0m, built in', round(time() - build_start, 1), 'seconds'

	if execute:
		# If binary doesn't have a path, prefix with ./ so it runs
		if '/' not in output_file:
			output_file = './' + output_file

		# Execute the app, printing output as it comes
		run_result = run_cmd(output_file, print_output = True)
		if run_result[1] != 0:
			return False
	return True
	
def all_files_of_ext(extension, path = None, exclude = []):
	""" Return all files of a certain file extension (include the .!, e.g. '.cpp') path defaults to current directory. Pass a list to exclude of substrings in files to exclude from output list. """
	return [f for f in os.listdir(path or os.getcwd()) if f.endswith(extension) and not [e for e in exclude if e in f]]

if __name__ == '__main__':
	import __main__
