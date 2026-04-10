import unittest

from utils.text_utils import chunk_text


class ChunkTextTests(unittest.TestCase):
    def test_chunk_text_splits_into_expected_sizes(self) -> None:
        source = "abcdefghij"
        chunks = chunk_text(source, chunk_size=4)

        self.assertEqual(chunks, ["abcd", "efgh", "ij"])

    def test_chunk_text_returns_empty_list_for_empty_text(self) -> None:
        self.assertEqual(chunk_text("", chunk_size=5), [])

    def test_chunk_text_raises_for_invalid_chunk_size(self) -> None:
        with self.assertRaises(ValueError):
            chunk_text("hello", chunk_size=0)


if __name__ == "__main__":
    unittest.main()
