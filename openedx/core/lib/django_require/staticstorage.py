"""
:class:`~django_require.staticstorage.OptimizedCachedRequireJsStorage`
"""

from django_pipeline_forgiving.storages import PipelineForgivingStorage


class OptimizedCachedRequireJsStorage(PipelineForgivingStorage):
    """
    Custom storage backend that is used by Django-require.
    """
    pass
