from solution import flatten_dict

def test_flat_dict():
    input_dict = {"id": 1, "role": "admin"}
    expected = {"id": 1, "role": "admin"}
    assert flatten_dict(input_dict) == expected

def test_nested_dict_two_levels():
    input_dict = {"user": {"id": 1, "name": "Bob"}}
    expected = {"user_id": 1, "user_name": "Bob"}
    assert flatten_dict(input_dict) == expected

def test_nested_dictionary_multiple_levels():
    input_dict = {
        "api": {
            "v1": {
                "users": {
                    "count": 100
                }
            }
        }
    }
    expected = {"api_v1_users_count": 100}

    assert flatten_dict(input_dict) == expected

def test_empty_dictionary():
    assert flatten_dict({}) == {}
