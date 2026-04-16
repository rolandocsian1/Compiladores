# ============================================================
#   PitCode - Analizador Semántico
#   Compiladores 2026 - Fase II
# ============================================================

class SemanticAnalyzer:
    """
    Recorre el AST (tuplas) y verifica:
    - Variables no declaradas
    - Variables duplicadas en el mismo ámbito
    - Tipos incompatibles en asignaciones y operaciones
    - Funciones no declaradas
    - Número de argumentos en llamadas a funciones
    - break/continue fuera de ciclos
    - Variables declaradas pero no usadas (advertencia, NO error)
    """

    TYPE_MAP = {
        'lap':         'entero',
        'split':       'decimal',
        'pitboard':    'caracter',
        'yellow_flag': 'booleano',
        'radio':       'cadena',
    }

    ARITHMETIC_OPS = {'Tow', 'Gap', 'ERS', 'Stint', 'Fuel_Delta',
                      'pitstow', 'pitgap', 'piters', 'pitstint'}

    COMPARISON_OPS = {'DEAD_HEAT', 'Outlap', 'UNDERCUT', 'OVERCUT',
                      'undereq', 'overeq', 'BOTH_TYRES', 'EITHER_TYRE',
                      'REVERSE_GRID', 'safety', 'overtake', 'reverse'}

    def __init__(self):
        self.errors = []       # Errores reales (bloquean compilación)
        self.warnings = []     # Advertencias (NO bloquean)
        self.scopes = [{}]
        self.scope_names = ['global']
        self.functions = {}
        self.loop_depth = 0
        self.current_function = None
        self.vars_declared = 0
        self.vars_used = 0
        self.funcs_declared = 0
        self.funcs_called = 0
        self._source_code = ''

    def _lexpos_to_col(self, lexpos):
        """Convierte una posición absoluta (lexpos) a número de columna."""
        if not self._source_code or not lexpos:
            return 0
        line_start = self._source_code.rfind('\n', 0, lexpos) + 1
        return (lexpos - line_start) + 1

    def analyze(self, ast, source_code=''):
        """Ejecuta el análisis semántico completo."""
        self.errors.clear()
        self.warnings.clear()
        self.scopes = [{}]
        self.scope_names = ['global']
        self.functions = {}
        self.loop_depth = 0
        self.current_function = None
        self.vars_declared = 0
        self.vars_used = 0
        self.funcs_declared = 0
        self.funcs_called = 0
        self._source_code = source_code

        if ast is None:
            return self.errors

        self._collect_functions(ast)
        self._visit(ast)
        self._check_unused()

        return self.errors

    def get_errors(self):
        """Retorna solo errores reales (bloquean compilación)."""
        result = []
        for e in self.errors:
            result.append({
                'type': 'Semántico',
                'line': e['line'],
                'column': e['column'],
                'message': e['message']
            })
        return result

    def get_warnings(self):
        """Retorna solo advertencias (NO bloquean)."""
        result = []
        for w in self.warnings:
            result.append({
                'type': 'Advertencia',
                'line': w['line'],
                'column': w['column'],
                'message': w['message']
            })
        return result

    def get_all_for_report(self):
        """Retorna errores + advertencias para el reporte HTML."""
        return self.get_errors() + self.get_warnings()

    # ─────────────────────────────────────────
    #  RECOLECCIÓN DE FUNCIONES (primer pase)
    # ─────────────────────────────────────────

    def _collect_functions(self, ast):
        if not isinstance(ast, tuple):
            return
        if ast[0] == 'program':
            for f in ast[1]:
                self._register_function(f)
            for f in ast[3]:
                self._register_function(f)

    def _register_function(self, node):
        if not isinstance(node, tuple) or node[0] != 'func_def':
            return
        ret_type = node[1]
        name = node[2]
        params = node[3]
        line   = node[5] if len(node) > 5 else 0
        lexpos = node[6] if len(node) > 6 else 0
        col    = self._lexpos_to_col(lexpos)

        if name in self.functions:
            self._add_error(f"Función '{name}' ya fue declarada", line, col)
        else:
            self.functions[name] = {
                'return_type': ret_type,
                'params': [(p[1], p[2]) for p in params],
                'line': line,
                'called': False,
                'has_return': False
            }
            self.funcs_declared += 1

    # ─────────────────────────────────────────
    #  VISITOR PRINCIPAL
    # ─────────────────────────────────────────

    def _visit(self, node):
        if node is None or not isinstance(node, tuple):
            return None
        kind = node[0]

        visitor = {
            'program':         self._visit_program,
            'func_def':        self._visit_func_def,
            'race_start':      self._visit_race_start,
            'block':           self._visit_block,
            'declare':         self._visit_declare,
            'declare_const':   self._visit_declare_const,
            'assign':          self._visit_assign,
            'compound_assign': self._visit_compound_assign,
            'increment':       self._visit_increment,
            'decrement':       self._visit_decrement,
            'if':              self._visit_if,
            'if_else':         self._visit_if_else,
            'while':           self._visit_while,
            'do_while':        self._visit_do_while,
            'for':             self._visit_for,
            'switch':          self._visit_switch,
            'return':          self._visit_return,
            'break':           self._visit_break,
            'continue':        self._visit_continue,
            'broadcast':       self._visit_broadcast,
            'telemetry':       self._visit_telemetry,
            'expr_stmt':       self._visit_expr_stmt,
            'end_program':     lambda n: None,
            'error_node':      lambda n: None,
            'binop':           self._visit_binop,
            'uminus':          self._visit_uminus,
            'not':             self._visit_not,
            'call':            self._visit_call,
            'id':              self._visit_id,
            'int':             lambda n: 'entero',
            'float':           lambda n: 'decimal',
            'string':          lambda n: 'cadena',
            'char':            lambda n: 'caracter',
            'bool':            lambda n: 'booleano',
            'null':            lambda n: 'nulo',
            'deref':           self._visit_deref,
            'address':         self._visit_address,
        }.get(kind)

        if visitor:
            return visitor(node)
        return None

    # ─────────────────────────────────────────
    #  VISITANTES POR TIPO DE NODO
    # ─────────────────────────────────────────

    def _visit_program(self, node):
        for f in node[1]:
            self._visit(f)
        self._visit(node[2])
        for f in node[3]:
            self._visit(f)

    def _visit_func_def(self, node):
        name = node[2]
        params = node[3]
        body = node[4]

        old_fn = self.current_function
        self.current_function = name
        self._enter_scope(name)

        for p in params:
            ptype, pname = p[1], p[2]
            pline = p[3] if len(p) > 3 else 0
            self._declare_var(pname, ptype, pline, 0)

        self._visit(body)
        self._exit_scope()
        self.current_function = old_fn

    def _visit_race_start(self, node):
        self._enter_scope('race_start')
        for item in node[1]:
            self._visit(item)
        self._exit_scope()

    def _visit_block(self, node):
        for item in node[1]:
            self._visit(item)

    def _visit_declare(self, node):
        dtype, name, expr = node[1], node[2], node[3]
        line   = node[4] if len(node) > 4 else 0
        lexpos = node[5] if len(node) > 5 else 0
        col    = self._lexpos_to_col(lexpos)

        self._declare_var(name, dtype, line, col)
        self.vars_declared += 1

        if expr:
            expr_type = self._visit(expr)
            internal_type = self.TYPE_MAP.get(dtype, dtype)
            if expr_type and not self._types_compatible(internal_type, expr_type):
                self._add_error(
                    f"No se puede asignar '{expr_type}' a variable '{name}' de tipo '{internal_type}'",
                    line, col
                )

    def _visit_declare_const(self, node):
        dtype, name, expr = node[1], node[2], node[3]
        line   = node[4] if len(node) > 4 else 0
        lexpos = node[5] if len(node) > 5 else 0
        col    = self._lexpos_to_col(lexpos)
        self._declare_var(name, dtype, line, col, const=True)
        self.vars_declared += 1
        if expr:
            self._visit(expr)

    def _visit_assign(self, node):
        name, expr = node[1], node[2]
        line = node[3]
        lexpos = node[4] 
        col = self._lexpos_to_col(lexpos)
        var  = self._lookup_var(name)
        if not var:
            self._add_error(f"Variable '{name}' no declarada", line, col)
            return
        
        if var.get('const'):
            self._add_error(f"No se puede modificar la constante '{name}'", line, col)
            return
        var['used'] = True
        self.vars_used += 1
        expr_type = self._visit(expr)
        internal_type = self.TYPE_MAP.get(var['type'], var['type'])
        if expr_type and not self._types_compatible(internal_type, expr_type):
            self._add_error(
                f"No se puede asignar '{expr_type}' a '{name}' de tipo '{internal_type}'",
                line, col
            )

    def _visit_compound_assign(self, node):
        op, name, expr = node[1], node[2], node[3]
        line = node[4] if len(node) > 4 else 0
        var  = self._lookup_var(name)
        if not var:
            self._add_error(f"Variable '{name}' no declarada", line, 0)
            return
        var['used'] = True
        self.vars_used += 1
        self._visit(expr)

    def _visit_increment(self, node):
        name = node[1]
        line = node[2] if len(node) > 2 else 0
        var  = self._lookup_var(name)
        if not var:
            self._add_error(f"Variable '{name}' no declarada", line, 0)
            return
        var['used'] = True
        col = var.get('column', 0)
        internal_type = self.TYPE_MAP.get(var['type'], var['type'])
        if internal_type not in ('entero', 'decimal'):
            self._add_error(f"No se puede incrementar '{name}' de tipo '{internal_type}'", line, col)

    def _visit_decrement(self, node):
        name = node[1]
        line = node[2] if len(node) > 2 else 0
        var  = self._lookup_var(name)
        if not var:
            self._add_error(f"Variable '{name}' no declarada", line, 0)
            return
        var['used'] = True
        col = var.get('column', 0)
        internal_type = self.TYPE_MAP.get(var['type'], var['type'])
        if internal_type not in ('entero', 'decimal'):
            self._add_error(f"No se puede decrementar '{name}' de tipo '{internal_type}'", line, col)

    def _visit_if(self, node):
        self._visit(node[1])
        self._enter_scope('if')
        self._visit(node[2])
        self._exit_scope()

    def _visit_if_else(self, node):
        self._visit(node[1])
        self._enter_scope('if')
        self._visit(node[2])
        self._exit_scope()
        self._enter_scope('else')
        if node[3]:
            self._visit(node[3])
        self._exit_scope()

    def _visit_while(self, node):
        self.loop_depth += 1
        self._visit(node[1])
        self._enter_scope('while')
        self._visit(node[2])
        self._exit_scope()
        self.loop_depth -= 1

    def _visit_do_while(self, node):
        self.loop_depth += 1
        self._enter_scope('do_while')
        self._visit(node[1])
        self._exit_scope()
        self._visit(node[2])
        self.loop_depth -= 1

    def _visit_for(self, node):
        self.loop_depth += 1
        self._enter_scope('for')
        if node[1]: self._visit(node[1])
        if node[2]: self._visit(node[2])
        if node[3]: self._visit(node[3])
        self._visit(node[4])
        self._exit_scope()
        self.loop_depth -= 1

    def _visit_switch(self, node):
        self._visit(node[1])
        for case in node[2]:
            self._visit_case(case)

    def _visit_case(self, node):
        if node[0] == 'case':
            self._visit(node[1])
            for stmt in node[2]:
                self._visit(stmt)
        elif node[0] == 'default':
            for stmt in node[1]:
                self._visit(stmt)

    def _visit_return(self, node):
        if node[1]:
            self._visit(node[1])
        if self.current_function and self.current_function in self.functions:
            self.functions[self.current_function]['has_return'] = True

    def _visit_break(self, node):
        line = node[1] 
        lexpos = node[2]
        col = self._lexpos_to_col(lexpos)
        if self.loop_depth == 0:
            self._add_error("'box_box' (break) usado fuera de un ciclo", line, col)

    def _visit_continue(self, node):
        line = node[1] 
        lexpos = node[2]
        col = self._lexpos_to_col(lexpos)
        if self.loop_depth == 0:
            self._add_error("'drs' (continue) usado fuera de un ciclo", line, col)

    def _visit_broadcast(self, node):
        self._visit(node[1])

    def _visit_telemetry(self, node):
        name = node[1]
        line = node[2] if len(node) > 2 else 0
        var  = self._lookup_var(name)
        if not var:
            self._add_error(f"Variable '{name}' no declarada en telemetry", line, 0)
        else:
            var['used'] = True

    def _visit_expr_stmt(self, node):
        if node[1]:
            self._visit(node[1])

    def _visit_binop(self, node):
        op = node[1]
        left_type = self._visit(node[2])
        right_type = self._visit(node[3])
        line = node[4] 
        lexpos = node[5] 
        col = self._lexpos_to_col(lexpos)

        if left_type and right_type:
            if op in self.ARITHMETIC_OPS:
                if left_type not in ('entero', 'decimal') or right_type not in ('entero', 'decimal'):
                    self._add_error(
                        f"Operación aritmética '{op}' no válida entre '{left_type}' y '{right_type}'",
                        line, col
                    )
                return 'decimal' if 'decimal' in (left_type, right_type) else 'entero'
            elif op in self.COMPARISON_OPS:
                return 'booleano'

        return left_type or right_type

    def _visit_uminus(self, node):
        t = self._visit(node[1])
        line = node[2] if len(node) > 2 else 0
        if t and t not in ('entero', 'decimal'):
            self._add_error(f"Negación no válida para tipo '{t}'", line, 0)
        return t

    def _visit_not(self, node):
        self._visit(node[1])
        return 'booleano'

    def _visit_call(self, node):
        name = node[1]
        args = node[2]
        line = node[3] if len(node) > 3 else 0

        if name not in self.functions:
            self._add_error(f"Función '{name}' no declarada", line, 0)
            return None

        func = self.functions[name]
        func['called'] = True
        self.funcs_called += 1
        col = self._lexpos_to_col(func.get('lexpos', 0))

        expected = len(func['params'])
        got = len(args)
        if expected != got:
            self._add_error(
                f"Función '{name}' espera {expected} argumento(s), recibió {got}",
                line, col
            )

        for arg in args:
            self._visit(arg)

        return self.TYPE_MAP.get(func['return_type'], func['return_type'])

    def _visit_id(self, node):
        print("DEBUG ID NODE:", node)
        name = node[1]
        line = node[2] 
        lexpos = node[3] if len(node) > 3 else 0
        col = self._lexpos_to_col(lexpos)
        var  = self._lookup_var(name)
        if not var:
            self._add_error(f"Variable '{name}' no declarada", line, col)
            return None
        var['used'] = True
        self.vars_used += 1
        return self.TYPE_MAP.get(var['type'], var['type'])

    def _visit_deref(self, node):
        return self._visit(node[1])

    def _visit_address(self, node):
        return self._visit(node[1])

    # ─────────────────────────────────────────
    #  MANEJO DE ÁMBITOS
    # ─────────────────────────────────────────

    def _enter_scope(self, name):
        self.scopes.append({})
        self.scope_names.append(name)

    def _exit_scope(self):
        if len(self.scopes) > 1:
            leaving = self.scopes[-1]
            scope_name = self.scope_names[-1]
            for vname, vinfo in leaving.items():
                if not vinfo.get('used'):
                    # Advertencia, NO error
                    self.warnings.append({
                        'message': f"Variable '{vname}' declarada pero no usada en ámbito '{scope_name}'",
                        'line': vinfo.get('line', 0),
                        'column': 0
                    })
            self.scopes.pop()
            self.scope_names.pop()

    def _declare_var(self, name, dtype, line, col, const=False):
        current = self.scopes[-1]
        if name in current:
            self._add_error(f"Variable '{name}' ya declarada en este ámbito", line, col)
            return
        current[name] = {
            'type': dtype,
            'line': line,
            'column': col,
            'used': False,
            'const': const
        }

    def _lookup_var(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    # ─────────────────────────────────────────
    #  COMPATIBILIDAD DE TIPOS
    # ─────────────────────────────────────────

    def _types_compatible(self, t1, t2):
        if t1 == t2:
            return True
        numeric = {'entero', 'decimal'}
        return t1 in numeric and t2 in numeric

    # ─────────────────────────────────────────
    #  REGISTRO DE ERRORES
    # ─────────────────────────────────────────

    def _add_error(self, msg, line, col):
        self.errors.append({'message': msg, 'line': line, 'column': col})

    def _check_unused(self):
        for fname, finfo in self.functions.items():
            if not finfo['called'] and fname != 'race_start':
                self.warnings.append({
                    'message': f"Función '{fname}' declarada pero nunca llamada",
                    'line': finfo['line'],
                    'column': 0
                })