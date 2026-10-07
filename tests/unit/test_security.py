from backend.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    has_permission,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("s3cret!")
    assert verify_password("s3cret!", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_roundtrip():
    token = create_access_token(subject="alice", role="operator")
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "alice"
    assert payload["role"] == "operator"


def test_jwt_rejects_garbage():
    assert decode_access_token("not-a-real-token") is None


def test_rbac_permissions():
    assert has_permission("admin", "manage_users")
    assert not has_permission("viewer", "write")
    assert has_permission("operator", "query")
