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
parser.add_argument('--includepaths', help='Space-separated list of include paths to search', default='')
parser.add_argument('--librarypaths', help='Space-separated list of library paths to search', default='')
parser.add_argument('--libraries', help='Space-separated list of additional libraries to include (no l prefix!)', default='')
parser.add_argument('--buildflags', help='Space-separated list of additional flags to pass to the compiler, defaults to \'-O2 -g -mtune-mative -fopenmp\'', default='-O2 -g -mtune=native -fopenmp')
parser.add_argument('--linkflags', help='Space-separated list of additional flags to pass to the linker. Defaults to compile flags if none are provided.', default='')
parser.add_argument('--ignorefiles', help='If a C or CPP file contains this text, it will be ignored. Space-separated list.', default='')
parser.add_argument('-r', help='Search for source files recursively (look in subdirectories)', action='store_true')
args = parser.parse_args()

if not build_project(all_files_of_ext('.cpp', recursive=args.r, exclude=args.ignorefiles.split()) + all_files_of_ext('.c', recursive=args.r, exclude=args.ignorefiles.split()),
	output_file = args.output,
	compile_args = args.buildflags.split(),
	link_args = args.linkflags.split() if args.linkflags else args.buildflags.split(),
	compiler = args.compiler,
	force_rebuild = args.rebuild,
	linker = args.linker or None,
	build_dir = args.builddir,
	concurrency = args.concurrency or cpu_count(),
	include_paths = args.includepaths.split(),
	library_paths = args.librarypaths.split(),
	libraries = args.libraries.split(),
	execute = args.run):
	sys.exit(1)