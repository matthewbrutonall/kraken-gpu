import importlib.metadata

from typing import TYPE_CHECKING


__all__ = ['create_model']

if TYPE_CHECKING:
    from .base import BaseModel


def create_model(name, *args, **kwargs) -> 'BaseModel':
    """
    Constructs an empty model from the model registry.
    """
    if not type(name) in (type, str):
        raise ValueError(f'`{name}` is neither type nor string.')

    try:
        eps = importlib.metadata.entry_points(group='kraken.models', name=name)
        if not eps:
            raise ValueError(f'`{name}` is not in model registry.')
        entry_point = tuple(eps)[0]
    except Exception as e:
        raise ValueError(f'`{name}` is not in model registry: {e}')

    try:
        cls = entry_point.load()
    except (ImportError, ModuleNotFoundError) as e:
        raise ValueError(f'Failed to load model class {name}: {e}') from e
    try:
        return cls(*args, **kwargs)
    except Exception as e:
        raise ValueError(f'Failed to instantiate model {name}: {e}') from e
