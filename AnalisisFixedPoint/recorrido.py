"""
#-------------------------------------------------------------------------
# recorrido: searchs in a sequence of comparable (<) elements an element equal to its index
# @inputs: A, a reference to a secuence of comparable elements.
# @outputs: Boolean, if A[i]=i is found
# @author: Valeria Catalina Caycedo
#-------------------------------------------------------------------------
"""
## -------------------------------------------------------------------------
## recorrido: Recorrido lineal CORRECTO para el problema del "fixed point".
## Recorre todas las posiciones y retorna True si existe i con A[i]==i.
## (Este es el enfoque "brute force"/lineal, en contraste con binary search.) :contentReference[oaicite:1]{index=1}
## @inputs:  A, lista de enteros.
## @outputs: bool, True si existe punto fijo; False si no existe.
## @complexity: Tiempo O(n), Espacio O(1). :contentReference[oaicite:2]{index=2}
## -------------------------------------------------------------------------
def recorrido(A):
    for i in range (len(A)):
        if A[i] == i:
            return True
        # si no coincide, seguimos revisando
    # si terminamos el for, no hubo punto fijo
    return False
## end defalse