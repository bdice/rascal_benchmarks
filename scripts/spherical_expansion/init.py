# init.py
import signac
import sys
from copy import deepcopy
import numpy as np
from os.path import join,dirname

sys.path.insert(0, join(dirname(__file__), '../'))
from representation_params import REPRESENTATION_PARAMS

project = signac.init_project('spherical_expansion')

fixed_params = {
    'normalize':False,
    'coefficient_subselection':None,
    'inversion_symmetry':True,
    'soap_type':'PowerSpectrum',
}
del_params = fixed_params
# fixed_params = {k:REPRESENTATION_PARAMS[0]['representation'][k] for k in fixed_params}
fixed_accuracy = 1e-8


for REPRESENTATION_PARAM in REPRESENTATION_PARAMS:
    if np.all([REPRESENTATION_PARAM['representation'][k] == v for k,v in fixed_params.items()]):
        if 'accuracy' in REPRESENTATION_PARAM['representation']['optimization_args']:
            if REPRESENTATION_PARAM['representation']['optimization_args']['accuracy'] != fixed_accuracy:
                continue
        rep_args = deepcopy(REPRESENTATION_PARAM)
        rep_args['representation'] = {
            k:v for k,v in rep_args['representation'].items() if k not in del_params}
        job = project.open_job(rep_args)
        job.init()