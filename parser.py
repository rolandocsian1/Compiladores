#   PitCode - Analizador Sintáctico
#   Compiladores 2026 - Fase I
#   Basado en ANSI C Yacc Grammar 


import ply.yacc as yacc
import sys
from lexer import tokens, lexer, find_column, read_file


#  LISTA DE ERRORES SINTÁCTICOS

syntax_errors = []
_source_code  = ''   
_error_set    = set()


#  PRECEDENCIA 

precedence = (
    ('left',  'EITHER_TYRE', 'OVERTAKE'),
    ('left',  'BOTH_TYRES', 'SAFETY'),
    ('left',  'DEAD_HEAT', 'OUTLAP'),
    ('left',  'UNDERCUT', 'OVERCUT', 'UNDEREQ', 'OVEREQ'),
    ('left',  'TOW', 'GAP'),
    ('left',  'ERS', 'STINT', 'FUEL_DELTA'),
    ('right', 'REVERSE_GRID', 'REVERSE'),
    ('right', 'UMINUS'),
    ('right', 'SLIPSTREAM', 'POSITION'),
)


#  TRADUCCIÓN

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


#  LISTA FUNCIONES

def p_function_list_single(p):
    '''function_list : function_definition'''
    p[0] = [p[1]]

def p_function_list_multiple(p):
    '''function_list : function_list function_definition'''
    p[0] = p[1] + [p[2]]


#  PROG PRINCIPAL

def p_main_program_with_body(p):
    '''main_program : RACE_START GARAGE block_item_list READY'''
    p[0] = ('race_start', p[3])

def p_main_program_empty(p):
    '''main_program : RACE_START GARAGE READY'''
    p[0] = ('race_start', [])


#  DEFINICIÓN DE FUNCIONES

def p_function_def_with_params(p):
    '''function_definition : STRATEGY type_specifier ID CORNER parameter_list APEX compound_statement'''
    p[0] = ('func_def', p[2], p[3], p[5], p[7], p.lineno(3), p.lexpos(3))

def p_function_def_no_params(p):
    '''function_definition : STRATEGY type_specifier ID CORNER APEX compound_statement'''
    p[0] = ('func_def', p[2], p[3], [], p[6], p.lineno(3), p.lexpos(3))

def p_function_def_void_with_params(p):
    '''function_definition : STRATEGY NEUTRO ID CORNER parameter_list APEX compound_statement'''
    p[0] = ('func_def', 'neutro', p[3], p[5], p[7], p.lineno(3), p.lexpos(3))

def p_function_def_void_no_params(p):
    '''function_definition : STRATEGY NEUTRO ID CORNER APEX compound_statement'''
    p[0] = ('func_def', 'neutro', p[3], [], p[6], p.lineno(3), p.lexpos(3))


#  PARÁMETROS

def p_parameter_list_single(p):
    '''parameter_list : parameter_declaration'''
    p[0] = [p[1]]

def p_parameter_list_multiple(p):
    '''parameter_list : parameter_list ALSO parameter_declaration'''
    p[0] = p[1] + [p[3]]

def p_parameter_declaration(p):
    '''parameter_declaration : type_specifier ID'''
    p[0] = ('param', p[1], p[2], p.lineno(2), p.lexpos(2))


#  TIPOS DATOS

def p_type_specifier(p):
    '''type_specifier : LAP
                      | SPLIT
                      | PITBOARD
                      | YELLOW_FLAG
                      | RADIO'''
    p[0] = p[1]


#  INSTRUCCIONES

def p_compound_statement_with_body(p):
    '''compound_statement : GARAGE block_item_list READY'''
    p[0] = ('block', p[2])

def p_compound_statement_empty(p):
    '''compound_statement : GARAGE READY'''
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


def p_declaration_with_init(p):
    '''declaration : type_specifier ID SETUP expression STOP'''
    p[0] = ('declare', p[1], p[2], p[4], p.lineno(2), p.lexpos(2))

def p_declaration_no_init(p):
    '''declaration : type_specifier ID STOP'''
    p[0] = ('declare', p[1], p[2], None, p.lineno(2), p.lexpos(2))

def p_declaration_const(p):
    '''declaration : VSC type_specifier ID SETUP expression STOP'''
    p[0] = ('declare_const', p[2], p[3], p[5], p.lineno(3), p.lexpos(3))


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
    '''expression_statement : expression STOP'''
    p[0] = ('expr_stmt', p[1])

def p_expression_statement_empty(p):
    '''expression_statement : STOP'''
    p[0] = ('expr_stmt', None)


# ═══════════════════════════════════════════════════════════
#  REGLAS DE RECUPERACIÓN DE ERRORES
# ═══════════════════════════════════════════════════════════

def p_block_item_error(p):
    '''block_item : error STOP'''
    p[0] = ('error_node',)

def p_compound_error(p):
    '''compound_statement : GARAGE error READY'''
    p[0] = ('error_node',)

def p_function_def_error(p):
    '''function_definition : STRATEGY error READY'''
    p[0] = ('error_node',)

def p_main_program_error(p):
    '''main_program : RACE_START GARAGE error READY'''
    p[0] = ('race_start', [])


def p_if_only(p):
    '''selection_statement : STRATEGY_CHECK CORNER expression APEX compound_statement'''
    p[0] = ('if', p[3], p[5], None)

def p_if_else(p):
    '''selection_statement : STRATEGY_CHECK CORNER expression APEX compound_statement STAY_OUT compound_statement'''
    p[0] = ('if_else', p[3], p[5], p[7])

def p_if_else_if(p):
    '''selection_statement : STRATEGY_CHECK CORNER expression APEX compound_statement STAY_OUT selection_statement'''
    p[0] = ('if_else', p[3], p[5], p[7])

def p_switch(p):
    '''selection_statement : GAP_CHECK CORNER expression APEX GARAGE case_list READY
                           | PITWALL CORNER expression APEX GARAGE case_list READY'''
    p[0] = ('switch', p[3], p[6])

def p_case_list_single(p):
    '''case_list : case_item'''
    p[0] = [p[1]]

def p_case_list_multiple(p):
    '''case_list : case_list case_item'''
    p[0] = p[1] + [p[2]]

def p_case_item_sector(p):
    '''case_item : SECTOR expression MARSHALL block_item_list'''
    p[0] = ('case', p[2], p[4])

def p_case_item_no_data(p):
    '''case_item : NO_DATA MARSHALL block_item_list'''
    p[0] = ('default', p[3])


def p_while(p):
    '''iteration_statement : PUSH CORNER expression APEX compound_statement'''
    p[0] = ('while', p[3], p[5])

def p_do_while(p):
    '''iteration_statement : BOX compound_statement PUSH CORNER expression APEX STOP'''
    p[0] = ('do_while', p[2], p[5])

def p_for_full(p):
    '''iteration_statement : FORMATION_LAP CORNER for_init expression for_semi expression APEX compound_statement'''
    p[0] = ('for', p[3], p[4], p[6], p[8])

def p_for_no_update(p):
    '''iteration_statement : FORMATION_LAP CORNER for_init expression for_semi APEX compound_statement'''
    p[0] = ('for', p[3], p[4], None, p[7])

def p_for_empty(p):
    '''iteration_statement : FORMATION_LAP CORNER for_semi for_semi APEX compound_statement'''
    p[0] = ('for', None, None, None, p[6])

def p_for_semi(p):
    '''for_semi : STOP'''
    p[0] = p[1]

def p_for_init_declare(p):
    '''for_init : type_specifier ID SETUP expression for_semi'''
    p[0] = ('declare', p[1], p[2], p[4], p.lineno(2), p.lexpos(2))

def p_for_init_expr(p):
    '''for_init : expression for_semi'''
    p[0] = ('expr_stmt', p[1])

def p_for_init_empty(p):
    '''for_init : for_semi'''
    p[0] = None


def p_return_value(p):
    '''jump_statement : PODIO expression STOP'''
    p[0] = ('return', p[2])

def p_return_void(p):
    '''jump_statement : PODIO STOP'''
    p[0] = ('return', None)

def p_break(p):
    '''jump_statement : BOX_BOX STOP'''
    p[0] = ('break',)

def p_continue(p):
    '''jump_statement : DRS STOP'''
    p[0] = ('continue',)


def p_broadcast(p):
    '''io_statement : BROADCAST CORNER expression APEX STOP'''
    p[0] = ('broadcast', p[3])

def p_telemetry(p):
    '''io_statement : TELEMETRY CORNER ID APEX STOP'''
    p[0] = ('telemetry', p[3])


def p_end_statement(p):
    '''end_statement : CHECKERED_FLAG STOP'''
    p[0] = ('end_program',)


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

def p_expr_uminus(p):
    '''expression : GAP expression %prec UMINUS'''
    p[0] = ('uminus', p[2])

def p_expr_not(p):
    '''expression : REVERSE_GRID expression
                  | REVERSE expression'''
    p[0] = ('not', p[2])

def p_expr_group(p):
    '''expression : CORNER expression APEX'''
    p[0] = p[2]

def p_expr_assign(p):
    '''expression : ID SETUP expression'''
    p[0] = ('assign', p[1], p[3])

def p_expr_compound_assign(p):
    '''expression : ID PITSTOW expression
                  | ID PITGAP expression
                  | ID PITERS expression
                  | ID PITSTINT expression'''
    p[0] = ('compound_assign', p[2], p[1], p[3])

def p_expr_increment(p):
    '''expression : ID FASTLAP'''
    p[0] = ('increment', p[1])

def p_expr_decrement(p):
    '''expression : ID DEGRADATION'''
    p[0] = ('decrement', p[1])

def p_expr_deref(p):
    '''expression : SLIPSTREAM expression %prec SLIPSTREAM'''
    p[0] = ('deref', p[2])

def p_expr_address(p):
    '''expression : POSITION expression %prec POSITION'''
    p[0] = ('address', p[2])

def p_expr_call_with_args(p):
    '''expression : ID CORNER argument_list APEX'''
    p[0] = ('call', p[1], p[3])

def p_expr_call_no_args(p):
    '''expression : ID CORNER APEX'''
    p[0] = ('call', p[1], [])

def p_argument_list_single(p):
    '''argument_list : expression'''
    p[0] = [p[1]]

def p_argument_list_multiple(p):
    '''argument_list : argument_list ALSO expression'''
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
    '''expression : GREEN_LIGHT'''
    p[0] = ('bool', True)

def p_expr_false(p):
    '''expression : RED_LIGHT'''
    p[0] = ('bool', False)

def p_expr_dnf(p):
    '''expression : DNF'''
    p[0] = ('null',)


# ═══════════════════════════════════════════════════════════
#  ERRORES SINTÁCTICOS
# ═══════════════════════════════════════════════════════════

def p_error(p):
    global syntax_errors, _source_code, _error_set
    if p:
        error_key = (p.lineno, p.lexpos, p.type)
        if error_key not in _error_set:
            _error_set.add(error_key)
            col = find_column(p.lexer.lexdata, p)
            syntax_errors.append({
                'type'    : 'Sintáctico',
                'token'   : p.type,
                'value'   : str(p.value),
                'line'    : p.lineno,
                'column'  : col,
                'message' : f"Token inesperado '{p.value}' (tipo: {p.type})"
            })

        parser.token()
        parser.errok()

    else:
        last_line = _source_code.count('\n') + 1 if _source_code else 0
        last_col  = len(_source_code.split('\n')[-1]) if _source_code else 0
        syntax_errors.append({
            'type'    : 'Sintáctico',
            'token'   : 'EOF',
            'value'   : '',
            'line'    : last_line,
            'column'  : last_col,
            'message' : 'Fin de archivo inesperado — ¿falta cerrar un bloque con ready?'
        })


parser = yacc.yacc()


def parse(source_code):
    global syntax_errors, _source_code, _error_set
    syntax_errors = []
    _source_code  = source_code
    _error_set    = set()

    lex_instance = lexer.clone()
    lex_instance.lineno = 1

    ast = parser.parse(source_code, lexer=lex_instance)
    return ast, syntax_errors