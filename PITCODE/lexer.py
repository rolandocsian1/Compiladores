# ============================================================
#   PitCode - Analizador Léxico 
#   Compiladores 2026 - Fase I
#   Lenguaje: PitCode 
# ============================================================

import ply.lex as lex
import sys
import os

# ─────────────────────────────────────────────
#  PALABRAS RESERVADAS
# ─────────────────────────────────────────────
reserved = {
    # Tipos de datos
    'lap'            : 'LAP',
    'split'          : 'SPLIT',
    'pitboard'       : 'PITBOARD',
    'yellow_flag'    : 'YELLOW_FLAG',
    'radio'          : 'RADIO',

    # Estructuras de control
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
    'pitwall'        : 'PITWALL',          # switch

    # Funciones y retorno
    'strategy'       : 'STRATEGY',
    'podio'          : 'PODIO',
    'neutro'         : 'NEUTRO',
    'race_start'     : 'RACE_START',

    # Entrada / Salida
    'broadcast'      : 'BROADCAST',
    'telemetry'      : 'TELEMETRY',

    # Palabras adicionales reservadas
    'undercut'       : 'UNDERCUT_KW',
    'dnf'            : 'DNF',
    'vsc'            : 'VSC',
    'paddock'        : 'PADDOCK',

    # Banderas especiales
    'red_flag'       : 'RED_FLAG',
    'blue_flag'      : 'BLUE_FLAG',
    'black_flag'     : 'BLACK_FLAG',
    'checkered_flag' : 'CHECKERED_FLAG',

    # Booleanos
    'true'           : 'TRUE',
    'false'          : 'FALSE',

    # ── Operadores aritméticos (palabras) ──
    'Tow'            : 'TOW',              # +
    'Gap'            : 'GAP',              # -
    'ERS'            : 'ERS',              # *
    'Stint'          : 'STINT',            # /
    'Fuel_Delta'     : 'FUEL_DELTA',       # %

    # ── Operadores de comparación (palabras) ──
    'DEAD_HEAT'      : 'DEAD_HEAT',        # ==
    'Outlap'         : 'OUTLAP',           # >
    'UNDERCUT'       : 'UNDERCUT',         # <
    'OVERCUT'        : 'OVERCUT',          # !=  / >
    'undereq'        : 'UNDEREQ',          # <=
    'overeq'         : 'OVEREQ',           # >=

    # ── Operadores lógicos (palabras) ──
    'BOTH_TYRES'     : 'BOTH_TYRES',       # && (alias legacy)
    'EITHER_TYRE'    : 'EITHER_TYRE',      # || (alias legacy)
    'REVERSE_GRID'   : 'REVERSE_GRID',     # !  (alias legacy)
    'safety'         : 'SAFETY',           # &&
    'overtake'       : 'OVERTAKE',         # ||
    'reverse'        : 'REVERSE',          # !

    # ── Operadores de asignación (palabras) ──
    'setup'          : 'SETUP',            # =
    'pitstow'        : 'PITSTOW',         # +=
    'pitgap'         : 'PITGAP',          # -=
    'piters'         : 'PITERS',          # *=
    'pitstint'       : 'PITSTINT',        # /=

    # ── Operadores de incremento/decremento (palabras) ──
    'fastlap'        : 'FASTLAP',         # ++
    'degradation'    : 'DEGRADATION',     # --

    # ── Operadores de puntero (palabras) ──
    'slipstream'     : 'SLIPSTREAM',       # * (puntero)
    'position'       : 'POSITION',         # & (dirección)

    # ── Delimitadores (palabras) ──
    'corner'         : 'CORNER',           # (
    'apex'           : 'APEX',             # )
    'garage'         : 'GARAGE',           # {
    'ready'          : 'READY',            # }
    'grid'           : 'GRID',             # [
    'endgrid'        : 'ENDGRID',          # ]
    'stop'           : 'STOP',             # ;
    'also'           : 'ALSO',             # ,
    'then'           : 'THEN',             # :
}

# ─────────────────────────────────────────────
#  LISTA DE TOKENS
# ─────────────────────────────────────────────
tokens = list(set(reserved.values())) + [
    # Identificadores y literales
    'ID',
    'INT_LITERAL',
    'FLOAT_LITERAL',
    'STRING_LITERAL',
    'CHAR_LITERAL',

    # Asignación simple (símbolo =)
    'ASSIGN',

    # Delimitadores (símbolos)
    'SEMICOLON',    # ;
    'LBRACE',       # {
    'RBRACE',       # }
    'LPAREN',       # (
    'RPAREN',       # )
    'COMMA',        # ,
    'LBRACKET',     # [
    'RBRACKET',     # ]
    'COLON',        # :
]

# ─────────────────────────────────────────────
#  REGLAS COMPLEJAS (funciones)
#  IMPORTANTE: PLY prioriza funciones sobre
#  strings, y dentro de funciones, el orden
#  de definición importa. Las más específicas
#  deben ir primero.
# ─────────────────────────────────────────────

def t_COMMENT_BLOCK(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')
    # Comentarios de bloque ignorados

def t_COMMENT_LINE(t):
    r'\#\..*'
    pass  # Comentarios de línea ignorados

def t_FLOAT_LITERAL(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t

def t_INT_LITERAL(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_STRING_LITERAL(t):
    r'"([^"\\\n]|\\.)*"'
    t.value = t.value[1:-1]  # quitar comillas dobles
    return t

def t_CHAR_LITERAL(t):
    r"'([^'\\\n]|\\.)*'"
    t.value = t.value[1:-1]  # quitar comillas simples
    return t

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    # Verificar si es palabra reservada (case-sensitive)
    t.type = reserved.get(t.value, 'ID')
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# ─────────────────────────────────────────────
#  REGLAS SIMPLES (solo símbolos)
#  Los operadores son PALABRAS reservadas
#  reconocidas en t_ID via el diccionario reserved.
#  Aquí solo van los símbolos literales.
# ─────────────────────────────────────────────

# Asignación simple (símbolo)
t_ASSIGN        = r'='

# Delimitadores (símbolos)
t_SEMICOLON     = r';'
t_LBRACE        = r'\{'
t_RBRACE        = r'\}'
t_LPAREN        = r'\('
t_RPAREN        = r'\)'
t_COMMA         = r','
t_LBRACKET      = r'\['
t_RBRACKET      = r'\]'
t_COLON         = r':'

# Ignorar espacios, tabs y retornos de carro
t_ignore = ' \t\r'

# ─────────────────────────────────────────────
#  MANEJO DE ERRORES LÉXICOS (recuperable)
# ─────────────────────────────────────────────
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
    t.lexer.skip(1)  # Recuperación: saltar carácter y continuar

# ─────────────────────────────────────────────
#  UTILIDADES
# ─────────────────────────────────────────────

def find_column(input_text, token):
    """Calcula la columna exacta de un token dentro de su línea."""
    line_start = input_text.rfind('\n', 0, token.lexpos) + 1
    return (token.lexpos - line_start) + 1

def read_file(filepath):
    """Lee un archivo fuente .pitcode y retorna su contenido."""
    if not os.path.exists(filepath):
        print(f"[ERROR] Archivo no encontrado: {filepath}")
        sys.exit(1)
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

# ─────────────────────────────────────────────
#  CONSTRUIR LEXER
# ─────────────────────────────────────────────
lexer = lex.lex()

# ─────────────────────────────────────────────
#  FUNCIÓN PRINCIPAL: analizar código fuente
# ─────────────────────────────────────────────

def analyze(source_code):
    """
    Analiza léxicamente el código fuente de PitCode.
    Retorna:
        token_list : lista de dicts {token, lexema, línea, columna}
                     (vacía si se encontraron errores léxicos)
        error_list : lista de errores léxicos encontrados
    """
    global error_list
    error_list = []
    token_list = []

    # Clonar lexer para evitar estado compartido entre llamadas
    lex_instance = lexer.clone()
    lex_instance.lineno = 1
    lex_instance.input(source_code)

    for tok in lex_instance:
        col = find_column(source_code, tok)
        token_list.append({
            'token'   : tok.type,
            'lexeme'  : str(tok.value),
            'line'    : tok.lineno,
            'column'  : col,
        })

    # ── Si hay errores léxicos, NO reportar tokens ──
    if error_list:
        return [], error_list

    return token_list, error_list

# ─────────────────────────────────────────────
#  EJECUCIÓN DIRECTA
#  Uso: python lexer.py [archivo.pitcode]
# ─────────────────────────────────────────────

if __name__ == '__main__':

    if len(sys.argv) > 1:
        source = read_file(sys.argv[1])
        print(f"[PitCode Lexer] Analizando: {sys.argv[1]}\n")
    else:
        source = """
#. Programa de prueba PitCode con nuevos operadores
/* Bloque de comentario:
   Prueba completa del lexer */

strategy lap calcular_gap corner lap a also lap b apex garage
    lap diferencia setup a Gap b stop
    podio diferencia stop
ready

race_start garage
    lap vueltas setup 5 stop
    split tiempo setup 1.23 stop
    radio piloto setup "Max Verstappen" stop
    yellow_flag activo setup true stop
    pitboard letra setup 'A' stop

    formation_lap corner lap i setup 0 stop i UNDERCUT vueltas stop i fastlap apex garage
        tiempo pitstow 71.3 stop
    ready

    strategy_check corner tiempo UNDERCUT 350.0 apex garage
        broadcast corner "Tiempo excelente" apex stop
    ready stay_out garage
        broadcast corner "Conservar neumaticos" apex stop
    ready

    push corner activo DEAD_HEAT true apex garage
        lap fuel setup 80 stop
        strategy_check corner fuel undereq 20 apex garage
            activo setup false stop
            box_box stop
        ready stay_out garage
            fuel pitgap 5 stop
        ready
    ready

    lap resultado setup calcular_gap corner 120 also 115 apex stop
    broadcast corner resultado apex stop
    checkered_flag stop
ready
        """
        print("[PitCode Lexer] Ejecutando código de prueba interno\n")

    tokens_found, errors_found = analyze(source)

    # ── Imprimir tokens ──
    print("=" * 58)
    print(f"  {'TOKEN':<28} {'LEXEMA':<15} {'LÍN':>4} {'COL':>4}")
    print("=" * 58)
    for t in tokens_found:
        print(f"  {t['token']:<28} {str(t['lexeme']):<15} {t['line']:>4} {t['column']:>4}")

    # ── Resumen y errores ──
    print("=" * 58)
    if errors_found:
        print(f"\n  ⚠  ERRORES LÉXICOS ({len(errors_found)} encontrado(s)):")
        for e in errors_found:
            print(f"  → Línea {e['line']}, Col {e['column']}: {e['message']}")
    else:
        print(f"\n  ✓  Análisis léxico completado sin errores.")
        print(f"  ✓  {len(tokens_found)} tokens encontrados.")
