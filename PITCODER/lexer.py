#   PitCode - Analizador Léxico 
#   Compiladores 2026 - Fase I
#   Lenguaje: PitCode 

import ply.lex as lex
import sys
import os

states = (
    ('transmission', 'exclusive'),
    ('signal',       'exclusive'),
)

#  PALABRAS RESERVADAS
reserved = {
    'lap'            : 'LAP',
    'split'          : 'SPLIT',
    'pitboard'       : 'PITBOARD',
    'yellow_flag'    : 'YELLOW_FLAG',
    'radio'          : 'RADIO',

    'strategy_check' : 'STRATEGY_CHECK',
    'stay_out'       : 'STAY_OUT',
    'push'           : 'PUSH',
    'box'            : 'BOX',
    'formation_lap'  : 'FORMATION_LAP',
    'gap_check'      : 'GAP_CHECK',
    'sector'         : 'SECTOR',
    'no_data'        : 'NO_DATA',
    'box_box'        : 'BOX_BOX',
    'drs'            : 'DRS',
    'pitwall'        : 'PITWALL',          

    'strategy'       : 'STRATEGY',
    'podio'          : 'PODIO',
    'neutro'         : 'NEUTRO',
    'race_start'     : 'RACE_START',

    'broadcast'      : 'BROADCAST',
    'telemetry'      : 'TELEMETRY',

    'undercut'       : 'UNDERCUT_KW',
    'dnf'            : 'DNF',
    'vsc'            : 'VSC',
    'paddock'        : 'PADDOCK',

    'red_flag'       : 'RED_FLAG',
    'blue_flag'      : 'BLUE_FLAG',
    'black_flag'     : 'BLACK_FLAG',
    'checkered_flag' : 'CHECKERED_FLAG',

    'true'           : 'TRUE',
    'false'          : 'FALSE',

    'Tow'            : 'TOW',
    'Gap'            : 'GAP',
    'ERS'            : 'ERS',
    'Stint'          : 'STINT',
    'Fuel_Delta'     : 'FUEL_DELTA',

    'DEAD_HEAT'      : 'DEAD_HEAT',
    'Outlap'         : 'OUTLAP',
    'UNDERCUT'       : 'UNDERCUT',
    'OVERCUT'        : 'OVERCUT',
    'undereq'        : 'UNDEREQ',
    'overeq'         : 'OVEREQ',

    'BOTH_TYRES'     : 'BOTH_TYRES',
    'EITHER_TYRE'    : 'EITHER_TYRE',
    'REVERSE_GRID'   : 'REVERSE_GRID',
    'safety'         : 'SAFETY',
    'overtake'       : 'OVERTAKE',
    'reverse'        : 'REVERSE',

    'setup'          : 'SETUP',
    'pitstow'        : 'PITSTOW',
    'pitgap'         : 'PITGAP',
    'piters'         : 'PITERS',
    'pitstint'       : 'PITSTINT',

    'fastlap'        : 'FASTLAP',
    'degradation'    : 'DEGRADATION',

    'slipstream'     : 'SLIPSTREAM',
    'position'       : 'POSITION',

    'corner'         : 'CORNER',
    'apex'           : 'APEX',
    'garage'         : 'GARAGE',
    'ready'          : 'READY',
    'grid'           : 'GRID',
    'endgrid'        : 'ENDGRID',
    'stop'           : 'STOP',
    'also'           : 'ALSO',
    'marshall'       : 'MARSHALL',

    'pitlane'        : 'NEUTRO',
    'backmarker'     : 'UNDERCUT',

    'lap_note'       : 'LAP_NOTE',
    'safety_in'      : 'SAFETY_IN',
    'safety_out'     : 'SAFETY_OUT',
}

tokens = list(set(reserved.values())) + [
    'ID',
    'INT_LITERAL',
    'FLOAT_LITERAL',
    'STRING_LITERAL',
    'CHAR_LITERAL',
]


def t_COMMENT_BLOCK(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')


def t_COMMENT_LINE(t):
    r'\#\..*'
    pass  


def t_FLOAT_LITERAL(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t


def t_INT_LITERAL(t):
    r'\d+'
    t.value = int(t.value)
    return t


def t_INITIAL_transmission(t):
    r'transmission'
    t.lexer.string_start = t.lexpos
    t.lexer.string_content = []
    t.lexer.begin('transmission')


def t_transmission_end(t):
    r'transmission'
    t.type  = 'STRING_LITERAL'
    t.value = ' '.join(t.lexer.string_content).strip()
    t.lexer.begin('INITIAL')
    return t


def t_transmission_WORD(t):
    r'[^\ \t\n]+'
    t.lexer.string_content.append(t.value)


def t_transmission_SPACE(t):
    r'[ \t]+'
    t.lexer.string_content.append(' ')


def t_transmission_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


def t_transmission_error(t):
    t.lexer.skip(1)


def t_INITIAL_signal(t):
    r'signal'
    t.lexer.char_content = []
    t.lexer.begin('signal')


def t_signal_end(t):
    r'signal'
    t.type  = 'CHAR_LITERAL'
    t.value = ''.join(t.lexer.char_content).strip()
    t.lexer.begin('INITIAL')
    return t


def t_signal_CONTENT(t):
    r'[^\ \t\n]+'
    t.lexer.char_content.append(t.value)


def t_signal_SPACE(t):
    r'[ \t]+'
    pass


def t_signal_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


def t_signal_error(t):
    t.lexer.skip(1)


def t_LAP_NOTE(t):
    r'lap_note[^\n]*'
    pass  


def t_SAFETY_BLOCK(t):
    r'safety_in[\s\S]*?safety_out'
    t.lexer.lineno += t.value.count('\n')


def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'ID')
    return t


def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


t_ignore = ' \t\r'
t_transmission_ignore = ' '
t_signal_ignore = ' '


error_list = []

def t_error(t):
    col = find_column(t.lexer.lexdata, t)

    error_list.append({
        'type'    : 'Léxico',
        'char'    : t.value[0],
        'line'    : t.lineno,
        'column'  : col,
        'message' : f"Carácter no reconocido '{t.value[0]}'"
    })

    t.lexer.skip(1)


def find_column(input_text, token):
    line_start = input_text.rfind('\n', 0, token.lexpos) + 1
    return (token.lexpos - line_start) + 1


def read_file(filepath):
    if not os.path.exists(filepath):
        print(f"[ERROR] Archivo no encontrado: {filepath}")
        sys.exit(1)
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


lexer = lex.lex()


def analyze(source_code):
    global error_list
    error_list = []
    token_list = []

    lex_instance = lexer.clone()
    lex_instance.lineno = 1
    lex_instance.input(source_code)

    while True:
        tok = lex_instance.token()
        if not tok:
            break

        col = find_column(source_code, tok)
        token_list.append({
            'token'   : tok.type,
            'lexeme'  : str(tok.value),
            'line'    : tok.lineno,
            'column'  : col,
        })


    local_errors = list(error_list)
    error_list   = []

    if local_errors:
        return [], local_errors
    return token_list, local_errors


if __name__ == '__main__':

    if len(sys.argv) > 1:
        source = read_file(sys.argv[1])
        print(f"[PitCode Lexer] Analizando: {sys.argv[1]}\n")
    else:
        source = """
lap x setup 10 @ 20 stop
        """
        print("[PitCode Lexer] Ejecutando código de prueba interno\n")

    tokens_found, errors_found = analyze(source)

    print("=" * 58)
    print(f"  {'TOKEN':<28} {'LEXEMA':<15} {'LÍN':>4} {'COL':>4}")
    print("=" * 58)
    for t in tokens_found:
        print(f"  {t['token']:<28} {str(t['lexeme']):<15} {t['line']:>4} {t['column']:>4}")

    print("=" * 58)
    if errors_found:
        print(f"\n  ⚠  ERRORES LÉXICOS ({len(errors_found)} encontrado(s)):")
        for e in errors_found:
            print(f"  → Línea {e['line']}, Col {e['column']}: {e['message']}")
    else:
        print(f"\n  ✓  Análisis léxico completado sin errores.")
        print(f"  ✓  {len(tokens_found)} tokens encontrados.")