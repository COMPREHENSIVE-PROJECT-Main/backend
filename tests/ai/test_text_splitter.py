import unittest

from app.ai.utils.text_splitter import split_text


class TextSplitterTest(unittest.TestCase):
    def test_split_text_returns_empty_for_blank_text(self):
        self.assertEqual(split_text("   "), [])

    def test_split_text_applies_overlap(self):
        chunks = split_text("가" * 30, chunk_size=10, overlap=3)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(chunks[1].startswith(chunks[0][-3:]))


if __name__ == "__main__":
    unittest.main()
