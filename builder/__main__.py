import argparse
import sys
from multiprocessing import cpu_count
from builder import build_project, all_files_of_ext

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