from __future__ import annotations

from collections.abc import Sequence

from datenbanktool.gui_model import NEXT_STEPS, SUMMARY_CARDS, WORKSPACE_TABS, NEON_ARCHIVE_THEME


def run_gui(argv: Sequence[str] | None = None) -> int:
    """Open the additive desktop shell without changing the safe CLI core."""
    del argv
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
    style.configure("Treeview", background=theme.panel, fieldbackground=theme.panel, foreground=theme.text, rowheight=28)
    style.configure("Treeview.Heading", background=theme.panel_alt, foreground=theme.accent)

    root.columnconfigure(1, weight=1)
    root.rowconfigure(0, weight=1)

    nav = tk.Frame(root, bg=theme.panel, padx=12, pady=16, width=220)
    nav.grid(row=0, column=0, sticky="ns")
    nav.grid_propagate(False)
    tk.Label(nav, text="DATENBANKTOOL", bg=theme.panel, fg=theme.accent, font=("Sans", 18, "bold")).pack(anchor="w", pady=(0, 18))
    for label in (
        "Analyse & Inventur",
        "Schnellmodi & Presets",
        "Duplikate & Umbenennen",
        "Listen & Ergebnisse",
        "Testsystem & Prüfläufe",
        "Transparenz & Monitor",
        "Einstellungen",
        "Protokolle",
    ):
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

    center = tk.Frame(root, bg=theme.background, padx=14, pady=14)
    center.grid(row=0, column=1, sticky="nsew")
    center.columnconfigure(0, weight=1)
    center.rowconfigure(3, weight=1)

    header = tk.Frame(center, bg=theme.panel, highlightthickness=1, highlightbackground=theme.border, padx=16, pady=12)
    header.grid(row=0, column=0, sticky="ew")
    tk.Label(header, text="Duplikate, Umbenennen & Listen — Workspace", bg=theme.panel, fg=theme.text, font=("Sans", 19, "bold")).pack(anchor="w")
    tk.Label(header, text="Projekt: Alte HDD-Sammlung · Nur-Lese-Modus · sichere Simulation vor Änderungen", bg=theme.panel, fg=theme.muted).pack(anchor="w", pady=(4, 0))

    cards = tk.Frame(center, bg=theme.background)
    cards.grid(row=1, column=0, sticky="ew", pady=12)
    for index, (title, value, detail) in enumerate(SUMMARY_CARDS):
        cards.columnconfigure(index, weight=1)
        frame = tk.Frame(cards, bg=theme.panel_alt, highlightthickness=1, highlightbackground=theme.border, padx=14, pady=10)
        frame.grid(row=0, column=index, sticky="ew", padx=(0 if index == 0 else 6, 0))
        tk.Label(frame, text=title, bg=theme.panel_alt, fg=theme.muted).pack(anchor="w")
        tk.Label(frame, text=value, bg=theme.panel_alt, fg=theme.accent, font=("Sans", 18, "bold")).pack(anchor="w")
        tk.Label(frame, text=detail, bg=theme.panel_alt, fg=theme.text).pack(anchor="w")

    tools = tk.Frame(center, bg=theme.panel, highlightthickness=1, highlightbackground=theme.border, padx=12, pady=10)
    tools.grid(row=2, column=0, sticky="ew")
    for index, tab in enumerate(WORKSPACE_TABS):
        tk.Button(tools, text=tab, bg=theme.success if index == 0 else theme.panel_alt, fg="#00120d" if index == 0 else theme.text, relief="flat", padx=12, pady=7).pack(side="left", padx=(0, 6))
    tk.Entry(tools, bg="#041014", fg=theme.text, insertbackground=theme.text, relief="flat").pack(side="left", fill="x", expand=True, padx=8)

    detail = tk.Frame(center, bg=theme.panel, highlightthickness=1, highlightbackground=theme.border, padx=10, pady=10)
    detail.grid(row=3, column=0, sticky="nsew", pady=(10, 0))
    detail.rowconfigure(0, weight=1)
    detail.columnconfigure(0, weight=1)
    columns = ("Dateiname", "Pfad", "Größe", "Datum", "Typ", "Status", "Aktion")
    tree = ttk.Treeview(detail, columns=columns, show="headings")
    for name in columns:
        tree.heading(name, text=name)
        tree.column(name, width=120 if name != "Pfad" else 300, anchor="w")
    rows = (
        ("IMG_2020_1234.JPG", "/Fotos/Urlaub/2020", "12,45 MB", "12.08.2020", "JPG", "Exakt", "Behalten"),
        ("IMG_2020_1234_Kopie.JPG", "/Backup/Fotos/Urlaub/2020", "12,45 MB", "12.08.2020", "JPG", "Exakt", "Papierkorb"),
        ("Video_2019_0001.mp4", "/Videos/2019", "1,25 GB", "03.11.2019", "MP4", "Ähnlich 98%", "Prüfen"),
        ("Dokument_Version1.docx", "/Dokumente/Projekte", "2,34 MB", "21.02.2018", "DOCX", "Exakt", "Behalten"),
    )
    for row in rows:
        tree.insert("", "end", values=row)
    tree.grid(row=0, column=0, sticky="nsew")

    rename = tk.Frame(detail, bg=theme.panel_alt, padx=12, pady=10)
    rename.grid(row=1, column=0, sticky="ew", pady=(10, 0))
    tk.Label(rename, text="Umbenennen — Vorschau & Regel", bg=theme.panel_alt, fg=theme.accent, font=("Sans", 11, "bold")).pack(anchor="w")
    tk.Label(rename, text="IMG_2020_1234 (Kopie).JPG   →   2020-08-12_14-32-01_IMG_1234.JPG", bg=theme.panel_alt, fg=theme.text).pack(anchor="w", pady=(5, 0))

    assistant = tk.Frame(root, bg=theme.panel, padx=14, pady=16, width=260, highlightthickness=1, highlightbackground=theme.border)
    assistant.grid(row=0, column=2, sticky="ns")
    assistant.grid_propagate(False)
    tk.Label(assistant, text="ASSISTENT & TIPPS", bg=theme.panel, fg=theme.accent, font=("Sans", 12, "bold")).pack(anchor="w")
    tk.Label(assistant, text="Hier behältst du die Kontrolle.\nOriginaldaten bleiben unangetastet,\nbis du ausdrücklich freigibst.", justify="left", bg=theme.panel, fg=theme.text).pack(anchor="w", pady=12)
    for state in ("✓ Nur lesender Zugriff", "✓ Testlauf zuerst", "✓ Papierkorb aktiv", "✓ Undo & Rollback", "✓ Protokollierung 100%"):
        tk.Label(assistant, text=state, bg=theme.panel, fg=theme.success, anchor="w").pack(fill="x", pady=2)
    tk.Label(assistant, text="NÄCHSTE SCHRITTE", bg=theme.panel, fg=theme.accent, font=("Sans", 11, "bold")).pack(anchor="w", pady=(18, 6))
    for index, step in enumerate(NEXT_STEPS, 1):
        tk.Label(assistant, text=f"{index}. {step}", bg=theme.panel, fg=theme.text, anchor="w").pack(fill="x", pady=2)
    for action in ("Vorschau aktualisieren", "Testlauf starten", "Auswahl prüfen", "Sichere Simulation"):
        tk.Button(assistant, text=action, bg=theme.success, fg="#00120d", relief="flat", pady=8).pack(fill="x", pady=(8, 0))

    root.mainloop()
    return 0
