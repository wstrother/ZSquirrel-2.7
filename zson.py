from collections import OrderedDict

import json
from zs_constants import Zson


def load_zson(file_name):
    """
    loads ZSON formatted file as dict object
    """
    file = open(file_name, "r")
    text = file.read()
    file.close()

    return get_zson_data(text)


def save_zson(d, file_name, p=False):
    """
    saves a ZSON congruent dict object as ZSON syntax ''*.zson' file
    """
    file = open(file_name, "w")

    text = format_zson(d, p=p)
    if p:
        print(text)

    file.write(text)
    file.close()


def load_json(file_name):
    """
    loads JSON formatted file as dict object
    """
    file = open(file_name, "r")
    d = json.load(file)
    file.close()

    return d


def save_json(d, file_name):
    """
    saves a JSON congruent dict object as JSON formatted .json file
    """
    file = open(file_name, "w")
    json.dump(d, file)
    file.close()


def string_to_value(s):
    """
    checks if string can be converted into an int, float, list, or tuple
      if not, returns string unchanged
    """
    # check for numeric expression
    try:
        num = float(s)

        if num.is_integer():
            num = int(num)

        return num

    except ValueError:
        # EXPRESSION                # EXAMPLE

        # quotation expression      "some string here"
        if s[0] == "\"" and s[-1] == "\"":
            value = s

        # true keyword              true
        elif s == Zson.TRUE_KEYWORD:
            value = True

        # false keyword             false
        elif s == Zson.FALSE_KEYWORD:
            value = False

        # none keyword              null
        elif s == Zson.NONE_KEYWORD:
            value = None

        # single expression         some string here
        elif "," not in s:
            value = s

        # list single item          some value,
        elif s[-1] == ",":
            value = [string_to_value(s[:-1])]

        # list expression           value1, value2
        else:
            args = s.split(", ")

            if args[-1] == "":
                args = args[:-1]

            value = [string_to_value(v) for v in args]

        return value


def format_zson(d, p=False):
    """
    formats ZSON congruent dict items to ZSON formatted string
    """
    text = ""

    for section in d:
        text += "# " + section + "\n\n"

        text += format_dict(d[section])

    if p:
        print(text)

    return text


def format_dict(d, t=0):
    """
    formats dict items to string with recursive indentation
    """
    output = ""
    tab = "\t" * t

    # method converts Python str repr for
    # False, True, and None to JSON style:
    # false, true, null
    def get_str(x):
        s = str(x)

        if s == "True":
            s = "true"

        if s == "None":
            s = "null"

        if s == "False":
            s = "false"

        return s

    for key in d:
        value = d[key]

        # recursive call for dicts within dicts
        if isinstance(value, dict):
            output += "\n" + tab + str(key) + "\n"
            output += format_dict(value, t=t + 1) + "\n"

        else:
            if type(value) is list:
                rhs = ", ".join([get_str(item) for item in value])
                if len(value) == 1:
                    rhs += ","
            else:
                rhs = get_str(value)
                # if "," in rhs:
                #     rhs = "\"{}\"".format(rhs)

            output += tab + str(key) + ": " + rhs + "\n"

    return output


def check_zson_syntax(s, warning=True, p=False):
    """
    checks string for ZSON syntax compatibility
      optionally raises ValueError or warnings
    returns string if OK, or 'corrected' string if warning=True
    """
    sections = s.split("#")
    output = []

    for section in [s for s in sections if s]:
        lines = [l for l in section.split("\n") if l]

        for line in lines:
            ignore = line.isspace() or line == ""

            if not ignore:
                syntax_error = False
                error_type = ""

                # check section header syntax       '# section_header'
                if line == lines[0]:
                    if not (line[0] == " " and len(line) > 1):
                        syntax_error = True
                        error_type = "Bad section header"

                # check item header syntax          'item name'
                elif line[0] != "\t" and line[0].isspace():
                    syntax_error = True
                    error_type = "Bad item header"

                # check parameter syntax            '\tparameter'
                #                                   '\tparameter: value'
                if line[0] == "\t" and ":" in line:
                    blank_name = line.split(":")[0].isspace() or line.split(":")[1].isspace()
                    blank_value = (line[-1] == ":")
                    if blank_value or blank_name:
                        syntax_error = True
                        error_type = "Bad parameter expression"

                if not syntax_error:
                    if line == lines[0]:
                        line = "#" + line
                    output.append(line)

                else:
                    msg = "ERROR in ZSON syntax: {}\n line: '{}'".format(
                        error_type, line)

                    if warning:
                        print("\n\nZ SQUIRREL WARNING!!!\n" + msg)

                    else:
                        raise ValueError(msg)

    text = "\n".join(output)

    if p:
        print(text)

    return text


def get_zson_data(s, ordered=False):
    """
    get a dict object from a ZSON formatted string
    """
    sections = check_zson_syntax(s).split("# ")
    d = {}

    for section in (s for s in sections if s):
        name = section.split("\n")[0]
        body = section[len(name):]

        # automatically order sections specified by zs_globals.py
        if not ordered:
            ordered = name in Zson.ORDERED_SECTIONS

        d[name] = get_section(body, ordered=ordered)

    return d


def get_section(s, ordered=False):
    """
    get a dict object from a single section of a CFG formatted string
    """
    lines = [l for l in s.split("\n") if l]

    item_strings = []
    item_names = []
    current = ""

    for line in lines:
        # find item headers
        header = not line[0] == "\t"

        if header:
            item_names.append(line)

            if len(item_names) > 1:
                # find parameters for current item
                item_strings.append(current)
                current = ""

        else:
            current += line + "\n"

    # add remaining item parameters
    item_strings.append(current)

    # make section dict an OrderedDict if flag is set
    section = {True: OrderedDict(), False: {}}[ordered]

    for name in item_names:
        i = item_names.index(name)
        item_str = item_strings[i]
        section[name] = get_item(item_str, ordered=ordered)

    return section


def get_item(s, ordered=False):
    """
    get a dict object from a single CFG formatted item expression
    """
    lines = [l for l in s.split("\n") if (l and l[0] == "\t")]
    if not ordered:
        item = {}
    else:
        item = OrderedDict()

    for line in lines:
        line = line[1:]

        # simple True bool expression       value_name
        if ":" not in line:
            key = string_to_value(line)
            value = True

        # key, value expression             value_name: some_value
        else:
            key, value = line.split(": ")
            value = string_to_value(value)

        item[key] = value

    return item
