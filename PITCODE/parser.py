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
    ('left',  'EITHER_TYRE'),                      # ||
    ('left',  'BOTH_TYRES'),                       # &&
    ('left',  'DEAD_HEAT', 'OUTLAP'),              # == !=
    ('left',  'UNDERCUT', 'OVERCUT'),              # < >
    ('left',  'TOW', 'GAP'),                       # + -
    ('left',  'ERS', 'STINT', 'FUEL_DELTA'),       # * / %
    ('right', 'REVERSE_GRID'),                     # !
    ('right', 'UMINUS'),                           # negativo unario -x
)

# ═══════════════════════════════════════════════════════════
#  UNIDAD DE TRADUCCIÓN
#  Un programa PitCode puede tener funciones antes y/o
#  después del bloque principal race_start { }
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
#  race_start { ... }
# ═══════════════════════════════════════════════════════════

def p_main_program_with_body(p):
    '''main_program : RACE_START LBRACE block_item_list RBRACE'''
    p[0] = ('race_start', p[3])

def p_main_program_empty(p):
    '''main_program : RACE_START LBRACE RBRACE'''
    p[0] = ('race_start', [])

# ═══════════════════════════════════════════════════════════
#  DEFINICIÓN DE FUNCIONES
#  strategy <tipo> nombre ( params ) { bloque }
#  strategy neutro nombre ( params ) { bloque }
# ═══════════════════════════════════════════════════════════

def p_function_def_with_params(p):
    '''function_definition : STRATEGY type_specifier ID LPAREN parameter_list RPAREN compound_statement'''
    p[0] = ('func_def', p[2], p[3], p[5], p[7], p.lineno(3), p.lexpos(3))

def p_function_def_no_params(p):
    '''function_definition : STRATEGY type_specifier ID LPAREN RPAREN compound_statement'''
    p[0] = ('func_def', p[2], p[3], [], p[6], p.lineno(3), p.lexpos(3))

def p_function_def_void_with_params(p):
    '''function_definition : STRATEGY NEUTRO ID LPAREN parameter_list RPAREN compound_statement'''
    p[0] = ('func_def', 'neutro', p[3], p[5], p[7], p.lineno(3), p.lexpos(3))

def p_function_def_void_no_params(p):
    '''function_definition : STRATEGY NEUTRO ID LPAREN RPAREN compound_statement'''
    p[0] = ('func_def', 'neutro', p[3], [], p[6], p.lineno(3), p.lexpos(3))

# ─────────────────────────────────────────────
#  PARÁMETROS
# ─────────────────────────────────────────────

def p_parameter_list_single(p):
    '''parameter_list : parameter_declaration'''
    p[0] = [p[1]]

def p_parameter_list_multiple(p):
    '''parameter_list : parameter_list COMMA parameter_declaration'''
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
    '''compound_statement : LBRACE block_item_list RBRACE'''
    p[0] = ('block', p[2])

def p_compound_statement_empty(p):
    '''compound_statement : LBRACE RBRACE'''
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
#  lap x = 5;
#  split y;
#  vsc lap PI = 3.14;   (constante)
# ═══════════════════════════════════════════════════════════

def p_declaration_with_init(p):
    '''declaration : type_specifier ID ASSIGN expression SEMICOLON'''
    p[0] = ('declare', p[1], p[2], p[4], p.lineno(2), p.lexpos(2))

def p_declaration_no_init(p):
    '''declaration : type_specifier ID SEMICOLON'''
    p[0] = ('declare', p[1], p[2], None, p.lineno(2), p.lexpos(2))

def p_declaration_const(p):
    '''declaration : VSC type_specifier ID ASSIGN expression SEMICOLON'''
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
    '''expression_statement : expression SEMICOLON'''
    p[0] = ('expr_stmt', p[1])

def p_expression_statement_empty(p):
    '''expression_statement : SEMICOLON'''
    p[0] = ('expr_stmt', None)

# ═══════════════════════════════════════════════════════════
#  SELECCIÓN: strategy_check / stay_out / gap_check
# ═══════════════════════════════════════════════════════════

def p_if_only(p):
    '''selection_statement : STRATEGY_CHECK LPAREN expression RPAREN compound_statement'''
    p[0] = ('if', p[3], p[5], None)

def p_if_else(p):
    '''selection_statement : STRATEGY_CHECK LPAREN expression RPAREN compound_statement STAY_OUT compound_statement'''
    p[0] = ('if_else', p[3], p[5], p[7])

def p_if_else_if(p):
    '''selection_statement : STRATEGY_CHECK LPAREN expression RPAREN compound_statement STAY_OUT selection_statement'''
    p[0] = ('if_else', p[3], p[5], p[7])

def p_switch(p):
    '''selection_statement : GAP_CHECK LPAREN expression RPAREN LBRACE case_list RBRACE'''
    p[0] = ('switch', p[3], p[6])

def p_case_list_single(p):
    '''case_list : case_item'''
    p[0] = [p[1]]

def p_case_list_multiple(p):
    '''case_list : case_list case_item'''
    p[0] = p[1] + [p[2]]

def p_case_item_sector(p):
    '''case_item : SECTOR expression COLON block_item_list'''
    p[0] = ('case', p[2], p[4])

def p_case_item_no_data(p):
    '''case_item : NO_DATA COLON block_item_list'''
    p[0] = ('default', p[3])

# ═══════════════════════════════════════════════════════════
#  ITERACIÓN: push / box...push / formation_lap
# ═══════════════════════════════════════════════════════════

def p_while(p):
    '''iteration_statement : PUSH LPAREN expression RPAREN compound_statement'''
    p[0] = ('while', p[3], p[5])

def p_do_while(p):
    '''iteration_statement : BOX compound_statement PUSH LPAREN expression RPAREN SEMICOLON'''
    p[0] = ('do_while', p[2], p[5])

def p_for_full(p):
    '''iteration_statement : FORMATION_LAP LPAREN for_init expression SEMICOLON expression RPAREN compound_statement'''
    p[0] = ('for', p[3], p[4], p[6], p[8])

def p_for_no_update(p):
    '''iteration_statement : FORMATION_LAP LPAREN for_init expression SEMICOLON RPAREN compound_statement'''
    p[0] = ('for', p[3], p[4], None, p[7])

def p_for_empty(p):
    '''iteration_statement : FORMATION_LAP LPAREN SEMICOLON SEMICOLON RPAREN compound_statement'''
    p[0] = ('for', None, None, None, p[6])

def p_for_init_declare(p):
    '''for_init : type_specifier ID ASSIGN expression SEMICOLON'''
    p[0] = ('declare', p[1], p[2], p[4], p.lineno(2), p.lexpos(2))

def p_for_init_expr(p):
    '''for_init : expression SEMICOLON'''
    p[0] = ('expr_stmt', p[1])

def p_for_init_empty(p):
    '''for_init : SEMICOLON'''
    p[0] = None

# ═══════════════════════════════════════════════════════════
#  SALTOS: podio / box_box / drs
# ═══════════════════════════════════════════════════════════

def p_return_value(p):
    '''jump_statement : PODIO expression SEMICOLON'''
    p[0] = ('return', p[2])

def p_return_void(p):
    '''jump_statement : PODIO SEMICOLON'''
    p[0] = ('return', None)

def p_break(p):
    '''jump_statement : BOX_BOX SEMICOLON'''
    p[0] = ('break',)

def p_continue(p):
    '''jump_statement : DRS SEMICOLON'''
    p[0] = ('continue',)

# ═══════════════════════════════════════════════════════════
#  ENTRADA / SALIDA: broadcast / telemetry
# ═══════════════════════════════════════════════════════════

def p_broadcast(p):
    '''io_statement : BROADCAST LPAREN expression RPAREN SEMICOLON'''
    p[0] = ('broadcast', p[3])

def p_telemetry(p):
    '''io_statement : TELEMETRY LPAREN ID RPAREN SEMICOLON'''
    p[0] = ('telemetry', p[3])

# ═══════════════════════════════════════════════════════════
#  FIN DE PROGRAMA: checkered_flag;
# ═══════════════════════════════════════════════════════════

def p_end_statement(p):
    '''end_statement : CHECKERED_FLAG SEMICOLON'''
    p[0] = ('end_program',)

# ═══════════════════════════════════════════════════════════
#  EXPRESIONES
# ═══════════════════════════════════════════════════════════

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
                  | expression BOTH_TYRES expression
                  | expression EITHER_TYRE expression'''
    p[0] = ('binop', p[2], p[1], p[3])

def p_expr_uminus(p):
    '''expression : GAP expression %prec UMINUS'''
    p[0] = ('uminus', p[2])

def p_expr_not(p):
    '''expression : REVERSE_GRID expression'''
    p[0] = ('not', p[2])

def p_expr_group(p):
    '''expression : LPAREN expression RPAREN'''
    p[0] = p[2]

def p_expr_assign(p):
    '''expression : ID ASSIGN expression'''
    p[0] = ('assign', p[1], p[3])

def p_expr_call_with_args(p):
    '''expression : ID LPAREN argument_list RPAREN'''
    p[0] = ('call', p[1], p[3])

def p_expr_call_no_args(p):
    '''expression : ID LPAREN RPAREN'''
    p[0] = ('call', p[1], [])

def p_argument_list_single(p):
    '''argument_list : expression'''
    p[0] = [p[1]]

def p_argument_list_multiple(p):
    '''argument_list : argument_list COMMA expression'''
    p[0] = p[1] + [p[3]]

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
        parser.errok()  # Recuperación: continuar después del error
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
    """
    Analiza sintácticamente el código fuente PitCode.
    Retorna:
        ast          : árbol sintáctico abstracto
        syntax_errors: lista de errores sintácticos
    """
    global syntax_errors
    syntax_errors = []

    lex_instance = lexer.clone()
    lex_instance.lineno = 1

    ast = parser.parse(source_code, lexer=lex_instance)
    return ast, syntax_errors

# ─────────────────────────────────────────────
#  EJECUCIÓN DIRECTA
#  Uso: python parser.py [archivo.pitcode]
# ─────────────────────────────────────────────

if __name__ == '__main__':

    if len(sys.argv) > 1:
        source = read_file(sys.argv[1])
        print(f"[PitCode Parser] Analizando: {sys.argv[1]}\n")
    else:
        source = """
#. Programa de prueba completo

strategy lap calcular_gap(lap a, lap b) {
    lap diferencia = a Gap b;
    podio diferencia;
}

strategy neutro mostrar_info(radio msg) {
    broadcast(msg);
}

race_start {
    lap vueltas = 5;
    split tiempo = 0.0;
    radio piloto = "Max Verstappen";
    yellow_flag activo = true;
    vsc lap MAX_VUELTAS = 70;

    formation_lap (lap i = 0; i UNDERCUT vueltas; i = i Tow 1) {
        tiempo = tiempo Tow 71.3;
    }

    strategy_check (tiempo UNDERCUT 350.0) {
        broadcast("Tiempo excelente, modo push");
    } stay_out {
        broadcast("Conservar neumaticos");
    }

    push (activo DEAD_HEAT true) {
        lap fuel = 80;
        strategy_check (fuel UNDERCUT 20) {
            activo = false;
            box_box;
        } stay_out {
            fuel = fuel Gap 5;
        }
    }

    gap_check (vueltas) {
        sector 1: broadcast("Sector 1");
        sector 2: broadcast("Sector 2");
        no_data: broadcast("Sin datos");
    }

    lap resultado = calcular_gap(120, 115);
    mostrar_info("Carrera finalizada");
    checkered_flag;
}
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
