# ============================================================
#   PitCode
#   Compiladores 2026 - Fase I
#   Uso: python main.py [archivo.pitcode]
# ============================================================

import sys
import os
from lexer import analyze, read_file
from parser import parse

# ─────────────────────────────────────────────
#  TABLA DE SÍMBOLOS
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


def build_symbol_table(ast, source_code=''):
    """Recorre el AST y construye la tabla de símbolos."""
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
            for f in funcs_before:
                walk(f)
            walk(main)
            for f in funcs_after:
                walk(f)

        elif kind == 'func_def':
            # node: (func_def, dtype, name, params, body, line, lexpos)
            dtype  = node[1]
            name   = node[2]
            params = node[3]
            body   = node[4]
            line   = node[5] if len(node) > 5 else 0
            lexpos = node[6] if len(node) > 6 else 0
            table.insert(name, dtype, 'función', line, lexpos_to_col(lexpos))
            table.enter_scope(name)
            for p in params:
                ptype  = p[1]
                pname  = p[2]
                pline  = p[3] if len(p) > 3 else 0
                plexpos= p[4] if len(p) > 4 else 0
                table.insert(pname, ptype, 'parámetro', pline, lexpos_to_col(plexpos))
            walk(body)
            table.exit_scope()

        elif kind == 'race_start':
            _, items = node
            for item in items:
                walk(item)

        elif kind in ('declare', 'declare_const'):
            dtype  = node[1]
            name   = node[2]
            val    = node[3]
            line   = node[4] if len(node) > 4 else 0
            lexpos = node[5] if len(node) > 5 else 0
            table.insert(name, dtype, 'variable', line, lexpos_to_col(lexpos))
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



# Reserved words set for categorization
RESERVED_WORDS = {
    'LAP','SPLIT','PITBOARD','YELLOW_FLAG','RADIO',
    'STRATEGY_CHECK','STAY_OUT','PUSH','BOX','FORMATION_LAP',
    'GAP_CHECK','SECTOR','NO_DATA','BOX_BOX','DRS',
    'STRATEGY','PODIO','NEUTRO','RACE_START',
    'BROADCAST','TELEMETRY','UNDERCUT_KW','DNF','VSC',
    'APEX','PADDOCK','RED_FLAG','BLUE_FLAG','BLACK_FLAG',
    'CHECKERED_FLAG','TRUE','FALSE'
}
OPERATORS = {'TOW','GAP','ERS','STINT','FUEL_DELTA','DEAD_HEAT','OUTLAP','UNDERCUT','OVERCUT','BOTH_TYRES','EITHER_TYRE','REVERSE_GRID','ASSIGN'}
LITERALS  = {'INT_LITERAL','FLOAT_LITERAL','STRING_LITERAL','CHAR_LITERAL'}
DELIMITERS= {'SEMICOLON','LBRACE','RBRACE','LPAREN','RPAREN','COMMA','LBRACKET','RBRACKET','COLON'}

def get_category(token_type):
    if token_type in RESERVED_WORDS:  return ('Palabra Reservada', 'cat-reserved')
    if token_type in OPERATORS:        return ('Operador',          'cat-operator')
    if token_type in LITERALS:         return ('Literal',           'cat-literal')
    if token_type in DELIMITERS:       return ('Delimitador',       'cat-delimiter')
    if token_type == 'ID':             return ('Identificador',     'cat-id')
    return ('Otro', 'cat-other')

def generate_token_report(token_list, error_list, source_file, output_path):
    """Reporte HTML de tokens y lexemas con categoría, filtros y estadísticas."""

    # ── Estadísticas ──
    from collections import Counter
    cat_counts = Counter()
    for t in token_list:
        cat, _ = get_category(t['token'])
        cat_counts[cat] += 1

    # ── Filas de la tabla ──
    rows = ""
    for t in token_list:
        cat_label, cat_class = get_category(t['token'])
        rows += f"""
        <tr data-cat="{cat_label}">
          <td class="tag-token">{t['token']}</td>
          <td class="tag-lexeme">{t['lexeme']}</td>
          <td><span class="cat-badge {cat_class}">{cat_label}</span></td>
          <td class="tag-line">{t['line']}</td>
          <td class="tag-line">{t['column']}</td>
        </tr>"""

    # ── Errores léxicos ──
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

    # ── Tarjetas de estadísticas ──
    stat_cards = ""
    colors = {
        'Palabra Reservada': '#e10600',
        'Operador':          '#ff8c00',
        'Literal':           '#4fc3f7',
        'Identificador':     '#a5d6a7',
        'Delimitador':       '#ce93d8',
        'Otro':              '#888'
    }
    for cat, count in sorted(cat_counts.items()):
        color = colors.get(cat, '#888')
        stat_cards += f'<div class="stat-card" style="border-top:3px solid {color}"><div class="stat-num" style="color:{color}">{count}</div><div class="stat-label">{cat}</div></div>'

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>PitCode - Reporte de Tokens</title>
  {HTML_STYLE}
  <style>
    .cat-badge {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 3px;
      font-size: 0.75rem;
      font-weight: bold;
    }}
    .cat-reserved  {{ background:#4a0000; color:#ff6b6b; }}
    .cat-operator  {{ background:#4a2800; color:#ffb347; }}
    .cat-literal   {{ background:#003a4a; color:#4fc3f7; }}
    .cat-id        {{ background:#1a3a1a; color:#a5d6a7; }}
    .cat-delimiter {{ background:#2a1a3a; color:#ce93d8; }}
    .cat-other     {{ background:#2a2a2a; color:#888; }}
    .filter-bar {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 16px;
    }}
    .filter-btn {{
      padding: 6px 14px;
      border-radius: 4px;
      border: 1px solid #333;
      background: #1a1a1a;
      color: #ccc;
      cursor: pointer;
      font-size: 0.82rem;
      transition: all 0.2s;
    }}
    .filter-btn:hover, .filter-btn.active {{
      background: #e10600;
      color: white;
      border-color: #e10600;
    }}
    .stats-row {{
      display: flex;
      gap: 14px;
      flex-wrap: wrap;
      margin-bottom: 24px;
    }}
    .stat-card {{
      background: #1a1a1a;
      border-radius: 6px;
      padding: 14px 20px;
      min-width: 130px;
      text-align: center;
    }}
    .stat-num   {{ font-size: 1.8rem; font-weight: bold; }}
    .stat-label {{ font-size: 0.75rem; color: #888; margin-top: 4px; text-transform: uppercase; }}
    .search-box {{
      width: 100%;
      padding: 8px 14px;
      background: #1a1a1a;
      border: 1px solid #333;
      border-radius: 4px;
      color: #ccc;
      font-size: 0.9rem;
      margin-bottom: 12px;
    }}
    .search-box:focus {{ outline: none; border-color: #e10600; }}
  </style>
</head>
<body>
  <h1>🏎 PitCode — Reporte de Tokens</h1>
  <div class="summary">
    Archivo: <strong>{source_file}</strong> &nbsp;|&nbsp;
    Tokens: <strong>{len(token_list)}</strong> &nbsp;|&nbsp;
    Errores léxicos: <strong>{len(error_list)}</strong>
  </div>

  <h2>Resumen Estadístico</h2>
  <div class="stats-row">{stat_cards}</div>

  <h2>Tokens y Lexemas <span class="badge ok">{len(token_list)}</span></h2>

  <input class="search-box" type="text" id="searchBox" placeholder="🔍 Buscar token o lexema..." onkeyup="filterTable()">

  <div class="filter-bar">
    <button class="filter-btn active" onclick="filterCat('', this)">Todos</button>
    <button class="filter-btn" onclick="filterCat('Palabra Reservada', this)">Palabras Reservadas</button>
    <button class="filter-btn" onclick="filterCat('Operador', this)">Operadores</button>
    <button class="filter-btn" onclick="filterCat('Literal', this)">Literales</button>
    <button class="filter-btn" onclick="filterCat('Identificador', this)">Identificadores</button>
    <button class="filter-btn" onclick="filterCat('Delimitador', this)">Delimitadores</button>
  </div>

  <table id="tokenTable">
    <thead>
      <tr><th>Token</th><th>Lexema</th><th>Categoría</th><th>Línea</th><th>Columna</th></tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>

  {error_section}

  <script>
    let currentCat = '';
    let currentSearch = '';

    function filterCat(cat, btn) {{
      currentCat = cat;
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      applyFilters();
    }}

    function filterTable() {{
      currentSearch = document.getElementById('searchBox').value.toLowerCase();
      applyFilters();
    }}

    function applyFilters() {{
      const rows = document.querySelectorAll('#tokenTable tbody tr');
      rows.forEach(row => {{
        const cat     = row.getAttribute('data-cat') || '';
        const text    = row.innerText.toLowerCase();
        const catOk   = !currentCat || cat === currentCat;
        const searchOk= !currentSearch || text.includes(currentSearch);
        row.style.display = (catOk && searchOk) ? '' : 'none';
      }});
    }}
  </script>

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
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    if len(sys.argv) > 1:
        source_file = os.path.abspath(sys.argv[1])
    else:
        source_file = os.path.join(BASE_DIR, 'prueba.pitcode')

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
    symbol_table = build_symbol_table(ast, source_code)
    print(f"        {len(symbol_table.get_all())} símbolos registrados")

    # ── Generar reportes HTML ──
    print()
    print("  Generando reportes HTML...")
    reports_dir = os.path.join(BASE_DIR, 'reports')
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
    print(f"   Reportes en: {reports_dir}")
    print("=" * 60)


if __name__ == '__main__':
    main()


