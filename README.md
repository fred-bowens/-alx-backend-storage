## Replay Call History

The `replay()` function allows viewing the call history of a decorated method, showing:

- How many times it was called
- All input arguments and corresponding outputs

### Example:

```python
from exercise import Cache, replay

cache = Cache()
cache.store("hello")
cache.store("world")
replay(cache.store)
