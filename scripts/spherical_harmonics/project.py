# project.py
from flow import FlowProject
from subprocess import Popen, PIPE
from os.path import join,dirname
from copy import deepcopy
from memory_profiler import memory_usage


import sys, os


sys.path.insert(0, join(dirname(__file__), '../'))
from path import STRUCTURE_PATH, RASCAL_BUILD_PATH, BUILD_PATH
from utils.io import tojson, fromjson
sys.path.insert(0, RASCAL_BUILD_PATH)
from rascal.representations import SphericalInvariants, SphericalExpansion


groups = {
    'spherical_harmonics_cpp' : {
        'name' : 'spherical_harmonics_cpp',
        'fn_out' : 'out_sph_cpp.json',
        'fn_res' : 'res_sph_cpp.json',
        'fn_in' : 'in_sph_cpp.json',
        'executable' : join(BUILD_PATH,'src/spherical_harmonics'),
    },
}

group = groups['spherical_harmonics_cpp']

@FlowProject.label
def sph_cpp_computed(job):
    return job.isfile(group['fn_out']) and job.isfile(group['fn_res'])

@FlowProject.operation
@FlowProject.post(sph_cpp_computed)
def compute_sph_cpp(job):
    # setup input for the script
    data = job.statepoint()
    rep = SphericalExpansion(**data['representation'])
    data['calculator'] = rep.hypers

    tojson(job.fn(group['fn_in']), data)
    # look at memory footprint
    p = Popen([group['executable'], job.fn(group['fn_in']), job.fn(group['fn_out'])], stdout=PIPE, stderr=PIPE)
    max_mem = memory_usage(p, interval=0.001, max_usage=True)
    # look at timings
    p = Popen([group['executable'], job.fn(group['fn_in']), job.fn(group['fn_out'])], stdout=PIPE, stderr=PIPE)
    if p.stderr.read(): print(p.stderr.read())
    data = fromjson(job.fn(group['fn_out']))
    data = data['results']
    data['mem_max'] = max_mem
    data['mem_unit'] = 'MiB'
    tojson(job.fn(group['fn_res']), data)

@FlowProject.operation
@FlowProject.pre.after(compute_sph_cpp)
@FlowProject.post(lambda job: group['name'] in job.document)
def store_sph_cpp_in_document(job):
    data = fromjson(job.fn(group['fn_res']))
    job.document = data

if __name__ == '__main__':
    FlowProject().main()