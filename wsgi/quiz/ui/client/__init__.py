from ..page import register_pages


def register_views(bp):
    """Register pages for the school client."""
    from .views import page_views
    from .quiz_b import BPagesMetadata
    from .quiz_cqc import CqcPagesMetadata
    from .quiz_scooter import ScooterPagesMetadata

    register_pages(bp, page_views, [BPagesMetadata, CqcPagesMetadata,
                                    ScooterPagesMetadata])
