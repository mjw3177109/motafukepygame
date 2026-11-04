"""Static source audit for independent tile-24 branches in original Move_arrow.

The report describes textual ordering, NOT Flash runtime reachability or parity.
"""
import re

GUARDS = (
    ("initial_dialogue", "_root.Display_say[0] == 0", (
        '_root.Display_say[0] = 1;', '_root.CopyMovie("mt_say_01","mtsay_001",1350,380,207);')),
    ("ending_state_change", "_root.mt_changes == 1 && _root.my_love == 0", (
        '_root.mtsay_001.gotoAndPlay("say_three");', '_root.mt_changes = 0;', '_root.mt_LastGame_ID = 1;')),
    ("love_dialogue", "_root.my_love == 1", (
        '_root.mt_line_20[7][5] = 13;', '_root.my_love = 0;', '_root.mt_changes = 0;')),
    ("floor22_dialogue", "_root.Now_line == 22", (
        '_root.mtsay_001.gotoAndPlay("say_six");', '_root.mtsay_001.gotoAndPlay("say_five");')),
)


def _code_only(source: str) -> str:
    """Mask comments and string contents while preserving offsets and newlines."""
    out = list(source)
    state = 'code'
    i = 0
    while i < len(source):
        c = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ''
        if state == 'code':
            if c in ('"', "'"):
                state = c
                out[i] = ' '
            elif c == '/' and nxt in ('/', '*'):
                state = 'line' if nxt == '/' else 'block'
                out[i] = out[i + 1] = ' '
                i += 1
        elif state in ('"', "'"):
            if c == chr(92) and nxt:
                out[i] = ' '
                i += 1
                if source[i] not in '\r\n':
                    out[i] = ' '
            elif c == state:
                out[i] = ' '
                state = 'code'
            elif c not in '\r\n':
                out[i] = ' '
        elif state == 'line':
            if c in '\r\n':
                state = 'code'
            else:
                out[i] = ' '
        elif state == 'block':
            if c == '*' and nxt == '/':
                out[i] = out[i + 1] = ' '
                i += 1
                state = 'code'
            elif c not in '\r\n':
                out[i] = ' '
        i += 1
    if state in ('"', "'", 'block'):
        raise ValueError('unterminated ActionScript string or comment')
    return ''.join(out)


def _braced_body(source: str, brace_index: int) -> str:
    """Return a code brace-delimited block, ignoring braces in literals/comments."""
    code = _code_only(source)
    if code[brace_index] != '{':
        raise ValueError('expected code opening brace')
    depth = 0
    for i in range(brace_index, len(code)):
        if code[i] == '{':
            depth += 1
        elif code[i] == '}':
            depth -= 1
            if depth == 0:
                return source[brace_index + 1:i]
    raise ValueError('unterminated tile-24 branch')


def _verify_love_dialogue_arms(branch_body: str) -> None:
    """Require both original item-dependent arms; a shared write alone is insufficient."""
    start = re.search(
        r'(?m)^[ \t]*if\s*\(\s*Number\(_root\.mt_GetMoney\[0\]\)\s*==\s*1\s*\)\s*\{',
        _code_only(branch_body),
    )
    if start is None:
        raise ValueError('tile-24 love_dialogue missing item-dependent if arm')
    yes_body = _braced_body(branch_body, start.end() - 1)
    closing_brace = start.end() - 1 + len(yes_body) + 1
    else_match = re.match(r'\s*else\s*\{', _code_only(branch_body)[closing_brace + 1:])
    if else_match is None:
        raise ValueError('tile-24 love_dialogue missing else arm')
    else_brace = closing_brace + 1 + else_match.end() - 1
    no_body = _braced_body(branch_body, else_brace)
    # The original resets run after the entire if/else, regardless of item choice.
    # Checking only the outer branch would incorrectly accept a reset in one arm.
    after_choice = branch_body[else_brace + len(no_body) + 2:]
    # Require direct execution after the item choice, not a nested conditional.
    depth = 0
    direct_resets = []
    for line, code_line in zip(after_choice.splitlines(), _code_only(after_choice).splitlines()):
        stripped = line.strip()
        if depth == 0:
            direct_resets.append(stripped)
        depth += code_line.count('{') - code_line.count('}')
        if depth < 0:
            raise ValueError('tile-24 love_dialogue unbalanced post-choice block')
    if depth != 0:
        raise ValueError('tile-24 love_dialogue unbalanced post-choice block')
    for statement in ('_root.my_love = 0;', '_root.mt_changes = 0;'):
        if direct_resets.count(statement) != 1:
            raise ValueError(f'tile-24 love_dialogue missing shared post-choice reset (not direct): {statement}')
    # Original ActionScript clears my_love before mt_changes at the same level.
    reset_order = [line for line in direct_resets if line in (
        '_root.my_love = 0;', '_root.mt_changes = 0;')]
    if reset_order != ['_root.my_love = 0;', '_root.mt_changes = 0;']:
        raise ValueError('tile-24 love_dialogue shared reset order differs from original')
    for label, body, expected in (
        ('if', yes_body, '_root.mtsay_001.gotoAndPlay("say_four");'),
        ('else', no_body, '_root.mtsay_001.gotoAndPlay("say_two");'),
    ):
        for statement in (expected, '_root.mt_line_20[7][5] = 13;'):
            if not re.search(r'(?m)^[ \t]*' + re.escape(statement) + r'[ \t\r]*$', body):
                raise ValueError(f'tile-24 love_dialogue {label} arm missing statement: {statement}')


def _verify_floor22_dialogue_arms(branch_body: str) -> None:
    """Check the exact three-item AND guard, setup, and both exclusive dialogue arms."""
    item_guard = (
        r'(?m)^[ \t]*if\s*\(\s*'
        r'Number\(_root\.mt_GetMoney\[0\]\)\s*==\s*1\s*&&\s*'
        r'Number\(_root\.mt_GetMoney\[1\]\)\s*==\s*1\s*&&\s*'
        r'Number\(_root\.mt_GetMoney\[2\]\)\s*==\s*1\s*\)\s*\{'
    )
    matches = list(re.finditer(item_guard, _code_only(branch_body)))
    if len(matches) != 1:
        raise ValueError('tile-24 floor22_dialogue missing exact three-item AND guard')
    start = matches[0]
    # These effects must precede the nested choice, not be confined to one arm.
    setup = branch_body[:start.start()]
    setup_positions = []
    for statement in (
        '_root.Now_key_flag = 0;',
        '_root.Display_say[0] = 1;',
        '_root.CopyMovie("mt_say_01","mtsay_001",1350,380,207);',
    ):
        matches = list(re.finditer(r'(?m)^[ \t]*' + re.escape(statement) + r'[ \t\r]*(?=\n|\Z)', setup))
        if len(matches) != 1:
            raise ValueError(f'tile-24 floor22_dialogue missing or duplicated pre-choice setup: {statement}')
        setup_positions.append(matches[0].start())
    if setup_positions != sorted(setup_positions):
        raise ValueError('tile-24 floor22_dialogue pre-choice setup order differs from original')

    yes_body = _braced_body(branch_body, start.end() - 1)
    closing_brace = start.end() - 1 + len(yes_body) + 1
    else_match = re.match(r'\s*else\s*\{', _code_only(branch_body)[closing_brace + 1:])
    if else_match is None:
        raise ValueError('tile-24 floor22_dialogue missing else arm')
    else_brace = closing_brace + 1 + else_match.end() - 1
    no_body = _braced_body(branch_body, else_brace)
    for label, body, statement in (
        ('if', yes_body, '_root.mtsay_001.gotoAndPlay("say_six");'),
        ('else', no_body, '_root.mtsay_001.gotoAndPlay("say_five");'),
    ):
        if not re.search(r'(?m)^[ \t]*' + re.escape(statement) + r'[ \t\r]*$', body):
            raise ValueError(f'tile-24 floor22_dialogue {label} arm missing statement: {statement}')


def verify_tile24_branch_order(source: str) -> dict:
    declarations = list(re.finditer(r'(?m)^function[ \t]+Move_arrow\(arrow_id\)[ \t]*\r?\n\{', source))
    if len(declarations) != 1:
        raise ValueError('expected exactly one Move_arrow declaration')
    tail = source[declarations[0].end():]
    end = re.search(r'(?m)^}[ \t\r]*$', tail)
    if end is None:
        raise ValueError('missing Move_arrow closing brace')
    body = tail[:end.start()]
    # Match branch guards only in executable source, never inside comments/strings.
    guard_code = _code_only(body)
    prefix = r'(?m)^[ \t]+if\s*\(\s*Number\(eval\(temp_lines\)\[temp_x\]\[temp_y\]\)\s*==\s*24\s*&&\s*'
    tile_guards = list(re.finditer(prefix, guard_code))
    if len(tile_guards) != 4:
        raise ValueError(f'expected four independent tile-24 guards, found {len(tile_guards)}')
    positions = []
    output = []
    for label, condition, statements in GUARDS:
        cond_regex = re.escape(condition).replace(r'\ ', r'\s*')
        pattern = prefix + cond_regex + r'\s*\)\s*\{'
        matches = list(re.finditer(pattern, guard_code))
        if len(matches) != 1:
            raise ValueError(f'tile-24 {label} guard missing or duplicated')
        match = matches[0]
        positions.append(match.start())
        branch_body = _braced_body(body, match.end() - 1)
        if label == 'floor22_dialogue':
            _verify_floor22_dialogue_arms(branch_body)
        for statement in statements:
            pattern = r'(?m)^[ \t]*' + re.escape(statement) + r'[ \t\r]*$'
            code = _code_only(branch_body)
            if not any(code[m.start():].lstrip().startswith('_root.')
                       for m in re.finditer(pattern, branch_body)):
                raise ValueError(f'tile-24 {label} missing branch statement: {statement}')
        if label == 'love_dialogue':
            _verify_love_dialogue_arms(branch_body)
        output.append({'branch': label, 'guard': condition,
                       'line': source.count('\n', 0, declarations[0].end())
                       + body.count('\n', 0, match.start()) + 1})
    if positions != sorted(positions) or positions != [m.start() for m in tile_guards]:
        raise ValueError('tile-24 independent guard order differs from original')
    return {'source_order': output, 'independent_if_statements_verified': True,
            'love_dialogue_both_arms_verified': True,
            'floor22_three_item_both_arms_verified': True,
            'runtime_combined_branch_execution_verified': False,
            'runtime_event_reachability_verified': False,
            'flash_parity_verified': False}


