from solution import is_valid_password

def test_valid_password():
    assert is_valid_password("PassWord1") is True
    assert is_valid_password("aBcDeFgH") is True

def test_reject_short_password():
    assert is_valid_password("aBcDeF") is False
    assert is_valid_password("AbCd123") is False

def test_reject_adjacent_uppercase():
    assert is_valid_password("ABcdefgh1") is False
    assert is_valid_password("passWORD") is False

def test_reject_triple_repetition():
    assert is_valid_password("aBcaaaDe") is False
    assert is_valid_password("Abcdefff") is False

def test_reject_insufficient_uppercase():
    assert is_valid_password("Abcdefgh") is False
    assert is_valid_password("abcdefgh") is False
