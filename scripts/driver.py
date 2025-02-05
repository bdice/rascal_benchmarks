import sys
import os
import argparse
from subprocess import Popen, PIPE, run
from pathlib import Path
import signac

ROOT = os.path.dirname(__file__)
back2root = ['&&','cd',ROOT]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--rm', action='store_true',
                        help='remove entries in all workspaces')
    parser.add_argument('--init', action='store_true',
                        help='init all signac project subfolders')
    parser.add_argument('--run', action='store_true',
                        help='run all signac project subfolders')
    parser.add_argument('--status', action='store_true',
                        help='get status from all signac project subfolders')
    parser.add_argument('--prune', action='store_true',
                        help="remove state points that don't have a document")
    parser.add_argument('--submit', action='store_true',
                        help="submit all slurm script")
    parser.add_argument('-np','--parallel', type=int, default=-1,
                        help='set the number of process to use when running a project')

    args = parser.parse_args()

    if args.parallel == -1:
        parallel = ''
    else:
        parallel = '--parallel {}'.format(args.parallel)

    if args.rm:
        print('Remove files from workspaces')
        run('rm -rf ./*/workspace/*',shell=True)

    if args.prune:
        for path in Path('./').rglob('init.py'):
            print('    ',os.path.dirname(path))
            project = signac.get_project(os.path.dirname(os.path.abspath(path)))
            for job in project:
                if len(job.document) < 1:
                    job.remove()

    if args.init:
        print('Initialize all projects')
        for path in Path('./').rglob('init.py'):
            print('    ',os.path.dirname(path))
            move = ['cd',os.path.dirname(path),'&&']
            command = ' '.join(move+['python', os.path.abspath(path)]+back2root)
            run(command, shell=True)

    if args.run:
        print('Run all project')
        for path in Path('./').rglob('project.py'):
            # if 'model' in os.path.dirname(path):continue
            print('    ',os.path.dirname(path))
            move = ['cd',os.path.dirname(path),'&&']
            command = ' '.join(move+['python', os.path.abspath(path), 'run', parallel, '--progress']+back2root)
            run(command ,shell=True)

    if args.status:
        print('Run all project')
        for path in Path('./').rglob('project.py'):
            # if 'model' in os.path.dirname(path):continue
            print('    ',os.path.dirname(path))
            move = ['cd',os.path.dirname(path),'&&']
            command = ' '.join(move+['python', os.path.abspath(path), 'status']+back2root)
            run(command ,shell=True)

    if args.submit:
        print('submit all projects')
        for path in Path('./').rglob('submit*.sh'):
            print('    ',os.path.dirname(path))
            command = ' '.join(['sbatch', os.path.abspath(path)])
            run(command, shell=True)