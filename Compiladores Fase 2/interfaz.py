# ============================================================
#   PitCode - Interfaz Gráfica
#   Compiladores 2026 - Fase I & II
# ============================================================

import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
import os
import threading
import webbrowser
import html_gen
from lexer import analyze as analizar_codigo
from parser import parse as analizar_sintaxis
from semantic import SemanticAnalyzer
from codegen import ThreeAddressGenerator, CppTranslator

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class LineNumbers(tk.Canvas):
    """Widget de números de línea sincronizado con un CTkTextbox."""

    def __init__(self, parent, textbox, **kwargs):
        super().__init__(parent, **kwargs)
        self.textbox = textbox
        self._text_widget = textbox._textbox
        self.configure(bg="#1a1a1a", bd=0, highlightthickness=0, width=45)

        self._text_widget.bind("<<Modified>>", self._on_modify)
        self._text_widget.bind("<Configure>", self._on_modify)
        self._text_widget.bind("<KeyRelease>", self._on_modify)
        self._text_widget.bind("<MouseWheel>", self._on_scroll)
        self._text_widget.bind("<Button-1>", self._on_modify)
        self._text_widget.configure(yscrollcommand=self._on_text_scroll)
        self.after(100, self.redraw)

    def _on_modify(self, event=None):
        self.after_idle(self.redraw)
        try:
            self._text_widget.edit_modified(False)
        except:
            pass

    def _on_scroll(self, event=None):
        self.after_idle(self.redraw)

    def _on_text_scroll(self, *args):
        self.after_idle(self.redraw)

    def redraw(self):
        self.delete("all")
        first_visible = self._text_widget.index("@0,0")
        first_line = int(first_visible.split(".")[0])
        last_line_idx = self._text_widget.index("end-1c")
        total_lines = int(last_line_idx.split(".")[0])

        i = first_line
        while True:
            dline = self._text_widget.dlineinfo(f"{i}.0")
            if dline is None:
                break
            y = dline[1]
            line_height = dline[3]
            self.create_text(
                40, y + line_height // 2,
                anchor="e", text=str(i),
                fill="#555555", font=("Consolas", 12)
            )
            i += 1
            if i > total_lines:
                break


class PitCodeApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PitCode - Compiladores 2026")
        self.geometry("1100x700")
        self.minsize(900, 600)

        self.ruta_archivo = None
        self.tokens_list  = []
        self.errores_list = []

        self._build_ui()

    # ─────────────────────────────────────────
    #  CONSTRUCCIÓN DE LA INTERFAZ
    # ─────────────────────────────────────────
    def _build_ui(self):

        # ── HEADER ──
        self.header = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.header.pack(fill="x", side="top")
        self.header.pack_propagate(False)

        ctk.CTkLabel(
            self.header, text="PitCode",
            font=ctk.CTkFont(family="Consolas", size=22, weight="bold")
        ).pack(side="left", padx=20, pady=10)

        ctk.CTkLabel(
            self.header, text="// Compiladores 2026 - Fase I & II",
            font=ctk.CTkFont(family="Consolas", size=13), text_color="gray"
        ).pack(side="left", padx=5, pady=10)

        # ── PANEL IZQUIERDO ──
        self.panel_izq = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.panel_izq.pack(fill="y", side="left")
        self.panel_izq.pack_propagate(False)

        self.lbl_archivo = ctk.CTkLabel(
            self.panel_izq, text="Sin archivo",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="gray", wraplength=180
        )
        self.lbl_archivo.pack(padx=10, pady=(20, 5))

        ctk.CTkButton(
            self.panel_izq, text="Cargar archivo .pit",
            command=self._cargar_archivo,
            font=ctk.CTkFont(family="Consolas", size=12), height=35
        ).pack(padx=10, pady=5, fill="x")

        self.btn_analizar = ctk.CTkButton(
            self.panel_izq, text="Analizar",
            command=self._analizar,
            font=ctk.CTkFont(family="Consolas", size=12),
            height=35, state="disabled"
        )
        self.btn_analizar.pack(padx=10, pady=5, fill="x")

        ctk.CTkLabel(
            self.panel_izq, text="── Reportes ──",
            font=ctk.CTkFont(family="Consolas", size=11), text_color="gray"
        ).pack(padx=10, pady=(20, 5))

        self.btn_tokens = ctk.CTkButton(
            self.panel_izq, text="Ver Tokens",
            command=lambda: self._mostrar_tab("tokens"),
            font=ctk.CTkFont(family="Consolas", size=12),
            height=35, state="disabled", fg_color="transparent", border_width=1
        )
        self.btn_tokens.pack(padx=10, pady=5, fill="x")

        self.btn_errores = ctk.CTkButton(
            self.panel_izq, text="Ver Errores",
            command=lambda: self._mostrar_tab("errores"),
            font=ctk.CTkFont(family="Consolas", size=12),
            height=35, state="disabled", fg_color="transparent", border_width=1
        )
        self.btn_errores.pack(padx=10, pady=5, fill="x")

        ctk.CTkLabel(
            self.panel_izq, text="── Navegador ──",
            font=ctk.CTkFont(family="Consolas", size=11), text_color="gray"
        ).pack(padx=10, pady=(20, 5))

        self.btn_browser = ctk.CTkButton(
            self.panel_izq, text="Abrir en Navegador",
            command=self._abrir_navegador,
            font=ctk.CTkFont(family="Consolas", size=12),
            height=35, state="disabled"
        )
        self.btn_browser.pack(padx=10, pady=5, fill="x")

        # ── PANEL PRINCIPAL ──
        self.panel_main = ctk.CTkFrame(self, corner_radius=0)
        self.panel_main.pack(fill="both", expand=True, side="left")

        self.tabview = ctk.CTkTabview(self.panel_main)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_editor  = self.tabview.add("Editor")
        self.tab_tokens  = self.tabview.add("Tokens")
        self.tab_errores = self.tabview.add("Errores")

        self._build_editor()
        self._build_tokens()
        self._build_errores()

        # ── STATUS BAR ──
        self.statusbar = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.statusbar.pack(fill="x", side="bottom")
        self.statusbar.pack_propagate(False)

        self.lbl_status = ctk.CTkLabel(
            self.statusbar, text="Listo",
            font=ctk.CTkFont(family="Consolas", size=11), text_color="gray"
        )
        self.lbl_status.pack(side="left", padx=10)

    def _build_editor(self):
        self.editor_frame = ctk.CTkFrame(self.tab_editor, fg_color="transparent")
        self.editor_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.editor = ctk.CTkTextbox(
            self.editor_frame,
            font=ctk.CTkFont(family="Consolas", size=13),
            wrap="none"
        )

        self.line_numbers = LineNumbers(self.editor_frame, self.editor)
        self.line_numbers.pack(side="left", fill="y")
        self.editor.pack(side="left", fill="both", expand=True)

        self.editor.insert("0.0", "lap_note Escribe tu codigo PitCode aqui\n\nrace_start garage\n    \nready")

        self.editor._textbox.configure(yscrollcommand=lambda *a: self.line_numbers.redraw())
        self.editor._textbox.bind("<KeyRelease>", lambda e: self.line_numbers.redraw())
        self.editor._textbox.bind("<MouseWheel>", lambda e: self.after(10, self.line_numbers.redraw))
        self.editor._textbox.bind("<Button-1>", lambda e: self.after(10, self.line_numbers.redraw))
        self.editor._textbox.bind("<Configure>", lambda e: self.after(10, self.line_numbers.redraw))
        self.after(200, self.line_numbers.redraw)

    def _build_tokens(self):
        self.frame_stats_tokens = ctk.CTkFrame(self.tab_tokens)
        self.frame_stats_tokens.pack(fill="x", padx=5, pady=5)

        self.lbl_total_tokens = ctk.CTkLabel(
            self.frame_stats_tokens, text="Total: 0",
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.lbl_total_tokens.pack(side="left", padx=15, pady=8)

        self.lbl_reservadas = ctk.CTkLabel(
            self.frame_stats_tokens, text="Reservadas: 0",
            font=ctk.CTkFont(family="Consolas", size=12), text_color="#569cd6"
        )
        self.lbl_reservadas.pack(side="left", padx=15, pady=8)

        self.lbl_ids = ctk.CTkLabel(
            self.frame_stats_tokens, text="Identificadores: 0",
            font=ctk.CTkFont(family="Consolas", size=12), text_color="#6a9955"
        )
        self.lbl_ids.pack(side="left", padx=15, pady=8)

        self.lbl_literales = ctk.CTkLabel(
            self.frame_stats_tokens, text="Literales: 0",
            font=ctk.CTkFont(family="Consolas", size=12), text_color="#ce9178"
        )
        self.lbl_literales.pack(side="left", padx=15, pady=8)

        self.txt_tokens = ctk.CTkTextbox(
            self.tab_tokens, font=ctk.CTkFont(family="Consolas", size=12), wrap="none"
        )
        self.txt_tokens.pack(fill="both", expand=True, padx=5, pady=5)
        self.txt_tokens.configure(state="disabled")

    def _build_errores(self):
        self.frame_stats_errores = ctk.CTkFrame(self.tab_errores)
        self.frame_stats_errores.pack(fill="x", padx=5, pady=5)

        self.lbl_total_errores = ctk.CTkLabel(
            self.frame_stats_errores, text="Total: 0",
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.lbl_total_errores.pack(side="left", padx=15, pady=8)

        self.lbl_lexicos = ctk.CTkLabel(
            self.frame_stats_errores, text="Lexicos: 0",
            font=ctk.CTkFont(family="Consolas", size=12), text_color="#f44747"
        )
        self.lbl_lexicos.pack(side="left", padx=15, pady=8)

        self.lbl_sintacticos = ctk.CTkLabel(
            self.frame_stats_errores, text="Sintacticos: 0",
            font=ctk.CTkFont(family="Consolas", size=12), text_color="#ce9178"
        )
        self.lbl_sintacticos.pack(side="left", padx=15, pady=8)

        self.lbl_semanticos = ctk.CTkLabel(
            self.frame_stats_errores, text="Semanticos: 0",
            font=ctk.CTkFont(family="Consolas", size=12), text_color="#ff8c00"
        )
        self.lbl_semanticos.pack(side="left", padx=15, pady=8)

        self.txt_errores = ctk.CTkTextbox(
            self.tab_errores, font=ctk.CTkFont(family="Consolas", size=12), wrap="none"
        )
        self.txt_errores.pack(fill="both", expand=True, padx=5, pady=5)
        self.txt_errores.configure(state="disabled")

    # ─────────────────────────────────────────
    #  FUNCIONES PRINCIPALES
    # ─────────────────────────────────────────
    def _cargar_archivo(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo PitCode",
            filetypes=[
                ("PitCode", "*.pit"), ("PitCode", "*.pitcode"),
                ("Texto", "*.txt"), ("Todos", "*.*")
            ]
        )
        if not ruta:
            return

        self.ruta_archivo = ruta
        nombre = os.path.basename(ruta)
        self.lbl_archivo.configure(text=nombre)
        self._set_status(f"Archivo cargado: {nombre}")

        with open(ruta, "r", encoding="utf-8") as f:
            codigo = f.read()

        self.editor.delete("0.0", "end")
        self.editor.insert("0.0", codigo)
        self.btn_analizar.configure(state="normal")
        self.after(100, self.line_numbers.redraw)

    def _analizar(self):
        codigo = self.editor.get("0.0", "end").strip()

        if not codigo:
            messagebox.showwarning("Aviso", "El editor esta vacio.")
            return

        self._set_status("Analizando...")
        self.btn_analizar.configure(state="disabled")

        def proceso():
            try:
                # ── Fase 1: Léxico ──
                tokens_list, errores_lexicos = analizar_codigo(codigo)

                # ── Fase 1: Sintáctico ──
                ast, errores_sintacticos = analizar_sintaxis(codigo)

                # ── Fase 2: Semántico ──
                errores_semanticos = []   # Errores REALES (bloquean)
                advertencias = []          # Advertencias (NO bloquean)

                if not errores_lexicos and not errores_sintacticos and ast:
                    sem = SemanticAnalyzer()
                    sem.analyze(ast, codigo)
                    errores_semanticos = sem.get_errors()       # Solo errores reales
                    advertencias = sem.get_warnings()           # Solo advertencias

                # ── Errores que BLOQUEAN (sin advertencias) ──
                errores_reales = errores_lexicos + errores_sintacticos + errores_semanticos
                hay_errores = len(errores_reales) > 0

                # ── Todo para mostrar (con advertencias) ──
                errores_para_mostrar = errores_reales + advertencias

                self.tokens_list  = tokens_list
                self.errores_list = errores_para_mostrar

                # Guardar referencia para saber si hay errores reales
                self._hay_errores_reales = hay_errores

                # ── Fase 2: Generación de código (solo si NO hay errores reales) ──
                code_3d_str = ""
                cpp_code = ""

                if not hay_errores and ast:
                    # Código de tres direcciones
                    gen = ThreeAddressGenerator()
                    gen.generate(ast)
                    code_3d_str = gen.get_code_string()

                    # Traducción a C++
                    translator = CppTranslator()
                    reports_dir = os.path.join(
                        os.path.dirname(os.path.abspath(__file__)), "reports"
                    )
                    cpp_path = os.path.join(reports_dir, "output.cpp")
                    cpp_code = translator.save_to_file(ast, cpp_path)

                # Actualizar UI
                self.after(0, self._actualizar_ui)

                # Generar reportes HTML
                tokens_para_reporte = [] if hay_errores else tokens_list
                html_gen.generar_reporte_tokens(tokens_para_reporte)
                html_gen.generar_reporte_errores(errores_para_mostrar)
                html_gen.generar_reporte_simbolos(ast, codigo)

                if not hay_errores and code_3d_str:
                    html_gen.generar_reporte_codigo(code_3d_str, cpp_code)

                html_gen.generar_index(
                    hay_errores=hay_errores,
                    hay_codigo=not hay_errores
                )

            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.after(0, lambda: self.btn_analizar.configure(state="normal"))

        threading.Thread(target=proceso, daemon=True).start()

    def _actualizar_ui(self):
        self._actualizar_tokens()
        self._actualizar_errores()

        hay_errores = getattr(self, '_hay_errores_reales', False)

        if hay_errores:
            self.btn_tokens.configure(state="disabled")
            self.btn_errores.configure(state="normal")
            self.btn_browser.configure(state="normal")
            self.tabview.set("Errores")
        else:
            self.btn_tokens.configure(state="normal")
            self.btn_errores.configure(state="normal")
            self.btn_browser.configure(state="normal")

        total_errores = len(self.errores_list)
        if hay_errores:
            self._set_status(
                f"Analisis completado. {total_errores} error(es). "
                f"Tokens y código no disponibles."
            )
        elif total_errores > 0:
            # Solo advertencias, no errores reales
            self._set_status(
                f"Analisis completado. {len(self.tokens_list)} tokens. "
                f"Código C++ generado. {total_errores} advertencia(s)."
            )
        else:
            self._set_status(
                f"Analisis completado. {len(self.tokens_list)} tokens. "
                f"Sin errores. Código C++ generado."
            )

    def _actualizar_tokens(self):
        RESERVADAS = [
            'LAP','SPLIT','PITBOARD','YELLOW_FLAG','RADIO',
            'STRATEGY_CHECK','STAY_OUT','PUSH','BOX','FORMATION_LAP',
            'GAP_CHECK','SECTOR','NO_DATA','BOX_BOX','DRS','PITWALL',
            'STRATEGY','PODIO','NEUTRO','RACE_START',
            'BROADCAST','TELEMETRY','DNF','VSC',
            'PADDOCK','RED_FLAG','BLUE_FLAG','BLACK_FLAG',
            'CHECKERED_FLAG','GREEN_LIGHT','RED_LIGHT'
        ]
        LITERALES = ['INT_LITERAL','FLOAT_LITERAL','STRING_LITERAL','CHAR_LITERAL']

        hay_errores = getattr(self, '_hay_errores_reales', False)

        self.txt_tokens.configure(state="normal")
        self.txt_tokens.delete("0.0", "end")

        if hay_errores:
            self.lbl_total_tokens.configure(text="Total: 0")
            self.lbl_reservadas.configure(text="Reservadas: 0")
            self.lbl_ids.configure(text="Identificadores: 0")
            self.lbl_literales.configure(text="Literales: 0")
            self.txt_tokens.insert("end", "  No se generaron tokens debido a errores encontrados.\n")
            self.txt_tokens.insert("end", "  Revise la pestaña de Errores para mas detalles.\n")
        else:
            total      = len(self.tokens_list)
            reservadas = sum(1 for t in self.tokens_list if t['token'] in RESERVADAS)
            ids        = sum(1 for t in self.tokens_list if t['token'] == 'ID')
            literales  = sum(1 for t in self.tokens_list if t['token'] in LITERALES)

            self.lbl_total_tokens.configure(text=f"Total: {total}")
            self.lbl_reservadas.configure(text=f"Reservadas: {reservadas}")
            self.lbl_ids.configure(text=f"Identificadores: {ids}")
            self.lbl_literales.configure(text=f"Literales: {literales}")

            header = f"{'#':<5} {'TOKEN':<20} {'LEXEMA':<20} {'LINEA':<8} {'COLUMNA'}\n"
            header += "-" * 65 + "\n"
            self.txt_tokens.insert("end", header)

            for i, tok in enumerate(self.tokens_list, 1):
                linea = f"{i:<5} {tok['token']:<20} {str(tok['lexeme']):<20} {tok['line']:<8} {tok['column']}\n"
                self.txt_tokens.insert("end", linea)

        self.txt_tokens.configure(state="disabled")

    def _actualizar_errores(self):
        errores_lex  = [e for e in self.errores_list if e.get('type') == 'Léxico']
        errores_syn  = [e for e in self.errores_list if e.get('type') == 'Sintáctico']
        errores_sem  = [e for e in self.errores_list if e.get('type') in ('Semántico', 'Advertencia')]

        total       = len(self.errores_list)
        lexicos     = len(errores_lex)
        sintacticos = len(errores_syn)
        semanticos  = len(errores_sem)

        self.lbl_total_errores.configure(text=f"Total: {total}")
        self.lbl_lexicos.configure(text=f"Lexicos: {lexicos}")
        self.lbl_sintacticos.configure(text=f"Sintacticos: {sintacticos}")
        self.lbl_semanticos.configure(text=f"Semanticos: {semanticos}")

        self.txt_errores.configure(state="normal")
        self.txt_errores.delete("0.0", "end")

        if total == 0:
            self.txt_errores.insert("end", "Sin errores. Codigo PitCode valido.\n")
        else:
            header = f"{'#':<5} {'TIPO':<15} {'MENSAJE':<50} {'LINEA':<8} {'COL'}\n"
            header += "-" * 85 + "\n"
            self.txt_errores.insert("end", header)

            for i, e in enumerate(self.errores_list, 1):
                tipo    = e.get('type', 'Desconocido')
                mensaje = e.get('message', str(e))
                linea   = e.get('line', 0)
                col     = e.get('column', 0)
                fila    = f"{i:<5} {tipo:<15} {mensaje:<50} {linea:<8} {col}\n"
                self.txt_errores.insert("end", fila)

        self.txt_errores.configure(state="disabled")

    def _mostrar_tab(self, tab):
        hay_errores = getattr(self, '_hay_errores_reales', False)
        if tab == "tokens" and hay_errores:
            messagebox.showinfo(
                "Tokens no disponibles",
                "No se pueden mostrar tokens porque se encontraron errores.\n"
                "Corrija los errores e intente de nuevo."
            )
            return

        tabs = {"tokens": "Tokens", "errores": "Errores"}
        self.tabview.set(tabs[tab])

    def _abrir_navegador(self):
        ruta = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "reports", "index.html")
        )
        webbrowser.open(f"file://{ruta}")

    def _set_status(self, mensaje):
        self.lbl_status.configure(text=mensaje)


# ─────────────────────────────────────────────
#  PUNTO DE ENTRADA
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = PitCodeApp()
    app.mainloop()