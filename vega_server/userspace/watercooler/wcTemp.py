import watercooler.cpuDegreeToSpeed as cpuDegreeToSpeed


def set_wc_fan_speed(devices, index, degree):
    """_summary_

    Args:
        watercoolers (_type_): _description_
        degree (_type_): _description_

    Returns:
        _type_: _description_
    """
    if len(devices) > 0:
        device = devices[index]

        speed = cpuDegreeToSpeed.degree_to_speed(degree)

        device.set_fixed_speed("fan", speed)

    return speed
