from backend.models.llm_router import downgrade_tier, score_complexity


def test_simple_factual_query_routes_fast():
    result = score_complexity("What is well W-123?")
    assert result.tier in {"fast", "haiku"}
    assert 0.0 <= result.score <= 1.0


def test_analytical_query_scores_higher_than_simple():
    simple = score_complexity("What is the pressure?")
    analytical = score_complexity(
        "Why does the wellhead pressure fluctuate and how does that impact casing integrity over time?"
    )
    assert analytical.score > simple.score


def test_downgrade_tier_order():
    assert downgrade_tier("sonnet") == "haiku"
    assert downgrade_tier("haiku") == "fast"
    assert downgrade_tier("fast") == "fast"
