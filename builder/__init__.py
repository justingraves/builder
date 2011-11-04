#!/usr/bin/env python
import subprocess
import pipes
import os
import sys
import argparse
from multiprocessing import Pool, cpu_count
from time import time

def run_cmd(cmd, args = [], print_output = False):
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

def build_file(src_file, compile_args, build_dir = 'build', force_rebuild = False, compiler = 'g++', include_paths = [], library_paths = []):
	build_start = time()
	if build_dir.strip()[0] != '/':
		build_dir = os.getcwd() + '/' + build_dir

	is_header = True if (src_file.endswith('.h') or src_file.endswith('.hpp')) else False
	output_file = ''
	if is_header:
		output_file += src_file + '.gch'
	else:
		output_file = build_dir + '/' + src_file[:src_file.rfind('.')] + '.o'

	try:
		src_mod_time = os.stat(src_file).st_mtime
	except OSError:
		print '\033[1;31mFile not found:\033[0m', src_file
		return False

	if not force_rebuild:
		try:
			output_mod_time = os.stat(output_file).st_mtime

			if output_mod_time >= src_mod_time:
				return output_file, False
		except OSError:
			pass

	extra_args = [src_file,] + ['-I' + p for p in include_paths] + ['-L' + p for p in library_paths]
	if not is_header:
		extra_args += ['-c', '-o', output_file]

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
	build_start = time()

	header_files = []
	src_files = []
	for f in files:
		if f.endswith('.h') or f.endswith('.hpp'):
			header_files.append(f)
		elif f.endswith('.c') or f.endswith('.cpp'):
			src_files.append(f)
		else:
			print 'Unknown file type:', f

	if not src_files:
		print 'No source files found. Nothing to do.'
		return False

	needs_linking = False

	return_vals = Pool(concurrency).map(_build_file_tuple, [(f, compile_args, build_dir, force_rebuild, compiler, include_paths, library_paths) for f in header_files])
	for r in return_vals:
		if not r:
			print 'Project build failed :('
			return False
		if r[1]:
			needs_linking = True

	return_vals = Pool(concurrency).map(_build_file_tuple, [(f, compile_args + ['-H',], build_dir, force_rebuild, compiler, include_paths, library_paths) for f in src_files])
	for r in return_vals:
		if not r:
			print 'Project build failed :('
			return False
		if r[1]:
			needs_linking = True

	if not needs_linking:
		print 'Nothing modified. No build required.'
		if not execute:
			return True
	else:
		if not linker:
			linker = compiler

		link_files = [a[0] for a in return_vals]

		# Link omg
		link_result = run_cmd(linker, compile_args + ['-o', output_file] + link_files)
		if link_result[1] != 0:
			print '\033[1;31mLinking Failed\033[0m (exit code:', str(link_result[1]) + '):'
			print link_result[0]
			return False
		print '\033[1;32mLinking Succeeded\033[0m, built in', round(time() - build_start, 1), 'seconds'

	if execute:
		if '/' not in output_file:
			output_file = './' + output_file
		run_result = run_cmd(output_file, print_output = True)
		if run_result[1] != 0:
			return False
	return True
	
def all_files_of_ext(extension, path = None, exclude = []):
	return [f for f in os.listdir(path or os.getcwd()) if f.endswith(extension) and not [e for e in exclude if e in f]]

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Build stuff here')
	parser.add_argument('--run', help='Run the built executable after a succesful compilation', action='store_true')
	parser.add_argument('--rebuild', help='Force a full rebuild', action='store_true')
	parser.add_argument('--compiler', help='Compiler to use', default='g++')
	parser.add_argument('--linker', help='Linker to use (defaults to the compiler)', default='')
	parser.add_argument('--output', help='Name of binary to output', default='builder.out')
	parser.add_argument('--builddir', help='Directory for intermediate build files', default='./')
	parser.add_argument('--concurrency', help='Maximum number of files to build in parallel, defaults to number of CPUs you have', type=int, default=cpu_count())
	args = parser.parse_args()

	if not build_project(all_files_of_ext('.cpp') + all_files_of_ext('.c'),
		output_file = args.output,
		compile_args = ['-O2', '-g', '-mtune=native', '-fopenmp'],
		compiler = args.compiler,
		force_rebuild = args.rebuild,
		linker = args.linker or None,
		build_dir = args.builddir,
		concurrency = args.concurrency or cpu_count(),
		execute = args.run):
		sys.exit(1)


