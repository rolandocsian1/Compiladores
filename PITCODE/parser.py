# ============================================================
#   PitCode - Analizador Sintáctico
#   Compiladores 2026 - Fase I
#   Basado en ANSI C Yacc Grammar 
# ============================================================

import ply.yacc as yacc
import sys
from lexer import tokens, lexer, find_column, read_file

# ─────────────────────────────────────────────
#  LISTA DE ERRORES SINTÁCTICOS
# ─────────────────────────────────────────────
syntax_errors = []

# ─────────────────────────────────────────────
#  PRECEDENCIA DE OPERADORES
#  De menor a mayor precedencia (como ANSI C)
# ─────────────────────────────────────────────
precedence = (
    ('left',  'EITHER_TYRE', 'OVERTAKE'),                  # ||
    ('left',  'BOTH_TYRES', 'SAFETY'),                     # &&
    ('left',  'DEAD_HEAT', 'OUTLAP'),                      # == !=
    ('left',  'UNDERCUT', 'OVERCUT', 'UNDEREQ', 'OVEREQ'), # < > <= >=
    ('left',  'TOW', 'GAP'),                               # + -
    ('left',  'ERS', 'STINT', 'FUEL_DELTA'),               # * / %
    ('right', 'REVERSE_GRID', 'REVERSE'),                  # !
    ('right', 'UMINUS'),                                   # negativo unario -x
    ('right', 'SLIPSTREAM', 'POSITION'),                   # * (puntero) & (dirección)
)

# ═══════════════════════════════════════════════════════════
#  UNIDAD DE TRADUCCIÓN
# ═══════════════════════════════════════════════════════════

def p_translation_unit_only_main(p):
    '''translation_unit : main_program'''
    p[0] = ('program', [], p[1], [])

def p_translation_unit_funcs_before(p):
    '''translation_unit : function_list main_program'''
    p[0] = ('program', p[1], p[2], [])

def p_translation_unit_funcs_after(p):
    '''translation_unit : main_program function_list'''
    p[0] = ('program', [], p[1], p[2])

def p_translation_unit_funcs_both(p):
    '''translation_unit : function_list main_program function_list'''
    p[0] = ('program', p[1], p[2], p[3])

# ─────────────────────────────────────────────
#  LISTA DE FUNCIONES EXTERNAS
# ─────────────────────────────────────────────

def p_function_list_single(p):
    '''function_list : function_definition'''
    p[0] = [p[1]]

def p_function_list_multiple(p):
    '''function_list : function_list function_definition'''
    p[0] = p[1] + [p[2]]

# ═══════════════════════════════════════════════════════════
#  PROGRAMA PRINCIPAL
#  race_start { ... }  /  race_start garage ... ready
# ═══════════════════════════════════════════════════════════

def p_main_program_with_body(p):
    '''main_program : RACE_START LBRACE block_item_list RBRACE
                    | RACE_START GARAGE block_item_list READY
                    | RACE_START LBRACE block_item_list READY
                    | RACE_START GARAGE block_item_list RBRACE'''
    p[0] = ('race_start', p[3])

def p_main_program_empty(p):
    '''main_program : RACE_START LBRACE RBRACE
                    | RACE_START GARAGE READY
                    | RACE_START LBRACE READY
                    | RACE_START GARAGE RBRACE'''
    p[0] = ('race_start', [])

# ═══════════════════════════════════════════════════════════
#  DEFINICIÓN DE FUNCIONES
# ═══════════════════════════════════════════════════════════

def p_function_def_with_params(p):
    '''function_definition : STRATEGY type_specifier ID LPAREN parameter_list RPAREN compound_statement
                           | STRATEGY type_specifier ID CORNER parameter_list APEX compound_statement
                           | STRATEGY type_specifier ID LPAREN parameter_list APEX compound_statement
                           | STRATEGY type_specifier ID CORNER parameter_list RPAREN compound_statement'''
    p[0] = ('func_def', p[2], p[3], p[5], p[7], p.lineno(3), p.lexpos(3))

def p_function_def_no_params(p):
    '''function_definition : STRATEGY type_specifier ID LPAREN RPAREN compound_statement
                           | STRATEGY type_specifier ID CORNER APEX compound_statement
                           | STRATEGY type_specifier ID LPAREN APEX compound_statement
                           | STRATEGY type_specifier ID CORNER RPAREN compound_statement'''
    p[0] = ('func_def', p[2], p[3], [], p[6], p.lineno(3), p.lexpos(3))

def p_function_def_void_with_params(p):
    '''function_definition : STRATEGY NEUTRO ID LPAREN parameter_list RPAREN compound_statement
                           | STRATEGY NEUTRO ID CORNER parameter_list APEX compound_statement
                           | STRATEGY NEUTRO ID LPAREN parameter_list APEX compound_statement
                           | STRATEGY NEUTRO ID CORNER parameter_list RPAREN compound_statement'''
    p[0] = ('func_def', 'neutro', p[3], p[5], p[7], p.lineno(3), p.lexpos(3))

def p_function_def_void_no_params(p):
    '''function_definition : STRATEGY NEUTRO ID LPAREN RPAREN compound_statement
                           | STRATEGY NEUTRO ID CORNER APEX compound_statement
                           | STRATEGY NEUTRO ID LPAREN APEX compound_statement
                           | STRATEGY NEUTRO ID CORNER RPAREN compound_statement'''
    p[0] = ('func_def', 'neutro', p[3], [], p[6], p.lineno(3), p.lexpos(3))

# ─────────────────────────────────────────────
#  PARÁMETROS
# ─────────────────────────────────────────────

def p_parameter_list_single(p):
    '''parameter_list : parameter_declaration'''
    p[0] = [p[1]]

def p_parameter_list_multiple(p):
    '''parameter_list : parameter_list COMMA parameter_declaration
                      | parameter_list ALSO parameter_declaration'''
    p[0] = p[1] + [p[3]]

def p_parameter_declaration(p):
    '''parameter_declaration : type_specifier ID'''
    p[0] = ('param', p[1], p[2], p.lineno(2), p.lexpos(2))

# ═══════════════════════════════════════════════════════════
#  TIPOS DE DATOS
# ═══════════════════════════════════════════════════════════

def p_type_specifier(p):
    '''type_specifier : LAP
                      | SPLIT
                      | PITBOARD
                      | YELLOW_FLAG
                      | RADIO'''
    p[0] = p[1]

# ═══════════════════════════════════════════════════════════
#  BLOQUES Y LISTAS DE INSTRUCCIONES
# ═══════════════════════════════════════════════════════════

def p_compound_statement_with_body(p):
    '''compound_statement : LBRACE block_item_list RBRACE
                          | GARAGE block_item_list READY
                          | LBRACE block_item_list READY
                          | GARAGE block_item_list RBRACE'''
    p[0] = ('block', p[2])

def p_compound_statement_empty(p):
    '''compound_statement : LBRACE RBRACE
                          | GARAGE READY
                          | LBRACE READY
                          | GARAGE RBRACE'''
    p[0] = ('block', [])

def p_block_item_list_single(p):
    '''block_item_list : block_item'''
    p[0] = [p[1]]

def p_block_item_list_multiple(p):
    '''block_item_list : block_item_list block_item'''
    p[0] = p[1] + [p[2]]

def p_block_item(p):
    '''block_item : declaration
                  | statement'''
    p[0] = p[1]

# ═══════════════════════════════════════════════════════════
#  DECLARACIONES DE VARIABLES
# ═══════════════════════════════════════════════════════════

def p_declaration_with_init(p):
    '''declaration : type_specifier ID ASSIGN expression SEMICOLON
                   | type_specifier ID ASSIGN expression STOP
                   | type_specifier ID SETUP expression SEMICOLON
                   | type_specifier ID SETUP expression STOP'''
    p[0] = ('declare', p[1], p[2], p[4], p.lineno(2), p.lexpos(2))

def p_declaration_no_init(p):
    '''declaration : type_specifier ID SEMICOLON
                   | type_specifier ID STOP'''
    p[0] = ('declare', p[1], p[2], None, p.lineno(2), p.lexpos(2))

def p_declaration_const(p):
    '''declaration : VSC type_specifier ID ASSIGN expression SEMICOLON
                   | VSC type_specifier ID ASSIGN expression STOP
                   | VSC type_specifier ID SETUP expression SEMICOLON
                   | VSC type_specifier ID SETUP expression STOP'''
    p[0] = ('declare_const', p[2], p[3], p[5], p.lineno(3), p.lexpos(3))

# ═══════════════════════════════════════════════════════════
#  INSTRUCCIONES (statements)
# ═══════════════════════════════════════════════════════════

def p_statement(p):
    '''statement : expression_statement
                 | compound_statement
                 | selection_statement
                 | iteration_statement
                 | jump_statement
                 | io_statement
                 | end_statement'''
    p[0] = p[1]

def p_expression_statement_expr(p):
    '''expression_statement : expression SEMICOLON
                            | expression STOP'''
    p[0] = ('expr_stmt', p[1])

def p_expression_statement_empty(p):
    '''expression_statement : SEMICOLON
                            | STOP'''
    p[0] = ('expr_stmt', None)

# ═══════════════════════════════════════════════════════════
#  SELECCIÓN: strategy_check / stay_out / gap_check / pitwall
# ═══════════════════════════════════════════════════════════

def p_if_only(p):
    '''selection_statement : STRATEGY_CHECK LPAREN expression RPAREN compound_statement
                           | STRATEGY_CHECK CORNER expression APEX compound_statement
                           | STRATEGY_CHECK LPAREN expression APEX compound_statement
                           | STRATEGY_CHECK CORNER expression RPAREN compound_statement'''
    p[0] = ('if', p[3], p[5], None)

def p_if_else(p):
    '''selection_statement : STRATEGY_CHECK LPAREN expression RPAREN compound_statement STAY_OUT compound_statement
                           | STRATEGY_CHECK CORNER expression APEX compound_statement STAY_OUT compound_statement
                           | STRATEGY_CHECK LPAREN expression APEX compound_statement STAY_OUT compound_statement
                           | STRATEGY_CHECK CORNER expression RPAREN compound_statement STAY_OUT compound_statement'''
    p[0] = ('if_else', p[3], p[5], p[7])

def p_if_else_if(p):
    '''selection_statement : STRATEGY_CHECK LPAREN expression RPAREN compound_statement STAY_OUT selection_statement
                           | STRATEGY_CHECK CORNER expression APEX compound_statement STAY_OUT selection_statement
                           | STRATEGY_CHECK LPAREN expression APEX compound_statement STAY_OUT selection_statement
                           | STRATEGY_CHECK CORNER expression RPAREN compound_statement STAY_OUT selection_statement'''
    p[0] = ('if_else', p[3], p[5], p[7])

def p_switch(p):
    '''selection_statement : GAP_CHECK LPAREN expression RPAREN LBRACE case_list RBRACE
                           | GAP_CHECK CORNER expression APEX GARAGE case_list READY
                           | GAP_CHECK LPAREN expression RPAREN GARAGE case_list READY
                           | GAP_CHECK CORNER expression APEX LBRACE case_list RBRACE
                           | PITWALL LPAREN expression RPAREN LBRACE case_list RBRACE
                           | PITWALL CORNER expression APEX GARAGE case_list READY
                           | PITWALL LPAREN expression RPAREN GARAGE case_list READY
                           | PITWALL CORNER expression APEX LBRACE case_list RBRACE'''
    p[0] = ('switch', p[3], p[6])

def p_case_list_single(p):
    '''case_list : case_item'''
    p[0] = [p[1]]

def p_case_list_multiple(p):
    '''case_list : case_list case_item'''
    p[0] = p[1] + [p[2]]

def p_case_item_sector(p):
    '''case_item : SECTOR expression COLON block_item_list
                 | SECTOR expression THEN block_item_list'''
    p[0] = ('case', p[2], p[4])

def p_case_item_no_data(p):
    '''case_item : NO_DATA COLON block_item_list
                 | NO_DATA THEN block_item_list'''
    p[0] = ('default', p[3])

# ═══════════════════════════════════════════════════════════
#  ITERACIÓN: push / box...push / formation_lap
# ═══════════════════════════════════════════════════════════

def p_while(p):
    '''iteration_statement : PUSH LPAREN expression RPAREN compound_statement
                           | PUSH CORNER expression APEX compound_statement
                           | PUSH LPAREN expression APEX compound_statement
                           | PUSH CORNER expression RPAREN compound_statement'''
    p[0] = ('while', p[3], p[5])

def p_do_while(p):
    '''iteration_statement : BOX compound_statement PUSH LPAREN expression RPAREN SEMICOLON
                           | BOX compound_statement PUSH CORNER expression APEX STOP
                           | BOX compound_statement PUSH LPAREN expression RPAREN STOP
                           | BOX compound_statement PUSH CORNER expression APEX SEMICOLON
                           | BOX compound_statement PUSH LPAREN expression APEX SEMICOLON
                           | BOX compound_statement PUSH LPAREN expression APEX STOP
                           | BOX compound_statement PUSH CORNER expression RPAREN SEMICOLON
                           | BOX compound_statement PUSH CORNER expression RPAREN STOP'''
    p[0] = ('do_while', p[2], p[5])

def p_for_full(p):
    '''iteration_statement : FORMATION_LAP LPAREN for_init expression for_semi expression RPAREN compound_statement
                           | FORMATION_LAP CORNER for_init expression for_semi expression APEX compound_statement
                           | FORMATION_LAP LPAREN for_init expression for_semi expression APEX compound_statement
                           | FORMATION_LAP CORNER for_init expression for_semi expression RPAREN compound_statement'''
    p[0] = ('for', p[3], p[4], p[6], p[8])

def p_for_no_update(p):
    '''iteration_statement : FORMATION_LAP LPAREN for_init expression for_semi RPAREN compound_statement
                           | FORMATION_LAP CORNER for_init expression for_semi APEX compound_statement
                           | FORMATION_LAP LPAREN for_init expression for_semi APEX compound_statement
                           | FORMATION_LAP CORNER for_init expression for_semi RPAREN compound_statement'''
    p[0] = ('for', p[3], p[4], None, p[7])

def p_for_empty(p):
    '''iteration_statement : FORMATION_LAP LPAREN for_semi for_semi RPAREN compound_statement
                           | FORMATION_LAP CORNER for_semi for_semi APEX compound_statement
                           | FORMATION_LAP LPAREN for_semi for_semi APEX compound_statement
                           | FORMATION_LAP CORNER for_semi for_semi RPAREN compound_statement'''
    p[0] = ('for', None, None, None, p[6])

def p_for_semi(p):
    '''for_semi : SEMICOLON
               | STOP'''
    p[0] = p[1]

def p_for_init_declare(p):
    '''for_init : type_specifier ID ASSIGN expression for_semi
                | type_specifier ID SETUP expression for_semi'''
    p[0] = ('declare', p[1], p[2], p[4], p.lineno(2), p.lexpos(2))

def p_for_init_expr(p):
    '''for_init : expression for_semi'''
    p[0] = ('expr_stmt', p[1])

def p_for_init_empty(p):
    '''for_init : for_semi'''
    p[0] = None

# ═══════════════════════════════════════════════════════════
#  SALTOS: podio / box_box / drs
# ═══════════════════════════════════════════════════════════

def p_return_value(p):
    '''jump_statement : PODIO expression SEMICOLON
                      | PODIO expression STOP'''
    p[0] = ('return', p[2])

def p_return_void(p):
    '''jump_statement : PODIO SEMICOLON
                      | PODIO STOP'''
    p[0] = ('return', None)

def p_break(p):
    '''jump_statement : BOX_BOX SEMICOLON
                      | BOX_BOX STOP'''
    p[0] = ('break',)

def p_continue(p):
    '''jump_statement : DRS SEMICOLON
                      | DRS STOP'''
    p[0] = ('continue',)

# ═══════════════════════════════════════════════════════════
#  ENTRADA / SALIDA: broadcast / telemetry
# ═══════════════════════════════════════════════════════════

def p_broadcast(p):
    '''io_statement : BROADCAST LPAREN expression RPAREN SEMICOLON
                    | BROADCAST CORNER expression APEX STOP
                    | BROADCAST LPAREN expression RPAREN STOP
                    | BROADCAST CORNER expression APEX SEMICOLON
                    | BROADCAST LPAREN expression APEX SEMICOLON
                    | BROADCAST LPAREN expression APEX STOP
                    | BROADCAST CORNER expression RPAREN SEMICOLON
                    | BROADCAST CORNER expression RPAREN STOP'''
    p[0] = ('broadcast', p[3])

def p_telemetry(p):
    '''io_statement : TELEMETRY LPAREN ID RPAREN SEMICOLON
                    | TELEMETRY CORNER ID APEX STOP
                    | TELEMETRY LPAREN ID RPAREN STOP
                    | TELEMETRY CORNER ID APEX SEMICOLON
                    | TELEMETRY LPAREN ID APEX SEMICOLON
                    | TELEMETRY LPAREN ID APEX STOP
                    | TELEMETRY CORNER ID RPAREN SEMICOLON
                    | TELEMETRY CORNER ID RPAREN STOP'''
    p[0] = ('telemetry', p[3])

# ═══════════════════════════════════════════════════════════
#  FIN DE PROGRAMA: checkered_flag;
# ═══════════════════════════════════════════════════════════

def p_end_statement(p):
    '''end_statement : CHECKERED_FLAG SEMICOLON
                     | CHECKERED_FLAG STOP'''
    p[0] = ('end_program',)

# ═══════════════════════════════════════════════════════════
#  EXPRESIONES
# ═══════════════════════════════════════════════════════════

# ── Operaciones binarias ──
def p_expr_binop(p):
    '''expression : expression TOW expression
                  | expression GAP expression
                  | expression ERS expression
                  | expression STINT expression
                  | expression FUEL_DELTA expression
                  | expression DEAD_HEAT expression
                  | expression OUTLAP expression
                  | expression UNDERCUT expression
                  | expression OVERCUT expression
                  | expression UNDEREQ expression
                  | expression OVEREQ expression
                  | expression BOTH_TYRES expression
                  | expression EITHER_TYRE expression
                  | expression SAFETY expression
                  | expression OVERTAKE expression'''
    p[0] = ('binop', p[2], p[1], p[3])

# ── Negativo unario ──
def p_expr_uminus(p):
    '''expression : GAP expression %prec UMINUS'''
    p[0] = ('uminus', p[2])

# ── NOT lógico ──
def p_expr_not(p):
    '''expression : REVERSE_GRID expression
                  | REVERSE expression'''
    p[0] = ('not', p[2])

# ── Agrupación con paréntesis ──
def p_expr_group(p):
    '''expression : LPAREN expression RPAREN
                  | CORNER expression APEX
                  | LPAREN expression APEX
                  | CORNER expression RPAREN'''
    p[0] = p[2]

# ── Asignación simple ──
def p_expr_assign(p):
    '''expression : ID ASSIGN expression
                  | ID SETUP expression'''
    p[0] = ('assign', p[1], p[3])

# ── Asignaciones compuestas ──
def p_expr_compound_assign(p):
    '''expression : ID PITSTOW expression
                  | ID PITGAP expression
                  | ID PITERS expression
                  | ID PITSTINT expression'''
    p[0] = ('compound_assign', p[2], p[1], p[3])

# ── Incremento / Decremento ──
def p_expr_increment(p):
    '''expression : ID FASTLAP'''
    p[0] = ('increment', p[1])

def p_expr_decrement(p):
    '''expression : ID DEGRADATION'''
    p[0] = ('decrement', p[1])

# ── Operadores de puntero ──
def p_expr_deref(p):
    '''expression : SLIPSTREAM expression %prec SLIPSTREAM'''
    p[0] = ('deref', p[2])

def p_expr_address(p):
    '''expression : POSITION expression %prec POSITION'''
    p[0] = ('address', p[2])

# ── Llamada a función ──
def p_expr_call_with_args(p):
    '''expression : ID LPAREN argument_list RPAREN
                  | ID CORNER argument_list APEX
                  | ID LPAREN argument_list APEX
                  | ID CORNER argument_list RPAREN'''
    p[0] = ('call', p[1], p[3])

def p_expr_call_no_args(p):
    '''expression : ID LPAREN RPAREN
                  | ID CORNER APEX
                  | ID LPAREN APEX
                  | ID CORNER RPAREN'''
    p[0] = ('call', p[1], [])

def p_argument_list_single(p):
    '''argument_list : expression'''
    p[0] = [p[1]]

def p_argument_list_multiple(p):
    '''argument_list : argument_list COMMA expression
                     | argument_list ALSO expression'''
    p[0] = p[1] + [p[3]]

# ── Literales e identificadores ──
def p_expr_id(p):
    '''expression : ID'''
    p[0] = ('id', p[1])

def p_expr_int(p):
    '''expression : INT_LITERAL'''
    p[0] = ('int', p[1])

def p_expr_float(p):
    '''expression : FLOAT_LITERAL'''
    p[0] = ('float', p[1])

def p_expr_string(p):
    '''expression : STRING_LITERAL'''
    p[0] = ('string', p[1])

def p_expr_char(p):
    '''expression : CHAR_LITERAL'''
    p[0] = ('char', p[1])

def p_expr_true(p):
    '''expression : TRUE'''
    p[0] = ('bool', True)

def p_expr_false(p):
    '''expression : FALSE'''
    p[0] = ('bool', False)

def p_expr_dnf(p):
    '''expression : DNF'''
    p[0] = ('null',)

# ═══════════════════════════════════════════════════════════
#  MANEJO DE ERRORES SINTÁCTICOS (recuperable)
# ═══════════════════════════════════════════════════════════

def p_error(p):
    global syntax_errors
    if p:
        col = find_column(p.lexer.lexdata, p)
        syntax_errors.append({
            'type'    : 'Sintáctico',
            'token'   : p.type,
            'value'   : str(p.value),
            'line'    : p.lineno,
            'column'  : col,
            'message' : f"Token inesperado '{p.value}' (tipo: {p.type})"
        })
        parser.errok()
    else:
        syntax_errors.append({
            'type'    : 'Sintáctico',
            'token'   : 'EOF',
            'value'   : '',
            'line'    : 0,
            'column'  : 0,
            'message' : 'Fin de archivo inesperado — ¿falta cerrar un bloque?'
        })

# ─────────────────────────────────────────────
#  CONSTRUIR PARSER
# ─────────────────────────────────────────────
parser = yacc.yacc()

# ─────────────────────────────────────────────
#  FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────

def parse(source_code):
    global syntax_errors
    syntax_errors = []

    lex_instance = lexer.clone()
    lex_instance.lineno = 1

    ast = parser.parse(source_code, lexer=lex_instance)
    return ast, syntax_errors

# ─────────────────────────────────────────────
#  EJECUCIÓN DIRECTA
# ─────────────────────────────────────────────

if __name__ == '__main__':

    if len(sys.argv) > 1:
        source = read_file(sys.argv[1])
        print(f"[PitCode Parser] Analizando: {sys.argv[1]}\n")
    else:
        source = """
#. Programa de prueba completo

strategy lap calcular_gap corner lap a also lap b apex garage
    lap diferencia setup a Gap b stop
    podio diferencia stop
ready

race_start garage
    lap vueltas setup 5 stop
    split tiempo setup 0.0 stop
    radio piloto setup "Max Verstappen" stop
    yellow_flag activo setup true stop

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
        print("[PitCode Parser] Ejecutando código de prueba interno\n")

    ast, errors = parse(source)

    print("=" * 55)
    if errors:
        print(f"  ⚠  ERRORES SINTÁCTICOS ({len(errors)} encontrado(s)):")
        print("=" * 55)
        for e in errors:
            print(f"  → Línea {e['line']}, Col {e['column']}: {e['message']}")
    else:
        print(f"  ✓  Análisis sintáctico completado sin errores.")
        print(f"  ✓  Nodo raíz del AST: {ast[0] if ast else 'None'}")
    print("=" * 55)
