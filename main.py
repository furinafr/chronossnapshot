import os
import hashlib
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

class SnapshotEngine:
    def __init__(self, target_dir: str, algorithm: str = 'md5'):
        self.target_dir = Path(target_dir).resolve()
        self.algorithm = algorithm
        if not self.target_dir.is_dir():
            throw ValueError(f'Invalid directory: {target_dir}')

    def _hash_file(self, file_path: Path) -> str:
        hasher = hashlib.new(self.algorithm)
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (PermissionError, FileNotFoundError):
            return 'permission_denied'

    def generate_manifest(self) -> Dict[str, Any]:
        manifest = {
            'metadata': {
                'timestamp': datetime.utcnow().isoformat(),
                'root': str(self.target_dir),
                'algorithm': self.algorithm
            },
            'files': {}
        }
        for root, _, files in os.walk(self.target_dir):
            for name in files:
                path = Path(root) / name
                relative_path = str(path.relative_to(self.target_dir))
                manifest['files'][relative_path] = {
                    'hash': self._hash_file(path),
                    'size': path.stat().st_size
                }
        return manifest

class DiffEngine:
    @staticmethod
    def compare(manifest_a: Dict[str, Any], manifest_b: Dict[str, Any]) -> Dict[str, List[str]]:
        files_a = manifest_a.get('files', {})
        files_b = manifest_b.get('files', {})
        
        added = [f for f in files_b if f not in files_a]
        removed = [f for f in files_a if f not in files_b]
        modified = [
            f for f in files_a 
            if f in files_b and files_a[f]['hash'] != files_b[f]['hash']
        ]
        
        return {
            'added': added,
            'removed': removed,
            'modified': modified
        }

def main():
    parser = argparse.ArgumentParser(description='ChronosSnapshot: Directory State Management')
    subparsers = parser.add_subparsers(dest='command')

    capture_parser = subparsers.add_parser('capture')
    capture_parser.add_argument('path', help='Directory to snapshot')
    capture_parser.add_argument('-o', '--output', help='Output manifest file', default='snapshot.json')

    diff_parser = subparsers.add_parser('diff')
    diff_parser.add_argument('file1', help='First manifest')
    diff_parser.add_argument('file2', help='Second manifest')

    args = parser.parse_args()

    if args.command == 'capture':
        engine = SnapshotEngine(args.path)
        manifest = engine.generate_manifest()
        with open(args.output, 'w') as f:
            json.dump(manifest, f, indent=4)
        print(f'Snapshot saved to {args.output}')

    elif args.command == 'diff':
        with open(args.file1, 'r') as f1, open(args.file2, 'r') as f2:
            m1, m2 = json.load(f1), json.load(f2)
        diff = DiffEngine.compare(m1, m2)
        print(json.dumps(diff, indent=4))

if __name__ == '__main__':
    main()