# ChronosSnapshot

## Overview
ChronosSnapshot is a professional-grade tool for auditing directory changes over time. It generates structured JSON manifests of filesystem states and provides sub-second diffing capabilities.

## Installation
Requires Python 3.8+.

## Usage
### Capture a snapshot
`python chronos.py capture ./my_project -o baseline.json`

### Compare snapshots
`python chronos.py diff baseline.json current.json`

## Features
- Cryptographic file integrity checking.
- Atomic manifest generation.
- Lightweight JSON-based storage.