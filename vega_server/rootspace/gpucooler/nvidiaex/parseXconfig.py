
def parse_sections(lines):
    sections = []
    start = None
    end = None

    for index, line in enumerate(lines):
        if 'Section "' in line:
            start = index
        if "EndSection" in line:
            end = index

        if start and end:
            sections.append({"start": start, "end": end})
            start = None
            end = None

    return sections


def get_specific_section(lines, sections, section_name):
    for section in sections:
        index = section["start"]
        section_header = lines[index]
        if section_name in section_header:
            return section
    return None


def get_specific_sections(lines, sections, section_name):
    selected_sections = []
    for section in sections:
        index = section["start"]
        section_header = lines[index]
        if section_name in section_header:
            selected_sections.append(section)

    return selected_sections
