"""APORTE UI 1: ventana, navegación y controladores de NEXO GYM.

Rama: feature/ui-1. Conserva el nombre exigido por la rúbrica.
Actualizar conserva búsqueda, selección y desplazamiento de la vista.
Importa componentes de UI 2 y consume un servicio inyectado. No usa JSON,
no calcula vigencia y no realiza operaciones comerciales por su cuenta.
"""

import tkinter as tk
from tkinter import ttk
import traceback

from src.domain.exceptions import DomainError
from src.ui import (AccessResult, Column, DataTable, EntitySelector, FieldSpec,
                    FormDialog, HeroBanner, InputError, Notifier, StatCard,
                    Theme, format_date, format_money)

_FAILED = object()


class GymInterface:
    PAGES = (("inicio", "01", "Inicio", "La operación, en perspectiva."),
             ("socios", "02", "Socios", "Personas que forman parte de tu comunidad."),
             ("planes", "03", "Planes", "Una propuesta para cada objetivo."),
             ("membresias", "04", "Membresías", "Períodos, planes y estados en un solo lugar."),
             ("entrenadores", "05", "Entrenadores", "El equipo que impulsa el progreso."),
             ("acceso", "06", "Control de acceso", "Verifica la membresía antes de registrar el ingreso."),
             ("asistencias", "07", "Asistencias", "Trazabilidad de los ingresos al gimnasio."),
             ("vencimientos", "08", "Vencimientos", "Anticipa el seguimiento de las membresías."))

    def __init__(self, root, service, demo=False):
        self.root, self.service, self.demo = root, service, demo
        self.page = "inicio"
        self.table = None
        self.active_form = None
        self._membership_filter = "TODAS"
        self._expiration_filter = "PROXIMAS"
        self._attendance_filter = ""
        self._verified_id = None
        self._last_width = 0
        Theme.apply(root)
        root.title("NEXO GYM · Membresías y acceso" + (" · DEMOSTRACIÓN" if demo else ""))
        root.geometry("1280x820")
        root.minsize(1000, 650)
        root.report_callback_exception = self._callback_exception
        self._build_shell()
        self.navigate("inicio")
        for number, (key, *_rest) in enumerate(self.PAGES, start=1):
            root.bind(f"<Control-Key-{number}>", lambda event, page=key: self.navigate(page))
        root.bind("<F5>", lambda event: self.refresh())

    def _build_shell(self):
        sidebar = tk.Frame(self.root, bg=Theme.NAVY, width=216)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        brand = tk.Canvas(sidebar, height=90, bg=Theme.NAVY, highlightthickness=0)
        brand.pack(fill="x", padx=20, pady=(14, 0))
        brand.create_polygon(0, 23, 12, 23, 34, 45, 34, 23, 46, 23,
                             46, 67, 34, 67, 12, 45, 12, 67, 0, 67, fill=Theme.MINT)
        brand.create_text(60, 33, text="NEXO", fill="white", anchor="w",
                          font=(Theme.FONT, 21, "bold"))
        brand.create_text(61, 58, text="GYM MANAGEMENT", fill="#9DACBF", anchor="w",
                          font=(Theme.FONT, 8, "bold"))
        tk.Label(sidebar, text="ESPACIO DE TRABAJO", bg=Theme.NAVY, fg="#7E91AE",
                 font=(Theme.FONT, 8, "bold"), anchor="w").pack(fill="x", padx=24, pady=(8, 8))
        self.nav_buttons = {}
        for key, number, name, _description in self.PAGES:
            button = tk.Button(sidebar, text=f"{number}   {name}", anchor="w", padx=15, pady=10,
                               bg=Theme.NAVY, fg="#C1CDDE", activebackground=Theme.NAV_ACTIVE,
                               activeforeground="white", relief="flat", bd=0, cursor="hand2",
                               highlightthickness=1, highlightbackground=Theme.NAVY,
                               highlightcolor=Theme.MINT, font=(Theme.FONT, 10),
                               command=lambda page=key: self.navigate(page))
            button.pack(fill="x", padx=12, pady=2)
            button.bind("<Return>", lambda event, b=button: b.invoke())
            self.nav_buttons[key] = button
        footer = tk.Frame(sidebar, bg=Theme.NAVY)
        self.sidebar_footer = footer
        footer.pack(side="bottom", fill="x", padx=24, pady=22)
        tk.Frame(footer, height=1, bg="#2B3B53").pack(fill="x", pady=(0, 15))
        tk.Label(footer, text="DEMO · EN MEMORIA" if self.demo else "GESTIÓN LOCAL",
                 bg=Theme.NAVY, fg=Theme.MINT, font=(Theme.FONT, 9, "bold"), anchor="w").pack(fill="x")
        tk.Label(footer, text="Ctrl + 1…8 · Navegación\nF5 · Actualizar datos", bg=Theme.NAVY,
                 fg="#9DACBF", font=(Theme.FONT, 9), justify="left", anchor="w").pack(
                     fill="x", pady=(8, 0))
        workspace = tk.Frame(self.root, bg=Theme.BG)
        workspace.pack(side="right", fill="both", expand=True)
        top = tk.Frame(workspace, bg=Theme.SURFACE, height=60)
        top.pack(fill="x")
        top.pack_propagate(False)
        tk.Label(top, text="ADMINISTRACIÓN  /  GIMNASIO", fg=Theme.MUTED, bg=Theme.SURFACE,
                 font=(Theme.FONT, 9, "bold")).pack(side="left", padx=26)
        self.today_label = tk.Label(top, text="", fg=Theme.TEXT, bg=Theme.SURFACE,
                                    font=(Theme.FONT, 10))
        self.today_label.pack(side="right", padx=26)
        self.notifier = Notifier(workspace)
        self.notifier.pack(fill="x", padx=25, pady=(16, 0))
        self.notifier.show("Demostración: datos ficticios; los cambios se descartan al cerrar."
                           if self.demo else "Listo para gestionar la operación del gimnasio.")
        container = tk.Frame(workspace, bg=Theme.BG)
        container.pack(fill="both", expand=True, padx=(25, 10), pady=16)
        self.canvas = tk.Canvas(container, bg=Theme.BG, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview,
                                   style="Gym.Vertical.TScrollbar")
        scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.content = tk.Frame(self.canvas, bg=Theme.BG)
        self._content_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.canvas.bind("<Configure>", self._canvas_resized)
        self.content.bind("<Configure>", self._content_resized)
        # El binding solo afecta la ventana de esta aplicación. Las tablas usan su propio scroll.
        self.root.bind("<MouseWheel>", self._mousewheel, add="+")

    def _canvas_resized(self, event):
        self.canvas.itemconfigure(self._content_id, width=event.width)
        self._last_width = event.width
        self._content_resized()

    def _content_resized(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _mousewheel(self, event):
        if isinstance(event.widget, (ttk.Treeview, ttk.Combobox, tk.Toplevel)):
            return
        if event.widget.winfo_toplevel() != self.root:
            return
        if self.content.winfo_height() > self.canvas.winfo_height():
            self.canvas.yview_scroll(-int(event.delta / 120), "units")

    def _callback_exception(self, exc_type, value, tb):
        traceback.print_exception(exc_type, value, tb)
        self.notifier.show("Ocurrió un error inesperado. Revisa la terminal e intenta nuevamente.", "error")

    def _guard(self, action):
        try:
            return action()
        except (DomainError, InputError) as exc:
            self.notifier.show(str(exc), "error")
        except Exception:
            traceback.print_exc()
            self.notifier.show("No se pudo completar la consulta. Revisa la conexión con el servicio.", "error")
        return _FAILED

    def navigate(self, page):
        if page not in {row[0] for row in self.PAGES}:
            raise ValueError("Pantalla no reconocida.")
        if self.active_form and self.active_form.winfo_exists():
            self.active_form.destroy()
        self.active_form = None
        self.page, self.table, self._verified_id = page, None, None
        for child in self.content.winfo_children():
            child.destroy()
        self.canvas.yview_moveto(0)
        for key, button in self.nav_buttons.items():
            selected = key == page
            button.configure(bg=Theme.NAV_ACTIVE if selected else Theme.NAVY,
                             fg=Theme.MINT if selected else "#C1CDDE",
                             font=(Theme.FONT, 10, "bold" if selected else "normal"))
        today = self._guard(self.service.fecha_actual)
        self.today_label.configure(text="" if today is _FAILED else format_date(today))
        name, description = next((row[2], row[3]) for row in self.PAGES if row[0] == page)
        header = tk.Frame(self.content, bg=Theme.BG)
        header.pack(fill="x", pady=(0, 20))
        titles = tk.Frame(header, bg=Theme.BG)
        titles.pack(side="left", fill="x", expand=True)
        tk.Label(titles, text=name, bg=Theme.BG, fg=Theme.TEXT,
                 font=(Theme.FONT, 25, "bold"), anchor="w").pack(fill="x")
        tk.Label(titles, text=description, bg=Theme.BG, fg=Theme.MUTED,
                 font=(Theme.FONT, 10), anchor="w").pack(fill="x", pady=(5, 0))
        self.header_actions = tk.Frame(header, bg=Theme.BG)
        self.header_actions.pack(side="right", padx=(15, 0))
        Theme.button(self.header_actions, "Actualizar", self.refresh, "secondary").pack(side="left")
        builder = {"inicio": self._home, "socios": self._members, "planes": self._plans,
                   "membresias": self._memberships, "entrenadores": self._trainers,
                   "acceso": self._access, "asistencias": self._attendance,
                   "vencimientos": self._expirations}[page]
        self._guard(builder)
        self.root.update_idletasks()
        self._content_resized()

    def refresh(self):
        """Consulta datos nuevos manteniendo el contexto de la pantalla actual."""
        state = self._capture_view_state()
        self.navigate(self.page)
        self._restore_view_state(state)

    def _capture_view_state(self):
        state = {"canvas_y": self.canvas.yview()[0]}
        if self.table is not None and self.table.winfo_exists():
            selected = self.table.selected_row()
            state["table"] = {"query": self.table.query.get(),
                              "selected_id": selected.get("id") if selected else None,
                              "x": self.table.tree.xview()[0],
                              "y": self.table.tree.yview()[0],
                              "search_focused": self.root.focus_get() == self.table.search}
        if self.page == "acceso" and getattr(self, "access_selector", None) is not None:
            if self.access_selector.winfo_exists():
                try:
                    state["access_id"] = self.access_selector.value()
                except InputError:
                    pass
        return state

    def _restore_view_state(self, state):
        table_state = state.get("table")
        if table_state is not None and self.table is not None:
            self.table.set_query(table_state["query"])
            selected_id = table_state["selected_id"]
            if selected_id is not None:
                for item, row in zip(self.table.tree.get_children(), self.table.visible_rows()):
                    if row.get("id") == selected_id:
                        self.table.tree.selection_set(item)
                        self.table.tree.focus(item)
                        break
            self.table.tree.xview_moveto(table_state["x"])
            self.table.tree.yview_moveto(table_state["y"])
            if table_state["search_focused"]:
                self.table.search.focus_set()
        if self.page == "acceso" and "access_id" in state:
            if getattr(self, "access_selector", None) is not None and self.access_selector.winfo_exists():
                try:
                    # Se conserva el socio, pero nunca una autorización anterior.
                    self.access_selector.select(state["access_id"])
                except InputError:
                    pass  # El socio ya no está en la lista: queda sin selección.
        self.root.update_idletasks()
        self._content_resized()
        self.canvas.yview_moveto(state["canvas_y"])

    def _add_action(self, text, command):
        Theme.button(self.header_actions, text, command).pack(side="left", padx=(8, 0))

    def _section(self, title, subtitle=""):
        block = tk.Frame(self.content, bg=Theme.BG)
        block.pack(fill="x", pady=(20, 10))
        tk.Label(block, text=title, bg=Theme.BG, fg=Theme.TEXT, font=(Theme.FONT, 13, "bold"),
                 anchor="w").pack(fill="x")
        if subtitle:
            tk.Label(block, text=subtitle, bg=Theme.BG, fg=Theme.MUTED,
                     anchor="w").pack(fill="x", pady=(5, 0))

    def _make_table(self, columns, rows, search_keys=None):
        table = DataTable(self.content, columns, search_keys=search_keys)
        table.pack(fill="both", expand=True, pady=(5, 0))
        table.set_rows(rows)
        self.table = table
        return table

    @staticmethod
    def _member_choices(rows):
        return tuple((r["id"], f"{r['nombre']} {r['apellido']} · {r['documento']}") for r in rows)

    @staticmethod
    def _membership_rows(rows):
        return [{**row, "estado_visible": ("VIGENTE · PRÓXIMA" if row["proxima"]
                                            else row["estado"])} for row in rows]

    @staticmethod
    def _membership_columns():
        return (Column("socio", "SOCIO", 185), Column("plan", "PLAN", 190),
                Column("fecha_inicio", "INICIO", 115, formatter=format_date),
                Column("fecha_fin", "VENCIMIENTO", 125, formatter=format_date),
                Column("estado_visible", "ESTADO", 180))

    def _home(self):
        self._add_action("+ Registrar socio", lambda: self.open_form("socio"))
        HeroBanner(self.content, "Cada ingreso, un nuevo comienzo.",
                   "Conecta personas, membresías y progreso en un espacio de gestión claro.").pack(fill="x")
        summary = self.service.resumen()
        cards = tk.Frame(self.content, bg=Theme.BG)
        cards.pack(fill="x", pady=18)
        for index, (label, key, detail, color) in enumerate((
            ("Socios", "socios", "Comunidad registrada", Theme.TEAL),
            ("Membresías vigentes", "vigentes", "Estado informado por el servicio", Theme.PURPLE),
            ("Ingresos de hoy", "asistencias_hoy", "Asistencias registradas", Theme.CORAL),
            ("Próximas a vencer", "proximas", "Seguimiento de membresías", Theme.TEAL),
        )):
            cards.columnconfigure(index, weight=1, uniform="cards")
            StatCard(cards, label, summary[key], detail, color).grid(
                row=0, column=index, sticky="nsew", padx=(0, 10 if index < 3 else 0))
        quick = tk.Frame(self.content, bg=Theme.BG)
        quick.pack(fill="x")
        for text, route in (("Verificar acceso", "acceso"), ("Ver membresías", "membresias"),
                            ("Consultar asistencias", "asistencias")):
            Theme.button(quick, text, lambda p=route: self.navigate(p), "secondary").pack(
                side="left", padx=(0, 10))
        self._section("Seguimiento prioritario", "Membresías que el servicio marca como próximas a vencer.")
        self._make_table(self._membership_columns(),
                         self._membership_rows(self.service.listar_membresias("PROXIMAS")),
                         ("socio", "documento", "plan", "estado_visible"))
        tk.Label(self.content, text=f"{summary['planes']} planes disponibles  ·  "
                 f"{summary['entrenadores']} entrenadores registrados", bg=Theme.BG,
                 fg=Theme.MUTED, anchor="w").pack(fill="x", pady=16)

    def _members(self):
        self._add_action("+ Registrar socio", lambda: self.open_form("socio"))
        rows = [{**r, "nombre_completo": f"{r['nombre']} {r['apellido']}"}
                for r in self.service.listar_socios()]
        action = tk.Frame(self.content, bg=Theme.BG)
        action.pack(fill="x", pady=(0, 12))
        Theme.button(action, "Ir a control de acceso", self._member_to_access, "secondary").pack(side="left")
        Theme.button(action, "Consultar membresías", self._member_to_memberships, "secondary").pack(
            side="left", padx=10)
        self._make_table((Column("nombre_completo", "NOMBRE Y APELLIDO", 230),
                          Column("documento", "DOCUMENTO", 125), Column("telefono", "TELÉFONO", 140),
                          Column("correo", "CORREO", 240)), rows)

    def _selected_member(self):
        row = self.table.selected_row() if self.table else None
        if not row:
            raise InputError("Selecciona primero un socio en la tabla.")
        return row

    def _member_to_access(self):
        def action():
            row = self._selected_member()
            self.navigate("acceso")
            self.access_selector.select(row["id"])
        self._guard(action)

    def _member_to_memberships(self):
        def action():
            row = self._selected_member()
            self._membership_filter = "TODAS"
            self.navigate("membresias")
            self.table.set_query(row["documento"])
        self._guard(action)

    def _plans(self):
        self._add_action("+ Registrar plan", lambda: self.open_form("plan"))
        self._make_table((Column("nombre", "PLAN", 260), Column("precio", "PRECIO", 140,
                          formatter=format_money), Column("duracion_dias", "DURACIÓN · DÍAS", 155)),
                         self.service.listar_planes())
        self._section("El plan define el período", "Las fechas de membresía y su vigencia se calculan en el servicio.")

    def _filter_bar(self, label, mapping, current, on_change):
        bar = tk.Frame(self.content, bg=Theme.BG)
        bar.pack(fill="x", pady=(0, 12))
        tk.Label(bar, text=label, bg=Theme.BG, fg=Theme.MUTED,
                 font=(Theme.FONT, 10, "bold")).pack(side="left", padx=(0, 12))
        variable = tk.StringVar(bar, value=next(name for name, key in mapping.items() if key == current))
        combo = ttk.Combobox(bar, textvariable=variable, values=tuple(mapping), state="readonly",
                             style="Gym.TCombobox", width=24)
        combo.pack(side="left")
        combo.bind("<<ComboboxSelected>>", lambda event: on_change(mapping[variable.get()]))
        return combo

    def _memberships(self):
        self._add_action("+ Registrar membresía", lambda: self.open_form("membresia"))
        def changed(key):
            self._membership_filter = key
            self.refresh()
        self.membership_combo = self._filter_bar("Mostrar", {"Todas": "TODAS", "Vigentes": "VIGENTE",
                "Programadas": "PROGRAMADA", "Vencidas": "VENCIDA", "Próximas a vencer": "PROXIMAS"},
                self._membership_filter, changed)
        self._make_table(self._membership_columns(),
                         self._membership_rows(self.service.listar_membresias(self._membership_filter)),
                         ("socio", "documento", "plan", "estado_visible"))

    def _trainers(self):
        self._add_action("+ Registrar entrenador", lambda: self.open_form("entrenador"))
        self._make_table((Column("nombre", "ENTRENADOR", 260),
                          Column("especialidad", "ESPECIALIDAD", 400)), self.service.listar_entrenadores())

    def _access(self):
        card = tk.Frame(self.content, bg=Theme.SURFACE, padx=24, pady=24,
                        highlightthickness=1, highlightbackground=Theme.BORDER)
        card.pack(fill="x")
        self.access_selector = EntitySelector(card, "Socio · busca por nombre o documento",
                                               self._member_choices(self.service.listar_socios()))
        self.access_selector.pack(fill="x", pady=(0, 16))
        actions = tk.Frame(card, bg=Theme.SURFACE)
        actions.pack(fill="x")
        self.verify_button = Theme.button(actions, "Verificar acceso", self.check_access)
        self.verify_button.pack(side="left")
        self.attendance_button = Theme.button(actions, "Registrar asistencia", self.register_attendance, "secondary")
        self.attendance_button.pack(side="left", padx=10)
        self.attendance_button.configure(state="disabled")
        self.access_result = AccessResult(card)
        self.access_result.pack(fill="x", pady=(22, 0))
        self.access_selector.bind_change(self._access_selection_changed)
        self._section("Una verificación, una decisión clara",
                      "El servicio vuelve a validar la membresía al registrar la asistencia.")
        tk.Label(self.content, text="Si no aparece un socio, regístralo en Socios. "
                 "Luego asigna su plan desde Membresías.", bg=Theme.BG, fg=Theme.MUTED,
                 wraplength=650, justify="left", anchor="w").pack(fill="x")

    def _access_selection_changed(self):
        self._verified_id = None
        self.access_result.reset()
        self.attendance_button.configure(state="disabled")

    def check_access(self):
        def action():
            identifier = self.access_selector.value()
            dto = self.service.verificar_acceso(identifier)
            self.access_result.show_result(dto)
            self._verified_id = identifier if dto["permitido"] else None
            self.attendance_button.configure(state="normal" if dto["permitido"] else "disabled")
            return dto
        self._access_selection_changed()
        return self._guard(action)

    def register_attendance(self):
        def action():
            identifier = self.access_selector.value()
            if self._verified_id != identifier:
                raise InputError("Verifica el acceso del socio seleccionado antes de registrar su asistencia.")
            if not self.notifier.confirm("Registrar asistencia", "¿Confirmas el ingreso de este socio?"):
                return None
            result = self.service.registrar_asistencia(identifier)
            self.notifier.show("Asistencia registrada correctamente.", "success")
            self.attendance_button.configure(state="disabled")
            self._verified_id = None
            return result
        result = self._guard(action)
        if result is _FAILED:
            self._access_selection_changed()
        return result

    def _attendance(self):
        bar = tk.Frame(self.content, bg=Theme.BG)
        bar.pack(fill="x", pady=(0, 12))
        tk.Label(bar, text="Fecha · AAAA-MM-DD", bg=Theme.BG, fg=Theme.MUTED).pack(side="left", padx=(0, 10))
        self.attendance_date = tk.StringVar(bar, value=self._attendance_filter)
        ttk.Entry(bar, textvariable=self.attendance_date, style="Gym.TEntry", width=16).pack(side="left")
        Theme.button(bar, "Filtrar", self._apply_attendance_filter, "secondary").pack(side="left", padx=8)
        Theme.button(bar, "Hoy", self._attendance_today, "secondary").pack(side="left")
        Theme.button(bar, "Todas", self._attendance_all, "secondary").pack(side="left", padx=8)
        self._make_table((Column("socio", "SOCIO", 230), Column("documento", "DOCUMENTO", 130),
                          Column("fecha_hora", "FECHA Y HORA", 215, formatter=format_date)),
                         self.service.listar_asistencias(self._attendance_filter))

    def _apply_attendance_filter(self):
        value = self.attendance_date.get().strip()
        result = self._guard(lambda: self.service.listar_asistencias(value))
        if result is not _FAILED:
            self._attendance_filter = value
            self.table.set_rows(result)

    def _attendance_today(self):
        today = self._guard(self.service.fecha_actual)
        if today is not _FAILED:
            self.attendance_date.set(today)
            self._apply_attendance_filter()

    def _attendance_all(self):
        self.attendance_date.set("")
        self._apply_attendance_filter()

    def _expirations(self):
        def changed(key):
            self._expiration_filter = key
            self.refresh()
        self.expiration_combo = self._filter_bar("Seguimiento", {"Próximas a vencer": "PROXIMAS",
                   "Ya vencidas": "VENCIDA"}, self._expiration_filter, changed)
        self._make_table(self._membership_columns(),
                         self._membership_rows(self.service.listar_membresias(self._expiration_filter)),
                         ("socio", "documento", "plan", "estado_visible"))
        self._section("Información lista para actuar", "El criterio de vencimientos lo define la célula de servicios.")

    def open_form(self, kind):
        def action():
            if self.active_form and self.active_form.winfo_exists():
                self.active_form.lift()
                return self.active_form
            if kind == "socio":
                title, method = "Registrar socio", self.service.registrar_socio
                fields = (FieldSpec("nombre", "Nombre"), FieldSpec("apellido", "Apellido"),
                          FieldSpec("documento", "Documento", hint="Identificación única del socio."),
                          FieldSpec("telefono", "Teléfono", required=False),
                          FieldSpec("correo", "Correo electrónico", "email", required=False))
            elif kind == "plan":
                title, method = "Registrar plan", self.service.registrar_plan
                fields = (FieldSpec("nombre", "Nombre del plan"),
                          FieldSpec("precio", "Precio · S/", "money", hint="Ejemplo: 89.90"),
                          FieldSpec("duracion_dias", "Duración · días", "integer"))
            elif kind == "membresia":
                socios, planes = self.service.listar_socios(), self.service.listar_planes()
                if not socios or not planes:
                    raise InputError("Registra al menos un socio y un plan antes de crear una membresía.")
                title, method = "Registrar membresía", self.service.registrar_membresia
                fields = (FieldSpec("socio_id", "Socio", "choice", choices=self._member_choices(socios)),
                          FieldSpec("plan_id", "Plan", "choice",
                                    choices=tuple((p["id"], f"{p['nombre']} · {p['duracion_dias']} días · "
                                                   f"{format_money(p['precio'])}") for p in planes)),
                          FieldSpec("fecha_inicio", "Fecha de inicio", "date",
                                    default=self.service.fecha_actual(), hint="Formato: AAAA-MM-DD"))
            elif kind == "entrenador":
                title, method = "Registrar entrenador", self.service.registrar_entrenador
                fields = (FieldSpec("nombre", "Nombre completo"), FieldSpec("especialidad", "Especialidad"))
            else:
                raise InputError("Formulario no reconocido.")
            self.active_form = FormDialog(self.root, title, fields, self._save_callback(method),
                                           subtitle="Los campos con * son obligatorios.")
            return self.active_form
        return self._guard(action)

    def _save_callback(self, method):
        def save(payload):
            try:
                method(**payload)
            except DomainError as exc:
                return str(exc)
            except Exception:
                traceback.print_exc()
                return "No se pudo guardar. Revisa la conexión con el servicio y vuelve a intentar."
            # El diálogo se destruye después de que este callback regresa.
            self.active_form = None
            self.refresh()
            self.notifier.show("Registro guardado correctamente.", "success")
            return None
        return save
