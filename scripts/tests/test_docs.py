"""Documentation must stay in sync with the tooling."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import lint_solutions as lint  # noqa: E402

DOCS = Path(__file__).resolve().parent.parent.parent / "docs"


@unittest.skipUnless(DOCS.is_dir(), "docs/ not found")
class DocsTest(unittest.TestCase):
    def test_every_lint_rule_is_documented(self) -> None:
        text = "\n".join(p.read_text(encoding="utf-8") for p in DOCS.rglob("*.md"))
        rule_ids = [r.id for r in lint.RULES] + list(lint.EXTRA_RULE_IDS)
        missing = [rule_id for rule_id in rule_ids if f"`{rule_id}`" not in text]
        self.assertEqual(missing, [], f"rules not documented in docs/: {missing}")

    def test_every_language_has_a_style_guide(self) -> None:
        guides = {p.stem for p in (DOCS / "style-guides").glob("*.md")}
        self.assertEqual(guides, {"cpp", "c", "python", "javascript", "rust", "sql"})

    def test_relative_links_resolve(self) -> None:
        import re

        broken: list[str] = []
        for page in DOCS.rglob("*.md"):
            for target in re.findall(r"\]\(([^)#]+\.md)\)", page.read_text(encoding="utf-8")):
                if not target.startswith("http") and not (page.parent / target).resolve().is_file():
                    broken.append(f"{page.relative_to(DOCS)} -> {target}")
        self.assertEqual(broken, [])


if __name__ == "__main__":
    unittest.main()
