# ============================================================
#   PitCode - Script de Demostración de Errores
#   Compiladores 2026 - Fase II
#   Uso: python demo_errores.py
# ============================================================

import os
import sys
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from lexer    import analyze, read_file
from parser   import parse
from semantic import SemanticAnalyzer
from codegen  import ThreeAddressGenerator, CppTranslator
import html_gen

ARCHIVOS = {
    '1': ('Errores Léxicos',     'ejemplo_lexicos.pitcode'),
    '2': ('Errores Sintácticos', 'ejemplo_sintacticos.pitcode'),
    '3': ('Errores Semánticos',  'ejemplo_semanticos.pitcode'),
}

SEP  = "=" * 62
SEP2 = "-" * 62


def compilar(source_file):
    source_code = read_file(source_file)

    # ── Léxico ──
    token_list, lex_errors = analyze(source_code)

    # ── Sintáctico ──
    if lex_errors:
        ast, syn_errors = None, []
    else:
        ast, syn_errors = parse(source_code)

    # ── Semántico ──
    sem_errors, sem_warnings = [], []
    hay_bloqueantes = bool(lex_errors) or bool(syn_errors)

    if not hay_bloqueantes and ast:
        sem = SemanticAnalyzer()
        sem.analyze(ast)
        sem_errors   = sem.get_errors()
        sem_warnings = sem.get_warnings()

    hay_bloqueantes = hay_bloqueantes or bool(sem_errors)
    todos_errores   = lex_errors + syn_errors + sem_errors + sem_warnings

    # ── Código (solo si no hay errores bloqueantes) ──
    code_3d_str, cpp_code = "", ""
    if not hay_bloqueantes and ast:
        gen = ThreeAddressGenerator()
        gen.generate(ast)
        code_3d_str = gen.get_code_string()
        reports_dir = os.path.join(BASE_DIR, 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        translator = CppTranslator()
        cpp_code   = translator.save_to_file(ast, os.path.join(reports_dir, 'output.cpp'))

    # ── Reportes HTML ──
    tokens_para_reporte = [] if hay_bloqueantes else token_list
    html_gen.generar_reporte_tokens(tokens_para_reporte)
    html_gen.generar_reporte_errores(todos_errores)
    html_gen.generar_reporte_simbolos(ast, source_code)
    if not hay_bloqueantes and code_3d_str:
        html_gen.generar_reporte_codigo(code_3d_str, cpp_code)
    html_gen.generar_index(hay_errores=hay_bloqueantes, hay_codigo=not hay_bloqueantes)

    return token_list, lex_errors, syn_errors, sem_errors, sem_warnings, hay_bloqueantes


def mostrar_resultado(nombre, token_list, lex_errors, syn_errors,
                      sem_errors, sem_warnings, hay_bloqueantes):

    total = len(lex_errors) + len(syn_errors) + len(sem_errors)
    estado = "CON ERRORES" if hay_bloqueantes else "EXITOSO"
    print(f"\n  Estado  : {estado}")
    print(f"  Tokens  : {len(token_list)}")
    print(f"  Léxicos : {len(lex_errors)}")
    print(f"  Sintáct.: {len(syn_errors)}")
    print(f"  Semánt. : {len(sem_errors)}")
    if sem_warnings:
        print(f"  Adverte.: {len(sem_warnings)}")

    if lex_errors:
        print(f"\n  {SEP2}")
        print("  ERRORES LÉXICOS:")
        for e in lex_errors:
            print(f"    Línea {e['line']:>3}, Col {e['column']:>3} | {e['message']}")

    if syn_errors:
        print(f"\n  {SEP2}")
        print("  ERRORES SINTÁCTICOS:")
        for e in syn_errors:
            print(f"    Línea {e['line']:>3}, Col {e['column']:>3} | {e['message']}")

    if sem_errors:
        print(f"\n  {SEP2}")
        print("  ERRORES SEMÁNTICOS:")
        for e in sem_errors:
            print(f"    Línea {e['line']:>3}, Col {e['column']:>3} | {e['message']}")

    if sem_warnings:
        print(f"\n  {SEP2}")
        print("  ADVERTENCIAS:")
        for w in sem_warnings:
            print(f"    Línea {w['line']:>3}, Col {w['column']:>3} | {w['message']}")

    if not hay_bloqueantes:
        print(f"\n  {SEP2}")
        print("  Código C++ generado en reports/output.cpp")


def menu():
    while True:
        print(f"\n{SEP}")
        print("  PitCode — Demo de Errores | Compiladores 2026")
        print(SEP)
        print("  Seleccione el tipo de error a demostrar:\n")
        for k, (nombre, archivo) in ARCHIVOS.items():
            ruta = os.path.join(BASE_DIR, archivo)
            existe = "✓" if os.path.exists(ruta) else "✗"
            print(f"    [{k}] {existe} {nombre:<25} ({archivo})")
        print("    [4]   Abrir reportes en navegador")
        print("    [0]   Salir")
        print(SEP2)

        opcion = input("  Opción: ").strip()

        if opcion == '0':
            print("\n  Cerrando demo. ¡Hasta luego!\n")
            break

        elif opcion == '4':
            ruta_index = os.path.join(BASE_DIR, 'reports', 'index.html')
            if os.path.exists(ruta_index):
                webbrowser.open(f"file://{ruta_index}")
                print("  Abriendo reportes en el navegador...")
            else:
                print("  No hay reportes generados aún. Ejecute primero una opción 1-3.")

        elif opcion in ARCHIVOS:
            nombre, archivo = ARCHIVOS[opcion]
            ruta = os.path.join(BASE_DIR, archivo)

            if not os.path.exists(ruta):
                print(f"\n  ERROR: No se encontró el archivo '{archivo}'")
                print(f"  Asegúrese de que esté en: {BASE_DIR}")
                continue

            print(f"\n{SEP}")
            print(f"  Compilando: {archivo}")
            print(f"  Tipo demo : {nombre}")
            print(SEP)

            # Mostrar el contenido del archivo
            print("\n  CÓDIGO FUENTE:")
            print(f"  {SEP2}")
            with open(ruta, encoding='utf-8') as f:
                for i, linea in enumerate(f, 1):
                    print(f"  {i:>3} | {linea}", end='')
            print(f"\n  {SEP2}")

            # Compilar
            resultados = compilar(ruta)
            mostrar_resultado(nombre, *resultados)

            print(f"\n  Reportes HTML actualizados en: reports/")
            input("\n  Presione ENTER para continuar...")

        else:
            print("  Opción no válida. Intente de nuevo.")


if __name__ == '__main__':
    # Suprimir warnings de PLY en la salida
    import warnings
    warnings.filterwarnings('ignore')
    menu()
