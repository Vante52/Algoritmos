import time
import recorrido
import FindFixedPoint


def time_call(fn, A):
    t0 = time.perf_counter_ns()
    out = fn(A)
    t1 = time.perf_counter_ns()
    return out, (t1 - t0)


def main():
    tests = [
        ("Prueba para true", [-3, -1, 0, 3, 5, 7]),
        ("Prueba para false", list(range(1, 10001))),  # ordenado, sin i tal que A[i]==i (0-index)
    ]

    for name, A in tests:
        r1, t1 = time_call(recorrido.recorrido, A)
        r2, t2 = time_call(FindFixedPoint.find_fixed_point, A)

        print(f"\nCaso: {name}")
        print(f"  Recorrido:     {r1}   ({t1} ns)")
        print(f"  FindFixedPoint:{r2}   ({t2} ns)")


if __name__ == "__main__":
    main()