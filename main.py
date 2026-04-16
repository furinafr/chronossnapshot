import hashlib
import json
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Set

# Configure logging for production-grade visibility
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class SnapshotEngine:
    """Handles filesystem scanning and streaming hash generation."""
    
    def __init__(self, target_dir: str, algorithm: str = 'sha256', buffer_size: int = 65536):
        self.target_dir = Path(target_dir).resolve()
        self.algorithm = algorithm
        self.buffer_size = buffer_size
        if not self.target_dir.is_dir():
            raise ValueError(f'Invalid directory path: {target_dir}')

    def _hash_file(self, file_path: Path) -> str:
        """Generates a hash for a file using streaming reads to minimize memory usage."""
        hasher = hashlib.new(self.algorithm)
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(self.buffer_size):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (PermissionError, FileNotFoundError) as e:
            logger.warning(f'Skipping {file_path}: {e}')
            return 'access_denied'

    def generate_manifest(self) -> Dict[str, Any]:
        """Walks the directory and computes state for all files."""
        logger.info(f'Generating manifest for: {self.target_dir}')
        manifest = {
            'metadata': {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'root': str(self.target_dir),
                'algorithm': self.algorithm
            },
            'files': {}
        }

        for path in self.target_dir.rglob('*'):
            if path.is_file():
                try:
                    relative_path = str(path.relative_to(self.target_dir))
                    stats = path.stat()
                    manifest['files'][relative_path] = {
                        'hash': self._hash_file(path),
                        'size': stats.st_size,
                        'mtime': stats.st_mtime
                    }
                except Exception as e:
                    logger.error(f'Error processing {path}: {e}')

        return manifest

class DiffEngine:
    """Pure functional engine to compare two manifest states."""
    
    @staticmethod
    def compare(manifest_a: Dict[str, Any], manifest_b: Dict[str, Any]) -> Dict[str, List[str]]:
        files_a = manifest_a.get('files', {})
        files_b = manifest_b.get('files', {})
        
        keys_a: Set[str] = set(files_a.keys())
        keys_b: Set[str] = set(files_b.keys())

        added = list(keys_b - keys_a)
        removed = list(keys_a - keys_b)
        
        common = keys_a & keys_b
        modified = [
            f for f in common 
            if files_a[f]['hash'] != files_b[f]['hash']
        ]
        
        return {
            'added': sorted(added),
            'removed': sorted(removed),
            'modified': sorted(modified)
        }

class CLIController:
    """Handles command routing and data persistence."""

    @staticmethod
    def run():
        parser = argparse.ArgumentParser(description='ChronosSnapshot: Advanced Directory State Auditor')
        subparsers = parser.add_subparsers(dest='command', required=True)

        # Capture Command
        cap = subparsers.add_parser('capture', help='Create a filesystem snapshot')
        cap.add_argument('path', type=str, help='Target directory')
        cap.add_argument('-o', '--output', type=str, default='snapshot.json', help='Output file path')
        cap.add_argument('--algo', type=str, default='sha256', choices=['md5', 'sha1', 'sha256'])

        # Diff Command
        diff = subparsers.add_parser('diff', help='Compare two snapshots')
        diff.add_argument('file1', type=str, help='Original manifest')
        diff.add_argument('file2', type=str, help='New manifest')

        args = parser.parse_args()

        try:
            if args.command == 'capture':
                engine = SnapshotEngine(args.path, algorithm=args.algo)
                manifest = engine.generate_manifest()
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(manifest, f, indent=4)
                logger.info(f'Successfully saved snapshot to {args.output}')

            elif args.command == 'diff':
                with open(args.file1, 'r', encoding='utf-8') as f1, \
                     open(args.file2, 'r', encoding='utf-8') as f2:
                    m1, m2 = json.load(f1), json.load(f2)
                
                diff_data = DiffEngine.compare(m1, m2)
                print(json.dumps(diff_data, indent=4))

        except Exception as e:
            logger.error(f'Operation failed: {e}')
            sys.exit(1)

if __name__ == '__main__':
    CLIController.run()