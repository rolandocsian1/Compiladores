# ============================================================
#   PitCode - Código de Tres Direcciones + Traducción a C++
#   Compiladores 2026 - Fase II
#
#   El código de tres direcciones se genera como C++ válido
#   compilable. Los temporales se declaran al inicio de cada
#   función para evitar conflictos con goto.
# ============================================================

import os

# ─────────────────────────────────────────────
#  MAPEO DE OPERADORES PITCODE → SÍMBOLOS C++
# ─────────────────────────────────────────────

OP_MAP = {
    'Tow': '+', 'Gap': '-', 'ERS': '*', 'Stint': '/', 'Fuel_Delta': '%',
    'DEAD_HEAT': '==', 'Outlap': '>', 'UNDERCUT': '<', 'OVERCUT': '!=',
    'undereq': '<=', 'overeq': '>=',
    'BOTH_TYRES': '&&', 'EITHER_TYRE': '||', 'REVERSE_GRID': '!',
    'safety': '&&', 'overtake': '||', 'reverse': '!',
    'pitstow': '+', 'pitgap': '-', 'piters': '*', 'pitstint': '/',
}

TYPE_TO_CPP = {
    'lap': 'int', 'split': 'double', 'pitboard': 'char',
    'yellow_flag': 'bool', 'radio': 'std::string', 'neutro': 'void',
}

BOOL_OPS = {'==', '!=', '<', '>', '<=', '>=', '&&', '||'}
ARITH_OPS = {'+', '-', '*', '/', '%'}


# ─────────────────────────────────────────────
#  GENERADOR DE CÓDIGO DE TRES DIRECCIONES
#  (Genera C++ válido compilable)
# ─────────────────────────────────────────────

class ThreeAddressGenerator:
    def __init__(self):
        self.lines = []
        self.temp_count = 0
        self.label_count = 0
        self.indent = 0
        self.var_types = {}
        self.temp_declarations = []  # temporales usados en la función actual

    def generate(self, ast):
        self.lines = []
        self.temp_count = 0
        self.label_count = 0
        self.indent = 0
        self.var_types = {}
        self.temp_declarations = []

        if ast is None:
            return self.lines

        needs_iostream = self._scan_for(ast, ('broadcast', 'telemetry'))
        needs_string = self._scan_for_type(ast, 'radio')

        if needs_iostream:
            self._emit("#include <iostream>")
        if needs_string:
            self._emit("#include <string>")
        if needs_iostream or needs_string:
            self._emit("")
            self._emit("using namespace std;")
        self._emit("")

        self._gen(ast)
        return self.lines

    def get_code_string(self):
        return "\n".join(self.lines)

    # ─── Helpers ───

    def new_temp(self):
        t = f"t{self.temp_count}"
        self.temp_count += 1
        return t

    def new_label(self):
        lbl = f"L{self.label_count}"
        self.label_count += 1
        return lbl

    def _emit(self, text):
        self.lines.append("    " * self.indent + text)

    def _emit_label(self, lbl):
        self.lines.append(f"{lbl}:;")

    def _register_temp(self, name, cpp_type):
        """Registra un temporal para declararlo al inicio de la función."""
        self.temp_declarations.append((name, cpp_type))
        self.var_types[name] = cpp_type

    # ─── Detección de headers ───

    def _scan_for(self, node, kinds):
        if node is None or not isinstance(node, tuple):
            return False
        if node[0] in kinds:
            return True
        for child in node:
            if isinstance(child, tuple):
                if self._scan_for(child, kinds):
                    return True
            elif isinstance(child, list):
                for item in child:
                    if self._scan_for(item, kinds):
                        return True
        return False

    def _scan_for_type(self, node, tipo):
        if node is None or not isinstance(node, tuple):
            return False
        kind = node[0]
        if kind in ('declare', 'declare_const') and node[1] == tipo:
            return True
        if kind == 'param' and node[1] == tipo:
            return True
        if kind == 'func_def' and node[1] == tipo:
            return True
        for child in node:
            if isinstance(child, tuple):
                if self._scan_for_type(child, tipo):
                    return True
            elif isinstance(child, list):
                for item in child:
                    if self._scan_for_type(item, tipo):
                        return True
        return False

    # ─── Dispatcher ───

    def _gen(self, node):
        if node is None or not isinstance(node, tuple):
            return None
        kind = node[0]
        method = getattr(self, f"_gen_{kind}", None)
        if method:
            return method(node)
        return None

    # ─── Programa ───

    def _gen_program(self, node):
        for f in node[1]:
            self._gen(f)
        self._gen(node[2])
        for f in node[3]:
            self._gen(f)

    def _gen_race_start(self, node):
        self.temp_declarations = []

        # Generar cuerpo en buffer temporal
        body_lines = []
        old_lines = self.lines
        self.lines = body_lines
        self.indent = 1

        for item in node[1]:
            self._gen(item)
        self._emit("return 0;")

        # Restaurar y construir función
        self.lines = old_lines
        self.indent = 0
        self._emit("int main() {")
        self.indent = 1

        for tname, ttype in self.temp_declarations:
            self._emit(f"{ttype} {tname};")

        self.lines.extend(body_lines)
        self.indent = 0
        self._emit("}")

    def _gen_func_def(self, node):
        ret_type = TYPE_TO_CPP.get(node[1], 'void')
        name = node[2]
        params = node[3]
        body = node[4]

        self.temp_declarations = []

        param_parts = []
        for p in params:
            pt = TYPE_TO_CPP.get(p[1], 'auto')
            pn = p[2]
            self.var_types[pn] = pt
            param_parts.append(f"{pt} {pn}")

        # Generar cuerpo en buffer
        body_lines = []
        old_lines = self.lines
        self.lines = body_lines
        self.indent = 1

        self._gen(body)

        # Restaurar y construir función
        self.lines = old_lines
        self.indent = 0
        self._emit(f"{ret_type} {name}({', '.join(param_parts)}) {{")
        self.indent = 1

        for tname, ttype in self.temp_declarations:
            self._emit(f"{ttype} {tname};")

        self.lines.extend(body_lines)
        self.indent = 0
        self._emit("}")
        self._emit("")

    # ─── Bloques ───

    def _gen_block(self, node):
        for item in node[1]:
            self._gen(item)

    # ─── Declaraciones ───

    def _gen_declare(self, node):
        cpp_type = TYPE_TO_CPP.get(node[1], 'auto')
        name = node[2]
        expr = node[3]
        self.var_types[name] = cpp_type

        if expr:
            val = self._gen(expr)
            self._emit(f"{cpp_type} {name} = {val};")
        else:
            self._emit(f"{cpp_type} {name};")

    def _gen_declare_const(self, node):
        cpp_type = TYPE_TO_CPP.get(node[1], 'auto')
        name = node[2]
        expr = node[3]
        self.var_types[name] = cpp_type
        if expr:
            val = self._gen(expr)
            self._emit(f"const {cpp_type} {name} = {val};")

    # ─── Asignaciones ───

    def _gen_assign(self, node):
        name = node[1]
        val = self._gen(node[2])
        self._emit(f"{name} = {val};")

    def _gen_compound_assign(self, node):
        op_word = node[1]
        name = node[2]
        val = self._gen(node[3])
        op = OP_MAP.get(op_word, op_word)
        temp = self.new_temp()
        var_type = self.var_types.get(name, 'int')
        self._register_temp(temp, var_type)
        self._emit(f"{temp} = {name} {op} {val};")
        self._emit(f"{name} = {temp};")

    def _gen_increment(self, node):
        self._emit(f"{node[1]} = {node[1]} + 1;")

    def _gen_decrement(self, node):
        self._emit(f"{node[1]} = {node[1]} - 1;")

    # ─── Condicionales ───

    def _gen_if(self, node):
        cond = self._gen(node[1])
        end_lbl = self.new_label()
        self._emit(f"if (!({cond})) goto {end_lbl};")
        self._gen(node[2])
        self._emit_label(end_lbl)

    def _gen_if_else(self, node):
        cond = self._gen(node[1])
        else_lbl = self.new_label()
        end_lbl = self.new_label()
        self._emit(f"if (!({cond})) goto {else_lbl};")
        self._gen(node[2])
        self._emit(f"goto {end_lbl};")
        self._emit_label(else_lbl)
        if node[3]:
            self._gen(node[3])
        self._emit_label(end_lbl)

    # ─── Ciclos ───

    def _gen_while(self, node):
        start_lbl = self.new_label()
        end_lbl = self.new_label()
        self._emit_label(start_lbl)
        cond = self._gen(node[1])
        self._emit(f"if (!({cond})) goto {end_lbl};")
        self._gen(node[2])
        self._emit(f"goto {start_lbl};")
        self._emit_label(end_lbl)

    def _gen_do_while(self, node):
        start_lbl = self.new_label()
        end_lbl = self.new_label()
        self._emit_label(start_lbl)
        self._gen(node[1])
        cond = self._gen(node[2])
        self._emit(f"if (!({cond})) goto {end_lbl};")
        self._emit(f"goto {start_lbl};")
        self._emit_label(end_lbl)

    def _gen_for(self, node):
        if node[1]:
            self._gen(node[1])
        start_lbl = self.new_label()
        end_lbl = self.new_label()
        self._emit_label(start_lbl)
        if node[2]:
            cond = self._gen(node[2])
            self._emit(f"if (!({cond})) goto {end_lbl};")
        self._gen(node[4])
        if node[3]:
            self._gen(node[3])
        self._emit(f"goto {start_lbl};")
        self._emit_label(end_lbl)

    def _gen_switch(self, node):
        expr = self._gen(node[1])
        end_lbl = self.new_label()
        for case in node[2]:
            if case[0] == 'case':
                case_val = self._gen(case[1])
                next_case = self.new_label()
                temp = self.new_temp()
                self._register_temp(temp, 'bool')
                self._emit(f"{temp} = ({expr} == {case_val});")
                self._emit(f"if (!{temp}) goto {next_case};")
                for stmt in case[2]:
                    self._gen(stmt)
                self._emit(f"goto {end_lbl};")
                self._emit_label(next_case)
            elif case[0] == 'default':
                for stmt in case[1]:
                    self._gen(stmt)
        self._emit_label(end_lbl)

    # ─── Saltos ───

    def _gen_return(self, node):
        if node[1]:
            val = self._gen(node[1])
            self._emit(f"return {val};")
        else:
            self._emit("return;")

    def _gen_break(self, node):
        self._emit("break;")

    def _gen_continue(self, node):
        self._emit("continue;")

    # ─── E/S ───

    def _gen_broadcast(self, node):
        val = self._gen(node[1])
        self._emit(f"cout << {val} << endl;")

    def _gen_telemetry(self, node):
        self._emit(f"cin >> {node[1]};")

    def _gen_end_program(self, node):
        pass

    def _gen_error_node(self, node):
        pass

    def _gen_expr_stmt(self, node):
        if node[1]:
            val = self._gen(node[1])
            if val:
                self._emit(f"{val};")

    # ─── Expresiones ───

    def _gen_binop(self, node):
        op_word = node[1]
        left = self._gen(node[2])
        right = self._gen(node[3])
        op = OP_MAP.get(op_word, op_word)
        temp = self.new_temp()

        if op in BOOL_OPS:
            self._register_temp(temp, 'bool')
        elif op in ARITH_OPS:
            left_type = self.var_types.get(left, 'int')
            right_type = self.var_types.get(right, 'int')
            if left_type == 'double' or right_type == 'double':
                self._register_temp(temp, 'double')
            else:
                self._register_temp(temp, 'int')
        else:
            self._register_temp(temp, 'int')

        self._emit(f"{temp} = {left} {op} {right};")
        return temp

    def _gen_uminus(self, node):
        val = self._gen(node[1])
        temp = self.new_temp()
        val_type = self.var_types.get(val, 'int')
        self._register_temp(temp, val_type)
        self._emit(f"{temp} = -{val};")
        return temp

    def _gen_not(self, node):
        val = self._gen(node[1])
        temp = self.new_temp()
        self._register_temp(temp, 'bool')
        self._emit(f"{temp} = !{val};")
        return temp

    def _gen_call(self, node):
        name = node[1]
        args = node[2]
        arg_strs = []
        for arg in args:
            a = self._gen(arg)
            arg_strs.append(str(a))
        temp = self.new_temp()
        self._register_temp(temp, 'int')
        self._emit(f"{temp} = {name}({', '.join(arg_strs)});")
        return temp

    # ─── Literales ───

    def _gen_id(self, node):
        return node[1]

    def _gen_int(self, node):
        return str(node[1])

    def _gen_float(self, node):
        return str(node[1])

    def _gen_string(self, node):
        return f'"{node[1]}"'

    def _gen_char(self, node):
        return f"'{node[1]}'"

    def _gen_bool(self, node):
        return 'true' if node[1] else 'false'

    def _gen_null(self, node):
        return 'NULL'

    def _gen_deref(self, node):
        val = self._gen(node[1])
        temp = self.new_temp()
        self._register_temp(temp, 'int')
        self._emit(f"{temp} = *{val};")
        return temp

    def _gen_address(self, node):
        val = self._gen(node[1])
        temp = self.new_temp()
        self._register_temp(temp, 'int*')
        self._emit(f"{temp} = &{val};")
        return temp


# ─────────────────────────────────────────────
#  TRADUCTOR A C++ (código limpio/funcional)
# ─────────────────────────────────────────────

class CppTranslator:
    """Traduce el AST de PitCode directamente a código C++ funcional."""

    def __init__(self):
        self.output = []
        self.indent_level = 0

    def translate(self, ast):
        self.output = []
        self.indent_level = 0

        needs_string = self._needs_string(ast)
        needs_iostream = self._needs_iostream(ast)

        if needs_iostream:
            self._line("#include <iostream>")
        if needs_string:
            self._line("#include <string>")
        if needs_iostream or needs_string:
            self._line("")
            self._line("using namespace std;")
            self._line("")

        if ast and ast[0] == 'program':
            for f in ast[1]:
                self._translate_node(f)
                self._line("")
            self._translate_main(ast[2])
            for f in ast[3]:
                self._translate_node(f)
                self._line("")

        return "\n".join(self.output)

    def save_to_file(self, ast, filepath):
        code = self.translate(ast)
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)
        return code

    def _line(self, text):
        self.output.append("    " * self.indent_level + text)

    def _translate_node(self, node):
        if node is None or not isinstance(node, tuple):
            return
        kind = node[0]
        method = getattr(self, f"_tr_{kind}", None)
        if method:
            method(node)

    def _translate_main(self, node):
        if node[0] == 'race_start':
            self._line("int main() {")
            self.indent_level += 1
            for item in node[1]:
                self._translate_node(item)
            self._line("return 0;")
            self.indent_level -= 1
            self._line("}")

    def _tr_func_def(self, node):
        ret_type = TYPE_TO_CPP.get(node[1], 'void')
        name = node[2]
        params = node[3]
        body = node[4]
        param_str = ", ".join(f"{TYPE_TO_CPP.get(p[1], 'auto')} {p[2]}" for p in params)
        self._line(f"{ret_type} {name}({param_str}) {{")
        self.indent_level += 1
        self._translate_node(body)
        self.indent_level -= 1
        self._line("}")

    def _tr_block(self, node):
        for item in node[1]:
            self._translate_node(item)

    def _tr_declare(self, node):
        cpp_type = TYPE_TO_CPP.get(node[1], 'auto')
        name = node[2]
        expr = node[3]
        if expr:
            self._line(f"{cpp_type} {name} = {self._expr(expr)};")
        else:
            self._line(f"{cpp_type} {name};")

    def _tr_declare_const(self, node):
        cpp_type = TYPE_TO_CPP.get(node[1], 'auto')
        val = self._expr(node[3]) if node[3] else ""
        self._line(f"const {cpp_type} {node[2]} = {val};")

    def _tr_assign(self, node):
        self._line(f"{node[1]} = {self._expr(node[2])};")

    def _tr_compound_assign(self, node):
        op = OP_MAP.get(node[1], node[1])
        self._line(f"{node[2]} {op}= {self._expr(node[3])};")

    def _tr_increment(self, node):
        self._line(f"{node[1]}++;")

    def _tr_decrement(self, node):
        self._line(f"{node[1]}--;")

    def _tr_if(self, node):
        self._line(f"if ({self._expr(node[1])}) {{")
        self.indent_level += 1
        self._translate_node(node[2])
        self.indent_level -= 1
        self._line("}")

    def _tr_if_else(self, node):
        self._line(f"if ({self._expr(node[1])}) {{")
        self.indent_level += 1
        self._translate_node(node[2])
        self.indent_level -= 1
        self._line("} else {")
        self.indent_level += 1
        if node[3]:
            self._translate_node(node[3])
        self.indent_level -= 1
        self._line("}")

    def _tr_while(self, node):
        self._line(f"while ({self._expr(node[1])}) {{")
        self.indent_level += 1
        self._translate_node(node[2])
        self.indent_level -= 1
        self._line("}")

    def _tr_do_while(self, node):
        self._line("do {")
        self.indent_level += 1
        self._translate_node(node[1])
        self.indent_level -= 1
        self._line(f"}} while ({self._expr(node[2])});")

    def _tr_for(self, node):
        init = self._for_part(node[1]) if node[1] else ""
        cond = self._expr(node[2]) if node[2] else ""
        upd = self._for_part(node[3]) if node[3] else ""
        self._line(f"for ({init}; {cond}; {upd}) {{")
        self.indent_level += 1
        self._translate_node(node[4])
        self.indent_level -= 1
        self._line("}")

    def _for_part(self, node):
        if not isinstance(node, tuple): return ""
        if node[0] == 'declare':
            cpp_type = TYPE_TO_CPP.get(node[1], 'auto')
            val = self._expr(node[3]) if node[3] else ""
            return f"{cpp_type} {node[2]} = {val}"
        if node[0] == 'assign': return f"{node[1]} = {self._expr(node[2])}"
        if node[0] == 'expr_stmt' and node[1]: return self._expr(node[1])
        if node[0] == 'increment': return f"{node[1]}++"
        if node[0] == 'decrement': return f"{node[1]}--"
        return ""

    def _tr_switch(self, node):
        self._line(f"switch ({self._expr(node[1])}) {{")
        self.indent_level += 1
        for case in node[2]:
            if case[0] == 'case':
                self._line(f"case {self._expr(case[1])}:")
                self.indent_level += 1
                for stmt in case[2]: self._translate_node(stmt)
                self._line("break;")
                self.indent_level -= 1
            elif case[0] == 'default':
                self._line("default:")
                self.indent_level += 1
                for stmt in case[1]: self._translate_node(stmt)
                self._line("break;")
                self.indent_level -= 1
        self.indent_level -= 1
        self._line("}")

    def _tr_return(self, node):
        if node[1]: self._line(f"return {self._expr(node[1])};")
        else: self._line("return;")

    def _tr_break(self, node): self._line("break;")
    def _tr_continue(self, node): self._line("continue;")
    def _tr_broadcast(self, node): self._line(f"cout << {self._expr(node[1])} << endl;")
    def _tr_telemetry(self, node): self._line(f"cin >> {node[1]};")
    def _tr_end_program(self, node): pass
    def _tr_expr_stmt(self, node):
        if node[1]: self._line(f"{self._expr(node[1])};")
    def _tr_error_node(self, node): self._line("// Error en el código fuente")

    # ─── Detección de headers ───

    def _needs_string(self, node):
        if node is None or not isinstance(node, tuple): return False
        kind = node[0]
        if kind in ('declare', 'declare_const') and node[1] == 'radio': return True
        if kind == 'param' and node[1] == 'radio': return True
        if kind == 'func_def' and node[1] == 'radio': return True
        for child in node:
            if isinstance(child, tuple):
                if self._needs_string(child): return True
            elif isinstance(child, list):
                for item in child:
                    if self._needs_string(item): return True
        return False

    def _needs_iostream(self, node):
        if node is None or not isinstance(node, tuple): return False
        if node[0] in ('broadcast', 'telemetry'): return True
        for child in node:
            if isinstance(child, tuple):
                if self._needs_iostream(child): return True
            elif isinstance(child, list):
                for item in child:
                    if self._needs_iostream(item): return True
        return False

    # ─── Expresiones → string C++ ───

    def _expr(self, node):
        if node is None: return ""
        if not isinstance(node, tuple): return str(node)
        kind = node[0]
        if kind == 'int': return str(node[1])
        if kind == 'float': return str(node[1])
        if kind == 'string': return f'"{node[1]}"'
        if kind == 'char': return f"'{node[1]}'"
        if kind == 'bool': return 'true' if node[1] else 'false'
        if kind == 'null': return 'NULL'
        if kind == 'id': return node[1]
        if kind == 'binop':
            op = OP_MAP.get(node[1], node[1])
            return f"({self._expr(node[2])} {op} {self._expr(node[3])})"
        if kind == 'uminus': return f"(-{self._expr(node[1])})"
        if kind == 'not': return f"(!{self._expr(node[1])})"
        if kind == 'call':
            args = ", ".join(self._expr(a) for a in node[2])
            return f"{node[1]}({args})"
        if kind == 'assign': return f"{node[1]} = {self._expr(node[2])}"
        if kind == 'compound_assign':
            op = OP_MAP.get(node[1], node[1])
            return f"{node[2]} {op}= {self._expr(node[3])}"
        if kind == 'increment': return f"{node[1]}++"
        if kind == 'decrement': return f"{node[1]}--"
        if kind == 'deref': return f"(*{self._expr(node[1])})"
        if kind == 'address': return f"(&{self._expr(node[1])})"
        return str(node)