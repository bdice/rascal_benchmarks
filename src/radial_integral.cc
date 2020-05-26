/**
 * @file
 *
 * @author Felix Musil <felix.musil@epfl.ch>
 *
 * @date   26 June 2019
 *
 * @brief an executable to test ideas
 *
 */

#include "rascal/models/sparse_kernels.hh"
#include "rascal/models/sparse_points.hh"
#include "rascal/utils/basic_types.hh"
#include "rascal/models/kernels.hh"
#include "rascal/utils/utils.hh"
#include "rascal/representations/calculator_sorted_coulomb.hh"
#include "rascal/representations/calculator_spherical_expansion.hh"
#include "rascal/representations/calculator_spherical_invariants.hh"
#include "rascal/structure_managers/adaptor_increase_maxorder.hh"
#include "rascal/structure_managers/cluster_ref_key.hh"
#include "rascal/structure_managers/adaptor_center_contribution.hh"
#include "rascal/structure_managers/adaptor_half_neighbour_list.hh"
#include "rascal/structure_managers/adaptor_neighbour_list.hh"
#include "rascal/structure_managers/adaptor_strict.hh"
#include "rascal/structure_managers/make_structure_manager.hh"
#include "rascal/structure_managers/structure_manager_centers.hh"
#include "rascal/structure_managers/structure_manager_collection.hh"

#include <cmath>
#include <functional>
#include <initializer_list>
#include <iostream>
#include <list>
#include <random>
#include <string>
#include <algorithm>
#include <iterator>
#include <chrono>



using namespace rascal;  // NOLINT

using ManagerTypeHolder_t = StructureManagerTypeHolder<
                      StructureManagerCenters, AdaptorNeighbourList,
                          AdaptorCenterContribution, AdaptorStrict>;

using Manager_t = typename ManagerTypeHolder_t::type;
using Representation_t = CalculatorSphericalInvariants;
using ManagerCollection_t =
    typename TypeHolderInjector<ManagerCollection, ManagerTypeHolder_t::type_list>::type;
using Representation_t = CalculatorSphericalInvariants;
using Prop_t = typename Representation_t::template Property_t<Manager_t>;
using PropGrad_t = typename Representation_t::template PropertyGradient_t<Manager_t>;

constexpr static size_t ClusterLayer_{
          Manager_t::template cluster_layer_from_order<2>()};

template <internal::RadialBasisType RBT, internal::AtomicSmearingType AST,
            internal::OptimizationType OT>
auto downcast_radial_integral_handler(
    const std::shared_ptr<internal::RadialContributionBase> &
        radial_integral) {
  return std::static_pointer_cast<
      internal::RadialContributionHandler<RBT, AST, OT>>(radial_integral);
}

struct RadialIntegral {
  internal::AtomicSmearingType atomic_smearing_type{};
  std::shared_ptr<internal::RadialContributionBase> radial_integral{};
  internal::RadialBasisType radial_integral_type{};
  internal::OptimizationType optimization_type{};

  size_t max_radial{0};
  size_t max_angular{0};

  explicit RadialIntegral(const json & hyper) {
      using internal::AtomicSmearingType;
      using internal::OptimizationType;
      using internal::RadialBasisType;

      this->max_radial = hypers.at("max_radial");
      this->max_angular = hypers.at("max_angular");

      auto smearing_hypers = hypers.at("gaussian_density").get<json>();
      auto smearing_type = smearing_hypers.at("type").get<std::string>();

      if (smearing_type == "Constant") {
        this->atomic_smearing_type = AtomicSmearingType::Constant;
      } else if (smearing_type == "PerSpecies") {
        throw std::logic_error("Requested Smearing type \'PerSpecies\'"
                               "\' has not been implemented.  Must be one of"
                               ": \'Constant\'.");
      } else if (smearing_type == "Radial") {
        throw std::logic_error("Requested Smearing type \'Radial\'"
                               "\' has not been implemented.  Must be one of"
                               ": \'Constant\'.");
      } else {
        throw std::logic_error("Requested Smearing type \'" + smearing_type +
                               "\' is unknown.  Must be one of" +
                               ": \'Constant\'.");
      }

      auto radial_contribution_hypers =
          hypers.at("radial_contribution").get<json>();
      auto radial_contribution_type =
          radial_contribution_hypers.at("type").get<std::string>();

      // create the class that will compute the radial terms of the
      // expansion. the atomic smearing is an integral part of the
      // radial contribution
      if (radial_contribution_type == "GTO") {
        auto rc_shared = std::make_shared<
            internal::RadialContribution<RadialBasisType::GTO>>(hypers);
        this->atomic_smearing_type = rc_shared->atomic_smearing_type;
        this->radial_integral = rc_shared;
        this->radial_integral_type = RadialBasisType::GTO;

      } else if (radial_contribution_type == "DVR") {
        auto rc_shared = std::make_shared<
            internal::RadialContribution<RadialBasisType::DVR>>(hypers);
        this->atomic_smearing_type = rc_shared->atomic_smearing_type;
        this->radial_integral = rc_shared;
        this->radial_integral_type = RadialBasisType::DVR;
      } else {
        throw std::logic_error("Requested Radial contribution type \'" +
                               radial_contribution_type +
                               "\' has not been implemented.  Must be one of" +
                               ": \'GTO\' or \'DVR\'. ");
      }

      if (radial_contribution_hypers.find("optimization") !=
          radial_contribution_hypers.end()) {
        auto optimization_hypers =
            radial_contribution_hypers.at("optimization").get<json>();
        if (optimization_hypers.find("type") != optimization_hypers.end()) {
          auto intp_type_name{
              optimization_hypers.at("type").get<std::string>()};
          if (intp_type_name == "Spline") {
            this->optimization_type = OptimizationType::Interpolator;
          } else {
            std::runtime_error("Wrongly configured optimization type. Remove "
                               "optimization flag or use as type \'Spline\'.");
          }
        } else {
          std::runtime_error("Wrongly configured optimization. Please name an "
                             "optimization type.");
        }
      } else {  // Default false (don't use interpolator)
        this->optimization_type = OptimizationType::None;
      }

      switch (internal::combine_to_radial_contribution_type(
          this->radial_integral_type, this->atomic_smearing_type,
          this->optimization_type)) {
      case internal::combine_to_radial_contribution_type(
          RadialBasisType::GTO, AtomicSmearingType::Constant,
          OptimizationType::None): {
        auto rc_shared = std::make_shared<internal::RadialContributionHandler<
            RadialBasisType::GTO, AtomicSmearingType::Constant,
            OptimizationType::None>>(hypers);
        this->radial_integral = rc_shared;
        break;
      }
      case internal::combine_to_radial_contribution_type(
          RadialBasisType::GTO, AtomicSmearingType::Constant,
          OptimizationType::Interpolator): {
        auto rc_shared = std::make_shared<internal::RadialContributionHandler<
            RadialBasisType::GTO, AtomicSmearingType::Constant,
            OptimizationType::Interpolator>>(hypers);
        this->radial_integral = rc_shared;
        break;
      }
      case internal::combine_to_radial_contribution_type(
          RadialBasisType::DVR, AtomicSmearingType::Constant,
          OptimizationType::None): {
        auto rc_shared = std::make_shared<internal::RadialContributionHandler<
            RadialBasisType::DVR, AtomicSmearingType::Constant,
            OptimizationType::None>>(hypers);
        this->radial_integral = rc_shared;
        break;
      }
      case internal::combine_to_radial_contribution_type(
          RadialBasisType::DVR, AtomicSmearingType::Constant,
          OptimizationType::Interpolator): {
        auto rc_shared = std::make_shared<internal::RadialContributionHandler<
            RadialBasisType::DVR, AtomicSmearingType::Constant,
            OptimizationType::Interpolator>>(hypers);
        this->radial_integral = rc_shared;
        break;
      }
      default:
        throw std::logic_error(
            "The desired combination of parameters can not be handled.");
        break;
      }
    }

  template <class StructureManager>
  void compute(StructureManager & manager) {
    // specialize based on the type of radial contribution
    using internal::AtomicSmearingType;
    using internal::OptimizationType;
    using internal::RadialBasisType;

    switch (internal::combine_to_radial_contribution_type(
        this->radial_integral_type, this->atomic_smearing_type,
        this->optimization_type)) {
    case internal::combine_to_radial_contribution_type(
        RadialBasisType::GTO, AtomicSmearingType::Constant,
        OptimizationType::None): {
      this->compute_impl<RadialBasisType::GTO,
                         AtomicSmearingType::Constant, OptimizationType::None>(
          manager);
      break;
    }
    case internal::combine_to_radial_contribution_type(
        RadialBasisType::GTO, AtomicSmearingType::Constant,
        OptimizationType::Interpolator): {
      this->compute_impl<RadialBasisType::GTO,
                         AtomicSmearingType::Constant,
                         OptimizationType::Interpolator>(manager);
      break;
    }
    case internal::combine_to_radial_contribution_type(
        RadialBasisType::DVR, AtomicSmearingType::Constant,
        OptimizationType::None): {
      this->compute_impl<RadialBasisType::DVR,
                         AtomicSmearingType::Constant, OptimizationType::None>(
          manager);
      break;
    }
    case internal::combine_to_radial_contribution_type(
        RadialBasisType::DVR, AtomicSmearingType::Constant,
        OptimizationType::Interpolator): {
      this->compute_impl<RadialBasisType::DVR,
                         AtomicSmearingType::Constant,
                         OptimizationType::Interpolator>(manager);
      break;
    }

    }
  }

  template <internal::RadialBasisType RadialType,
            internal::AtomicSmearingType SmearingType,
            internal::OptimizationType OptType, class StructureManager>
  void compute_impl(std::shared_ptr<StructureManager> manager) {
    using math::PI;
    auto radial_integral{
        downcast_radial_integral_handler<RadialType, SmearingType, OptType>(
            this->radial_integral)};
    auto coefs_n = math::Matrix_t(this->max_radial, this->max_angular + 1);
    auto coefs_c = math::Vector_t(this->max_radial);

    for (auto center : manager) {
      coefs_c = radial_integral->template compute_center_contribution(center) /
          std::sqrt(4.0 * PI);
      for (auto neigh : center.pairs()) {
        const double & dist{manager->get_distance(neigh)};
        coefs_n = radial_integral->template compute_neighbour_contribution(dist,
                                                                     neigh);
      }
    }
  }
}

int main(int argc, char * argv[]) {
  if (argc < 3) {
    std::cerr << "Must provide setup json filename as argument and output filename";
    std::cerr << std::endl;
    return -1;
  }

  json timings{};

  timings["fn_input"] = argv[1];
  timings["fn_output"] = argv[2];

  json input = json_io::load(argv[1]);
  timings["input"] = input;

  std::string filename{input["filename"].get<std::string>()};
  const int N_ITERATIONS = input["N_ITERATIONS"].get<int>();
  json adaptors = input["adaptors"].get<json>();
  json calculator = input["calculator"].get<json>();

  Representation_t representation{calculator};

  std::cout << "Config filename: " << filename << std::endl;

  std::chrono::duration<double> elapsed{};

  // compute NL
  ManagerCollection_t managers{adaptors};
  managers.add_structures(filename, 0, input["n_structures"].get<int>());

  std::shared_ptr<internal::RadialContributionBase> radial_integral{};

  RadialIntegral radial_integral{hypers};
  auto start = std::chrono::high_resolution_clock::now();
  // This is the part that should get profiled
  for (int looper{0}; looper < N_ITERATIONS; looper++) {
    for (auto manager : managers) {
      radial_integral.compute(manager);
    }
  }
  auto finish = std::chrono::high_resolution_clock::now();

  std::vector<std::vector<size_t>> n_neighbors{};
  for (auto manager : managers) {
    n_neighbors.emplace_back();
    for (auto center : manager) {
      size_t n_neighbors_center{0};
      for (auto neigh : center.pairs()) {
        n_neighbors_center++;
      }
      n_neighbors.back().emplace_back(n_neighbors_center);
    }
  }

  json results{{
    {"elapsed", elapsed.count() / N_ITERATIONS},
    {"n_neighbors", n_neighbors}
  }};

  timings["results"] = results;

  std::ofstream o(argv[2]);
  o << std::setw(2) << timings << std::endl;
}
