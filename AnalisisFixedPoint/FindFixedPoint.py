"""
#-------------------------------------------------------------------------
# recorrido: searchs in a sequence of comparable (<) elements an element equal to its index
# @inputs: A, a reference to a secuence of comparable elements.
# @outputs: Boolean, if A[i]=i is found
# @author: Valeria Catalina Caycedo
#-------------------------------------------------------------------------
"""

import random


## -------------------------------------------------------------------------
## FindFixedPoint: Wrapper para buscar si existe un punto fijo en A
## @inputs:  A, referencia a una secuencia (lista) de enteros.
##          (Convención de índices: 0, 1, ..., len(A)-1)
## @outputs: bool, True si existe i tal que A[i] == i; False en caso contrario.
## -------------------------------------------------------------------------
def find_fixed_point(A):
    return fixed_point_search(A, 0, len(A) - 1)
## end def


## -------------------------------------------------------------------------
## FixedPointSearch: Búsqueda binaria recursiva de punto fijo (A[i] == i)
## @inputs:  A, referencia a una secuencia (lista) de enteros ordenada.
##          left, índice izquierdo del subarreglo
##          right, índice derecho del subarreglo
## @outputs: bool, True si existe i en [left, right] con A[i] == i; False si no.
##
## Nota importante:
## - Este algoritmo (tal como tu pseudocódigo) es el estándar para arreglos
##   ordenados (típicamente crecientes) y suele asumirse que los valores son
##   distintos para garantizar la decisión de descartar mitades.
## -------------------------------------------------------------------------
def fixed_point_search(A, left, right):
    # if left > right: O(1)
    if left > right:
        # return False: O(1)
        return False

    # pivot <- floor((left + right)/2): O(1)
    pivot = (left + right) // 2

    # if A[pivot] == pivot: O(1)
    if A[pivot] == pivot:
        # return True: O(1)
        return True

    # else if A[pivot] < pivot: O(1)
    elif A[pivot] < pivot:
        # return FixedPointSearch(A, pivot+1, right): T(n/2)
        return fixed_point_search(A, pivot + 1, right)

    # else: O(1)
    else:
        # return FixedPointSearch(A, left, pivot-1): T(n/2)
        return fixed_point_search(A, left, pivot - 1)
## end def


## -------------------------------------------------------------------------
## (Opcional) Versión iterativa equivalente a FixedPointSearch
## Útil si quieres evitar recursión, manteniendo EXACTAMENTE la misma lógica.
## -------------------------------------------------------------------------
def fixed_point_search_iterative(A, left, right):
    while left <= right:
        pivot = (left + right) // 2

        if A[pivot] == pivot:
            return True
        elif A[pivot] < pivot:
            left = pivot + 1
        else:
            right = pivot - 1

    return False
## end def

