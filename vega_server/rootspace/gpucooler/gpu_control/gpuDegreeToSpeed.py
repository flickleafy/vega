
def degree_to_speed(degree, modifier):
    """_summary_

    Args:
        degree (_type_): _description_

    Returns:
        _type_: _description_
    """
    speed = 0

    # NOSONAR
    # if degree <= 40:
    #     speed = round(degree + 1.5)

    # elif (degree > 40) and (degree <= 50):
    #     speed = round(degree * (1 + ((0.10 + modifier) * (degree - 40))))
    #     speed = min(100, speed)

    # elif (degree > 50) and (degree <= 60):
    #     speed = round(degree * 1.6)
    #     speed = min(100, speed)

    # else:
    #     speed = 100

    degree = degree * (1 + modifier)
    speed = round(((5 * degree) - 100) * 0.5)
    speed = min(100, speed)
    speed = max(0, speed)

    return speed
