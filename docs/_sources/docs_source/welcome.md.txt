# Welcome to dataclassframe's documentation!

A dataclass container with multi-indexing and bulk operations. Provides the typed benefits and ergonomics of dataclasses while having the efficiency of Pandas dataframes.

The container is based on data-oriented design by optimising the memory layout of the stored data, providing fast bulk operations and a smaller memory footprint for large collections. Bulk operations are enabled using Pandas which has a rich set of vectorised methods for both numerical and string data types.

Multi-indexing provides the ability to use multiple fields as keys to index the records. This is suitable for bidirectional and inverse dictionary keys.

A DataClassFrame provides good ergonomics for production code as columns are immutable and columns/data types are well defined by the dataclasses. This makes it easier for users to understand the "shape" of the data in large projects and refactor when necessary.