"""Models package – imports all ORM classes to ensure they are registered."""

from backend.models.account import Account, Contact, TriggerSignal
from backend.models.bid import Bid, BidDocument, ComplianceItem, RFI
from backend.models.estimating import ChecklistItem, EstimatingProject, ScopeGapItem
from backend.models.intel import BlogPost, CompanyIntel, ExecutiveProfile, NewsItem, UploadedPhoto
from backend.models.opportunity import Opportunity, QualificationScore

__all__ = [
    "Account",
    "Contact",
    "TriggerSignal",
    "Opportunity",
    "QualificationScore",
    "Bid",
    "BidDocument",
    "ComplianceItem",
    "RFI",
    "EstimatingProject",
    "ScopeGapItem",
    "ChecklistItem",
    "CompanyIntel",
    "ExecutiveProfile",
    "NewsItem",
    "BlogPost",
    "UploadedPhoto",
]
