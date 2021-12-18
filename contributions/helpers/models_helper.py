# TB
import re

from contributions.constants import RegexConstants


def detect_impact_loc(code):
    total_lines = code.count('\n')
    if total_lines > 0:
        lines = code.split("\n")
        # In case we should consider commented lines
        for line in lines:
            m = re.search(r"\u002F/.*", line)
            n = re.search(RegexConstants.COMMENTARY_REGEX, line)
            if m or n:
                if m:
                    found = m.group(0)
                    line = line.replace(found, '')
                    line.replace(' ', '', 1)
                    if not line.strip().isdigit():
                        return True
                elif n:
                    found = n.group(0)
                    line = line.replace(found, '')
                    line.replace(' ', '', 1)
                    if not line.strip().isdigit():
                        return True
            elif not line.replace(" ", "").isdigit() and (line != '' and line != '\n'):
                return True

    return False


def count_loc(code):
    total_lines = code.count('\n')
    return total_lines - count_blank_lines(code)


def count_blank_lines(code):
    blank_lines = 0
    lines = code.split('\n')
    for line in lines[1:]:
        if not line.strip() or line.replace(" ", "").isdigit():
            blank_lines += 1
    return blank_lines


def prepare_diff_text(text, result, type_symbol):
    for line in text:
        result = result + "\n" + str(line[0]) + ' ' + type_symbol + ' ' + line[1]
    return result


def has_impact_loc_calculation_static_method(diff):
    added_text = prepare_diff_text(diff['added'], "", "")
    deleted_text = prepare_diff_text(diff['deleted'], "", "")
    return detect_impact_loc(added_text) or detect_impact_loc(deleted_text)
