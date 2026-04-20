"""Provider adapters for driving-directions APIs.

Each provider module exposes a concrete subclass of
:class:`gotime.providers.base.BaseProvider` with a :meth:`directions` method
returning a :class:`~gotime.models.TripResult`.
"""
