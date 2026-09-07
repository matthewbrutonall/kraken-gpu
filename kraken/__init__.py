"""
entry point for kraken functionality
"""

import importlib.metadata


def get_distribution_version() -> str:
    for name in ('kraken-gpu', 'kraken'):
        try:
            return importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            pass
    return '0+unknown'
