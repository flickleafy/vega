
def list_average(list):
    """_summary_

    Args:
        list (_type_): _description_

    Returns:
        _type_: _description_
    """
    average = sum(list) / len(list)
    return average


def remove_first_add_last(list, last):
    """_summary_

    Args:
        list (_type_): _description_
        last (_type_): _description_

    Returns:
        _type_: _description_
    """
    del list[0]
    list.append(last)
    return list
