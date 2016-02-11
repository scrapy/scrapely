import numpy as np
cimport numpy as np
cimport cython
from cpython.version cimport PY_MAJOR_VERSION

cdef np_kmp_match_length(np.ndarray[np.int_t, ndim=1] sequence,
                         np.ndarray[np.int_t, ndim=1] pattern,
                         int start=0,
                         int end=-1):
    """Adaptated from KMP substring search:
    http://code.activestate.com/recipes/117214-knuth-morris-pratt-string-matching/

    The algorithm is modified to return the match length at the given position
    """
    ret = []
    cdef int m = len(pattern)
    if end == -1:
        end = m
    # build table of shift amounts
    cdef np.ndarray[np.int_t, ndim=1] shifts = np.ones((m + 1,), dtype=int)
    cdef int shift = 1
    cdef int pos
    for pos in range(m):
        while shift <= pos and pattern[pos] != pattern[pos-shift]:
            shift += shifts[pos-shift]
        shifts[pos+1] = shift

    # do the actual search
    cdef int startPos = start
    cdef int matchLen = 0
    cdef int c
    for c in sequence[start:]:
        if startPos >= end:
            break
        while matchLen == m or \
              matchLen >= 0 and pattern[matchLen] != c:
            if matchLen > 0:
                ret.append((startPos, matchLen))
            startPos += shifts[matchLen]
            matchLen -= shifts[matchLen]
        matchLen += 1
    if matchLen > 0 and startPos < end:
        ret.append((startPos, matchLen))

    return ret


cdef u_kmp_match_length(unicode sequence, unicode pattern, int start=0, int end=-1):
    """Adaptated from KMP substring search:
    http://code.activestate.com/recipes/117214-knuth-morris-pratt-string-matching/

    The algorithm is modified to return the match length at the given position
    """
    ret = []
    cdef int m = len(pattern)
    if end == -1:
        end = m
    # build table of shift amounts
    cdef np.ndarray[np.int_t, ndim=1] shifts = np.ones((m + 1,), dtype=int)
    cdef int shift = 1
    cdef int pos
    for pos in range(m):
        while shift <= pos and pattern[pos] != pattern[pos-shift]:
            shift += shifts[pos-shift]
        shifts[pos+1] = shift

    # do the actual search
    cdef int startPos = start
    cdef int matchLen = 0
    cdef Py_UCS4 c
    for c in sequence[start:]:
        if startPos >= end:
            break
        while matchLen == m or \
              matchLen >= 0 and pattern[matchLen] != c:
            if matchLen > 0:
                ret.append((startPos, matchLen))
            startPos += shifts[matchLen]
            matchLen -= shifts[matchLen]
        matchLen += 1
    if matchLen > 0 and startPos < end:
        ret.append((startPos, matchLen))

    return ret


cdef np_naive_match_length(np.ndarray[np.int_t, ndim=1] sequence,
                           np.ndarray[np.int_t, ndim=1] pattern,
                           int start=0,
                           int end=-1):
    ret = []
    cdef int m = len(sequence)
    cdef int n = min(m, len(pattern))
    cdef int i
    cdef int j
    cdef int k
    if end == -1:
        end = m
    else:
        end = min(end, m)
    for i in range(start, end):
        j = 0
        k = i
        while sequence[k] == pattern[j]:
            j += 1
            k += 1
            if k == m or j == n:
                break
        if j > 0:
            ret.append((i, j))
    return ret


cdef u_naive_match_length(unicode sequence,
                          unicode pattern, int start=0, int end=-1):
    ret = []
    cdef int m = len(sequence)
    cdef int n = min(m, len(pattern))
    cdef int i
    cdef int j
    cdef int k
    if end == -1:
        end = m
    else:
        end = min(end, m)
    for i in range(start, end):
        j = 0
        k = i
        while sequence[k] == pattern[j]:
            j += 1
            k += 1
            if k == m or j == n:
                break
        if j > 0:
            ret.append((i, j))
    return ret


cdef unicode _ustring(s):
    if type(s) is unicode:
        # fast path for most common case(s)
        return <unicode>s
    elif PY_MAJOR_VERSION < 3 and isinstance(s, bytes):
        # only accept byte strings in Python 2.x, not in Py3
        return (<bytes>s).decode('ascii')
    elif isinstance(s, unicode):
        # an evil cast to <unicode> might work here in some(!) cases,
        # depending on what the further processing does.  to be safe,
        # we can always create a copy instead
        return unicode(s)
    else:
        raise TypeError('Expected str or unicode')


cpdef naive_match_length(sequence, pattern, int start=0, int end=-1):
    if isinstance(sequence, np.ndarray):
        if isinstance(pattern, np.ndarray):
            return np_naive_match_length(sequence, pattern, start, end)
        else:
            raise TypeError('Different types for sequence and pattern')
    else:
        return u_naive_match_length(
            _ustring(sequence), _ustring(pattern), start, end)

cpdef kmp_match_length(sequence, pattern, int start=0, int end=-1):
    if isinstance(sequence, np.ndarray):
        if isinstance(pattern, np.ndarray):
            return np_kmp_match_length(sequence, pattern, start, end)
        else:
            raise TypeError('Different types for sequence and pattern')
    else:
        return u_kmp_match_length(
            _ustring(sequence), _ustring(pattern), start, end)
