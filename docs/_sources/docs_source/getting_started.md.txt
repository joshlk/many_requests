# Getting started

## Installing

Get the latest version using pip/PyPi

```shell
pip install dataclassframe
```

## Example usage

A container data-type for dataclasses...
```python
from dataclasses import dataclass
from dataclassframe import DataClassFrame

@dataclass
class ExampleDC:
    field1: str
    field2: int

records = [
    ExampleDC('a', 1),
    ExampleDC('b', 2),
    ExampleDC('c', 3),
]

dcf = DataClassFrame(
    record_class=ExampleDC,
    data=records,
    index=['field1', 'field2']
)
```

Which acts like a ordered dictionary with multi-indexing...
```python
# Obtain record `ExampleDC('b', 2)`
row_idx = dcf.iat[1]    # Using positional index
row_f1 = dcf.at['b']    # Using index of `field1`
row_f2 = dcf.at[:, 2]   # Using index of `field2`
assert row_idx == row_f1 == row_f2
```

With bulk operations on the columns..
```python
assert dcf.cols.field2.sum() == 6
```

Works nicely with Python 3 type hints...
```python
dcf: DataClassFrame[ExampleDC]
dcf.iat[1]: ExampleDC
```
