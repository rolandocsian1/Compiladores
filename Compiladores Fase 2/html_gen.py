# ============================================================
#   PitCode - Generador de Reportes HTML
#   Compiladores 2026 - Fase I & II
# ============================================================

import os
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

# ─────────────────────────────────────────────
#  DICCIONARIO DE SUGERENCIAS
# ─────────────────────────────────────────────
SUGERENCIAS = {
    'CORNER':('corner','Paréntesis izquierdo ('),'APEX':('apex','Paréntesis derecho )'),
    'GARAGE':('garage','Llave izquierda {'),'READY':('ready','Llave derecha }'),
    'GRID':('grid','Corchete izquierdo ['),'ENDGRID':('endgrid','Corchete derecho ]'),
    'STOP':('stop','Fin de sentencia ;'),'ALSO':('also','Separador ,'),
    'MARSHALL':('marshall','Dos puntos :'),
    'SETUP':('setup','Asignación ='),'PITSTOW':('pitstow','Asignación suma +='),
    'PITGAP':('pitgap','Asignación resta -='),'PITERS':('piters','Asignación multiplicación *='),
    'PITSTINT':('pitstint','Asignación división /='),
    'TOW':('Tow','Suma +'),'GAP':('Gap','Resta -'),'ERS':('ERS','Multiplicación *'),
    'STINT':('Stint','División /'),'FUEL_DELTA':('Fuel_Delta','Módulo %'),
    'DEAD_HEAT':('DEAD_HEAT','Igual que =='),'OUTLAP':('Outlap','Mayor que >'),
    'UNDERCUT':('UNDERCUT','Menor que <'),'OVERCUT':('OVERCUT','Diferente de !='),
    'UNDEREQ':('undereq','Menor o igual <='),'OVEREQ':('overeq','Mayor o igual >='),
    'SAFETY':('safety','AND lógico &&'),'OVERTAKE':('overtake','OR lógico ||'),
    'REVERSE':('reverse','NOT lógico !'),'BOTH_TYRES':('BOTH_TYRES','AND lógico &&'),
    'EITHER_TYRE':('EITHER_TYRE','OR lógico ||'),'REVERSE_GRID':('REVERSE_GRID','NOT lógico !'),
    'FASTLAP':('fastlap','Incremento ++'),'DEGRADATION':('degradation','Decremento --'),
    'SLIPSTREAM':('slipstream','Puntero *'),'POSITION':('position','Dirección &'),
    'GREEN_LIGHT':('green_light','Verdadero (true)'),'RED_LIGHT':('red_light','Falso (false)'),
    'LAP':('lap','Tipo entero (int)'),'SPLIT':('split','Tipo decimal (float)'),
    'PITBOARD':('pitboard','Tipo carácter (char)'),'YELLOW_FLAG':('yellow_flag','Tipo booleano (bool)'),
    'RADIO':('radio','Tipo cadena (string)'),
    'STRATEGY_CHECK':('strategy_check','Condicional (if)'),'STAY_OUT':('stay_out','Alternativa (else)'),
    'PUSH':('push','Ciclo while'),'BOX':('box','Inicio do-while'),
    'FORMATION_LAP':('formation_lap','Ciclo for'),'GAP_CHECK':('gap_check','Switch'),
    'PITWALL':('pitwall','Switch'),'SECTOR':('sector','Caso (case)'),
    'NO_DATA':('no_data','Caso por defecto (default)'),
    'STRATEGY':('strategy','Definición de función'),'NEUTRO':('neutro','Tipo void'),
    'PODIO':('podio','Retorno (return)'),'RACE_START':('race_start','Función principal (main)'),
    'BOX_BOX':('box_box','Break'),'DRS':('drs','Continue'),
    'CHECKERED_FLAG':('checkered_flag','Fin del programa'),
    'BROADCAST':('broadcast','Salida (print)'),'TELEMETRY':('telemetry','Entrada (input/scanf)'),
    'INT_LITERAL':('número entero','Ej: 5, 10, 100'),
    'FLOAT_LITERAL':('número decimal','Ej: 3.14, 0.5'),
    'STRING_LITERAL':('transmission...transmission','Cadena de texto'),
    'CHAR_LITERAL':('signal...signal','Carácter'),
    'DNF':('dnf','Valor nulo (null)'),'VSC':('vsc','Constante (const)'),
    'ID':('identificador','Nombre de variable o función'),
}

def _get_sugerencia(error):
    token = error.get('token', '')
    value = error.get('value', '')
    err_type = error.get('type', '')

    if err_type == 'Léxico':
        char = error.get('char', '')
        simbolos = {
            '(':'Use corner','## )':'Use apex','{':'Use garage','}':'Use ready',
            '[':'Use grid',']':'Use endgrid',';':'Use stop',',':'Use also',
            ':':'Use marshall','=':'Use setup','+':'Use Tow','-':'Use Gap',
            '*':'Use ERS','/':'Use Stint','%':'Use Fuel_Delta',
            '!':'Use reverse','&':'Use position',
            '@':'Carácter no válido','$':'Carácter no válido',
            '^':'Carácter no válido','~':'Carácter no válido',
            '`':'Carácter no válido','\\':'Carácter no válido',
            '|':'Use overtake para OR lógico',
        }
        return simbolos.get(char, f"Carácter '{char}' no es parte del lenguaje PitCode")

    if err_type == 'Sintáctico':
        if token == 'EOF':
            cierre = SUGERENCIAS.get('READY')
            apertura = SUGERENCIAS.get('GARAGE')

            if cierre and apertura:
                return f"Falta cerrar bloque: {apertura[0]} → {apertura[1]} ... {cierre[0]} → {cierre[1]}"
            else:
                return "Falta cerrar bloque con 'ready'"

        info = SUGERENCIAS.get(token)
        if info:
            return f"{info[0]} → {info[1]}"

        palabras = {
            'true':'Use green_light','false':'Use red_light',
            'if':'Use strategy_check','else':'Use stay_out',
            'while':'Use push','for':'Use formation_lap',
            'int':'Use lap','float':'Use split','char':'Use pitboard',
            'bool':'Use yellow_flag','string':'Use radio',
            'return':'Use podio','break':'Use box_box','continue':'Use drs',
            'switch':'Use pitwall','void':'Use neutro','null':'Use dnf',
            'print':'Use broadcast','main':'Use race_start','const':'Use vsc',
        }

        if value in palabras:
            return palabras[value]

        return f"Revise la sintaxis cerca de '{value}'"

    if err_type == 'Semántico' or err_type == 'Advertencia':
        return 'Verifique tipos de datos y declaraciones'

    return ''


def _ensure_reports():
    os.makedirs(REPORTS_DIR, exist_ok=True)


# ─────────────────────────────────────────────
#  INDEX.HTML
# ─────────────────────────────────────────────

def generar_index(hay_errores=False, hay_codigo=False):
    _ensure_reports()

    if hay_errores:
        boton_tokens = """<span style="display:inline-block;padding:15px 30px;background-color:#3a3a3a;color:#666;border-radius:3px;font-weight:bold;border:1px solid #555;cursor:not-allowed;">Bitacora de Tokens (no disponible)</span>"""
        boton_codigo = """<span style="display:inline-block;padding:15px 30px;background-color:#3a3a3a;color:#666;border-radius:3px;font-weight:bold;border:1px solid #555;cursor:not-allowed;">Código Generado (no disponible)</span>"""
    else:
        boton_tokens = '<a href="reporte_tokens.html">Bitacora de Tokens</a>'
        boton_codigo = '<a href="reporte_codigo.html">Código 3D / C++</a>' if hay_codigo else '<a href="reporte_codigo.html">Código 3D / C++</a>'

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8"><title>PitCode - Reportes</title>
    <style>
        body {{ background-color:#1e1e1e;color:#d4d4d4;font-family:Consolas,monospace;text-align:center;padding:50px; }}
        h1 {{ color:#569cd6;font-size:48px;margin-bottom:10px; }}
        p {{ color:#6a9955;margin-bottom:40px; }}
        .botones {{ display:flex;gap:15px;justify-content:center;flex-wrap:wrap; }}
        a {{ display:inline-block;padding:15px 30px;background-color:#264f78;color:#d4d4d4;text-decoration:none;border-radius:3px;font-weight:bold;border:1px solid #569cd6; }}
        a:hover {{ background-color:#094771;color:#ffffff; }}
    </style>
</head>
<body>
    <h1>PITCODE</h1>
    <p>// Compiladores 2026 - Fase I & II</p>
    <div class="botones">
        {boton_tokens}
        <a href="reporte_errores.html">Errores</a>
        <a href="reporte_simbolos.html">Tabla de Simbolos</a>
        {boton_codigo}
    </div>
</body>
</html>"""
    with open(os.path.join(REPORTS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)


# ─────────────────────────────────────────────
#  REPORTE DE TOKENS
# ─────────────────────────────────────────────

def generar_reporte_tokens(tokens_list):
    _ensure_reports()

    if not tokens_list:
        html = """<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>PitCode - Tokens</title>
<style>*{box-sizing:border-box;margin:0;padding:0}body{font-family:'Segoe UI',sans-serif;background:#0f0f0f;color:#e0e0e0;padding:30px}h1{font-size:2rem;color:#e10600;border-bottom:3px solid #e10600;padding-bottom:10px;margin-bottom:25px}.nav{margin-bottom:20px}.nav a{color:#569cd6;text-decoration:none;font-size:13px}.no-tokens{background:#3a1a1a;border:1px solid #e10600;border-radius:6px;padding:20px 24px;color:#ef9a9a;font-size:1rem;margin-top:20px}footer{margin-top:40px;color:#444;font-size:0.8rem;text-align:center}</style></head><body>
<div class="nav"><a href="index.html">&larr; Volver al inicio</a></div>
<h1>PitCode &mdash; Reporte de Tokens</h1>
<div class="no-tokens">&#9888; No se generaron tokens debido a errores encontrados.<br><br>Revise el <a href="reporte_errores.html" style="color:#4fc3f7">Reporte de Errores</a>.</div>
<footer>PitCode Compiler &middot; Compiladores 2026</footer></body></html>"""
        with open(os.path.join(REPORTS_DIR, "reporte_tokens.html"), "w", encoding="utf-8") as f:
            f.write(html)
        return

    RESERVADAS = {'LAP','SPLIT','PITBOARD','YELLOW_FLAG','RADIO','STRATEGY_CHECK','STAY_OUT','PUSH','BOX','FORMATION_LAP','GAP_CHECK','SECTOR','NO_DATA','BOX_BOX','DRS','PITWALL','STRATEGY','PODIO','NEUTRO','RACE_START','BROADCAST','TELEMETRY','DNF','VSC','PADDOCK','RED_FLAG','BLUE_FLAG','BLACK_FLAG','CHECKERED_FLAG','GREEN_LIGHT','RED_LIGHT'}
    OPERADORES = {'TOW','GAP','ERS','STINT','FUEL_DELTA','DEAD_HEAT','OUTLAP','UNDERCUT','OVERCUT','UNDEREQ','OVEREQ','BOTH_TYRES','EITHER_TYRE','REVERSE_GRID','SAFETY','OVERTAKE','REVERSE','SETUP','PITSTOW','PITGAP','PITERS','PITSTINT','FASTLAP','DEGRADATION','SLIPSTREAM','POSITION'}
    LITERALES = {'INT_LITERAL','FLOAT_LITERAL','STRING_LITERAL','CHAR_LITERAL'}
    DELIMITADORES = {'CORNER','APEX','GARAGE','READY','GRID','ENDGRID','STOP','ALSO','MARSHALL'}

    def get_cat(tt):
        if tt in RESERVADAS: return 'Palabra Reservada'
        if tt in OPERADORES: return 'Operador'
        if tt in LITERALES: return 'Literal'
        if tt in DELIMITADORES: return 'Delimitador'
        if tt == 'ID': return 'Identificador'
        return 'Otro'

    CAT_COLORS = {'Palabra Reservada':('#e10600','#fff'),'Operador':('#ff8c00','#fff'),'Literal':('#7b5ea7','#fff'),'Identificador':('#2e7d32','#fff'),'Delimitador':('#1a5276','#fff'),'Otro':('#444','#ccc')}

    conteos = {}
    for t in tokens_list:
        c = get_cat(t['token'])
        conteos[c] = conteos.get(c, 0) + 1

    stat_cards = ""
    for cat, count in sorted(conteos.items()):
        bg, _ = CAT_COLORS.get(cat, ('#444','#ccc'))
        stat_cards += f'<div class="stat-card" style="border-top:3px solid {bg}"><div class="stat-num" style="color:{bg}">{count}</div><div class="stat-label">{cat}</div></div>'

    rows = ""
    for t in tokens_list:
        cat = get_cat(t['token'])
        bg, fg = CAT_COLORS.get(cat, ('#444','#ccc'))
        badge = f'<span style="background:{bg};color:{fg};padding:2px 8px;border-radius:3px;font-size:0.75rem;font-weight:bold">{cat}</span>'
        # Obtener significado real del token
        info = SUGERENCIAS.get(t["token"], None)
        igualdad = info[1] if info else ""

        rows += f'''
        <tr data-cat="{cat}">
            <td class="tag-token">{t["token"]}</td>
            <td class="tag-lexeme">{t["lexeme"]}</td>
            <td style="color:#ffd54f;font-family:monospace">{igualdad}</td>
            <td>{badge}</td>
            <td class="tag-line">{t["line"]}</td>
            <td class="tag-line">{t["column"]}</td>
        </tr>
        '''

    total = len(tokens_list)
    html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>PitCode - Tokens</title>
<style>*{{box-sizing:border-box;margin:0;padding:0}}body{{font-family:'Segoe UI',sans-serif;background:#0f0f0f;color:#e0e0e0;padding:30px}}h1{{font-size:2rem;color:#e10600;border-bottom:3px solid #e10600;padding-bottom:10px;margin-bottom:25px}}h2{{font-size:1.2rem;color:#ff8c00;margin:25px 0 12px}}.nav{{margin-bottom:20px}}.nav a{{color:#569cd6;text-decoration:none;font-size:13px}}.summary{{background:#1a1a1a;border-left:4px solid #e10600;padding:12px 18px;margin-bottom:20px;border-radius:0 6px 6px 0;font-size:0.9rem;color:#bbb}}.stats-row{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:25px}}.stat-card{{background:#1a1a1a;padding:14px 20px;border-radius:6px;min-width:110px;text-align:center}}.stat-num{{font-size:1.8rem;font-weight:bold}}.stat-label{{font-size:0.75rem;color:#888;margin-top:4px;text-transform:uppercase}}.filter-bar{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}}.filter-btn{{background:transparent;border:1px solid #444;color:#aaa;padding:5px 14px;border-radius:4px;cursor:pointer;font-size:0.82rem}}.filter-btn:hover{{border-color:#e10600;color:white}}.filter-btn.active{{background:#e10600;border-color:#e10600;color:white}}.search-box{{width:100%;padding:8px 14px;background:#1a1a1a;border:1px solid #333;border-radius:4px;color:#ccc;font-size:0.9rem;margin-bottom:12px}}.search-box:focus{{outline:none;border-color:#e10600}}table{{width:100%;border-collapse:collapse;font-size:0.9rem}}th{{background:#e10600;color:white;padding:10px 14px;text-align:left;font-size:0.8rem;text-transform:uppercase}}td{{padding:8px 14px;border-bottom:1px solid #2a2a2a}}tr:nth-child(even) td{{background:#1a1a1a}}tr:hover td{{background:#222}}.tag-token{{color:#4fc3f7;font-weight:bold}}.tag-lexeme{{color:#a5d6a7;font-family:monospace}}.tag-line{{color:#888;font-family:monospace}}footer{{margin-top:40px;color:#444;font-size:0.8rem;text-align:center}}</style></head><body>
<div class="nav"><a href="index.html">&larr; Volver al inicio</a></div>
<h1>PitCode &mdash; Reporte de Tokens</h1>
<div class="summary">Tokens: <strong>{total}</strong></div>
<h2>Resumen</h2><div class="stats-row">{stat_cards}</div>
<h2>Tokens <span style="background:#2e7d32;color:white;padding:2px 10px;border-radius:4px;font-size:0.8rem">{total}</span></h2>
<input class="search-box" type="text" id="sb" placeholder="Buscar..." onkeyup="ff()">
<div class="filter-bar"><button class="filter-btn active" onclick="fc('',this)">Todos</button><button class="filter-btn" onclick="fc('Palabra Reservada',this)">Reservadas</button><button class="filter-btn" onclick="fc('Operador',this)">Operadores</button><button class="filter-btn" onclick="fc('Literal',this)">Literales</button><button class="filter-btn" onclick="fc('Identificador',this)">Identificadores</button><button class="filter-btn" onclick="fc('Delimitador',this)">Delimitadores</button></div>
<table id="tt"><thead><tr><th>Token</th><th>Lexema</th><th>Significado</th><th>Categoría</th><th>Línea</th><th>Columna</th></tr></thead><tbody>{rows}</tbody></table>
<script>let cc='';function fc(c,b){{cc=c;document.querySelectorAll('.filter-btn').forEach(x=>x.classList.remove('active'));b.classList.add('active');af()}}function ff(){{af()}}function af(){{const s=document.getElementById('sb').value.toLowerCase();document.querySelectorAll('#tt tbody tr').forEach(r=>{{r.style.display=(!cc||r.dataset.cat===cc)&&(!s||r.innerText.toLowerCase().includes(s))?'':'none'}})}}</script>
<footer>PitCode Compiler &middot; Compiladores 2026</footer></body></html>"""
    with open(os.path.join(REPORTS_DIR, "reporte_tokens.html"), "w", encoding="utf-8") as f:
        f.write(html)


# ─────────────────────────────────────────────
#  REPORTE DE ERRORES (léxicos + sintácticos + semánticos)
# ─────────────────────────────────────────────

def generar_reporte_errores(errores_list):
    _ensure_reports()

    total = len(errores_list)
    lexicos = sum(1 for e in errores_list if e.get('type') == 'Léxico')
    sintacticos = sum(1 for e in errores_list if e.get('type') == 'Sintáctico')
    semanticos = sum(1 for e in errores_list if e.get('type') in ('Semántico', 'Advertencia'))

    if total == 0:
        contenido = '<div class="no-errors">Sin errores lexicos, sintacticos ni semanticos.</div>'
    else:
        filas = ""
        for i, e in enumerate(errores_list, 1):
            tipo = e.get('type', 'Desconocido')
            mensaje = e.get('message', str(e))
            linea = e.get('line', 0)
            col = e.get('column', 0)
            sug = _get_sugerencia(e)
            tipo_class = 'tag-error' if tipo != 'Advertencia' else 'tag-warn'
            filas += f'<tr><td class="tag-line">{i}</td><td class="{tipo_class}">{tipo}</td><td>{mensaje}</td><td class="tag-line">{linea}</td><td class="tag-line">{col}</td><td class="tag-sug">{sug}</td></tr>'
        contenido = f"""<table><thead><tr><th>#</th><th>Tipo</th><th>Mensaje</th><th>Línea</th><th>Col</th><th>Sugerencia</th></tr></thead><tbody>{filas}</tbody></table>"""

    html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>PitCode - Errores</title>
<style>*{{box-sizing:border-box;margin:0;padding:0}}body{{font-family:'Segoe UI',sans-serif;background:#0f0f0f;color:#e0e0e0;padding:30px}}h1{{font-size:2rem;color:#e10600;border-bottom:3px solid #e10600;padding-bottom:10px;margin-bottom:25px}}h2{{font-size:1.2rem;color:#ff8c00;margin:30px 0 12px}}.nav{{margin-bottom:20px}}.nav a{{color:#569cd6;text-decoration:none;font-size:13px}}.badge{{display:inline-block;background:#e10600;color:white;border-radius:4px;padding:2px 10px;font-size:0.8rem;margin-left:8px}}.badge.ok{{background:#2e7d32}}.badge.warn{{background:#ff8c00}}table{{width:100%;border-collapse:collapse;font-size:0.9rem;margin-bottom:20px}}th{{background:#e10600;color:white;padding:10px 14px;text-align:left;font-size:0.8rem;text-transform:uppercase}}td{{padding:8px 14px;border-bottom:1px solid #2a2a2a}}tr:nth-child(even) td{{background:#1a1a1a}}tr:hover td{{background:#222}}.tag-error{{color:#ef9a9a;font-weight:bold}}.tag-warn{{color:#ffcc80;font-weight:bold}}.tag-line{{color:#888;font-family:monospace}}.tag-sug{{color:#81c784;font-style:italic;font-size:0.85rem}}.no-errors{{background:#1b3a1f;border:1px solid #2e7d32;border-radius:6px;padding:16px 20px;color:#a5d6a7}}.summary{{background:#1a1a1a;border-left:4px solid #e10600;padding:12px 18px;margin-bottom:20px;border-radius:0 6px 6px 0;font-size:0.9rem;color:#bbb}}footer{{margin-top:40px;color:#444;font-size:0.8rem;text-align:center}}</style></head><body>
<div class="nav"><a href="index.html">&larr; Volver al inicio</a></div>
<h1>PitCode &mdash; Reporte de Errores</h1>
<div class="summary">Léxicos: <strong>{lexicos}</strong> &nbsp;|&nbsp; Sintácticos: <strong>{sintacticos}</strong> &nbsp;|&nbsp; Semánticos: <strong>{semanticos}</strong> &nbsp;|&nbsp; Total: <strong>{total}</strong></div>
<h2>Errores Encontrados <span class="badge {'ok' if total==0 else 'warn'}">{total}</span></h2>
{contenido}
<footer>PitCode Compiler &middot; Compiladores 2026</footer></body></html>"""
    with open(os.path.join(REPORTS_DIR, "reporte_errores.html"), "w", encoding="utf-8") as f:
        f.write(html)


# ─────────────────────────────────────────────
#  REPORTE DE TABLA DE SÍMBOLOS
# ─────────────────────────────────────────────

def generar_reporte_simbolos(ast, source_code):
    _ensure_reports()
    scopes = [{}]; scope_names = ['global']; all_symbols = []

    def current_scope(): return scope_names[-1]
    def enter_scope(name): scopes.append({}); scope_names.append(name)
    def exit_scope():
        if len(scopes) > 1: scopes.pop(); scope_names.pop()

    def insert(name, dtype, role, line, lexpos, value=None):
        line_start = source_code.rfind('\n', 0, lexpos) + 1
        col = (lexpos - line_start) + 1 if lexpos > 0 else 0

        entry = {'name':name,'type':dtype,'role':role,'scope':current_scope(),'line':line,'column':col, 'value': value}
        scopes[-1][name] = entry; all_symbols.append(entry)

    def walk(node):
        if not isinstance(node, tuple): return
        kind = node[0]
        if kind == 'program':
            for f in node[1]: walk(f)
            walk(node[2])
            for f in node[3]: walk(f)
        elif kind == 'func_def':
            insert(node[2], node[1], 'función', node[5] if len(node)>5 else 0, node[6] if len(node)>6 else 0)
            enter_scope(node[2])
            for p in node[3]: insert(p[2], p[1], 'parámetro', p[3] if len(p)>3 else 0, p[4] if len(p)>4 else 0)
            walk(node[4]); exit_scope()
        elif kind == 'race_start':
            for item in node[1]: walk(item)
        elif kind in ('declare','declare_const'):
            value = None

            if node[3]:
                if isinstance(node[3], tuple) and node[3][0] == 'literal':
                    value = node[3][1]
                else:
                    value = 'expresión'

            insert(node[2], node[1], 'variable', node[4] if len(node)>4 else 0, node[5] if len(node)>5 else 0, value)

            if node[3]: 
                walk(node[3])
        elif kind == 'block':
            for item in node[1]: walk(item)
        elif kind in ('if','if_else'):
            for child in node[1:]:
                if child: walk(child)
        elif kind == 'while':
            walk(node[1]); enter_scope('while'); walk(node[2]); exit_scope()
        elif kind == 'do_while':
            enter_scope('do_while'); walk(node[1]); exit_scope(); walk(node[2])
        elif kind == 'for':
            enter_scope('for_loop')
            if node[1]: walk(node[1])
            if node[2]: walk(node[2])
            if node[3]: walk(node[3])
            walk(node[4]); exit_scope()
        elif kind == 'switch':
            walk(node[1])
            for c in node[2]: walk(c)
        elif kind in ('case','default'):
            for child in node[1:]:
                if isinstance(child, list):
                    for item in child: walk(item)
                elif child: walk(child)
        elif kind in ('return','broadcast','expr_stmt'):
            if len(node)>1 and node[1]: walk(node[1])
        elif kind == 'binop': walk(node[2]); walk(node[3])
        elif kind in ('uminus','not'): walk(node[1])
        elif kind == 'assign': 
            var_name = node[1]
            value = None

            if isinstance(node[2], tuple) and node[2][0] == 'literal':
                value = node[2][1]
            else:
                value = 'expresion'

            for scope in reversed(scopes):
                if var_name in scope:
                    scope[var_name]['value'] = value
                    break

            walk(node[2])
        elif kind == 'call':
            for arg in node[2]: walk(arg)

    if ast: walk(ast)

    rows = ""
    for s in all_symbols:
        rows += f"""
        <tr>
            <td style="color:#a5d6a7;font-family:monospace">{s.get("name","-")}</td>
            <td style="color:#ce93d8">{s.get("type","-")}</td>
            <td style="color:#ffcc80">{s.get("role","-")}</td>
            <td style="color:#80deea">{s.get("scope","-")}</td>
            <td style="color:#ffd54f">{s.get("value","-")}</td>
            <td style="color:#888;font-family:monospace">{s.get("line","-")}</td>
            <td style="color:#888;font-family:monospace">{s.get("column","-")}</td>
        </tr>
    
        """
    if not rows:
        rows = '<tr><td colspan="7" style="text-align:center;color:#666">Sin símbolos registrados</td></tr>'

    html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>PitCode - Símbolos</title>
<style>*{{box-sizing:border-box;margin:0;padding:0}}body{{font-family:'Segoe UI',sans-serif;background:#0f0f0f;color:#e0e0e0;padding:30px}}h1{{font-size:2rem;color:#e10600;border-bottom:3px solid #e10600;padding-bottom:10px;margin-bottom:25px}}.nav{{margin-bottom:20px}}.nav a{{color:#569cd6;text-decoration:none;font-size:13px}}.summary{{background:#1a1a1a;border-left:4px solid #e10600;padding:12px 18px;margin-bottom:20px;border-radius:0 6px 6px 0;font-size:0.9rem;color:#bbb}}table{{width:100%;border-collapse:collapse;font-size:0.9rem}}th{{background:#e10600;color:white;padding:10px 14px;text-align:left;font-size:0.8rem;text-transform:uppercase}}td{{padding:8px 14px;border-bottom:1px solid #2a2a2a}}tr:nth-child(even) td{{background:#1a1a1a}}tr:hover td{{background:#222}}footer{{margin-top:40px;color:#444;font-size:0.8rem;text-align:center}}</style></head><body>
<div class="nav"><a href="index.html">&larr; Volver al inicio</a></div>
<h1>PitCode &mdash; Tabla de Símbolos</h1>
<div class="summary">Símbolos: <strong>{len(all_symbols)}</strong></div>
<table><thead><tr><th>Nombre</th><th>Tipo</th><th>Rol</th><th>Ámbito</th><th>Valor</th><th>Línea</th><th>Columna</th></tr></thead><tbody>{rows}</tbody></table>
<footer>PitCode Compiler &middot; Compiladores 2026</footer></body></html>"""
    with open(os.path.join(REPORTS_DIR, "reporte_simbolos.html"), "w", encoding="utf-8") as f:
        f.write(html)


# ─────────────────────────────────────────────
#  REPORTE DE CÓDIGO 3D + C++
# ─────────────────────────────────────────────

def generar_reporte_codigo(code_3d_str, cpp_code, cpp_filename="output.cpp"):
    _ensure_reports()

    html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>PitCode - Código Generado</title>
<style>*{{box-sizing:border-box;margin:0;padding:0}}body{{font-family:'Segoe UI',sans-serif;background:#0f0f0f;color:#e0e0e0;padding:30px}}h1{{font-size:2rem;color:#e10600;border-bottom:3px solid #e10600;padding-bottom:10px;margin-bottom:25px}}h2{{font-size:1.2rem;color:#ff8c00;margin:30px 0 12px}}.nav{{margin-bottom:20px}}.nav a{{color:#569cd6;text-decoration:none;font-size:13px}}.code-block{{background:#1a1a1a;border:1px solid #333;border-radius:6px;padding:16px 20px;font-family:Consolas,monospace;font-size:0.85rem;white-space:pre;overflow-x:auto;line-height:1.6;margin-bottom:20px}}.code-3d{{color:#4fc3f7}}.code-cpp{{color:#a5d6a7}}.summary{{background:#1a1a1a;border-left:4px solid #e10600;padding:12px 18px;margin-bottom:20px;border-radius:0 6px 6px 0;font-size:0.9rem;color:#bbb}}.badge{{display:inline-block;background:#2e7d32;color:white;border-radius:4px;padding:2px 10px;font-size:0.8rem;margin-left:8px}}.download{{display:inline-block;padding:8px 20px;background:#264f78;color:#d4d4d4;text-decoration:none;border-radius:4px;font-weight:bold;border:1px solid #569cd6;margin-top:10px}}.download:hover{{background:#094771;color:white}}footer{{margin-top:40px;color:#444;font-size:0.8rem;text-align:center}}</style></head><body>
<div class="nav"><a href="index.html">&larr; Volver al inicio</a></div>
<h1>PitCode &mdash; Código Generado</h1>
<div class="summary">Código de tres direcciones e instrucciones &nbsp;|&nbsp; Traducción funcional a C++</div>

<h2>Código de Tres Direcciones <span class="badge">{code_3d_str.count(chr(10)) + 1} instrucciones</span></h2>
<div class="code-block code-3d">{code_3d_str}</div>

<h2>Traducción a C++ <span class="badge">Funcional</span></h2>
<div class="code-block code-cpp">{cpp_code}</div>
<a class="download" href="{cpp_filename}" download>Descargar {cpp_filename}</a>

<footer>PitCode Compiler &middot; Compiladores 2026 &middot; Fase II</footer></body></html>"""
    with open(os.path.join(REPORTS_DIR, "reporte_codigo.html"), "w", encoding="utf-8") as f:
        f.write(html)


def abrir_reporte(archivo="index.html"):
    ruta = os.path.join(REPORTS_DIR, archivo)
    webbrowser.open(f"file://{ruta}")