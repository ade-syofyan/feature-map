"""Conservative presentation filtering; unknown edits still require review."""
import difflib
import re

_ZERO = re.compile(r'[+\-]?(?:0+(?:\.0*)?|\.0+)(?:[A-Za-z%]+)?')
_STYLE_CLASS = re.compile(
    r'(?:[pm][trblxyse]?-(?:\d+(?:\.\d+)?|px)|'
    r'text-(?:left|right|center|start|end|xs|sm|base|lg|xl|[2-9]xl)|'
    r'font-(?:normal|medium|semibold|bold)|fw-(?:normal|bold)|'
    r'rounded(?:-(?:none|sm|md|lg|xl|full))?|'
    r'(?:bg|text|border)-(?:red|blue|green|gray|grey|slate|white|black)(?:-\d{2,3})?)')
_STYLE_PROPERTIES = {'color', 'background-color', 'font-size', 'font-weight',
                     'font-family', 'text-align', 'border-color', 'border-width',
                     'border-radius', 'padding', 'padding-left', 'padding-right',
                     'padding-top', 'padding-bottom', 'margin', 'margin-left',
                     'margin-right', 'margin-top', 'margin-bottom'}
_EXCEL_METHODS = {'getStyle', 'getFont', 'getAlignment', 'getFill', 'getColor',
                  'getStartColor', 'getBorders', 'getAllBorders', 'getRowDimension',
                  'getColumnDimension', 'setBold', 'setItalic', 'setSize', 'setName',
                  'setRGB', 'setARGB', 'setHorizontal', 'setVertical', 'setWidth',
                  'setHeight', 'setRowHeight', 'setAutoSize', 'setWrapText'}
_LITERAL = re.compile(r'''(?:'[^'$\\]*'|"[^"$\\]*"|true|false|\d+(?:\.\d+)?)''')


def edit_pairs(tool_name, tool_input):
    if tool_name == 'Edit':
        rows = [tool_input]
    elif tool_name == 'MultiEdit':
        rows = tool_input.get('edits')
    else:
        return None
    if not isinstance(rows, list) or not rows:
        return None
    if any(not isinstance(row, dict) or not all(isinstance(row.get(k), str)
            for k in ('old_string', 'new_string')) for row in rows):
        return None
    return [(row['old_string'], row['new_string']) for row in rows]


def _excel_style(line):
    if not re.fullmatch(r'\s*\$\w+(?:->\w+\([^()]*\))+\s*;\s*', line):
        return False
    calls = re.findall(r'->(\w+)\(([^()]*)\)', line)
    if not calls or calls[0][0] not in ('getStyle', 'getColumnDimension', 'getRowDimension'):
        return False
    for method, args in calls:
        if method not in _EXCEL_METHODS:
            return False
        if args.strip() and any(not _LITERAL.fullmatch(a.strip()) for a in args.split(',')):
            return False
        if method in ('setSize', 'setWidth', 'setHeight', 'setRowHeight') and _ZERO.fullmatch(args.strip()):
            return False
    return True


def _presentation_mask(text):
    def classes(value):
        if any(c in value for c in '${}:<>'):
            return value
        kept = [token for token in value.split() if not _STYLE_CLASS.fullmatch(token)]
        return ' '.join(kept)

    def styles(value):
        kept = []
        for declaration in value.split(';'):
            if not declaration.strip():
                continue
            key, separator, value = declaration.partition(':')
            safe = (separator and key.strip().lower() in _STYLE_PROPERTIES and
                    re.fullmatch(r'[A-Za-z0-9#.,% +\-]+', value.strip()) and
                    value.strip().lower() != 'transparent' and
                    not (key.strip().lower() == 'font-size' and _ZERO.fullmatch(value.strip())))
            if not safe:
                kept.append(declaration)
        return ';'.join(kept)

    lines = [line for line in text.splitlines() if not _excel_style(line)]
    result = '\n'.join(lines)
    def attribute(match):
        space, name, quote, value = match.groups()
        if name not in ('class', 'style'):
            return match.group(0)
        value = classes(value) if name == 'class' else styles(value)
        return space + name + '=' + quote + value + quote

    def tag(match):
        return re.sub(r"""(\s+)([A-Za-z_:][\w:.-]*)\s*=\s*(["'])(.*?)\3""", attribute, match.group(0), flags=re.DOTALL)

    return re.sub(r"""<[A-Za-z](?:[^<>'"]|"[^"]*"|'[^']*')*>""", tag, result)


def presentation_only(tool_name, tool_input):
    pairs = edit_pairs(tool_name, tool_input)
    return bool(pairs) and all(_presentation_mask(old) == _presentation_mask(new)
                               for old, new in pairs)


def changed_text(tool_name, tool_input):
    pairs = edit_pairs(tool_name, tool_input)
    if pairs is None:
        if tool_name == 'MultiEdit':
            return '\n'.join(row.get('new_string', '') for row in tool_input.get('edits', []) if isinstance(row, dict))
        return tool_input.get('new_string') or tool_input.get('content') or tool_input.get('new_source') or ''
    lines = []
    for old, new in pairs:
        if _presentation_mask(old) == _presentation_mask(new):
            continue
        before, after = old.splitlines(), new.splitlines()
        for kind, a, b, c, d in difflib.SequenceMatcher(None, before, after, autojunk=False).get_opcodes():
            if kind != 'equal':
                lines.extend(before[a:b]); lines.extend(after[c:d])
    return '\n'.join(lines)
