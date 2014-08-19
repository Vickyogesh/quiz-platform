from ..page import register_pages


def register_views(bp):
    from .views import page_views
    from .quiz_b import BPageModels
    from .quiz_cqc import CqcPageModels
    from .quiz_scooter import ScooterPageModels

    register_pages(bp, page_views, [BPageModels, CqcPageModels,
                                    ScooterPageModels])
