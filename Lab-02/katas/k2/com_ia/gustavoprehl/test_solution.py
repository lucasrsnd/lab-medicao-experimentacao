import pytest
from solution import has_conflicts

def test_no_overlap():
    assert has_conflicts([(1, 3), (4, 6), (7, 9)]) == False

def test_with_overlap():
    assert has_conflicts([(10, 12), (11, 13), (14, 15)]) is True

def test_adjacent_meetings():
    assert has_conflicts([(10, 12), (12, 14)]) is False

def test_empty_list():
    assert has_conflicts([]) is False

def test_single_meeting():
    assert has_conflicts([(10, 12)]) is False

def test_unsorted_meetings_no_conflict():
    assert has_conflicts([(4, 5), (1, 3), (6, 9)]) is False

def test_unsorted_meetings_with_conflict():
    assert has_conflicts([(14, 15), (10, 12), (11, 13)]) is True

def test_nested_overlap():
    assert has_conflicts([(10, 15), (11, 12)]) is True
