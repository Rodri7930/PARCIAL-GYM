

from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re
import tkinter as tk
from tkinter import messagebox, ttk
import traceback
import unicodedata

__all__ = ["Theme", "FieldSpec", "Column", "StatCard", "HeroBanner",
           "DataTable", "EntitySelector", "FormDialog", "AccessResult",
           "Notifier", "InputError", "format_date", "format_money"]


class InputError(ValueError):
    """Formato o selección inválidos; las reglas comerciales van en Services."""


def _search_text(value):
    normalized = unicodedata.normalize("NFKD", str(value).casefold())
    return "".join(c for c in normalized if not unicodedata.combining(c))


def format_date(value):
    """ISO a DD/MM/AAAA; si incluye hora, también muestra HH:MM."""
    if not value:
        return "—"
    try:
        text = str(value)
        if "T" in text:
            return datetime.fromisoformat(text).strftime("%d/%m/%Y  %H:%M")
        return date.fromisoformat(text).strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return str(value)


def format_money(value):
    """Presentación decimal; no determina precios ni cobra operaciones."""
    try:
        amount = Decimal(str(value))
        if not amount.is_finite():
            return "—"
        return f"S/ {amount:,.2f}"
    except (InvalidOperation, ValueError, TypeError):
        return str(value)


class Theme:
    NAVY = "#111B2E"
    NAV_ACTIVE = "#25324B"
    BG = "#F2F5FA"
    SURFACE = "#FFFFFF"
    TEXT = "#18253B"
    MUTED = "#627087"
    BORDER = "#DFE6F0"
    TEAL = "#0D8C82"
    MINT = "#68E0C4"
    CORAL = "#EE795F"
    PURPLE = "#7661BD"
    SUCCESS = "#176A50"
    WARNING = "#99600D"
    ERROR = "#B23D51"
    FONT = "Segoe UI"

    @classmethod
    def apply(cls, root):
        root.configure(bg=cls.BG)
        root.option_add("*Font", (cls.FONT, 10))
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("Gym.TEntry", padding=9, fieldbackground=cls.SURFACE,
                        foreground=cls.TEXT, bordercolor=cls.BORDER,
                        lightcolor=cls.BORDER, darkcolor=cls.BORDER)
        style.map("Gym.TEntry", bordercolor=[("focus", cls.TEAL)])
        style.configure("Gym.TCombobox", padding=8, fieldbackground=cls.SURFACE,
                        foreground=cls.TEXT, background=cls.BORDER, bordercolor=cls.BORDER)
        style.map("Gym.TCombobox", fieldbackground=[("readonly", cls.SURFACE)],
                  foreground=[("readonly", cls.TEXT)], selectbackground=[("!disabled", cls.SURFACE)],
                  selectforeground=[("!disabled", cls.TEXT)])
        style.configure("Gym.Treeview", rowheight=38, background=cls.SURFACE,
                        fieldbackground=cls.SURFACE, foreground=cls.TEXT,
                        borderwidth=0, font=(cls.FONT, 10))
        style.configure("Gym.Treeview.Heading", background="#EAF0F7", foreground=cls.MUTED,
                        font=(cls.FONT, 9, "bold"), relief="flat", padding=(10, 10))
        style.map("Gym.Treeview", background=[("selected", "#D8F1EA")],
                  foreground=[("selected", cls.TEXT)])
        style.map("Gym.Treeview.Heading", background=[("active", "#DDE7F3")])
        style.configure("Gym.Vertical.TScrollbar", background=cls.BORDER,
                        troughcolor=cls.BG, borderwidth=0, arrowsize=12)

    @classmethod
    def button(cls, parent, text, command, variant="primary", **kwargs):
        palettes = {"primary": (cls.TEAL, "white", "#08776F"),
                    "secondary": ("#E8EEF6", cls.TEXT, "#DCE5F0"),
                    "dark": (cls.NAV_ACTIVE, "white", "#354662"),
                    "coral": (cls.CORAL, cls.NAVY, "#E56D53")}
        bg, fg, active = palettes[variant]
        options = dict(bg=bg, fg=fg, activebackground=active, activeforeground=fg,
                       relief="flat", bd=0, font=(cls.FONT, 10, "bold"),
                       padx=17, pady=11, cursor="hand2", takefocus=True,
                       highlightthickness=2, highlightbackground=bg, highlightcolor=cls.PURPLE)
        options.update(kwargs)
        button = tk.Button(parent, text=text, command=command, **options)
        def keyboard_invoke(_event):
            button.invoke()
            return "break"
        button.bind("<Return>", keyboard_invoke)
        return button


@dataclass(frozen=True)
class FieldSpec:
    key: str
    label: str
    kind: str = "text"
    required: bool = True
    choices: tuple = ()
    default: str = ""
    hint: str = ""


@dataclass(frozen=True)
class Column:
    key: str
    title: str
    width: int = 140
    anchor: str = "w"
    formatter: object = None


class StatCard(tk.Frame):
    def __init__(self, parent, label, value, detail, accent):
        super().__init__(parent, bg=Theme.SURFACE, highlightthickness=1,
                         highlightbackground=Theme.BORDER)
        tk.Frame(self, height=4, bg=accent).pack(fill="x")
        body = tk.Frame(self, bg=Theme.SURFACE)
        body.pack(fill="both", expand=True, padx=18, pady=15)
        self.label = tk.Label(body, text=label.upper(), bg=Theme.SURFACE, fg=Theme.MUTED,
                              font=(Theme.FONT, 9, "bold"), anchor="w")
        self.label.pack(fill="x")
        self.number = tk.Label(body, text=str(value), bg=Theme.SURFACE, fg=Theme.TEXT,
                               font=(Theme.FONT, 29, "bold"), anchor="w")
        self.number.pack(fill="x", pady=(5, 1))
        self.detail = tk.Label(body, text=detail, bg=Theme.SURFACE, fg=Theme.MUTED,
                               font=(Theme.FONT, 9), anchor="w", justify="left")
        self.detail.pack(fill="x")
        self.bind("<Configure>", lambda e: self.detail.configure(wraplength=max(90, e.width - 40)))


class HeroBanner(tk.Canvas):
    """Ilustración vectorial original; sin imágenes ni recursos externos."""

    def __init__(self, parent, title, subtitle, kicker="OPERACIÓN DIARIA"):
        super().__init__(parent, height=180, bg=Theme.NAVY, highlightthickness=0)
        self.title, self.subtitle, self.kicker = title, subtitle, kicker
        self.bind("<Configure>", self._draw)

    def _draw(self, event):
        self.delete("all")
        width = event.width
        self.create_oval(width - 310, -140, width + 80, 250, fill="#1A3447", outline="")
        self.create_oval(width - 215, -67, width + 22, 170, outline=Theme.MINT, width=2)
        self.create_oval(width - 169, -21, width - 26, 122, outline=Theme.CORAL, width=6)
        self.create_line(width - 180, 149, width - 75, 44, fill=Theme.MINT, width=7)
        self.create_oval(width - 81, 128, width - 56, 153, fill=Theme.PURPLE, outline="")
        self.create_text(25, 25, text=self.kicker, anchor="nw", fill=Theme.MINT,
                         font=(Theme.FONT, 9, "bold"))
        title = self.create_text(25, 54, text=self.title, anchor="nw", fill="white",
                                 font=(Theme.FONT, 24 if width > 900 else 21, "bold"),
                                 width=max(200, width - 245), tags="title_text")
        subtitle_y = max(110, self.bbox(title)[3] + 15)
        subtitle = self.create_text(25, subtitle_y, text=self.subtitle, anchor="nw", fill="#CEDAE9",
                                    font=(Theme.FONT, 10), width=max(200, width - 245),
                                    tags="subtitle_text")
        desired_height = max(155, self.bbox(subtitle)[3] + 24)
        if int(self["height"]) != desired_height:
            self.configure(height=desired_height)


class DataTable(tk.Frame):
    def __init__(self, parent, columns, search_keys=None, on_select=None):
        super().__init__(parent, bg=Theme.SURFACE, highlightbackground=Theme.BORDER,
                         highlightthickness=1)
        self.columns = tuple(columns)
        self.search_keys = tuple(search_keys or [column.key for column in self.columns])
        self.on_select = on_select
        self._rows, self._visible = [], []
        self._sort_key, self._descending = None, False
        top = tk.Frame(self, bg=Theme.SURFACE)
        top.pack(fill="x", padx=16, pady=14)
        tk.Label(top, text="BUSCAR", bg=Theme.SURFACE, fg=Theme.MUTED,
                 font=(Theme.FONT, 9, "bold")).pack(side="left", padx=(0, 12))
        self.query = tk.StringVar(self)
        self.search = ttk.Entry(top, textvariable=self.query, style="Gym.TEntry", width=26)
        self.search.pack(side="left", fill="x", expand=True)
        self.clear_button = Theme.button(top, "Limpiar", self.clear_query, "secondary", padx=10, pady=7)
        self.clear_button.pack(side="left", padx=(8, 0))
        self.search.bind("<Escape>", self.clear_query)
        self.count = tk.Label(top, text="", bg=Theme.SURFACE, fg=Theme.MUTED,
                              font=(Theme.FONT, 9))
        self.count.pack(side="right", padx=(12, 0))
        container = tk.Frame(self, bg=Theme.SURFACE)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(container, columns=[c.key for c in self.columns], show="headings",
                                 selectmode="browse", style="Gym.Treeview", height=8)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vertical = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview,
                                 style="Gym.Vertical.TScrollbar")
        horizontal = ttk.Scrollbar(container, orient="horizontal", command=self.tree.xview)
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        self.tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        for col in self.columns:
            self.tree.heading(col.key, text=col.title,
                              command=lambda key=col.key: self.sort_by(key))
            self.tree.column(col.key, width=col.width, minwidth=85, anchor=col.anchor, stretch=True)
        self.tree.tag_configure("odd", background="#F6F8FC")
        self.tree.tag_configure("even", background="white")
        self.tree.tag_configure("VENCIDA", foreground=Theme.ERROR)
        self.tree.tag_configure("PROGRAMADA", foreground=Theme.PURPLE)
        self.empty = tk.Label(self, text="", bg=Theme.SURFACE, fg=Theme.MUTED, pady=12)
        self.empty.pack(fill="x", padx=16)
        self.tree.bind("<<TreeviewSelect>>", self._selection_changed)
        self.query.trace_add("write", lambda *_: self._render())
        self.set_rows([])

    def set_rows(self, rows):
        self._rows = deepcopy(list(rows))
        self._render()

    def set_query(self, text):
        self.query.set(text)

    def clear_query(self, _event=None):
        """Recupera todos los registros y devuelve el foco al buscador."""
        self.query.set("")
        self.search.focus_set()
        return "break"

    def visible_rows(self):
        return deepcopy(self._visible)

    def sort_by(self, key):
        self._descending = not self._descending if self._sort_key == key else False
        self._sort_key = key
        self._render()

    def _render(self):
        query = _search_text(self.query.get()).strip()
        rows = [row for row in self._rows if not query or query in
                _search_text(" ".join(str(row.get(k, "")) for k in self.search_keys))]
        if self._sort_key:
            def sort_value(row):
                value = row.get(self._sort_key, "")
                try:
                    number = Decimal(str(value))
                    if number.is_finite():
                        return (0, number)
                except InvalidOperation:
                    pass
                return (1, _search_text(value))
            rows.sort(key=sort_value, reverse=self._descending)
        for column in self.columns:
            indicator = (" ▼" if self._descending else " ▲") if column.key == self._sort_key else ""
            self.tree.heading(column.key, text=column.title + indicator)
        self.clear_button.configure(state="normal" if self.query.get() else "disabled")
        previous = self.selected_row()
        previous_id = previous.get("id") if previous else None
        self._visible = rows
        children = self.tree.get_children()
        if children:
            self.tree.delete(*children)
        for index, row in enumerate(rows):
            values = []
            for column in self.columns:
                value = row.get(column.key, "")
                values.append(column.formatter(value) if column.formatter else value)
            tags = ("odd" if index % 2 else "even", str(row.get("estado", "")))
            self.tree.insert("", "end", iid=str(index), values=values, tags=tags)
            if previous_id is not None and row.get("id") == previous_id:
                self.tree.selection_set(str(index))
        self.count.configure(text=f"{len(rows)} / {len(self._rows)} registros")
        self.empty.configure(text=("Sin resultados para esta búsqueda." if self._rows else
                                   "Todavía no hay registros. Puedes comenzar con el botón de registro.")
                             if not rows else "Selecciona una fila · Pulsa un encabezado para ordenar")

    def selected_row(self):
        selected = self.tree.selection()
        if selected:
            index = int(selected[0])
            if index < len(self._visible):
                return deepcopy(self._visible[index])
        return None

    def _selection_changed(self, _event=None):
        if self.on_select:
            self.on_select(self.selected_row())


class EntitySelector(tk.Frame):
    """Selección con búsqueda; el identificador se guarda separado de la etiqueta."""

    def __init__(self, parent, label, choices):
        super().__init__(parent, bg=Theme.SURFACE)
        tk.Label(self, text=label, bg=Theme.SURFACE, fg=Theme.TEXT,
                 font=(Theme.FONT, 10, "bold"), anchor="w").pack(fill="x", pady=(0, 6))
        self.variable = tk.StringVar(self)
        self.combo = ttk.Combobox(self, textvariable=self.variable, style="Gym.TCombobox")
        self.combo.pack(fill="x")
        self._change = None
        self._labels, self._by_id = {}, {}
        self.combo.bind("<<ComboboxSelected>>", self._changed)
        self.combo.bind("<KeyRelease>", self._typed)
        self.set_choices(choices)

    def set_choices(self, choices):
        missing = object()
        previous_text = self.variable.get()
        previous_id = self._labels.get(previous_text, missing)
        labels, by_id = {}, {}
        for identifier, label in choices:
            display = str(label)
            if display in labels:
                display += f" · {identifier}"
                base, suffix = display, 2
                while display in labels:
                    display = f"{base} ({suffix})"
                    suffix += 1
            labels[display] = identifier
            by_id[identifier] = display
        self._labels, self._by_id = labels, by_id
        preserved = previous_id is not missing and previous_id in by_id
        self.variable.set(by_id[previous_id] if preserved else "")
        self.combo.configure(values=tuple(labels), state="normal" if labels else "disabled")
        if not preserved and (previous_id is not missing or previous_text):
            self._notify_change()

    def value(self):
        label = self.variable.get()
        if label not in self._labels:
            raise InputError("Selecciona una opción existente de la lista.")
        return self._labels[label]

    def select(self, identifier):
        if identifier not in self._by_id:
            raise InputError("La selección no existe.")
        self.variable.set(self._by_id[identifier])
        self._changed()

    def bind_change(self, callback):
        self._change = callback

    def _changed(self, _event=None):
        # Tras elegir un resultado, la próxima apertura vuelve a ofrecer toda la lista.
        self.combo.configure(values=tuple(self._labels))
        self._notify_change()

    def _notify_change(self):
        if self._change:
            self._change()

    def _typed(self, _event=None):
        if _event and _event.keysym in ("Return", "KP_Enter", "Tab", "Escape", "Up", "Down",
                                       "Left", "Right", "Home", "End"):
            return
        query = _search_text(self.variable.get())
        self.combo.configure(values=tuple(label for label in self._labels
                                          if query in _search_text(label)))
        self._notify_change()


class FormDialog(tk.Toplevel):
    def __init__(self, parent, title, fields, on_submit, subtitle=""):
        super().__init__(parent)
        self.title(title + " · NEXO GYM")
        self.configure(bg=Theme.SURFACE)
        self.transient(parent)
        self.resizable(False, False)
        self.fields, self.on_submit = tuple(fields), on_submit
        self.variables, self.controls = {}, {}
        self._submitting = False
        self._invalid_field = None
        header = tk.Frame(self, bg=Theme.NAVY)
        header.pack(fill="x")
        tk.Label(header, text=title, bg=Theme.NAVY, fg="white",
                 font=(Theme.FONT, 18, "bold"), anchor="w").pack(fill="x", padx=24, pady=(20, 4))
        tk.Label(header, text=subtitle or "Completa los datos para continuar.", bg=Theme.NAVY,
                 fg="#C6D3E4", wraplength=460, justify="left", anchor="w").pack(
                     fill="x", padx=24, pady=(0, 18))
        body = tk.Frame(self, bg=Theme.SURFACE)
        body.pack(fill="both", expand=True, padx=24, pady=18)
        for field in self.fields:
            slot = tk.Frame(body, bg=Theme.SURFACE)
            slot.pack(fill="x", pady=(0, 11))
            label = field.label + (" *" if field.required else " · opcional")
            if field.kind == "choice":
                selector = EntitySelector(slot, label, field.choices)
                selector.pack(fill="x")
                self.controls[field.key] = selector
                if field.default:
                    selector.select(field.default)
            else:
                tk.Label(slot, text=label, bg=Theme.SURFACE, fg=Theme.TEXT,
                         font=(Theme.FONT, 10, "bold"), anchor="w").pack(fill="x", pady=(0, 5))
                variable = tk.StringVar(self, value=field.default)
                entry = ttk.Entry(slot, textvariable=variable, style="Gym.TEntry", width=45)
                entry.pack(fill="x")
                self.variables[field.key], self.controls[field.key] = variable, entry
            if field.hint:
                tk.Label(slot, text=field.hint, bg=Theme.SURFACE, fg=Theme.MUTED,
                         anchor="w", font=(Theme.FONT, 9)).pack(fill="x", pady=(4, 0))
        self.error = tk.Label(body, text="", bg=Theme.SURFACE, fg=Theme.ERROR,
                              anchor="w", justify="left", wraplength=450)
        self.error.pack(fill="x", pady=(0, 5))
        for field in self.fields:
            if field.key in self.variables:
                self.variables[field.key].trace_add("write", lambda *_, key=field.key: self._field_changed(key))
            else:
                self.controls[field.key].bind_change(lambda key=field.key: self._field_changed(key))
        footer = tk.Frame(body, bg=Theme.SURFACE)
        footer.pack(fill="x", pady=(4, 0))
        Theme.button(footer, "Cancelar", self.destroy, "secondary").pack(side="left")
        self.save = Theme.button(footer, "Guardar registro", self.submit)
        self.save.pack(side="right")
        self.bind("<Escape>", lambda event: self.destroy())
        self.bind("<Return>", self._enter)
        self.update_idletasks()
        x = max(0, parent.winfo_rootx() + (parent.winfo_width() - self.winfo_reqwidth()) // 2)
        y = max(0, parent.winfo_rooty() + (parent.winfo_height() - self.winfo_reqheight()) // 2)
        self.geometry(f"+{x}+{y}")
        self.grab_set()
        if self.fields:
            control = self.controls[self.fields[0].key]
            (control.combo if isinstance(control, EntitySelector) else control).focus_set()

    def set_value(self, key, value):
        if key in self.variables:
            self.variables[key].set(value)
        else:
            self.controls[key].select(value)

    def _enter(self, _event):
        self.submit()
        return "break"

    @staticmethod
    def _validate(field, value):
        value = value.strip()
        if not value:
            if field.required:
                raise InputError(f"{field.label}: completa este campo.")
            return ""
        if len(value) > 200 or any(ord(c) < 32 for c in value):
            raise InputError(f"{field.label}: el texto es demasiado largo o contiene controles.")
        if field.kind == "email" and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise InputError(f"{field.label}: usa una dirección de correo válida.")
        if field.kind == "date":
            try:
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                    raise ValueError
                date.fromisoformat(value)
            except ValueError as exc:
                raise InputError(f"{field.label}: usa una fecha válida AAAA-MM-DD.") from exc
        if field.kind == "integer" and not re.fullmatch(r"[0-9]+", value):
            raise InputError(f"{field.label}: usa un número entero sin decimales.")
        if field.kind == "money":
            if not re.fullmatch(r"[0-9]+(?:[.,][0-9]{1,2})?", value):
                raise InputError(f"{field.label}: usa un importe con hasta dos decimales.")
            value = value.replace(",", ".")
        return value

    def _read_field(self, field):
        control = self.controls[field.key]
        if field.kind == "choice":
            try:
                return "" if not field.required and not control.variable.get() else control.value()
            except InputError as exc:
                raise InputError(f"{field.label}: selecciona una opción de la lista.") from exc
        return self._validate(field, self.variables[field.key].get())

    def values(self):
        result = {}
        self._invalid_field = None
        for field in self.fields:
            try:
                result[field.key] = self._read_field(field)
            except InputError:
                self._invalid_field = field.key
                raise
        return result

    def _field_changed(self, key):
        if self._submitting or not self.error["text"]:
            return
        if self._invalid_field is not None:
            if key != self._invalid_field:
                return
            field = next(field for field in self.fields if field.key == key)
            try:
                self._read_field(field)
            except InputError:
                return
        self.error.configure(text="")
        self._invalid_field = None

    def _focus_invalid_field(self):
        if self._invalid_field is not None:
            control = self.controls[self._invalid_field]
            widget = control.combo if isinstance(control, EntitySelector) else control
            widget.focus_set()
            widget.selection_range(0, tk.END)

    def _is_open(self):
        try:
            return bool(self.winfo_exists())
        except tk.TclError:
            return False

    def submit(self):
        if self._submitting or not self._is_open():
            return False
        try:
            payload = self.values()
        except InputError as exc:
            self.error.configure(text=str(exc))
            self._focus_invalid_field()
            return False
        self._submitting = True
        self.error.configure(text="")
        self.save.configure(state="disabled")
        try:
            try:
                error = self.on_submit(payload)
            except InputError as exc:
                error = str(exc)
            except Exception:
                traceback.print_exc()
                error = "No se pudo guardar. Revisa la operación e inténtalo nuevamente."
            if not self._is_open():
                return error is None
            if error is not None:
                self.error.configure(text=str(error))
                return False
            self.destroy()
            return True
        finally:
            self._submitting = False
            if self._is_open():
                self.save.configure(state="normal")


class AccessResult(tk.Frame):
    """Presenta la decisión del servicio sin volver a calcularla."""

    def __init__(self, parent):
        super().__init__(parent, bg="#EAF0F7", padx=24, pady=22)
        self.title = tk.Label(self, bg=self["bg"], fg=Theme.TEXT,
                              font=(Theme.FONT, 20, "bold"), anchor="w")
        self.title.pack(fill="x")
        self.name = tk.Label(self, bg=self["bg"], fg=Theme.TEXT,
                             font=(Theme.FONT, 12, "bold"), anchor="w")
        self.name.pack(fill="x", pady=(9, 4))
        self.message = tk.Label(self, bg=self["bg"], fg=Theme.MUTED,
                                anchor="w", justify="left", wraplength=500)
        self.message.pack(fill="x")
        self.reset()
        self.bind("<Configure>", lambda e: self.message.configure(wraplength=max(150, e.width - 50)))

    def reset(self):
        self.result = None
        self.configure(bg="#EAF0F7")
        self.title.configure(text="Listo para verificar", fg=Theme.TEXT, bg=self["bg"])
        self.name.configure(text="Selecciona un socio", bg=self["bg"])
        self.message.configure(text="La autorización se consultará en el servicio.", bg=self["bg"])

    def show_result(self, dto):
        self.result = deepcopy(dto)
        allowed = dto["permitido"]
        background, color = ("#DFF3EB", Theme.SUCCESS) if allowed else ("#FCE8EB", Theme.ERROR)
        self.configure(bg=background)
        self.title.configure(text="ACCESO PERMITIDO" if allowed else "ACCESO DENEGADO",
                             fg=color, bg=background)
        self.name.configure(text=dto["socio"], bg=background)
        self.message.configure(text=dto["mensaje"], bg=background)


class Notifier(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#E7EEF8", padx=15, pady=10)
        self.message = ""
        self.kind = "info"
        self.label = tk.Label(self, text="", bg=self["bg"], fg=Theme.TEXT,
                              anchor="w", justify="left", font=(Theme.FONT, 10))
        self.label.pack(fill="x")
        self.bind("<Configure>", lambda e: self.label.configure(wraplength=max(100, e.width - 32)))

    def show(self, message, kind="info"):
        palette = {"info": ("#E7EEF8", Theme.TEXT), "success": ("#DFF3EB", Theme.SUCCESS),
                   "warning": ("#FFF0D9", Theme.WARNING), "error": ("#FCE8EB", Theme.ERROR)}
        bg, fg = palette[kind]
        self.message, self.kind = str(message), kind
        self.configure(bg=bg)
        self.label.configure(text=self.message, bg=bg, fg=fg)

    def clear(self):
        self.show("", "info")

    def confirm(self, title, message):
        return messagebox.askyesno(title, message, parent=self.winfo_toplevel())
