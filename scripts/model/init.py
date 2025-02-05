# init.py
import signac
import sys
from copy import deepcopy
import numpy as np
from os.path import join,dirname
from itertools import product
sys.path.insert(0, join(dirname(__file__), '../'))
from path import STRUCTURE_PATH, RASCAL_BUILD_PATH, BUILD_PATH

project = signac.init_project('model')
# Define parameter space

names = ['silicon_bulk', 'methane_liquid', 'methane_sulfonic', 'molecular_crystals', 'qm9']
seed = 10
fns = {
    'silicon_bulk': 'silicon_bulk.json',
    'methane_liquid': 'methane_liquid.json',
    'molecular_crystals': 'molecular_crystals_100.json',
    'qm9': 'qm9.json',
    'methane_sulfonic': 'methane_sulfonic_150.json',
}

misc_entries = {
    'silicon_bulk' : {
        "N_ITERATIONS" : 5,
        'start_structure': 600,
        "n_structures" : 120,
        "n_replication" : 3,
    },
    'methane_liquid' : {
        "N_ITERATIONS" : 5,
        'start_structure': 100,
        "n_structures" : 100,
        "n_replication" : 3,
    },
    'methane_sulfonic' : {
        "N_ITERATIONS" : 5,
        'start_structure': 0,
        "n_structures" : 50,
        "n_replication" : 3,
    },
    'molecular_crystals' : {
        "N_ITERATIONS" : 5,
        'start_structure': 0,
        "n_structures" : 90,
        "n_replication" : 2,
    },
    'qm9' : {
        "N_ITERATIONS" : 5,
        'start_structure': 0,
        "n_structures" : 800,
        "n_replication" : 1,
    }
}


global_species = {
    'qm9' : [1,6,7,8,9],
    'molecular_crystals' : [1, 6, 7, 8],
    'silicon_bulk' : [14],
    'methane_liquid' : [1, 6],
    'methane_sulfonic' : [1,6,8,16],
}

n_sparse = [100, 200, 500, 1000, 2000, 5000, 7000, 9000]

def get_per_sp_sparsepoints(n_sparse, sparse_proportions):
    aa = np.zeros(np.max(list(sparse_proportions))+1,dtype=int)
    for sp,f in sparse_proportions.items():
        val = int(n_sparse*f)
        if val == 0:
            val = 1
        aa[sp] = val

    v = np.sum(aa)
    if v != n_sparse:
        diff = n_sparse-v
        bb = aa.copy()
        iaa = np.argmax(bb)
        aa[iaa] = aa[iaa]+diff

    Nselect = {sp:aa[sp] for sp,f in sparse_proportions.items()}
    return Nselect

## these numbers correspond to the numbers of atoms of a certain type in the
# structure so they depend on the exact number of structures in misc_entries
sparse_proportions = {
    'silicon_bulk': {14: 1.0},
    'methane_liquid': {1: 0.8, 6: 0.2},
    'methane_sulfonic': {1: 0.4637329719706155, 6: 0.43149561372227374, 8: 0.10120533485486057, 16: 0.0035660794522501963},
    'molecular_crystals': {1: 0.46361619098630347, 6: 0.41808860662636776, 7: 0.043997245389853855, 8: 0.07429795699747493},
    'qm9': {1: 0.5121376057705646, 6: 0.35053405465390486, 7: 0.05562491330281592, 8: 0.07948397836038286, 9: 0.0022194479123318076}
}
sparse_point_subselections = {}
for name in names:
    sparse_point_subselections[name] = [dict(Nselect=get_per_sp_sparsepoints(v, sparse_proportions[name]), act_on='sample per species', seed=seed) for v in n_sparse]

models = {
    'silicon_bulk' : [
        {
         'representation' :
            dict(
            interaction_cutoff=5., cutoff_smooth_width=1.,
            max_radial=10, max_angular=12, gaussian_sigma_type="Constant",
            soap_type="PowerSpectrum",
            normalize=True,
            expansion_by_species_method='structure wise',
            global_species=global_species['silicon_bulk'],
            compute_gradients=False,
            cutoff_function_parameters=dict(),
            cutoff_function_type="ShiftedCosine",
            gaussian_sigma_constant=0.5,
            coefficient_subselection=None,
            radial_basis="GTO",
            optimization_args={
                  "type": "Spline", "accuracy": 1e-08, "range": [0, 5]
                },
            ),
         'kernel':
           dict(
               name='GAP', zeta=4, target_type='Structure', kernel_type='Sparse'
           ),
        },
    ],
    'qm9' : [
        {
         'representation' :
            dict(
            interaction_cutoff=5., cutoff_smooth_width=1.,
            max_radial=12, max_angular=9, gaussian_sigma_type="Constant",
            soap_type="PowerSpectrum",
            normalize=True,
            expansion_by_species_method='structure wise',
            global_species=global_species['qm9'],
            compute_gradients=False,
            cutoff_function_parameters=dict(rate = 1, scale = 2, exponent = 7),
            cutoff_function_type="RadialScaling",
            gaussian_sigma_constant=0.3,
            coefficient_subselection=None,
            radial_basis="GTO",
            optimization_args={
                  "type": "Spline", "accuracy": 1e-08, "range": [0, 5]
                },
            ),
         'kernel':
           dict(
               name='GAP', zeta=2, target_type='Structure', kernel_type='Sparse'
           ),
        },
    ],
    'molecular_crystals' : [
        {
         'representation' :
            dict(
            interaction_cutoff=5., cutoff_smooth_width=1.,
            max_radial=9, max_angular=9, gaussian_sigma_type="Constant",
            soap_type="PowerSpectrum",
            normalize=True,
            expansion_by_species_method='structure wise',
            global_species=global_species['molecular_crystals'],
            compute_gradients=False,
            cutoff_function_parameters=dict(),
            cutoff_function_type="ShiftedCosine",
            gaussian_sigma_constant=0.4,
            coefficient_subselection=None,
            radial_basis="GTO",
            optimization_args={
                  "type": "Spline", "accuracy": 1e-08, "range": [0, 5]
                },
            ),
         'kernel':
           dict(
               name='GAP', zeta=2, target_type='Structure', kernel_type='Sparse'
           ),
        },
    ],
    'methane_liquid' : [
        {
         'representation' :
            dict(
            interaction_cutoff=5, cutoff_smooth_width=1.,
            max_radial=8, max_angular=6, gaussian_sigma_type="Constant",
            soap_type="PowerSpectrum",
            normalize=True,
            expansion_by_species_method='structure wise',
            global_species=global_species['methane_liquid'],
            compute_gradients=False,
            cutoff_function_parameters=dict(),
            cutoff_function_type="ShiftedCosine",
            gaussian_sigma_constant=0.4,
            coefficient_subselection=None,
            radial_basis="GTO",
            optimization_args={
                  "type": "Spline", "accuracy": 1e-08, "range": [0, 5]
                },
            ),
         'kernel':
           dict(
               name='GAP', zeta=2, target_type='Structure', kernel_type='Sparse'
           ),
        },
    ],
    'methane_sulfonic' : [
        {
         'representation' :
            dict(
            interaction_cutoff=5., cutoff_smooth_width=1.,
            max_radial=8, max_angular=6, gaussian_sigma_type="Constant",
            soap_type="PowerSpectrum",
            normalize=True,
            expansion_by_species_method='structure wise',
            global_species=global_species['methane_sulfonic'],
            compute_gradients=False,
            cutoff_function_parameters=dict(),
            cutoff_function_type="ShiftedCosine",
            gaussian_sigma_constant=0.4,
            coefficient_subselection=None,
            radial_basis="GTO",
            optimization_args={
                  "type": "Spline", "accuracy": 1e-08, "range": [0, 5]
                },
            ),
         'kernel':
           dict(
               name='GAP', zeta=2, target_type='Structure', kernel_type='Sparse'
           ),
        },
    ],
}

f_feature = [0.02, 0.05, 0.1, 0.2,0.4, 0.5, 0.7, 1]
feature_subselections = {}
for name,dd in models.items():
    aa = dd[0]['representation']
    # number of PowerSpectrum features in QUIP
    n_feat = int((aa['max_angular']+1) * aa['max_radial']*len(global_species[name])*(aa['max_radial']*len(global_species[name])+1) /2)
    feature_subselections[name] = [dict(Nselect=int(v*n_feat), act_on='feature', seed=seed) for v in f_feature]+[dict(Nselect=None, act_on='feature', seed=seed)]

self_contributions = {
    'silicon_bulk' : {14: -158.54496821},
    'qm9': {1: 0, 6: 0, 7: 0, 8: 0, 9: 0},
    'molecular_crystals': {1: -1.2066278536666357, 6: -18.42141665763611, 7: -28.21055160856482, 8: -41.63852285569995},
    'methane_liquid': {1: 0, 6: 0},
    'methane_sulfonic': {1: -0.6645519125911715, 6: -5.654232251386078, 8: -15.852522852103935, 16: -9.17258361289801}
}

grads_timings = [True, False]

for name in names:
    for model, sparse_point_subselection, feature_subselection, grads_timing in product(models[name], sparse_point_subselections[name], feature_subselections[name], grads_timings):
        rep_args = deepcopy(model)
        rep_args['name'] = name
        rep_args['filename'] = join(STRUCTURE_PATH,fns[name])
        rep_args['self_contributions'] = self_contributions[name]
        rep_args['train_with_grad'] = False
        rep_args['grads_timing'] = grads_timing
        rep_args['sparse_point_subselection'] = sparse_point_subselection
        rep_args['feature_subselection'] = feature_subselection
        rep_args.update(misc_entries[name])
        job = project.open_job(rep_args)
        job.init()
