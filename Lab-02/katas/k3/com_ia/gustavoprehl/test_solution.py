import pytest
from solution import calculate_change

def test_exact_change_high_value_bills():
    inventory = {50: 1, 20: 2, 10: 5}
    amount = 70

    assert calculate_change(amount, inventory) == {50: 1, 20: 1}

def test_exact_change_using_smaller_bills():
    inventory = {50: 0, 20: 2, 10: 5}
    amount = 60

    assert calculate_change(amount, inventory) == {20: 2, 10: 2}

def test_impossible_insufficient_total_value():
    inventory = {50: 1, 20: 2, 10: 5}
    amount = 200

    assert calculate_change(amount, inventory) is None

def test_impossible_missing_small_bills():
    inventory = {50: 1, 20: 2}
    amount = 30
    assert calculate_change(amount, inventory) is None

def test_zero_change():
    inventory = {50: 1, 20: 2, 10: 5}
    amount = 0

    assert calculate_change(amount, inventory) == {}
