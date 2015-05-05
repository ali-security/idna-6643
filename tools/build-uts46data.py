#!/usr/bin/env python

"""Create a Python version of the IDNA Mapping Table from UTS46."""

import re
import sys

# pylint: disable=unused-import,import-error,undefined-variable
if sys.version_info[0] == 3:
    from urllib.request import urlopen
    unichr = chr
else:
    from urllib2 import urlopen
# pylint: enable=unused-import,import-error,undefined-variable



DATA_URL = "http://www.unicode.org/Public/idna/6.3.0/IdnaMappingTable.txt"
RE_CHAR_RANGE = re.compile(br"([0-9a-fA-F]{4,6})(?:\.\.([0-9a-fA-F]{4,6}))?$")
STATUSES = {
    b"valid": ("V", False),
    b"ignored": ("I", False),
    b"mapped": ("M", True),
    b"deviation": ("D", True),
    b"disallowed": ("X", False),
    b"disallowed_STD3_valid": ("3", False),
    b"disallowed_STD3_mapped": ("3", True)
}


def parse_idna_mapping_table(inputstream):
    """Parse IdnaMappingTable.txt and return a list of tuples."""
    ranges = []
    last_code = -1
    for line in inputstream:
        line = line.strip()
        if b"#" in line:
            line = line.split(b"#", 1)[0]
        if not line:
            continue
        fields = [field.strip() for field in line.split(b";")]
        char_range = RE_CHAR_RANGE.match(fields[0])
        if not char_range:
            raise ValueError(
                "Invalid character or range {!r}".format(fields[0]))
        start = int(char_range.group(1), 16)
        if start != last_code + 1:
            raise ValueError(
                "Code point {!r} is not continguous".format(fields[0]))
        if char_range.lastindex == 2:
            last_code = int(char_range.group(2), 16)
        else:
            last_code = start
        status, mapping = STATUSES[fields[1]]
        if mapping:
            mapping = (u"".join(unichr(int(codepoint, 16))
                for codepoint in fields[2].split()).
                replace("\\", "\\\\").replace("'", "\\'"))
        else:
            mapping = None
        first = True
        while first or (start < 256 and start <= last_code):
            if mapping is not None:
                ranges.append(u"(0x{:X}, '{}', u'{}')".format(
                    start, status, mapping))
            else:
                ranges.append(u"(0x{:X}, '{}')".format(start, status))
            first = False
            start += 1
    return ranges


def main():
    """Fetch the mapping table, parse it, and rewrite idna/uts46data.py."""
    ranges = parse_idna_mapping_table(urlopen(DATA_URL))
    with open("idna/uts46data.py", "wb") as outputstream:
        outputstream.write(b'''\
# This file is automatically generated by tools/build-uts46data.py
# vim: set fileencoding=utf-8 :

"""IDNA Mapping Table from UTS46."""

uts46data = (
''')
        for row in ranges:
            outputstream.write(u"    {},\n".format(row).encode("utf8"))
        outputstream.write(b")\n")


if __name__ == "__main__":
    main()
