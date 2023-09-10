
def degree_to_speed(degree):
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

    # elif (degree > 40) and (degree <= 55):
    #     speed = round(degree * (1 + (0.025 * (degree - 40))))
    #     speed = min(100, speed)

    # elif (degree > 55) and (degree <= 60):
    #     speed = round(degree * 1.6)
    #     speed = min(100, speed)

    # else:
    #     speed = 100

    speed = round((6 * degree) - 200)
    speed = min(100, speed)
    speed = max(0, speed)

    return speed
