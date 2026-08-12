"""P1.2 acceptance — named streams: reproducible, independent, continuous."""

from tatkal_sim.core import RngStreams, derive_stream


def draws(rng, n=8):
    return [rng.random() for _ in range(n)]


def test_same_seed_same_name_identical_draws():
    assert draws(derive_stream(42, "arrivals")) == draws(derive_stream(42, "arrivals"))


def test_different_names_differ():
    assert draws(derive_stream(42, "arrivals")) != draws(derive_stream(42, "service"))


def test_different_seeds_differ():
    assert draws(derive_stream(1, "arrivals")) != draws(derive_stream(2, "arrivals"))


def test_no_concatenation_ambiguity():
    # seed 1 + name "2x" must not collide with seed 12 + name "x"
    assert draws(derive_stream(1, "2x")) != draws(derive_stream(12, "x"))


def test_streams_are_independent():
    """Drawing from stream B must not perturb stream A's sequence (D6)."""
    world1 = RngStreams(7)
    world2 = RngStreams(7)
    # world1 interleaves B-draws; world2 never touches B
    a1 = world1.get("a")
    b1 = world1.get("b")
    seq1 = []
    for _ in range(5):
        seq1.append(a1.random())
        b1.random()  # interleaved draws on another stream
    seq2 = draws(world2.get("a"), 5)
    assert seq1 == seq2


def test_get_returns_same_live_stream_never_a_reset():
    streams = RngStreams(7)
    first = streams.get("a").random()
    second = streams.get("a").random()  # same object: state continues
    assert first != second
    fresh = derive_stream(7, "a")
    assert [first, second] == [fresh.random(), fresh.random()]
