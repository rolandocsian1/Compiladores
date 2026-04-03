# ============================================================
#   PitCode - Interfaz Gráfica
#   Compiladores 2026 - Fase I
# ============================================================

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading
import webbrowser
import html_gen
from lexer import analyze as analizar_codigo
from parser import parse as analizar_sintaxis


#  Config

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


COLOR_ROJO        = "#e10600"
COLOR_ROJO_HOVER  = "#ff1a0e"
COLOR_ROJO_DARK   = "#9b0400"
COLOR_BG          = "#0f0f0f"
COLOR_BG2         = "#1a1a1a"
COLOR_BG3         = "#222222"
COLOR_GRIS        = "#2a2a2a"
COLOR_TEXTO       = "#e0e0e0"
COLOR_TEXTO_DIM   = "#888888"

class PitCodeApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PitCode - Compiladores 2026")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(fg_color=COLOR_BG)

        self.ruta_archivo = None
        self.tokens_list  = []
        self.errores_list = []

        self._build_ui()

 
    #   INTERFAZ
    
    def _build_ui(self):

        
        self.header = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color=COLOR_ROJO_DARK)
        self.header.pack(fill="x", side="top")
        self.header.pack_propagate(False)

        ctk.CTkLabel(
            self.header,
            text="PitCode",
            font=ctk.CTkFont(family="Consolas", size=22, weight="bold"),
            text_color="white"
        ).pack(side="left", padx=20, pady=10)

        ctk.CTkLabel(
            self.header,
            text="// Compiladores 2026",
            font=ctk.CTkFont(family="Consolas", size=13),
            text_color="#ffaaaa"
        ).pack(side="left", padx=5, pady=10)

        # PANEL Izq
        self.panel_izq = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=COLOR_BG2)
        self.panel_izq.pack(fill="y", side="left")
        self.panel_izq.pack_propagate(False)

        self.lbl_archivo = ctk.CTkLabel(
            self.panel_izq,
            text="Sin archivo",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=COLOR_TEXTO_DIM,
            wraplength=180
        )
        self.lbl_archivo.pack(padx=10, pady=(20, 5))

        ctk.CTkButton(
            self.panel_izq,
            text="Cargar archivo .pit",
            command=self._cargar_archivo,
            font=ctk.CTkFont(family="Consolas", size=12),
            height=35,
            fg_color=COLOR_ROJO,
            hover_color=COLOR_ROJO_HOVER,
            text_color="white"
        ).pack(padx=10, pady=5, fill="x")

        self.btn_analizar = ctk.CTkButton(
            self.panel_izq,
            text="Analizar",
            command=self._analizar,
            font=ctk.CTkFont(family="Consolas", size=12),
            height=35,
            state="disabled",
            fg_color=COLOR_ROJO,
            hover_color=COLOR_ROJO_HOVER,
            text_color="white"
        )
        self.btn_analizar.pack(padx=10, pady=5, fill="x")

        ctk.CTkLabel(
            self.panel_izq,
            text="── Reportes ──",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=COLOR_TEXTO_DIM
        ).pack(padx=10, pady=(20, 5))

        self.btn_tokens = ctk.CTkButton(
            self.panel_izq,
            text="Ver Tokens",
            command=lambda: self._mostrar_tab("tokens"),
            font=ctk.CTkFont(family="Consolas", size=12),
            height=35,
            state="disabled",
            fg_color="transparent",
            border_width=1,
            border_color=COLOR_ROJO,
            text_color=COLOR_TEXTO,
            hover_color=COLOR_GRIS
        )
        self.btn_tokens.pack(padx=10, pady=5, fill="x")

        self.btn_errores = ctk.CTkButton(
            self.panel_izq,
            text="Ver Errores",
            command=lambda: self._mostrar_tab("errores"),
            font=ctk.CTkFont(family="Consolas", size=12),
            height=35,
            state="disabled",
            fg_color="transparent",
            border_width=1,
            border_color=COLOR_ROJO,
            text_color=COLOR_TEXTO,
            hover_color=COLOR_GRIS
        )
        self.btn_errores.pack(padx=10, pady=5, fill="x")

        ctk.CTkLabel(
            self.panel_izq,
            text="── Navegador ──",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=COLOR_TEXTO_DIM
        ).pack(padx=10, pady=(20, 5))

        self.btn_browser = ctk.CTkButton(
            self.panel_izq,
            text="Abrir en Navegador",
            command=self._abrir_navegador,
            font=ctk.CTkFont(family="Consolas", size=12),
            height=35,
            state="disabled",
            fg_color=COLOR_GRIS,
            hover_color=COLOR_BG3,
            text_color=COLOR_TEXTO
        )
        self.btn_browser.pack(padx=10, pady=5, fill="x")

        #  PRINCIo
        self.panel_main = ctk.CTkFrame(self, corner_radius=0, fg_color=COLOR_BG)
        self.panel_main.pack(fill="both", expand=True, side="left")

        self.tabview = ctk.CTkTabview(
            self.panel_main,
            fg_color=COLOR_BG2,
            segmented_button_fg_color=COLOR_BG3,
            segmented_button_selected_color=COLOR_ROJO,
            segmented_button_selected_hover_color=COLOR_ROJO_HOVER,
            segmented_button_unselected_color=COLOR_BG3,
            segmented_button_unselected_hover_color=COLOR_GRIS,
            text_color=COLOR_TEXTO,
            text_color_disabled=COLOR_TEXTO_DIM
        )
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_editor  = self.tabview.add("Editor")
        self.tab_tokens  = self.tabview.add("Tokens")
        self.tab_errores = self.tabview.add("Errores")

        self._build_editor()
        self._build_tokens()
        self._build_errores()

        
        self.statusbar = ctk.CTkFrame(self, height=30, corner_radius=0, fg_color=COLOR_BG3)
        self.statusbar.pack(fill="x", side="bottom")
        self.statusbar.pack_propagate(False)

        self.lbl_status = ctk.CTkLabel(
            self.statusbar,
            text="Listo",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=COLOR_TEXTO_DIM
        )
        self.lbl_status.pack(side="left", padx=10)

  
    #  EDITOR CON NÚMEROS DE LÍNEA
    
    def _build_editor(self):
        
        self.frame_editor = ctk.CTkFrame(self.tab_editor, fg_color="transparent")
        self.frame_editor.pack(fill="both", expand=True, padx=5, pady=5)

        # numeross
        self.line_numbers = ctk.CTkTextbox(
            self.frame_editor,
            width=45,
            font=ctk.CTkFont(family="Consolas", size=13),
            wrap="none",
            fg_color=COLOR_BG3,
            text_color=COLOR_ROJO,
            state="disabled",
            activate_scrollbars=False
        )
        self.line_numbers.pack(side="left", fill="y", padx=(0, 2))

        # Editor 
        self.editor = ctk.CTkTextbox(
            self.frame_editor,
            font=ctk.CTkFont(family="Consolas", size=13),
            wrap="none",
            fg_color=COLOR_BG2,
            text_color=COLOR_TEXTO
        )
        self.editor.pack(side="left", fill="both", expand=True)
        self.editor.insert("0.0", "lap_note Escribe tu codigo PitCode aqui\n\nrace_start garage\n    \nready")

        
        self.editor.bind("<KeyRelease>", self._actualizar_lineas)
        self.editor.bind("<MouseWheel>", self._sync_scroll)
        self.editor.bind("<Button-1>",   self._actualizar_lineas)
        self.editor.bind("<Button-4>",   self._sync_scroll)
        self.editor.bind("<Button-5>",   self._sync_scroll)

        
        self.editor._textbox.config(yscrollcommand=self._on_editor_scroll)

        # Dibujar números 
        self.after(100, self._actualizar_lineas)

    def _actualizar_lineas(self, event=None):
        """Actualiza el panel de números de línea."""
        contenido    = self.editor.get("0.0", "end")
        total_lineas = contenido.count("\n")
        if total_lineas < 1:
            total_lineas = 1

        self.line_numbers.configure(state="normal")
        self.line_numbers.delete("0.0", "end")
        nums = "\n".join(str(i) for i in range(1, total_lineas + 1))
        self.line_numbers.insert("0.0", nums)
        self.line_numbers.configure(state="disabled")

    def _on_editor_scroll(self, *args):
        """Sincroniza scroll del editor con los números de línea."""
        self.line_numbers._textbox.yview_moveto(args[0])

    def _sync_scroll(self, event=None):
        """Sincroniza scroll de rueda del mouse."""
        self.after(10, lambda: self.line_numbers._textbox.yview(
            "moveto", self.editor._textbox.yview()[0]
        ))

    #  TOKENS
  
    def _build_tokens(self):
        self.frame_stats_tokens = ctk.CTkFrame(self.tab_tokens, fg_color=COLOR_BG3)
        self.frame_stats_tokens.pack(fill="x", padx=5, pady=5)

        self.lbl_total_tokens = ctk.CTkLabel(
            self.frame_stats_tokens,
            text="Total: 0",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color=COLOR_TEXTO
        )
        self.lbl_total_tokens.pack(side="left", padx=15, pady=8)

        self.lbl_reservadas = ctk.CTkLabel(
            self.frame_stats_tokens,
            text="Reservadas: 0",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color="#569cd6"
        )
        self.lbl_reservadas.pack(side="left", padx=15, pady=8)

        self.lbl_ids = ctk.CTkLabel(
            self.frame_stats_tokens,
            text="Identificadores: 0",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color="#6a9955"
        )
        self.lbl_ids.pack(side="left", padx=15, pady=8)

        self.lbl_literales = ctk.CTkLabel(
            self.frame_stats_tokens,
            text="Literales: 0",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color="#ce9178"
        )
        self.lbl_literales.pack(side="left", padx=15, pady=8)

        self.txt_tokens = ctk.CTkTextbox(
            self.tab_tokens,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="none",
            fg_color=COLOR_BG2,
            text_color=COLOR_TEXTO
        )
        self.txt_tokens.pack(fill="both", expand=True, padx=5, pady=5)
        self.txt_tokens.configure(state="disabled")

  
    #  ERRORES
  
    def _build_errores(self):
        self.frame_stats_errores = ctk.CTkFrame(self.tab_errores, fg_color=COLOR_BG3)
        self.frame_stats_errores.pack(fill="x", padx=5, pady=5)

        self.lbl_total_errores = ctk.CTkLabel(
            self.frame_stats_errores,
            text="Total: 0",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color=COLOR_TEXTO
        )
        self.lbl_total_errores.pack(side="left", padx=15, pady=8)

        self.lbl_lexicos = ctk.CTkLabel(
            self.frame_stats_errores,
            text="Lexicos: 0",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color="#f44747"
        )
        self.lbl_lexicos.pack(side="left", padx=15, pady=8)

        self.lbl_sintacticos = ctk.CTkLabel(
            self.frame_stats_errores,
            text="Sintacticos: 0",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color="#ce9178"
        )
        self.lbl_sintacticos.pack(side="left", padx=15, pady=8)

        self.txt_errores = ctk.CTkTextbox(
            self.tab_errores,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="none",
            fg_color=COLOR_BG2,
            text_color=COLOR_TEXTO
        )
        self.txt_errores.pack(fill="both", expand=True, padx=5, pady=5)
        self.txt_errores.configure(state="disabled")

  
    #  FUNCIONES PRINCIPALES

    def _cargar_archivo(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo PitCode",
            filetypes=[
                ("PitCode", "*.pit"),
                ("PitCode", "*.pitcode"),
                ("Texto",   "*.txt"),
                ("Todos",   "*.*")
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
        self.after(100, self._actualizar_lineas)

    def _analizar(self):
        codigo = self.editor.get("0.0", "end").strip()

        if not codigo:
            messagebox.showwarning("Aviso", "El editor esta vacio.")
            return

        self._set_status("Analizando...")
        self.btn_analizar.configure(state="disabled")

        def proceso():
            try:
                tokens_list, errores_lexicos = analizar_codigo(codigo)

                if errores_lexicos:
                    ast                 = None
                    errores_sintacticos = []
                else:
                    ast, errores_sintacticos = analizar_sintaxis(codigo)

                errores_totales = errores_lexicos + errores_sintacticos

                self.tokens_list  = tokens_list
                self.errores_list = errores_totales

                self.after(0, self._actualizar_ui)

                hay_errores          = len(errores_totales) > 0
                tokens_para_reporte  = [] if hay_errores else tokens_list

                html_gen.generar_reporte_tokens(tokens_para_reporte)
                html_gen.generar_reporte_errores(errores_totales)
                html_gen.generar_reporte_simbolos(ast, codigo)
                html_gen.generar_index(hay_errores=hay_errores)

            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.after(0, lambda: self.btn_analizar.configure(state="normal"))

        threading.Thread(target=proceso, daemon=True).start()

    def _actualizar_ui(self):
        self._actualizar_tokens()
        self._actualizar_errores()

        hay_errores = len(self.errores_list) > 0

        if hay_errores:
            self.btn_tokens.configure(state="disabled")
            self.btn_errores.configure(state="normal")
            self.btn_browser.configure(state="normal")
            self.tabview.set("Errores")   # ← auto a errores
        else:
            self.btn_tokens.configure(state="normal")
            self.btn_errores.configure(state="normal")
            self.btn_browser.configure(state="normal")
            self.tabview.set("Tokens")    # ← auto a tokens

        total_errores = len(self.errores_list)
        if total_errores == 0:
            self._set_status(f"✓  Analisis completado — {len(self.tokens_list)} tokens — Sin errores.")
        else:
            self._set_status(f"⚠  Analisis completado — {total_errores} error(es) encontrado(s).")

    def _actualizar_tokens(self):
        RESERVADAS = ['LAP','SPLIT','PITBOARD','YELLOW_FLAG','RADIO',
                      'STRATEGY_CHECK','STAY_OUT','PUSH','BOX','FORMATION_LAP',
                      'GAP_CHECK','SECTOR','NO_DATA','BOX_BOX','DRS','PITWALL',
                      'STRATEGY','PODIO','NEUTRO','RACE_START',
                      'BROADCAST','TELEMETRY','DNF','VSC',
                      'PADDOCK','RED_FLAG','BLUE_FLAG','BLACK_FLAG',
                      'CHECKERED_FLAG','TRUE','FALSE']
        LITERALES  = ['INT_LITERAL','FLOAT_LITERAL','STRING_LITERAL','CHAR_LITERAL']

        total      = len(self.tokens_list)
        reservadas = sum(1 for t in self.tokens_list if t['token'] in RESERVADAS)
        ids        = sum(1 for t in self.tokens_list if t['token'] == 'ID')
        literales  = sum(1 for t in self.tokens_list if t['token'] in LITERALES)

        self.lbl_total_tokens.configure(text=f"Total: {total}")
        self.lbl_reservadas.configure(text=f"Reservadas: {reservadas}")
        self.lbl_ids.configure(text=f"Identificadores: {ids}")
        self.lbl_literales.configure(text=f"Literales: {literales}")

        self.txt_tokens.configure(state="normal")
        self.txt_tokens.delete("0.0", "end")

        hay_errores = len(self.errores_list) > 0

        if hay_errores:
            self.txt_tokens.insert("end", "  No se generaron tokens debido a errores encontrados.\n")
            self.txt_tokens.insert("end", "  Revise la pestana de Errores para mas detalles.\n")
        else:
            header = f"{'#':<5} {'TOKEN':<20} {'LEXEMA':<20} {'LINEA':<8} {'COLUMNA'}\n"
            header += "-" * 65 + "\n"
            self.txt_tokens.insert("end", header)

            for i, tok in enumerate(self.tokens_list, 1):
                linea = f"{i:<5} {tok['token']:<20} {str(tok['lexeme']):<20} {tok['line']:<8} {tok['column']}\n"
                self.txt_tokens.insert("end", linea)

        self.txt_tokens.configure(state="disabled")

    def _actualizar_errores(self):
        errores_lexicos = [e for e in self.errores_list
                          if e.get('type') == 'Léxico']
        errores_sint    = [e for e in self.errores_list
                          if e.get('type') == 'Sintáctico']

        total       = len(self.errores_list)
        lexicos     = len(errores_lexicos)
        sintacticos = len(errores_sint)

        self.lbl_total_errores.configure(text=f"Total: {total}")
        self.lbl_lexicos.configure(text=f"Lexicos: {lexicos}")
        self.lbl_sintacticos.configure(text=f"Sintacticos: {sintacticos}")

        self.txt_errores.configure(state="normal")
        self.txt_errores.delete("0.0", "end")

        if total == 0:
            self.txt_errores.insert("end", "Sin errores. Codigo PitCode valido.\n")
        else:
            header = f"{'#':<5} {'TIPO':<15} {'MENSAJE':<45} {'LINEA':<8} {'COL'}\n"
            header += "-" * 80 + "\n"
            self.txt_errores.insert("end", header)

            for i, e in enumerate(self.errores_list, 1):
                tipo    = e.get('type', 'Desconocido')
                mensaje = e.get('message', str(e))
                linea   = e.get('line', 0)
                col     = e.get('column', 0)
                fila    = f"{i:<5} {tipo:<15} {mensaje:<45} {linea:<8} {col}\n"
                self.txt_errores.insert("end", fila)

        self.txt_errores.configure(state="disabled")

    def _mostrar_tab(self, tab):
        if tab == "tokens" and len(self.errores_list) > 0:
            messagebox.showinfo(
                "Tokens no disponibles",
                "No se pueden mostrar tokens porque se encontraron errores.\n"
                "Corrija los errores e intente de nuevo."
            )
            return

        tabs = {
            "tokens"  : "Tokens",
            "errores" : "Errores"
        }
        self.tabview.set(tabs[tab])

    def _abrir_navegador(self):
        ruta = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "reports", "index.html")
        )
        webbrowser.open(f"file://{ruta}")

    def _set_status(self, mensaje):
        self.lbl_status.configure(text=mensaje)


#  PUNTO DE ENTRADA

if __name__ == "__main__":
    app = PitCodeApp()
    app.mainloop()