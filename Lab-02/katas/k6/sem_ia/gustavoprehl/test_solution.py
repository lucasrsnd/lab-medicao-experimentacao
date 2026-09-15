import pytest
from solution import group_anagrams_by_weight

def test_should_return_empty_dict_for_empty_list():
    assert group_anagrams_by_weight([]) == {}

def test_should_group_simple_anagrams_correctly():
    words = ["abc", "cab", "xyz"]
    result = group_anagrams_by_weight(words)

    key_abc = (294, "abc")
    key_xyz = (363, "xyz")

    assert key_abc in result
    assert key_xyz in result

    assert set(result[key_abc]) == {"abc", "cab"}
    assert set(result[key_xyz]) == {"xyz"}

def test_should_separate_words_with_same_ascii_sum_but_not_anagrams():
    words = ["ad", "bc", "da"]
    result = group_anagrams_by_weight(words)

    key_ad = (197, "ad")
    key_bc = (197, "bc")

    assert key_ad in result
    assert key_bc in result

    assert set(result[key_ad]) == {"ad", "da"}
    assert set(result[key_bc]) == {"bc"}

def test_should_handle_empty_words_in_list():
    words = ["", "a", "a"]
    result = group_anagrams_by_weight(words)

    assert (0, "") in result
    assert (97, "a") in result
    assert result[(0, "")] == [""]
    assert result[(97, "a")] == ["a", "a"]
