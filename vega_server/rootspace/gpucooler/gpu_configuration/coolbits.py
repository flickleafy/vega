
import gpucooler.nvidiaex.parseXconfig as parse_xconfig
import vega_common.utils.files_manipulation as files


def displays_has_coolbits():
    xorg_conf_file = files.read_file('/etc/X11/xorg.conf')
    sections = parse_xconfig.parse_sections(xorg_conf_file)
    display_sections = parse_xconfig.get_specific_sections(
        xorg_conf_file, sections, 'Screen')
    has_coolbits: bool = check_coolbits(xorg_conf_file, display_sections)
    return has_coolbits


def check_coolbits(lines, sections):
    coolbits = 0
    for section in sections:
        start = section['start']
        end = section['end']
        for index in range(start + 1, end - 1):
            line = lines[index]
            if 'Coolbits' in line:
                coolbits += 1
    if coolbits > 1:
        return True
    return False
