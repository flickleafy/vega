def read_file(path):
    file_obj = open(path, 'r')
    lines = file_obj.readlines()
    return lines


def write_file(path, lines):
    file_obj = open(path, 'w')
    file_obj.writelines(lines)
    file_obj.close()
    return None
