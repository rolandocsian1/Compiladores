# ============================================================
#   PitCode - Orquestador Principal
#   Compiladores 2026 - Fase I
#   Uso: python main.py [archivo.pitcode]
# ============================================================

import sys
import os
from lexer import analyze, read_file
from parser import parse

# ─────────────────────────────────────────────
#  TABLA DE SÍMBOLOS
#  Gestiona ámbitos: global / local por función
# ─────────────────────────────────────────────

class SymbolTable:
    def __init__(self):
        self.scopes = [{}]          # pila de ámbitos
        self.scope_names = ['global']
        self.all_symbols = []       # historial completo para reporte

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


def build_symbol_table(ast):
    """Recorre el AST y construye la tabla de símbolos."""
    table = SymbolTable()

    if ast is None:
        return table

    def walk(node):
        if not isinstance(node, tuple):
            return

        kind = node[0]

        if kind == 'program':
            _, funcs_before, main, funcs_after = node
            for f in funcs_before:
                walk(f)
            walk(main)
            for f in funcs_after:
                walk(f)

        elif kind == 'func_def':
            _, dtype, name, params, body = node
            table.insert(name, dtype, 'función', 0, 0)
            table.enter_scope(name)
            for p in params:
                _, ptype, pname = p
                table.insert(pname, ptype, 'parámetro', 0, 0)
            walk(body)
            table.exit_scope()

        elif kind == 'race_start':
            _, items = node
            for item in items:
                walk(item)

        elif kind in ('declare', 'declare_const'):
            _, dtype, name, val = node
            table.insert(name, dtype, 'variable', 0, 0)
            if val:
                walk(val)

        elif kind == 'block':
            _, items = node
            for item in items:
                walk(item)

        elif kind in ('if', 'if_else'):
            for child in node[1:]:
                if child:
                    walk(child)

        elif kind == 'switch':
            _, expr, cases = node
            walk(expr)
            for c in cases:
                walk(c)

        elif kind in ('while', 'do_while'):
            walk(node[1])
            walk(node[2])

        elif kind == 'for':
            _, init, cond, update, body = node
            table.enter_scope('for_loop')
            if init: walk(init)
            if cond: walk(cond)
            if update: walk(update)
            walk(body)
            table.exit_scope()

        elif kind in ('return', 'broadcast', 'expr_stmt'):
            if len(node) > 1 and node[1]:
                walk(node[1])

        elif kind == 'binop':
            walk(node[2])
            walk(node[3])

        elif kind in ('uminus', 'not'):
            walk(node[1])

        elif kind == 'assign':
            walk(node[2])

        elif kind == 'call':
            for arg in node[2]:
                walk(arg)

    walk(ast)
    return table


# ─────────────────────────────────────────────
#  GENERADOR DE REPORTES HTML
# ─────────────────────────────────────────────

HTML_STYLE = """
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Segoe UI', sans-serif;
    background: #0f0f0f;
    color: #e0e0e0;
    padding: 30px;
  }
  h1 {
    font-size: 2rem;
    color: #e10600;
    border-bottom: 3px solid #e10600;
    padding-bottom: 10px;
    margin-bottom: 25px;
    letter-spacing: 2px;
  }
  h2 {
    font-size: 1.2rem;
    color: #ff8c00;
    margin: 30px 0 12px;
    letter-spacing: 1px;
  }
  .badge {
    display: inline-block;
    background: #e10600;
    color: white;
    border-radius: 4px;
    padding: 2px 10px;
    font-size: 0.8rem;
    margin-left: 8px;
    vertical-align: middle;
  }
  .badge.ok  { background: #2e7d32; }
  .badge.warn { background: #ff8c00; }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
    margin-bottom: 20px;
  }
  th {
    background: #e10600;
    color: white;
    padding: 10px 14px;
    text-align: left;
    letter-spacing: 1px;
    font-size: 0.8rem;
    text-transform: uppercase;
  }
  td {
    padding: 8px 14px;
    border-bottom: 1px solid #2a2a2a;
  }
  tr:nth-child(even) td { background: #1a1a1a; }
  tr:hover td { background: #222; }
  .tag-token  { color: #4fc3f7; font-weight: bold; }
  .tag-lexeme { color: #a5d6a7; font-family: monospace; }
  .tag-type   { color: #ce93d8; }
  .tag-role   { color: #ffcc80; }
  .tag-scope  { color: #80deea; }
  .tag-error  { color: #ef9a9a; font-weight: bold; }
  .tag-line   { color: #888; font-family: monospace; }
  .no-errors {
    background: #1b3a1f;
    border: 1px solid #2e7d32;
    border-radius: 6px;
    padding: 16px 20px;
    color: #a5d6a7;
    font-size: 1rem;
  }
  .summary {
    background: #1a1a1a;
    border-left: 4px solid #e10600;
    padding: 12px 18px;
    margin-bottom: 20px;
    border-radius: 0 6px 6px 0;
    font-size: 0.9rem;
    color: #bbb;
  }
  footer {
    margin-top: 40px;
    color: #444;
    font-size: 0.8rem;
    text-align: center;
  }
</style>
"""


def generate_token_report(token_list, error_list, source_file, output_path):
    """Reporte HTML de tokens y lexemas."""
    rows = ""
    for t in token_list:
        rows += f"""
        <tr>
          <td class="tag-token">{t['token']}</td>
          <td class="tag-lexeme">{t['lexeme']}</td>
          <td class="tag-line">{t['line']}</td>
          <td class="tag-line">{t['column']}</td>
        </tr>"""

    error_rows = ""
    if error_list:
        for e in error_list:
            error_rows += f"""
            <tr>
              <td class="tag-error">{e['type']}</td>
              <td class="tag-lexeme">{e.get('char', '')}</td>
              <td class="tag-line">{e['line']}</td>
              <td class="tag-line">{e['column']}</td>
              <td>{e['message']}</td>
            </tr>"""
        error_section = f"""
        <h2>⚠ Errores Léxicos <span class="badge">{len(error_list)}</span></h2>
        <table>
          <thead><tr><th>Tipo</th><th>Carácter</th><th>Línea</th><th>Columna</th><th>Mensaje</th></tr></thead>
          <tbody>{error_rows}</tbody>
        </table>"""
    else:
        error_section = """
        <h2>Errores Léxicos <span class="badge ok">0</span></h2>
        <div class="no-errors">✓ No se encontraron errores léxicos.</div>"""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>PitCode - Reporte de Tokens</title>
  {HTML_STYLE}
</head>
<body>
  <h1>🏎 PitCode — Reporte de Tokens</h1>
  <div class="summary">
    Archivo analizado: <strong>{source_file}</strong> &nbsp;|&nbsp;
    Tokens encontrados: <strong>{len(token_list)}</strong> &nbsp;|&nbsp;
    Errores léxicos: <strong>{len(error_list)}</strong>
  </div>

  <h2>Tokens y Lexemas <span class="badge ok">{len(token_list)}</span></h2>
  <table>
    <thead>
      <tr><th>Token</th><th>Lexema</th><th>Línea</th><th>Columna</th></tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>

  {error_section}

  <footer>PitCode Compiler · Compiladores 2026 · Fase I</footer>
</body>
</html>"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  ✓ Reporte de tokens generado: {output_path}")


def generate_symbol_table_report(symbol_table, source_file, output_path):
    """Reporte HTML de la tabla de símbolos."""
    symbols = symbol_table.get_all()

    rows = ""
    for s in symbols:
        rows += f"""
        <tr>
          <td class="tag-lexeme">{s['name']}</td>
          <td class="tag-type">{s['type']}</td>
          <td class="tag-role">{s['role']}</td>
          <td class="tag-scope">{s['scope']}</td>
          <td class="tag-line">{s['line']}</td>
          <td class="tag-line">{s['column']}</td>
        </tr>"""

    if not rows:
        rows = "<tr><td colspan='6' style='text-align:center;color:#666'>Sin símbolos registrados</td></tr>"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>PitCode - Tabla de Símbolos</title>
  {HTML_STYLE}
</head>
<body>
  <h1>🏎 PitCode — Tabla de Símbolos</h1>
  <div class="summary">
    Archivo analizado: <strong>{source_file}</strong> &nbsp;|&nbsp;
    Símbolos registrados: <strong>{len(symbols)}</strong>
  </div>

  <h2>Símbolos <span class="badge ok">{len(symbols)}</span></h2>
  <table>
    <thead>
      <tr>
        <th>Nombre</th>
        <th>Tipo</th>
        <th>Rol</th>
        <th>Ámbito</th>
        <th>Línea</th>
        <th>Columna</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>

  <footer>PitCode Compiler · Compiladores 2026 · Fase I</footer>
</body>
</html>"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  ✓ Tabla de símbolos generada:  {output_path}")


def generate_error_report(lex_errors, syn_errors, source_file, output_path):
    """Reporte HTML de errores léxicos y sintácticos."""

    def make_rows(errors, tag):
        rows = ""
        for e in errors:
            rows += f"""
            <tr>
              <td class="tag-error">{tag}</td>
              <td class="tag-line">{e['line']}</td>
              <td class="tag-line">{e['column']}</td>
              <td>{e['message']}</td>
            </tr>"""
        return rows

    total = len(lex_errors) + len(syn_errors)
    all_rows = make_rows(lex_errors, 'Léxico') + make_rows(syn_errors, 'Sintáctico')

    if total == 0:
        content = '<div class="no-errors">✓ No se encontraron errores léxicos ni sintácticos.</div>'
    else:
        content = f"""
        <table>
          <thead>
            <tr><th>Tipo</th><th>Línea</th><th>Columna</th><th>Mensaje</th></tr>
          </thead>
          <tbody>{all_rows}</tbody>
        </table>"""

    badge_class = "ok" if total == 0 else "badge"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>PitCode - Reporte de Errores</title>
  {HTML_STYLE}
</head>
<body>
  <h1>🏎 PitCode — Reporte de Errores</h1>
  <div class="summary">
    Archivo analizado: <strong>{source_file}</strong> &nbsp;|&nbsp;
    Errores léxicos: <strong>{len(lex_errors)}</strong> &nbsp;|&nbsp;
    Errores sintácticos: <strong>{len(syn_errors)}</strong>
  </div>

  <h2>Errores Encontrados <span class="badge {badge_class}">{total}</span></h2>
  {content}

  <footer>PitCode Compiler · Compiladores 2026 · Fase I</footer>
</body>
</html>"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  ✓ Reporte de errores generado:  {output_path}")


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def main():
    # ── Leer archivo fuente ──
    if len(sys.argv) > 1:
        source_file = sys.argv[1]
    else:
        source_file = os.path.join(os.path.dirname(__file__), 'prueba.pitcode')

    print("=" * 60)
    print("  🏎  PitCode Compiler — Fase I")
    print("=" * 60)
    print(f"  Archivo: {source_file}")
    print()

    source_code = read_file(source_file)

    # ── Fase 1: Análisis Léxico ──
    print("[ 1/3 ] Análisis Léxico...")
    token_list, lex_errors = analyze(source_code)
    print(f"        {len(token_list)} tokens | {len(lex_errors)} errores léxicos")

    # ── Fase 2: Análisis Sintáctico ──
    print("[ 2/3 ] Análisis Sintáctico...")
    ast, syn_errors = parse(source_code)
    print(f"        {len(syn_errors)} errores sintácticos")

    # ── Fase 3: Tabla de Símbolos ──
    print("[ 3/3 ] Construyendo Tabla de Símbolos...")
    symbol_table = build_symbol_table(ast)
    print(f"        {len(symbol_table.get_all())} símbolos registrados")

    # ── Generar reportes HTML ──
    print()
    print("  Generando reportes HTML...")
    reports_dir = os.path.join(os.path.dirname(__file__), 'reports')
    os.makedirs(reports_dir, exist_ok=True)

    base = os.path.basename(source_file)
    generate_token_report(token_list, lex_errors, base,
                          os.path.join(reports_dir, 'reporte_tokens.html'))
    generate_symbol_table_report(symbol_table, base,
                                 os.path.join(reports_dir, 'reporte_simbolos.html'))
    generate_error_report(lex_errors, syn_errors, base,
                          os.path.join(reports_dir, 'reporte_errores.html'))

    # ── Resumen final ──
    print()
    print("=" * 60)
    total_errors = len(lex_errors) + len(syn_errors)
    if total_errors == 0:
        print("  ✓  Compilación exitosa — Sin errores.")
    else:
        print(f"  ⚠  Compilación con {total_errors} error(es).")
    print(f"  📁 Reportes en: {reports_dir}")
    print("=" * 60)


if __name__ == '__main__':
    main()

