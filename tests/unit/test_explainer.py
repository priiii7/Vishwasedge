from backend.trust.explainer import explain, generate_what_ifs, token_gradient_saliency


def test_saliency_covers_every_token():
    saliency, latency_ms = token_gradient_saliency("safe operating pressure well W-123")
    assert len(saliency) == 5
    assert all(0.0 <= t.importance <= 1.0 for t in saliency)
    assert latency_ms >= 0


def test_saliency_empty_query():
    saliency, _ = token_gradient_saliency("")
    assert saliency == []


def test_what_ifs_reference_top_tokens():
    saliency, _ = token_gradient_saliency("critical safety shutdown pressure threshold")
    what_ifs = generate_what_ifs(saliency, top_n=2)
    assert len(what_ifs) == 2


def test_explain_end_to_end():
    result = explain("what is the maximum casing pressure")
    assert len(result.token_saliency) > 0
    assert len(result.alternate_paths) > 0
    assert result.latency_ms >= 0
