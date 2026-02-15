import unittest
import random

import sort.insertion_sort
import sort.bubble_sort
import sort.quicksort


def is_sorted(S):
    for i in range(0, len(S) - 1):
        if S[i + 1] < S[i]:
            return False
    return True


class TestSorters(unittest.TestCase):

    def asserts_call(self, data):
        bubble_copy = data.copy()
        ins_copy = data.copy()
        quick_copy = data.copy()
        sort.bubble_sort.bubble_sort(bubble_copy)
        self.assertEqual(is_sorted(bubble_copy), True)
        sort.insertion_sort.insertion_sort(ins_copy)
        self.assertEqual(is_sorted(ins_copy), True)
        sort.quicksort.quicksort(quick_copy)
        self.assertEqual(is_sorted(quick_copy), True)

    def test_sorted_list(self):
        data = [i for i in range(100)]
        self.asserts_call(data)

    def test_reverse_sorted_list(self):
        data = [i for i in range(100, 0, -1)]
        self.asserts_call(data)

    def test_random_order_list(self):
        data = [i for i in range(100)]
        random.shuffle(data)
        self.asserts_call(data)

    def test_list_with_duplicates(self):
        data = [i for i in range(50)]
        data_concat = data + data
        random.shuffle(data_concat)
        self.asserts_call(data_concat)


if __name__ == '__main__':
    unittest.main()
