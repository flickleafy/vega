import gpucooler.nvidiaex.parseXconfig as parse_xconfig
from globals import ERROR_MESSAGE
import utils.filesManipulation as files


def layout_has_multi_screens():
    has_multi_screens = False
    try:
        xorg_conf_file = files.read_file('/etc/X11/xorg.conf')
        sections = parse_xconfig.parse_sections(xorg_conf_file)
        serverlayout_section = parse_xconfig.get_specific_section(
            xorg_conf_file, sections, 'ServerLayout')
        has_multi_screens: bool = check_multi_screens(
            xorg_conf_file, serverlayout_section)
        if has_multi_screens:
            check_and_fix_layout_order(xorg_conf_file, serverlayout_section)
    except Exception as err:
        print(ERROR_MESSAGE, err)

    return has_multi_screens


def check_multi_screens(lines, section):
    start = section['start']
    end = section['end']
    screens = 0
    for index in range(start + 1, end - 1):
        line = lines[index]
        if 'Screen' in line:
            screens += 1
    if screens > 1:
        return True
    return False


def check_and_fix_layout_order(lines, section):
    start = section['start']
    end = section['end']
    changed = False
    for index in range(start + 1, end - 1):
        line = lines[index]
        if ('RightOf' in line) or ('LeftOf' in line):
            new_line = '    Screen      1  "Screen1" Absolute 9999 9999\n'
            lines[index] = new_line
            changed = True

        if changed:
            files.write_file('/etc/X11/xorg.conf', lines)
