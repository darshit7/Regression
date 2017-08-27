from scipy import stats
import numpy as np
x = []
y = []

slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

