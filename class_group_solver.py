from sage.all import *
from solve_unit_group import compute_S_units


def solve_class_group(k: NumberField):
    bounded_ideals = k.get_bounded_ideals()
    S_units = compute_S_units(bounded_ideals)
    u, v = S_units

# Gets all prime ideals with norm less than Minkowski bound
# Involves enumerating primes less than this bound, which reqi
def get_bounded_prime_ideals(k: NumberField):
    # Factor (p) for all primes p less than or equal to Minkowski bound
    # Add 1, since prime_range is exclusive of the bound and rounds non-ints down
    primes = prime_range(k.minkowski_bound() + 1)

    bounded_ideals = []
    for prime in primes:
        ideal_factors = k.ideal(prime).factor()
        bounded_ideals.extend([ideal_factor[0] for ideal_factor in list(ideal_factors)])
    return bounded_ideals

