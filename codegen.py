# ============================================================
#   PitCode - Código de Tres Direcciones + Traducción a C++
#   Compiladores 2026 - Fase II
# ============================================================

import os


# ─────────────────────────────────────────────
#  INSTRUCCIÓN DE TRES DIRECCIONES
# ─────────────────────────────────────────────

class TAC:
    """Representa una instrucción de código de tres direcciones."""
    def __init__(self, op, arg1=None, arg2=None, result=None):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result

    def __str__(self):
        if self.op == 'ASSIGN':
            return f"{self.result} = {self.arg1}"
        if self.op in ('+', '-', '*', '/', '%'):
            return f"{self.result} = {self.arg1} {self.op} {self.arg2}"
        if self.op in ('==', '!=', '<', '>', '<=', '>=', '&&', '||'):
            return f"{self.result} = {self.arg1} {self.op} {self.arg2}"
        if self.op == 'NOT':
            return f"{self.result} = !{self.arg1}"
        if self.op == 'UMINUS':
            return f"{self.result} = -{self.arg1}"
        if self.op == 'GOTO':
            return f"goto {self.result}"
        if self.op == 'IF_FALSE':
            return f"if_false {self.arg1} goto {self.result}"
        if self.op == 'LABEL':
            return f"{self.result}:"
        if self.op == 'CALL':
            return f"{self.result} = call {self.arg1}, {self.arg2}"
        if self.op == 'PARAM':
            return f"param {self.arg1}"
        if self.op == 'RETURN':
            return f"return {self.arg1}" if self.arg1 else "return"
        if self.op == 'PRINT':
            return f"print {self.arg1}"
        if self.op == 'READ':
            return f"read {self.result}"
        if self.op == 'FUNC_BEGIN':
            return f"func_begin {self.result}"
        if self.op == 'FUNC_END':
            return f"func_end {self.result}"
        if self.op == 'INC':
            return f"{self.result} = {self.result} + 1"
        if self.op == 'DEC':
            return f"{self.result} = {self.result} - 1"
        if self.op == 'COMPOUND':
            return f"{self.result} = {self.result} {self.arg1} {self.arg2}"
        return f"{self.op} {self.arg1} {self.arg2} {self.result}"


# ─────────────────────────────────────────────
#  MAPEO DE OPERADORES PITCODE → SÍMBOLOS
# ─────────────────────────────────────────────

OP_MAP = {
    # Aritméticos
    'Tow': '+', 'Gap': '-', 'ERS': '*', 'Stint': '/', 'Fuel_Delta': '%',
    # Comparación
    'DEAD_HEAT': '==', 'Outlap': '>', 'UNDERCUT': '<', 'OVERCUT': '!=',
    'undereq': '<=', 'overeq': '>=',
    # Lógicos
    'BOTH_TYRES': '&&', 'EITHER_TYRE': '||', 'REVERSE_GRID': '!',
    'safety': '&&', 'overtake': '||', 'reverse': '!',
    # Asignación compuesta
    'pitstow': '+', 'pitgap': '-', 'piters': '*', 'pitstint': '/',
}

TYPE_TO_CPP = {
    'lap': 'int', 'split': 'double', 'pitboard': 'char',
    'yellow_flag': 'bool', 'radio': 'std::string', 'neutro': 'void',
}


# ─────────────────────────────────────────────
#  GENERADOR DE CÓDIGO DE TRES DIRECCIONES
# ─────────────────────────────────────────────

class ThreeAddressGenerator:
    def __init__(self):
        self.code = []
        self.temp_count = 0
        self.label_count = 0

    def generate(self, ast):
        self.code.clear()
        self.temp_count = 0
        self.label_count = 0
        if ast:
            self._gen(ast)
        return self.code

    def new_temp(self):
        t = f"t{self.temp_count}"
        self.temp_count += 1
        return t

    def new_label(self):
        lbl = f"L{self.label_count}"
        self.label_count += 1
        return lbl

    def _gen(self, node):
        if node is None or not isinstance(node, tuple):
            return None
        kind = node[0]
        method = getattr(self, f"_gen_{kind}", None)
        if method:
            return method(node)
        return None

    def _gen_program(self, node):
        for f in node[1]:
            self._gen(f)
        self._gen(node[2])
        for f in node[3]:
            self._gen(f)

    def _gen_func_def(self, node):
        name = node[2]
        params = node[3]
        body = node[4]
        self.code.append(TAC('FUNC_BEGIN', result=name))
        for p in params:
            self.code.append(TAC('PARAM', p[2]))
        self._gen(body)
        if not self.code or self.code[-1].op != 'RETURN':
            self.code.append(TAC('RETURN'))
        self.code.append(TAC('FUNC_END', result=name))

    def _gen_race_start(self, node):
        self.code.append(TAC('FUNC_BEGIN', result='main'))
        for item in node[1]:
            self._gen(item)
        self.code.append(TAC('RETURN', arg1='0'))
        self.code.append(TAC('FUNC_END', result='main'))

    def _gen_block(self, node):
        for item in node[1]:
            self._gen(item)

    def _gen_declare(self, node):
        name = node[2]
        expr = node[3]
        if expr:
            val = self._gen(expr)
            self.code.append(TAC('ASSIGN', val, None, name))

    def _gen_declare_const(self, node):
        self._gen_declare(('declare', node[1], node[2], node[3]))

    def _gen_assign(self, node):
        name = node[1]
        val = self._gen(node[2])
        self.code.append(TAC('ASSIGN', val, None, name))

    def _gen_compound_assign(self, node):
        op_word = node[1]
        name = node[2]
        val = self._gen(node[3])
        op = OP_MAP.get(op_word, op_word)
        temp = self.new_temp()
        self.code.append(TAC(op, name, val, temp))
        self.code.append(TAC('ASSIGN', temp, None, name))

    def _gen_increment(self, node):
        name = node[1]
        self.code.append(TAC('INC', result=name))

    def _gen_decrement(self, node):
        name = node[1]
        self.code.append(TAC('DEC', result=name))

    def _gen_if(self, node):
        cond = self._gen(node[1])
        end_lbl = self.new_label()
        self.code.append(TAC('IF_FALSE', cond, None, end_lbl))
        self._gen(node[2])
        self.code.append(TAC('LABEL', result=end_lbl))

    def _gen_if_else(self, node):
        cond = self._gen(node[1])
        else_lbl = self.new_label()
        end_lbl = self.new_label()
        self.code.append(TAC('IF_FALSE', cond, None, else_lbl))
        self._gen(node[2])
        self.code.append(TAC('GOTO', result=end_lbl))
        self.code.append(TAC('LABEL', result=else_lbl))
        if node[3]:
            self._gen(node[3])
        self.code.append(TAC('LABEL', result=end_lbl))

    def _gen_while(self, node):
        start_lbl = self.new_label()
        end_lbl = self.new_label()
        self.code.append(TAC('LABEL', result=start_lbl))
        cond = self._gen(node[1])
        self.code.append(TAC('IF_FALSE', cond, None, end_lbl))
        self._gen(node[2])
        self.code.append(TAC('GOTO', result=start_lbl))
        self.code.append(TAC('LABEL', result=end_lbl))

    def _gen_do_while(self, node):
        start_lbl = self.new_label()
        self.code.append(TAC('LABEL', result=start_lbl))
        self._gen(node[1])
        cond = self._gen(node[2])
        self.code.append(TAC('IF_FALSE', cond, None, self.new_label()))
        self.code.append(TAC('GOTO', result=start_lbl))
        end_lbl = f"L{self.label_count - 1}"
        self.code.append(TAC('LABEL', result=end_lbl))

    def _gen_for(self, node):
        if node[1]: self._gen(node[1])   # init
        start_lbl = self.new_label()
        end_lbl = self.new_label()
        self.code.append(TAC('LABEL', result=start_lbl))
        if node[2]:                       # cond
            cond = self._gen(node[2])
            self.code.append(TAC('IF_FALSE', cond, None, end_lbl))
        self._gen(node[4])                # body
        if node[3]: self._gen(node[3])    # update
        self.code.append(TAC('GOTO', result=start_lbl))
        self.code.append(TAC('LABEL', result=end_lbl))

    def _gen_switch(self, node):
        expr = self._gen(node[1])
        end_lbl = self.new_label()
        for case in node[2]:
            if case[0] == 'case':
                case_val = self._gen(case[1])
                next_case = self.new_label()
                temp = self.new_temp()
                self.code.append(TAC('==', expr, case_val, temp))
                self.code.append(TAC('IF_FALSE', temp, None, next_case))
                for stmt in case[2]:
                    self._gen(stmt)
                self.code.append(TAC('GOTO', result=end_lbl))
                self.code.append(TAC('LABEL', result=next_case))
            elif case[0] == 'default':
                for stmt in case[1]:
                    self._gen(stmt)
        self.code.append(TAC('LABEL', result=end_lbl))

    def _gen_return(self, node):
        if node[1]:
            val = self._gen(node[1])
            self.code.append(TAC('RETURN', val))
        else:
            self.code.append(TAC('RETURN'))

    def _gen_broadcast(self, node):
        val = self._gen(node[1])
        self.code.append(TAC('PRINT', val))

    def _gen_telemetry(self, node):
        self.code.append(TAC('READ', result=node[1]))

    def _gen_expr_stmt(self, node):
        if node[1]:
            self._gen(node[1])

    def _gen_end_program(self, node):
        pass

    def _gen_error_node(self, node):
        pass

    # Expresiones
    def _gen_binop(self, node):
        op_word = node[1]
        left = self._gen(node[2])
        right = self._gen(node[3])
        op = OP_MAP.get(op_word, op_word)
        temp = self.new_temp()
        self.code.append(TAC(op, left, right, temp))
        return temp

    def _gen_uminus(self, node):
        val = self._gen(node[1])
        temp = self.new_temp()
        self.code.append(TAC('UMINUS', val, None, temp))
        return temp

    def _gen_not(self, node):
        val = self._gen(node[1])
        temp = self.new_temp()
        self.code.append(TAC('NOT', val, None, temp))
        return temp

    def _gen_call(self, node):
        name = node[1]
        args = node[2]
        for arg in args:
            a = self._gen(arg)
            self.code.append(TAC('PARAM', a))
        temp = self.new_temp()
        self.code.append(TAC('CALL', name, len(args), temp))
        return temp

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
        self.code.append(TAC('ASSIGN', f"*{val}", None, temp))
        return temp

    def _gen_address(self, node):
        val = self._gen(node[1])
        temp = self.new_temp()
        self.code.append(TAC('ASSIGN', f"&{val}", None, temp))
        return temp

    def get_code_string(self):
        return "\n".join(f"{i:3d}: {instr}" for i, instr in enumerate(self.code))


# ─────────────────────────────────────────────
#  TRADUCTOR A C++
# ─────────────────────────────────────────────

class CppTranslator:
    """Traduce el AST de PitCode directamente a código C++ funcional."""

    def __init__(self):
        self.output = []
        self.indent_level = 0

    def translate(self, ast):
        self.output = []
        self.indent_level = 0

        self._line("#include <iostream>")
        self._line("#include <string>")
        self._line("")
        self._line("using namespace std;")
        self._line("")

        if ast and ast[0] == 'program':
            # Funciones antes del main
            for f in ast[1]:
                self._translate_node(f)
                self._line("")

            # Main
            self._translate_main(ast[2])

            # Funciones después del main (declarar prototipos arriba)
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

        param_str = ", ".join(
            f"{TYPE_TO_CPP.get(p[1], 'auto')} {p[2]}" for p in params
        )
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
            val = self._expr(expr)
            self._line(f"{cpp_type} {name} = {val};")
        else:
            self._line(f"{cpp_type} {name};")

    def _tr_declare_const(self, node):
        cpp_type = TYPE_TO_CPP.get(node[1], 'auto')
        name = node[2]
        expr = node[3]
        val = self._expr(expr) if expr else ""
        self._line(f"const {cpp_type} {name} = {val};")

    def _tr_assign(self, node):
        val = self._expr(node[2])
        self._line(f"{node[1]} = {val};")

    def _tr_compound_assign(self, node):
        op = OP_MAP.get(node[1], node[1])
        name = node[2]
        val = self._expr(node[3])
        self._line(f"{name} {op}= {val};")

    def _tr_increment(self, node):
        self._line(f"{node[1]}++;")

    def _tr_decrement(self, node):
        self._line(f"{node[1]}--;")

    def _tr_if(self, node):
        cond = self._expr(node[1])
        self._line(f"if ({cond}) {{")
        self.indent_level += 1
        self._translate_node(node[2])
        self.indent_level -= 1
        self._line("}")

    def _tr_if_else(self, node):
        cond = self._expr(node[1])
        self._line(f"if ({cond}) {{")
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
        cond = self._expr(node[1])
        self._line(f"while ({cond}) {{")
        self.indent_level += 1
        self._translate_node(node[2])
        self.indent_level -= 1
        self._line("}")

    def _tr_do_while(self, node):
        self._line("do {")
        self.indent_level += 1
        self._translate_node(node[1])
        self.indent_level -= 1
        cond = self._expr(node[2])
        self._line(f"}} while ({cond});")

    def _tr_for(self, node):
        init_str = self._for_part(node[1]) if node[1] else ""
        cond_str = self._expr(node[2]) if node[2] else ""
        upd_str = self._for_part(node[3]) if node[3] else ""
        self._line(f"for ({init_str}; {cond_str}; {upd_str}) {{")
        self.indent_level += 1
        self._translate_node(node[4])
        self.indent_level -= 1
        self._line("}")

    def _for_part(self, node):
        if not isinstance(node, tuple):
            return ""
        if node[0] == 'declare':
            cpp_type = TYPE_TO_CPP.get(node[1], 'auto')
            val = self._expr(node[3]) if node[3] else ""
            return f"{cpp_type} {node[2]} = {val}"
        if node[0] == 'assign':
            return f"{node[1]} = {self._expr(node[2])}"
        if node[0] == 'expr_stmt' and node[1]:
            return self._expr(node[1])
        if node[0] == 'increment':
            return f"{node[1]}++"
        if node[0] == 'decrement':
            return f"{node[1]}--"
        return ""

    def _tr_switch(self, node):
        expr = self._expr(node[1])
        self._line(f"switch ({expr}) {{")
        self.indent_level += 1
        for case in node[2]:
            if case[0] == 'case':
                val = self._expr(case[1])
                self._line(f"case {val}:")
                self.indent_level += 1
                for stmt in case[2]:
                    self._translate_node(stmt)
                self._line("break;")
                self.indent_level -= 1
            elif case[0] == 'default':
                self._line("default:")
                self.indent_level += 1
                for stmt in case[1]:
                    self._translate_node(stmt)
                self._line("break;")
                self.indent_level -= 1
        self.indent_level -= 1
        self._line("}")

    def _tr_return(self, node):
        if node[1]:
            val = self._expr(node[1])
            self._line(f"return {val};")
        else:
            self._line("return;")

    def _tr_break(self, node):
        self._line("break;")

    def _tr_continue(self, node):
        self._line("continue;")

    def _tr_broadcast(self, node):
        val = self._expr(node[1])
        self._line(f"cout << {val} << endl;")

    def _tr_telemetry(self, node):
        self._line(f"cin >> {node[1]};")

    def _tr_end_program(self, node):
        pass

    def _tr_expr_stmt(self, node):
        if node[1]:
            val = self._expr(node[1])
            self._line(f"{val};")

    def _tr_error_node(self, node):
        self._line("// Error en el código fuente")

    # ─────────────────────────────────────────
    #  EXPRESIONES → STRING C++
    # ─────────────────────────────────────────

    def _expr(self, node):
        if node is None:
            return ""
        if not isinstance(node, tuple):
            return str(node)

        kind = node[0]

        if kind == 'int':
            return str(node[1])
        if kind == 'float':
            return str(node[1])
        if kind == 'string':
            return f'"{node[1]}"'
        if kind == 'char':
            return f"'{node[1]}'"
        if kind == 'bool':
            return 'true' if node[1] else 'false'
        if kind == 'null':
            return 'NULL'
        if kind == 'id':
            return node[1]
        if kind == 'binop':
            op = OP_MAP.get(node[1], node[1])
            left = self._expr(node[2])
            right = self._expr(node[3])
            return f"({left} {op} {right})"
        if kind == 'uminus':
            return f"(-{self._expr(node[1])})"
        if kind == 'not':
            return f"(!{self._expr(node[1])})"
        if kind == 'call':
            args = ", ".join(self._expr(a) for a in node[2])
            return f"{node[1]}({args})"
        if kind == 'assign':
            return f"{node[1]} = {self._expr(node[2])}"
        if kind == 'compound_assign':
            op = OP_MAP.get(node[1], node[1])
            return f"{node[2]} {op}= {self._expr(node[3])}"
        if kind == 'increment':
            return f"{node[1]}++"
        if kind == 'decrement':
            return f"{node[1]}--"
        if kind == 'deref':
            return f"(*{self._expr(node[1])})"
        if kind == 'address':
            return f"(&{self._expr(node[1])})"

        return str(node)