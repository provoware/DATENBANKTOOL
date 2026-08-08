from __future__ import annotations

import unittest

from datenbanktool.gui_model import gui_contract


class GuiContractTests(unittest.TestCase):
    def test_layout_contract_matches_reference_workspace(self) -> None:
        contract = gui_contract()
        self.assertEqual(
            contract["layout"],
            (
                "left_navigation",
                "project_header",
                "summary_and_workload",
                "detail_list_workspace",
                "assistant_sidebar",
                "persistent_status_strip",
            ),
        )

    def test_safety_contract_is_visible_and_complete(self) -> None:
        contract = gui_contract()
        self.assertEqual(
            contract["safety_states"],
            (
                "Nur lesender Zugriff aktiv",
                "Testlauf zuerst empfohlen",
                "Papierkorb aktiv",
                "Undo & Rollback verfügbar",
                "Protokollierung 100%",
            ),
        )

    def test_reference_theme_keeps_dark_neon_and_green_action_language(self) -> None:
        theme = gui_contract()["theme"]
        self.assertEqual(theme.background, "#050b0e")
        self.assertEqual(theme.accent, "#00f0b5")
        self.assertEqual(theme.success, "#19d66b")
        self.assertEqual(theme.warning, "#ffb000")
        self.assertEqual(theme.danger, "#ff4d4d")

    def test_workspace_has_editable_detail_categories(self) -> None:
        tabs = gui_contract()["tabs"]
        self.assertIn("Duplikate", tabs)
        self.assertIn("Umbenennen", tabs)
        self.assertIn("Unbekannte", tabs)
        self.assertIn("Ausnahmen", tabs)


if __name__ == "__main__":
    unittest.main()
