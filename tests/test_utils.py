import math

from bibchex.util import chunked_pairs


class TestChunkedPairs:
    def test_complete(self):
        TESTSIZE = 10
        CHUNKSIZES = [1, 2, 10]
        items = list(range(0, TESTSIZE))
        item_count = TESTSIZE**2 / 2

        expected = set(((i, j)
                        for i in range(0, TESTSIZE)
                        for j in range(i+1, TESTSIZE)))

        for cs in CHUNKSIZES:
            chunk_count = int(math.floor(item_count / cs))
            chunks = []
            for i in range(0, chunk_count):
                cp = list(chunked_pairs(items, chunk_count, i))
                chunks.append(cp)

            computed = set((item for chunk in chunks for item in chunk))
            assert(expected == computed)
