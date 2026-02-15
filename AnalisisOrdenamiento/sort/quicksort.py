import random


## -------------------------------------------------------------------------
## Partition: Partitions a subsequence by the element in S[r]
## @inputs: S, a reference to a secuence of comparable elements.
##          p, start of the subsequence to be partitioned
##          r, end of the subsequence to be partitioned
## @outputs: i, the index of the pivot element placed in its final position.
#            S[p:i-1]<=S[i] and S[i]<=S[i+1:r]
## -------------------------------------------------------------------------
def partition(S, p, r):
    x = S[r]
    i = p
    for j in range(p, r):
        if S[j] < x:
            S[i], S[j] = S[j], S[i]
            i += 1
        # end if
    # end for
    S[i], S[r] = S[r], S[i]
    return i
# end def

## -------------------------------------------------------------------------
## randomized_partition:  Partitions a subsequence by a random element in the range S[p:r]
## @inputs: S, a reference to a secuence of comparable elements.
##          p, start of the subsequence
##          r, end of the subsequence
## @outputs: i, the index of the pivot element placed in its final position.
#            S[p:i-1]<=S[i] and S[i]<=S[i+1:r]
## -------------------------------------------------------------------------
def randomized_partition(S, p, r):
    i = random.randint(p, r)
    S[r], S[i] = S[i], S[r]
    return partition(S, p, r)
## end def

## -------------------------------------------------------------------------
## quick_sort_aux: sorts a subsequence of comparable (<) elements recursively via quicksort
## @inputs: S, a reference to a secuence of comparable elements.
##          p, start of the subsequence
##          r, end of the subsequence
## @outputs: S[p:r], an ordered permutation of the input.
## -------------------------------------------------------------------------
def quick_sort_aux(S, p, r):
    if p < r:
        q = randomized_partition(S, p, r)
        quick_sort_aux(S, p, q - 1)
        quick_sort_aux(S, q + 1, r)
    ## end if


## end def

## -------------------------------------------------------------------------
## quicksort: sorts a sequence of comparable (<) elements
## @inputs: S, a reference to a secuence of comparable elements.
## @outputs: S, an ordered permutation of the input.
## -------------------------------------------------------------------------
def quicksort(S):
    quick_sort_aux(S, 0, len(S) - 1)
## end def

## eof - quicksort.py
