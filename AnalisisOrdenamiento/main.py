import sys
import random
import time
import sort.insertion_sort
import sort.bubble_sort
import sort.quicksort


def measure_time(S, sort_function):
    S_copy = S.copy()
    start_time = time.perf_counter_ns()
    sort_function(S_copy)
    end_time = time.perf_counter_ns()
    return end_time - start_time


def run_experiments(min_s, max_s, s_step):
    for n in range(min_s, max_s + s_step, s_step):
        S = [random.randint(0, n) for i in range(n)]
        time_bubble = measure_time(S, sort.bubble_sort.bubble_sort)
        time_insertion = measure_time(S, sort.insertion_sort.insertion_sort)
        time_quick = measure_time(S, sort.quicksort.quicksort)
        print(f'{n}, {time_bubble} ,{time_insertion} ,{time_quick}')


if __name__ == "__main__":
    ## Check arguments
    if len(sys.argv) < 4:
        print("Usage: ", sys.argv[0], "min_s max_s s_step ")
        exit(1)
    ## end if

    min_s_arg = int(sys.argv[1])
    max_s_arg = int(sys.argv[2])
    s_step_arg = int(sys.argv[3])

    run_experiments(min_s_arg, max_s_arg, s_step_arg)
