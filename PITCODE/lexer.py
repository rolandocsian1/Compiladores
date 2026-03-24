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
    'apex'           : 'APEX',
    'paddock'        : 'PADDOCK',

    # Banderas especiales
    'red_flag'       : 'RED_FLAG',
    'blue_flag'      : 'BLUE_FLAG',
    'black_flag'     : 'BLACK_FLAG',
    'checkered_flag' : 'CHECKERED_FLAG',

    # Booleanos
    'true'           : 'TRUE',
    'false'          : 'FALSE',

    # Operadores aritméticos con nombre (palabras)
    'Tow'            : 'TOW',
    'Gap'            : 'GAP',
    'ERS'            : 'ERS',
    'Stint'          : 'STINT',
    'Fuel_Delta'     : 'FUEL_DELTA',

    # Operadores de comparación con nombre (palabras)
    'DEAD_HEAT'      : 'DEAD_HEAT',
    'Outlap'         : 'OUTLAP',
    'UNDERCUT'       : 'UNDERCUT',
    'OVERCUT'        : 'OVERCUT',

    # Operadores lógicos con nombre (palabras)
    'BOTH_TYRES'     : 'BOTH_TYRES',
    'EITHER_TYRE'    : 'EITHER_TYRE',
    'REVERSE_GRID'   : 'REVERSE_GRID',
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
#  (Tow, Gap, ERS, DEAD_HEAT, etc.) reconocidas
#  en t_ID via el diccionario reserved.
# ─────────────────────────────────────────────

# Asignación simple (símbolo)
t_ASSIGN        = r'='

# Delimitadores
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
#. Programa de prueba PitCode
/* Bloque de comentario:
   Calcula tiempo promedio */

race_start {
    lap vueltas = 5;
    split tiempo = 1.23;
    radio piloto = "Lewis Hamilton";
    yellow_flag activo = true;
    pitboard letra = 'A';

    strategy_check (vueltas OVERCUT 3) {
        broadcast("Modo push activado");
    } stay_out {
        broadcast("Stay out");
    }

    formation_lap (lap i = 0; i UNDERCUT vueltas; i = i Tow 1) {
        tiempo = tiempo Tow 0.5;
    }

    push (activo DEAD_HEAT true) {
        vueltas = vueltas Gap 1;
    }

    checkered_flag;
}

strategy lap calcular(lap a, lap b) {
    podio a Tow b;
}
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
