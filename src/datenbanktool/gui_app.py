from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from datenbanktool.gui_assistant import AssistantTimeline
from datenbanktool.gui_model import NAVIGATION, NEON_ARCHIVE_THEME, WORKSPACE_TABS
from datenbanktool.gui_presets import DEFAULT_PRESETS
from datenbanktool.gui_quality import quality_gate_passed
from datenbanktool.gui_readonly import GuiFileRow, GuiSummary, ReadOnlyIndexAdapter
from datenbanktool.gui_testlab import run_validation


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="datenbanktool gui",
        description="Öffnet die additive, rein lesende Desktop-Oberfläche.",
    )
    parser.add_argument(
        "--database",
        type=Path,
        help="Vorhandenen SQLite-Index ausschließlich lesend anzeigen.",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=250,
        help="Maximal 1 bis 2000 Dateizeilen in der Detailansicht laden.",
    )
    return parser


def _format_bytes(value: int) -> str:
    amount = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if abs(amount) < 1024.0 or unit == "PB":
            return f"{amount:.2f} {unit}"
        amount /= 1024.0
    return f"{amount:.2f} PB"


def _demo_summary() -> GuiSummary:
    return GuiSummary(
        database="Demo / kein Index gewählt",
        session_id=None,
        root="Alte HDD-Sammlung",
        status="demo",
        phase="preview",
        file_count=12_842_991,
        folder_count=1_248_731,
        total_bytes=6_320_000_000_000,
        duplicate_groups=3_421,
        duplicate_files=12_842,
        duplicate_bytes=1_870_000_000_000,
        warning_count=218,
        error_count=0,
        unknown_count=2_451,
        large_count=1_245,
        updated_utc=None,
    )


def _demo_rows() -> tuple[GuiFileRow, ...]:
    return (
        GuiFileRow(1, "Fotos/Urlaub/2020/IMG_2020_1234.JPG", 12_450_000, "2020-08-12", ".jpg", "image", False, 0, 124),
        GuiFileRow(2, "Backup/Fotos/Urlaub/2020/IMG_2020_1234_Kopie.JPG", 12_450_000, "2020-08-12", ".jpg", "image", False, 0, 124),
        GuiFileRow(3, "Videos/2019/Video_2019_0001.mp4", 1_250_000_000, "2019-11-03", ".mp4", "video", True, 0, 557),
        GuiFileRow(4, "Dokumente/Projekte/Dokument_Version1.docx", 2_340_000, "2018-02-21", ".docx", "document", False, 1, None),
    )


def _load_workspace(database: Path | None, rows: int) -> tuple[GuiSummary, tuple[GuiFileRow, ...], str | None]:
    if rows < 1 or rows > 2000:
        raise ValueError("--rows muss zwischen 1 und 2000 liegen")
    if database is None:
        return _demo_summary(), _demo_rows(), "Demoansicht — mit --database echten Index rein lesend öffnen"
    try:
        adapter = ReadOnlyIndexAdapter(database)
        return adapter.summary(), adapter.files(limit=rows), None
    except (FileNotFoundError, OSError, ValueError) as error:
        return _demo_summary(), _demo_rows(), f"Index konnte nicht gelesen werden: {error}"


def run_gui(argv: Sequence[str] | None = None) -> int:
    """Open the additive desktop shell without changing the safe CLI core."""
    arguments = _parser().parse_args(list(argv or ()))
    summary, rows, load_notice = _load_workspace(arguments.database, arguments.rows)
    test_report = run_validation()
    assistant_model = AssistantTimeline()
    assistant_message = assistant_model.explain_scan(
        files=summary.file_count,
        warnings=summary.warning_count,
        errors=summary.error_count,
    )

    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError as error:  # pragma: no cover - platform dependent
        raise RuntimeError("Die grafische Oberfläche benötigt Tk/Tkinter.") from error

    theme = NEON_ARCHIVE_THEME
    root = tk.Tk()
    root.title("DATENBANKTOOL — Duplikate, Umbenennen & Listen")
    root.geometry("1500x900")
    root.minsize(1180, 720)
    root.configure(bg=theme.background)

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(
        "Treeview",
        background=theme.panel,
        fieldbackground=theme.panel,
        foreground=theme.text,
        rowheight=28,
    )
    style.configure("Treeview.Heading", background=theme.panel_alt, foreground=theme.accent)

    root.columnconfigure(1, weight=1)
    root.rowconfigure(0, weight=1)

    nav = tk.Frame(root, bg=theme.panel, padx=12, pady=16, width=220)
    nav.grid(row=0, column=0, sticky="ns")
    nav.grid_propagate(False)
    tk.Label(
        nav, text="DATENBANKTOOL", bg=theme.panel, fg=theme.accent,
        font=("Sans", 18, "bold"),
    ).pack(anchor="w", pady=(0, 18))
    for label in NAVIGATION:
        active = label == "Duplikate & Umbenennen"
        tk.Label(
            nav,
            text=label,
            bg=theme.accent_soft if active else theme.panel,
            fg="#00120d" if active else theme.text,
            padx=10,
            pady=9,
            anchor="w",
            font=("Sans", 10, "bold" if active else "normal"),
        ).pack(fill="x", pady=2)

    tk.Label(
        nav,
        text=f"QUALITÄTSGATE\n{'GRÜN' if quality_gate_passed() else 'PRÜFEN'}",
        bg=theme.panel_alt,
        fg=theme.success if quality_gate_passed() else theme.warning,
        justify="left",
        padx=10,
        pady=10,
    ).pack(side="bottom", fill="x")

    center = tk.Frame(root, bg=theme.background, padx=14, pady=14)
    center.grid(row=0, column=1, sticky="nsew")
    center.columnconfigure(0, weight=1)
    center.rowconfigure(4, weight=1)

    header = tk.Frame(
        center, bg=theme.panel, highlightthickness=1,
        highlightbackground=theme.border, padx=16, pady=12,
    )
    header.grid(row=0, column=0, sticky="ew")
    tk.Label(
        header, text="Duplikate, Umbenennen & Listen — Workspace",
        bg=theme.panel, fg=theme.text, font=("Sans", 19, "bold"),
    ).pack(anchor="w")
    root_label = summary.root or "Noch kein Scan im Index"
    tk.Label(
        header,
        text=f"Projekt/Quelle: {root_label} · Index: {summary.database} · strikt rein lesende GUI-Abfrage",
        bg=theme.panel, fg=theme.muted,
    ).pack(anchor="w", pady=(4, 0))
    if load_notice:
        tk.Label(header, text=load_notice, bg=theme.panel, fg=theme.warning).pack(anchor="w", pady=(4, 0))

    cards_data = (
        ("Dateien", f"{summary.file_count:,}".replace(",", "."), _format_bytes(summary.total_bytes)),
        ("Duplikat-Gruppen", f"{summary.duplicate_groups:,}".replace(",", "."), f"{summary.duplicate_files:,} Dateien".replace(",", ".")),
        ("Aufräumpotenzial", _format_bytes(summary.duplicate_bytes), "nur exakte Indexgruppen"),
        ("Große Dateien", f"{summary.large_count:,}".replace(",", "."), f"{summary.warning_count:,} Hinweise".replace(",", ".")),
        ("Unbekannt", f"{summary.unknown_count:,}".replace(",", "."), f"{summary.error_count} Scanfehler"),
    )
    cards = tk.Frame(center, bg=theme.background)
    cards.grid(row=1, column=0, sticky="ew", pady=12)
    for index, (title, value, detail_text) in enumerate(cards_data):
        cards.columnconfigure(index, weight=1)
        frame = tk.Frame(
            cards, bg=theme.panel_alt, highlightthickness=1,
            highlightbackground=theme.border, padx=14, pady=10,
        )
        frame.grid(row=0, column=index, sticky="ew", padx=(0 if index == 0 else 6, 0))
        tk.Label(frame, text=title, bg=theme.panel_alt, fg=theme.muted).pack(anchor="w")
        tk.Label(
            frame, text=value, bg=theme.panel_alt, fg=theme.accent,
            font=("Sans", 16, "bold"),
        ).pack(anchor="w")
        tk.Label(frame, text=detail_text, bg=theme.panel_alt, fg=theme.text).pack(anchor="w")

    presets = tk.Frame(
        center, bg=theme.panel, highlightthickness=1,
        highlightbackground=theme.border, padx=10, pady=8,
    )
    presets.grid(row=2, column=0, sticky="ew")
    tk.Label(
        presets, text="SCHNELLMODI", bg=theme.panel, fg=theme.accent,
        font=("Sans", 10, "bold"),
    ).pack(side="left", padx=(0, 10))
    for preset in DEFAULT_PRESETS[:5]:
        tk.Button(
            presets, text=preset.title, bg=theme.panel_alt, fg=theme.text,
            relief="flat", padx=8, pady=5,
        ).pack(side="left", padx=(0, 5))

    tools = tk.Frame(
        center, bg=theme.panel, highlightthickness=1,
        highlightbackground=theme.border, padx=12, pady=10,
    )
    tools.grid(row=3, column=0, sticky="ew", pady=(10, 0))
    for index, tab in enumerate(WORKSPACE_TABS):
        tk.Button(
            tools, text=tab,
            bg=theme.success if index == 0 else theme.panel_alt,
            fg="#00120d" if index == 0 else theme.text,
            relief="flat", padx=12, pady=7,
        ).pack(side="left", padx=(0, 6))
    search = tk.Entry(
        tools, bg="#041014", fg=theme.text,
        insertbackground=theme.text, relief="flat",
    )
    search.insert(0, "Suche Datei, Pfad, Typ oder Kategorie …")
    search.pack(side="left", fill="x", expand=True, padx=8)

    detail = tk.Frame(
        center, bg=theme.panel, highlightthickness=1,
        highlightbackground=theme.border, padx=10, pady=10,
    )
    detail.grid(row=4, column=0, sticky="nsew", pady=(10, 0))
    detail.rowconfigure(0, weight=1)
    detail.columnconfigure(0, weight=1)
    columns = ("Dateiname", "Pfad", "Größe", "Datum", "Typ", "Status", "Aktion")
    tree = ttk.Treeview(detail, columns=columns, show="headings")
    for name in columns:
        tree.heading(name, text=name)
        tree.column(name, width=120 if name != "Pfad" else 300, anchor="w")
    for row in rows:
        path = Path(row.relative_path)
        status_parts: list[str] = []
        if row.duplicate_group_id is not None:
            status_parts.append(f"Duplikat #{row.duplicate_group_id}")
        if row.warning_count:
            status_parts.append(f"{row.warning_count} Hinweis")
        if row.is_large:
            status_parts.append("Groß")
        status = " · ".join(status_parts) or "Einzigartig"
        action = "Prüfen" if status_parts else "—"
        tree.insert(
            "", "end",
            values=(
                path.name, str(path.parent), _format_bytes(row.size_bytes), row.modified_utc,
                row.suffix.lstrip(".").upper() or row.category, status, action,
            ),
        )
    tree.grid(row=0, column=0, sticky="nsew")

    rename = tk.Frame(detail, bg=theme.panel_alt, padx=12, pady=10)
    rename.grid(row=1, column=0, sticky="ew", pady=(10, 0))
    tk.Label(
        rename, text="UMBENENNEN — VORSCHAU & REGEL",
        bg=theme.panel_alt, fg=theme.accent, font=("Sans", 11, "bold"),
    ).pack(anchor="w")
    tk.Label(
        rename,
        text="Regeln erzeugen ausschließlich eine Vorschau; keine Umbenennung aus dieser GUI-Schicht.",
        bg=theme.panel_alt, fg=theme.text,
    ).pack(anchor="w", pady=(5, 0))

    assistant = tk.Frame(
        root, bg=theme.panel, padx=14, pady=16, width=270,
        highlightthickness=1, highlightbackground=theme.border,
    )
    assistant.grid(row=0, column=2, sticky="ns")
    assistant.grid_propagate(False)
    tk.Label(
        assistant, text="ASSISTENT & TIPPS", bg=theme.panel,
        fg=theme.accent, font=("Sans", 12, "bold"),
    ).pack(anchor="w")
    tk.Label(
        assistant,
        text=f"{assistant_message.title}\n\n{assistant_message.body}",
        wraplength=235, justify="left", bg=theme.panel, fg=theme.text,
    ).pack(anchor="w", pady=12)
    for state in (
        "✓ Nur lesender Zugriff", "✓ Testlauf zuerst", "✓ Papierkorb-Konzept",
        "✓ Undo & Rollback-Vertrag", "✓ Protokollierung vorgesehen",
    ):
        tk.Label(assistant, text=state, bg=theme.panel, fg=theme.success, anchor="w").pack(fill="x", pady=2)

    tk.Label(
        assistant, text="TESTLABOR", bg=theme.panel, fg=theme.accent,
        font=("Sans", 11, "bold"),
    ).pack(anchor="w", pady=(18, 6))
    tk.Label(
        assistant,
        text=(
            f"Musterdateien: {test_report.files_seen}\n"
            f"Prüfungen: {test_report.passed} bestanden / {test_report.failed} fehlgeschlagen\n"
            f"Hinweise: {test_report.warnings}"
        ),
        justify="left", bg=theme.panel, fg=theme.text,
    ).pack(anchor="w")

    next_steps = assistant_model.next_steps(
        has_index=arguments.database is not None and load_notice is None,
        has_selection=False,
        test_passed=test_report.failed == 0,
    )
    tk.Label(
        assistant, text="NÄCHSTE SCHRITTE", bg=theme.panel, fg=theme.accent,
        font=("Sans", 11, "bold"),
    ).pack(anchor="w", pady=(18, 6))
    for index, step in enumerate(next_steps, 1):
        tk.Label(
            assistant, text=f"{index}. {step}", bg=theme.panel,
            fg=theme.text, anchor="w",
        ).pack(fill="x", pady=2)
    for action in ("Vorschau aktualisieren", "Testlauf öffnen", "Auswahl prüfen", "Sichere Simulation"):
        tk.Button(
            assistant, text=action, bg=theme.success,
            fg="#00120d", relief="flat", pady=8,
        ).pack(fill="x", pady=(8, 0))

    root.mainloop()
    return 0
