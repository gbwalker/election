import numpy as np
import pandas as pd

### Import the data.

# First the header file from FEC.gov.

header = pd.read_csv('C:/Users/Gabriel/Desktop/FEC individual contributions/indiv_header_file.csv', nrows=1)

# Next the 2019-2020 individual contribution data.

raw = pd.read_csv('C:/Users/Gabriel/Desktop/FEC individual contributions/2019-2020/itcont.txt', header=None, sep='|', nrows=10)

# Add the header to the raw file.
raw.columns = header.columns