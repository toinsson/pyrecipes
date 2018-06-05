#!/usr/bin/env python
# test-f.py

import numpy as np
import f  # loads f.so from cc-lib: f.pyx -> f.c + fc.o -> f.so

N = 3
a = np.arange( N, dtype=np.float64 )
b = np.arange( N, dtype=np.float64 )
z = np.ones( N, dtype=np.float64 ) * np.NaN

fret = f.fpy( N, a, b, z )
print "fpy -> fc z:", z

