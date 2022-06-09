import os
from FrozenOrbits.analysis import check_for_intersection, print_state_differences
from FrozenOrbits.bvp import *

import GravNN
import matplotlib.pyplot as plt
import numpy as np
from FrozenOrbits.boundary_conditions import *
from FrozenOrbits.gravity_models import (pinnGravityModel,
                                         polyhedralGravityModel)
from FrozenOrbits.LPE import LPE, LPE_Milankovitch
from FrozenOrbits.utils import propagate_orbit
from FrozenOrbits.visualization import plot_3d_trajectory
from GravNN.CelestialBodies.Asteroids import Eros
from FrozenOrbits.coordinate_transforms import cart2oe_tf

from GravNN.Networks.Layers import PreprocessingLayer, PostprocessingLayer

def sample_mirror_orbit(R, mu):
    v_0 = np.sqrt(2*mu/R)*0.7
    init_state = np.array([[R, 0, 0.1*R, 0, v_0, 0]])
    T = 2*np.pi*np.sqrt(R**3/mu)
    OE = cart2oe_tf(init_state, mu, element_set='milankovitch').numpy()
    return OE, T

def configure_processing_layers(model):
    x_transformer = model.config['x_transformer'][0]
    u_transformer = model.config['u_transformer'][0]

    x_preprocessor = PreprocessingLayer(x_transformer.min_, x_transformer.scale_, tf.float64)
    u_postprocessor = PostprocessingLayer(u_transformer.min_, u_transformer.scale_, tf.float64)

    model.gravity_model.x_preprocessor = x_preprocessor
    model.gravity_model.u_postprocessor = u_postprocessor


def main():
    """Solve a BVP problem using the dynamics of the cartesian state vector"""
    planet = Eros()
    np.random.seed(15)

    model = pinnGravityModel(os.path.dirname(GravNN.__file__) + \
        "/../Data/Dataframes/eros_pinn_III_031222_500R.data")  
    # model = polyhedralGravityModel(planet, planet.obj_8k)

    configure_processing_layers(model)

    lpe = LPE_Milankovitch(model.gravity_model, planet.mu)

    OE_0, T = sample_mirror_orbit(planet.radius*3, planet.mu)

    # Run the solver
    OE_0_sol, T_sol = general_variable_time_bvp_OE(T, OE_0, lpe)


    x_0 = oe2cart_tf(OE_0, planet.mu, 'milankovitch').numpy()
    x_0_sol = oe2cart_tf(OE_0_sol, planet.mu, 'milankovitch').numpy()

    # propagate the initial and solution orbits
    init_sol = propagate_orbit(T, x_0, model, tol=1E-8) 
    bvp_sol = propagate_orbit(T_sol, x_0_sol, model, tol=1E-8) 

    check_for_intersection(bvp_sol, planet.obj_8k)
    print_state_differences(bvp_sol)

    plot_3d_trajectory(init_sol, planet.obj_8k)
    plt.title("Initial Guess")
    plot_3d_trajectory(bvp_sol, planet.obj_8k)
    plt.title("BVP Solution")

    plt.show()


if __name__ == "__main__":
    main()