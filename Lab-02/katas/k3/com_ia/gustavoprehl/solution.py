def calculate_change(amount: int, inventory: dict) -> dict | None:
    if amount == 0:
        return {}

    change_given = {}
    available_bills = sorted(inventory.keys(), reverse=True)

    for bill in available_bills:
        if amount == 0:
            break

        available_quantity = inventory.get(bill, 0)

        if available_quantity > 0 and bill <= amount:
            required_quantity = amount // bill
            quantity_to_use = min(required_quantity, available_quantity)

            if quantity_to_use > 0:
                change_given[bill] = quantity_to_use
                amount -= bill * quantity_to_use

    if amount > 0:
        return None

    return change_given
