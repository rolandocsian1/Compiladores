#   PitCode
#   Compiladores 2026 - Fase I & II
#   Uso: python main.py [archivo.pitcode]

import sys
import os

from lexer    import analyze, read_file
from parser   import parse
from semantic import SemanticAnalyzer
from codegen  import ThreeAddressGenerator, CppTranslator
import html_gen


class SymbolTable:
    def __init__(self):
        self.scopes      = [{}]
        self.scope_names = ['global']
        self.all_symbols = []

    def enter_scope(self, name):
        self.scopes.append({})
        self.scope_names.append(name)

    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()
            self.scope_names.pop()

    def current_scope(self):
        return self.scope_names[-1]

    def insert(self, name, dtype, role, line, col):
        entry = {
            'name'  : name,
            'type'  : dtype,
            'role'  : role,
            'scope' : self.current_scope(),
            'line'  : line,
            'column': col,
        }
        self.scopes[-1][name] = entry
        self.all_symbols.append(entry)

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def get_all(self):
        return self.all_symbols


def build_symbol_table(ast, source_code=''):
    table = SymbolTable()
    if ast is None:
        return table

    def lexpos_to_col(lexpos):
        if not source_code or lexpos == 0:
            return 0
        line_start = source_code.rfind(chr(10), 0, lexpos) + 1
        return (lexpos - line_start) + 1

    def walk(node):
        if not isinstance(node, tuple):
            return
        kind = node[0]

        if kind == 'program':
            _, funcs_before, main, funcs_after = node
            for f in funcs_before: walk(f)
            walk(main)
            for f in funcs_after:  walk(f)

        elif kind == 'func_def':
            dtype  = node[1]; name = node[2]; params = node[3]; body = node[4]
            line   = node[5] if len(node) > 5 else 0
            lexpos = node[6] if len(node) > 6 else 0
            table.insert(name, dtype, 'funcion', line, lexpos_to_col(lexpos))
            table.enter_scope(name)
            for p in params:
                table.insert(p[2], p[1], 'parametro',
                             p[3] if len(p) > 3 else 0,
                             lexpos_to_col(p[4] if len(p) > 4 else 0))
            walk(body)
            table.exit_scope()

        elif kind == 'race_start':
            for item in node[1]: walk(item)

        elif kind in ('declare', 'declare_const'):
            dtype  = node[1]; name = node[2]; val = node[3]
            line   = node[4] if len(node) > 4 else 0
            lexpos = node[5] if len(node) > 5 else 0
            table.insert(name, dtype, 'variable', line, lexpos_to_col(lexpos))
            if val: walk(val)

        elif kind == 'block':
            for item in node[1]: walk(item)

        elif kind in ('if', 'if_else'):
            for child in node[1:]:
                if child: walk(child)

        elif kind == 'switch':
            walk(node[1])
            for c in node[2]: walk(c)

        elif kind in ('while', 'do_while'):
            walk(node[1]); walk(node[2])

        elif kind == 'for':
            _, init, cond, update, body = node
            table.enter_scope('for_loop')
            if init:   walk(init)
            if cond:   walk(cond)
            if update: walk(update)
            walk(body)
            table.exit_scope()

        elif kind in ('return', 'broadcast', 'expr_stmt'):
            if len(node) > 1 and node[1]: walk(node[1])

        elif kind == 'binop':
            walk(node[2]); walk(node[3])

        elif kind in ('uminus', 'not'):
            walk(node[1])

        elif kind == 'assign':
            walk(node[2])

        elif kind == 'call':
            for arg in node[2]: walk(arg)

    walk(ast)
    return table


def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    if len(sys.argv) > 1:
        source_file = os.path.abspath(sys.argv[1])
    else:
        source_file = os.path.join(BASE_DIR, 'prueba - copia.pitcode')

    print("=" * 60)
    print("  PitCode Compiler — Fase I & II")
    print("=" * 60)
    print(f"  Archivo: {source_file}")
    print()

    source_code = read_file(source_file)

    # ── Fase I: Lexico ──────────────────────────────────────
    print("[ 1/5 ] Analisis Lexico...")
    token_list, lex_errors = analyze(source_code)
    print(f"        {len(token_list)} tokens | {len(lex_errors)} errores lexicos")

    # ── Fase I: Sintactico ──────────────────────────────────
    print("[ 2/5 ] Analisis Sintactico...")
    if lex_errors:
        ast        = None
        syn_errors = []
        print("        Omitido por errores lexicos")
    else:
        ast, syn_errors = parse(source_code)
        print(f"        {len(syn_errors)} errores sintacticos")

    # ── Fase I: Tabla de Simbolos ───────────────────────────
    print("[ 3/5 ] Construyendo Tabla de Simbolos...")
    symbol_table = build_symbol_table(ast, source_code)
    print(f"        {len(symbol_table.get_all())} simbolos registrados")

    # ── Fase II: Semantico ──────────────────────────────────
    print("[ 4/5 ] Analisis Semantico...")
    sem_errors   = []
    sem_warnings = []
    hay_bloqueantes = bool(lex_errors) or bool(syn_errors)

    if not hay_bloqueantes and ast:
        sem = SemanticAnalyzer()
        sem.analyze(ast, codigo)
        sem_errors   = sem.get_errors()
        sem_warnings = sem.get_warnings()
        print(f"        {len(sem_errors)} errores semanticos | {len(sem_warnings)} advertencia(s)")
    else:
        print("        Omitido por errores anteriores")

    hay_bloqueantes = hay_bloqueantes or bool(sem_errors)
    todos_errores   = lex_errors + syn_errors + sem_errors + sem_warnings

    # ── Fase II: Generacion de Codigo ───────────────────────
    print("[ 5/5 ] Generando Codigo...")
    code_3d_str = ""
    cpp_code    = ""

    if not hay_bloqueantes and ast:
        reports_dir = os.path.join(BASE_DIR, 'reports')
        os.makedirs(reports_dir, exist_ok=True)

        gen = ThreeAddressGenerator()
        gen.generate(ast)
        code_3d_str = gen.get_code_string()

        cpp_path   = os.path.join(reports_dir, 'output.cpp')
        translator = CppTranslator()
        cpp_code   = translator.save_to_file(ast, cpp_path)

        print(f"        C3D: {len(gen.code)} instrucciones | C++ -> reports/output.cpp")
    else:
        print("        Omitido por errores en fases anteriores")

    # ── Reportes HTML ────────────────────────────────────────
    print()
    print("  Generando reportes HTML...")
    tokens_para_reporte = [] if hay_bloqueantes else token_list

    html_gen.generar_reporte_tokens(tokens_para_reporte)
    html_gen.generar_reporte_errores(todos_errores)
    html_gen.generar_reporte_simbolos(ast, source_code)

    if not hay_bloqueantes and code_3d_str:
        html_gen.generar_reporte_codigo(code_3d_str, cpp_code)

    html_gen.generar_index(
        hay_errores=hay_bloqueantes,
        hay_codigo=not hay_bloqueantes
    )

    # ── Resumen ──────────────────────────────────────────────
    print()
    print("=" * 60)
    total_errores = len(lex_errors) + len(syn_errors) + len(sem_errors)
    if total_errores == 0:
        print("  OK  Compilacion exitosa — Sin errores.")
        if cpp_code:
            print("  OK  Codigo C++ generado en reports/output.cpp")
    else:
        print(f"  ERR Compilacion con {total_errores} error(es).")
    reports_dir = os.path.join(BASE_DIR, 'reports')
    print(f"  Reportes en: {reports_dir}")
    print("=" * 60)


if __name__ == '__main__':
    main()
