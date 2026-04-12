The tool follows a decoupled architecture: 
1. **SnapshotEngine**: Handles filesystem I/O, recursion, and hashing logic. Uses streaming reads to maintain a low memory footprint.
2. **DiffEngine**: A pure functional component that takes two state dictionaries and computes the symmetric difference.
3. **Controller/CLI Layer**: Leverages argparse for command routing and handles serialization concerns. Use of Pathlib ensures cross-platform compatibility.