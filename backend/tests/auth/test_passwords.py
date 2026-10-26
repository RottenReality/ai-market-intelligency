from app.auth.passwords import hash_password, verify_password


def test_verify_password_accepts_correct_and_rejects_wrong():
    hashed = hash_password("correct horse", rounds=4)
    assert verify_password("correct horse", hashed)
    assert not verify_password("wrong horse", hashed)


def test_verify_password_rejects_malformed_hash():
    assert not verify_password("anything", "not-a-bcrypt-hash")
