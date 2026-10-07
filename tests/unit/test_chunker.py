from backend.rag.chunker import fixed_chunk, semantic_chunk


def test_fixed_chunk_respects_size():
    text = "word " * 500
    chunks = fixed_chunk(text, chunk_size=200, overlap=20)
    assert all(len(c) <= 200 for c in chunks)
    assert len(chunks) > 1


def test_fixed_chunk_empty_text():
    assert fixed_chunk("") == []


def test_semantic_chunk_respects_sentence_boundaries():
    text = "Sentence one is here. Sentence two follows. Sentence three ends it."
    chunks = semantic_chunk(text, target_size=40)
    joined = " ".join(chunks)
    assert "Sentence one is here." in joined
    assert "Sentence three ends it." in joined


def test_semantic_chunk_empty_text():
    assert semantic_chunk("") == []
