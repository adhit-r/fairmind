"""WEAT reports a real permutation p-value and no invented confidence."""
import asyncio

import numpy as np

from src.application.services.bias_testing_library import BiasTestingLibrary, TestingLibrary


def _weat(embeddings, targets, a, b):
    lib = BiasTestingLibrary()
    lib.available_libraries[TestingLibrary.WEAT] = True
    return asyncio.run(lib.run_weat_test(embeddings=embeddings, target_words=targets, attribute_words_a=a, attribute_words_b=b))


def test_strong_association_is_significant():
    rng = np.random.default_rng(1)
    axis = np.zeros(16); axis[0] = 1.0
    emb = {f"a{i}": axis + 0.1 * rng.normal(size=16) for i in range(6)}
    emb |= {f"b{i}": -axis + 0.1 * rng.normal(size=16) for i in range(6)}
    emb |= {f"t{i}": axis + 0.1 * rng.normal(size=16) for i in range(6)}
    r = _weat(emb, [f"t{i}" for i in range(6)], [f"a{i}" for i in range(6)], [f"b{i}" for i in range(6)])
    assert r.p_value < 0.01 and r.confidence is None


def test_no_association_is_not_significant():
    rng = np.random.default_rng(2)
    emb = {w: rng.normal(size=16) for w in [f"{p}{i}" for p in "abt" for i in range(6)]}
    r = _weat(emb, [f"t{i}" for i in range(6)], [f"a{i}" for i in range(6)], [f"b{i}" for i in range(6)])
    assert r.p_value > 0.05
