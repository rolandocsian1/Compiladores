# ============================================================
#   PitCode - Generador de Reportes HTML
#   Compiladores 2026 - Fase I
# ============================================================

import os
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

def _ensure_reports():
    os.makedirs(REPORTS_DIR, exist_ok=True)

def generar_reporte_tokens(tokens_list):
    _ensure_reports()

    RESERVADAS = {'LAP','SPLIT','PITBOARD','YELLOW_FLAG','RADIO',
                  'STRATEGY_CHECK','STAY_OUT','PUSH','BOX','FORMATION_LAP',
                  'GAP_CHECK','SECTOR','NO_DATA','BOX_BOX','DRS',
                  'STRATEGY','PODIO','NEUTRO','RACE_START',
                  'BROADCAST','TELEMETRY','DNF','VSC','APEX',
                  'PADDOCK','RED_FLAG','BLUE_FLAG','BLACK_FLAG',
                  'CHECKERED_FLAG','TRUE','FALSE'}
    OPERADORES  = {'TOW','GAP','ERS','STINT','FUEL_DELTA',
                  'DEAD_HEAT','OUTLAP','UNDERCUT','OVERCUT',
                  'BOTH_TYRES','EITHER_TYRE','REVERSE_GRID',
                  'ASSIGN'}
    LITERALES   = {'INT_LITERAL','FLOAT_LITERAL','STRING_LITERAL','CHAR_LITERAL'}
    DELIMITADORES = {'SEMICOLON','LBRACE','RBRACE','LPAREN','RPAREN',
                 'COMMA','LBRACKET','RBRACKET','COLON'}

    def get_categoria(token_type):
        if token_type in RESERVADAS:   return 'Palabra Reservada'
        if token_type in OPERADORES:   return 'Operador'
        if token_type in LITERALES:    return 'Literal'
        if token_type in DELIMITADORES:return 'Delimitador'
        if token_type == 'ID':         return 'Identificador'
        return 'Otro'

    CAT_COLORS = {
        'Palabra Reservada': ('#e10600', '#fff'),
        'Operador':          ('#ff8c00', '#fff'),
        'Literal':           ('#7b5ea7', '#fff'),
        'Identificador':     ('#2e7d32', '#fff'),
        'Delimitador':       ('#1a5276', '#fff'),
        'Otro':              ('#444',    '#ccc'),
    }

    # Conteos por categoría
    conteos = {}
    for t in tokens_list:
        cat = get_categoria(t['token'])
        conteos[cat] = conteos.get(cat, 0) + 1

    # Tarjetas de estadísticas
    stat_cards = ""
    for cat, count in sorted(conteos.items()):
        bg, fg = CAT_COLORS.get(cat, ('#444', '#ccc'))
        stat_cards += f"""
        <div class="stat-card" style="border-top: 3px solid {bg}">
            <div class="stat-num" style="color:{bg}">{count}</div>
            <div class="stat-label">{cat}</div>
        </div>"""

    # Filas de la tabla
    rows = ""
    for t in tokens_list:
        cat = get_categoria(t['token'])
        bg, fg = CAT_COLORS.get(cat, ('#444', '#ccc'))
        badge = f'<span style="background:{bg};color:{fg};padding:2px 8px;border-radius:3px;font-size:0.75rem;font-weight:bold">{cat}</span>'
        rows += f"""
        <tr data-cat="{cat}">
            <td class="tag-token">{t['token']}</td>
            <td class="tag-lexeme">{t['lexeme']}</td>
            <td>{badge}</td>
            <td class="tag-line">{t['line']}</td>
            <td class="tag-line">{t['column']}</td>
        </tr>"""

    total = len(tokens_list)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>PitCode - Reporte de Tokens</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', sans-serif; background: #0f0f0f; color: #e0e0e0; padding: 30px; }}
    h1 {{ font-size: 2rem; color: #e10600; border-bottom: 3px solid #e10600; padding-bottom: 10px; margin-bottom: 25px; letter-spacing: 2px; }}
    h2 {{ font-size: 1.2rem; color: #ff8c00; margin: 25px 0 12px; letter-spacing: 1px; }}
    .nav {{ margin-bottom: 20px; }}
    .nav a {{ color: #569cd6; text-decoration: none; font-size: 13px; }}
    .nav a:hover {{ color: white; }}
    .summary {{ background: #1a1a1a; border-left: 4px solid #e10600; padding: 12px 18px; margin-bottom: 20px; border-radius: 0 6px 6px 0; font-size: 0.9rem; color: #bbb; }}
    .stats-row {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 25px; }}
    .stat-card {{ background: #1a1a1a; padding: 14px 20px; border-radius: 6px; min-width: 110px; text-align: center; }}
    .stat-num   {{ font-size: 1.8rem; font-weight: bold; }}
    .stat-label {{ font-size: 0.75rem; color: #888; margin-top: 4px; text-transform: uppercase; }}
    .filter-bar {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }}
    .filter-btn {{ background: transparent; border: 1px solid #444; color: #aaa; padding: 5px 14px; border-radius: 4px; cursor: pointer; font-size: 0.82rem; }}
    .filter-btn:hover {{ border-color: #e10600; color: white; }}
    .filter-btn.active {{ background: #e10600; border-color: #e10600; color: white; }}
    .search-box {{ width: 100%; padding: 8px 14px; background: #1a1a1a; border: 1px solid #333; border-radius: 4px; color: #ccc; font-size: 0.9rem; margin-bottom: 12px; }}
    .search-box:focus {{ outline: none; border-color: #e10600; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
    th {{ background: #e10600; color: white; padding: 10px 14px; text-align: left; letter-spacing: 1px; font-size: 0.8rem; text-transform: uppercase; }}
    td {{ padding: 8px 14px; border-bottom: 1px solid #2a2a2a; }}
    tr:nth-child(even) td {{ background: #1a1a1a; }}
    tr:hover td {{ background: #222; }}
    .tag-token  {{ color: #4fc3f7; font-weight: bold; }}
    .tag-lexeme {{ color: #a5d6a7; font-family: monospace; }}
    .tag-line   {{ color: #888; font-family: monospace; }}
    footer {{ margin-top: 40px; color: #444; font-size: 0.8rem; text-align: center; }}
  </style>
</head>
<body>
  <div class="nav"><a href="index.html">← Volver al inicio</a></div>
  <h1>PitCode — Reporte de Tokens</h1>
  <div class="summary">
    Archivo analizado &nbsp;|&nbsp;
    Tokens: <strong>{total}</strong>
  </div>

  <h2>Resumen Estadístico</h2>
  <div class="stats-row">{stat_cards}</div>

  <h2>Tokens y Lexemas <span style="background:#2e7d32;color:white;padding:2px 10px;border-radius:4px;font-size:0.8rem;margin-left:8px">{total}</span></h2>

  <input class="search-box" type="text" id="searchBox" placeholder="Buscar token o lexema..." onkeyup="filterTable()">

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

  <script>
    let currentCat = '';
    function filterCat(cat, btn) {{
      currentCat = cat;
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      applyFilters();
    }}
    function filterTable() {{
      applyFilters();
    }}
    function applyFilters() {{
      const search = document.getElementById('searchBox').value.toLowerCase();
      document.querySelectorAll('#tokenTable tbody tr').forEach(row => {{
        const catOk    = !currentCat || row.getAttribute('data-cat') === currentCat;
        const searchOk = !search || row.innerText.toLowerCase().includes(search);
        row.style.display = (catOk && searchOk) ? '' : 'none';
      }});
    }}
  </script>

  <footer>PitCode Compiler · Compiladores 2026 · Fase I</footer>
</body>
</html>"""

    with open(os.path.join(REPORTS_DIR, "reporte_tokens.html"), "w", encoding="utf-8") as f:
        f.write(html)

def generar_reporte_errores(errores_list):
    _ensure_reports()

    total       = len(errores_list)
    lexicos     = sum(1 for e in errores_list if e.get('type') == 'Léxico')
    sintacticos = sum(1 for e in errores_list if e.get('type') == 'Sintáctico')

    if total == 0:
        contenido = '<div class="no-errors">Sin errores lexicos ni sintacticos.</div>'
    else:
        filas = ""
        for i, e in enumerate(errores_list, 1):
            tipo    = e.get('type', 'Desconocido')
            mensaje = e.get('message', str(e))
            linea   = e.get('line', 0)
            col     = e.get('column', 0)
            filas += f"""
            <tr>
                <td class="tag-line">{i}</td>
                <td class="tag-error">{tipo}</td>
                <td>{mensaje}</td>
                <td class="tag-line">{linea}</td>
                <td class="tag-line">{col}</td>
            </tr>
            """
        contenido = f"""
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Tipo</th>
                    <th>Mensaje</th>
                    <th>Linea</th>
                    <th>Columna</th>
                </tr>
            </thead>
            <tbody>{filas}</tbody>
        </table>
        """

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>PitCode - Reporte de Errores</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', sans-serif; background: #0f0f0f; color: #e0e0e0; padding: 30px; }}
    h1 {{ font-size: 2rem; color: #e10600; border-bottom: 3px solid #e10600; padding-bottom: 10px; margin-bottom: 25px; letter-spacing: 2px; }}
    h2 {{ font-size: 1.2rem; color: #ff8c00; margin: 30px 0 12px; letter-spacing: 1px; }}
    .nav {{ margin-bottom: 20px; }}
    .nav a {{ color: #569cd6; text-decoration: none; font-size: 13px; }}
    .nav a:hover {{ color: white; }}
    .badge {{ display: inline-block; background: #e10600; color: white; border-radius: 4px; padding: 2px 10px; font-size: 0.8rem; margin-left: 8px; vertical-align: middle; }}
    .badge.ok {{ background: #2e7d32; }}
    .badge.warn {{ background: #ff8c00; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; margin-bottom: 20px; }}
    th {{ background: #e10600; color: white; padding: 10px 14px; text-align: left; letter-spacing: 1px; font-size: 0.8rem; text-transform: uppercase; }}
    td {{ padding: 8px 14px; border-bottom: 1px solid #2a2a2a; }}
    tr:nth-child(even) td {{ background: #1a1a1a; }}
    tr:hover td {{ background: #222; }}
    .tag-error {{ color: #ef9a9a; font-weight: bold; }}
    .tag-line  {{ color: #888; font-family: monospace; }}
    .no-errors {{ background: #1b3a1f; border: 1px solid #2e7d32; border-radius: 6px; padding: 16px 20px; color: #a5d6a7; font-size: 1rem; }}
    .summary {{ background: #1a1a1a; border-left: 4px solid #e10600; padding: 12px 18px; margin-bottom: 20px; border-radius: 0 6px 6px 0; font-size: 0.9rem; color: #bbb; }}
    footer {{ margin-top: 40px; color: #444; font-size: 0.8rem; text-align: center; }}
  </style>
</head>
<body>
  <div class="nav"><a href="index.html">← Volver al inicio</a></div>
  <h1>PitCode — Reporte de Errores</h1>
  <div class="summary">
    Errores lexicos: <strong>{lexicos}</strong> &nbsp;|&nbsp;
    Errores sintacticos: <strong>{sintacticos}</strong> &nbsp;|&nbsp;
    Total: <strong>{total}</strong>
  </div>
  <h2>Errores Encontrados <span class="badge {'ok' if total == 0 else 'warn'}">{total}</span></h2>
  {contenido}
  <footer>PitCode Compiler · Compiladores 2026 · Fase I</footer>
</body>
</html>"""

    with open(os.path.join(REPORTS_DIR, "reporte_errores.html"), "w", encoding="utf-8") as f:
        f.write(html)

def generar_reporte_simbolos(ast, source_code):
    _ensure_reports()

    # ── Tabla de Símbolos inline (sin importar main) ──
    scopes = [{}]
    scope_names = ['global']
    all_symbols = []

    def current_scope():
        return scope_names[-1]

    def enter_scope(name):
        scopes.append({})
        scope_names.append(name)

    def exit_scope():
        if len(scopes) > 1:
            scopes.pop()
            scope_names.pop()

    def insert(name, dtype, role, line, lexpos):
        line_start = source_code.rfind('\n', 0, lexpos) + 1
        col = (lexpos - line_start) + 1 if lexpos > 0 else 0
        entry = {'name': name, 'type': dtype, 'role': role,
                 'scope': current_scope(), 'line': line, 'column': col}
        scopes[-1][name] = entry
        all_symbols.append(entry)

    def walk(node):
        if not isinstance(node, tuple):
            return
        kind = node[0]

        if kind == 'program':
            for f in node[1]: walk(f)
            walk(node[2])
            for f in node[3]: walk(f)

        elif kind == 'func_def':
            dtype, name, params, body = node[1], node[2], node[3], node[4]
            line   = node[5] if len(node) > 5 else 0
            lexpos = node[6] if len(node) > 6 else 0
            insert(name, dtype, 'función', line, lexpos)
            enter_scope(name)
            for p in params:
                insert(p[2], p[1], 'parámetro',
                       p[3] if len(p) > 3 else 0,
                       p[4] if len(p) > 4 else 0)
            walk(body)
            exit_scope()

        elif kind == 'race_start':
            for item in node[1]: walk(item)

        elif kind in ('declare', 'declare_const'):
            dtype, name, val = node[1], node[2], node[3]
            line   = node[4] if len(node) > 4 else 0
            lexpos = node[5] if len(node) > 5 else 0
            insert(name, dtype, 'variable', line, lexpos)
            if val: walk(val)

        elif kind == 'block':
            for item in node[1]: walk(item)

        elif kind == 'if':
            walk(node[1])
            enter_scope('if_block')
            walk(node[2])
            exit_scope()

        elif kind == 'if_else':
            walk(node[1])
            enter_scope('if_block')
            walk(node[2])
            exit_scope()
            enter_scope('else_block')
            if node[3]: walk(node[3])
            exit_scope()

        elif kind == 'while':
            walk(node[1])
            enter_scope('while_block')
            walk(node[2])
            exit_scope()

        elif kind == 'do_while':
            enter_scope('do_while_block')
            walk(node[1])
            exit_scope()
            walk(node[2])

        elif kind == 'for':
            enter_scope('for_loop')
            if node[1]: walk(node[1])
            if node[2]: walk(node[2])
            if node[3]: walk(node[3])
            walk(node[4])
            exit_scope()

        elif kind == 'switch':
            walk(node[1])
            for c in node[2]: walk(c)

        elif kind in ('case', 'default'):
            for child in node[1:]:
                if isinstance(child, list):
                    for item in child: walk(item)
                elif child: walk(child)

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

    if ast:
        walk(ast)

    # ── Generar HTML ──
    rows = ""
    for s in all_symbols:
        rows += f"""
        <tr>
          <td style="color:#a5d6a7;font-family:monospace">{s['name']}</td>
          <td style="color:#ce93d8">{s['type']}</td>
          <td style="color:#ffcc80">{s['role']}</td>
          <td style="color:#80deea">{s['scope']}</td>
          <td style="color:#888;font-family:monospace">{s['line']}</td>
          <td style="color:#888;font-family:monospace">{s['column']}</td>
        </tr>"""

    if not rows:
        rows = "<tr><td colspan='6' style='text-align:center;color:#666'>Sin símbolos registrados</td></tr>"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>PitCode - Tabla de Símbolos</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', sans-serif; background: #0f0f0f; color: #e0e0e0; padding: 30px; }}
    h1 {{ font-size: 2rem; color: #e10600; border-bottom: 3px solid #e10600; padding-bottom: 10px; margin-bottom: 25px; letter-spacing: 2px; }}
    .nav {{ margin-bottom: 20px; }}
    .nav a {{ color: #569cd6; text-decoration: none; font-size: 13px; }}
    .nav a:hover {{ color: white; }}
    .summary {{ background: #1a1a1a; border-left: 4px solid #e10600; padding: 12px 18px; margin-bottom: 20px; border-radius: 0 6px 6px 0; font-size: 0.9rem; color: #bbb; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
    th {{ background: #e10600; color: white; padding: 10px 14px; text-align: left; letter-spacing: 1px; font-size: 0.8rem; text-transform: uppercase; }}
    td {{ padding: 8px 14px; border-bottom: 1px solid #2a2a2a; }}
    tr:nth-child(even) td {{ background: #1a1a1a; }}
    tr:hover td {{ background: #222; }}
    footer {{ margin-top: 40px; color: #444; font-size: 0.8rem; text-align: center; }}
  </style>
</head>
<body>
  <div class="nav"><a href="index.html">← Volver al inicio</a></div>
  <h1>PitCode — Tabla de Símbolos</h1>
  <div class="summary">
    Símbolos registrados: <strong>{len(all_symbols)}</strong>
  </div>
  <table>
    <thead>
      <tr>
        <th>Nombre</th><th>Tipo</th><th>Rol</th>
        <th>Ámbito</th><th>Línea</th><th>Columna</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
  <footer>PitCode Compiler · Compiladores 2026 · Fase I</footer>
</body>
</html>"""

    with open(os.path.join(REPORTS_DIR, "reporte_simbolos.html"), "w", encoding="utf-8") as f:
        f.write(html)

def abrir_reporte(archivo="index.html"):
    ruta = os.path.join(REPORTS_DIR, archivo)
    webbrowser.open(f"file://{ruta}")

