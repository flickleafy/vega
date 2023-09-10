import watercooler.cpuDegreeToSpeed as cpuDegreeToSpeed


def set_wc_fan_speed(watercoolers, degree):
    """_summary_

    Args:
        watercoolers (_type_): _description_
        degree (_type_): _description_

    Returns:
        _type_: _description_
    """
    if len(watercoolers) == 1:
        device = watercoolers[0]

        speed = cpuDegreeToSpeed.degree_to_speed(degree)

        device.set_fixed_speed("fan", speed)

    return speed
