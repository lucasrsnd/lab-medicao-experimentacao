def flatten_dict(d: dict, parent_key: str = '') -> dict:
    """
    Achata um dicionário concatenando chaves com um underline.
    Args:
        d(dict) - Dicionário a ser achatado;
        parent_key(str) - Chave pai
    Returns:
        dict - Dicionário de nível único
    """
    items = []

    for k, v in d.items():
        new_key = f"{parent_key}_{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key).items())
        else:
            items.append((new_key, v))

    return dict (items)
