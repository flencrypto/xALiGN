"""Models package – imports all ORM classes to ensure they are registered."""

from backend.models.account import Account, Contact, TriggerSignal
from backend.models.bid import Bid, BidDocument, ComplianceItem, RFI
from backend.models.debrief import BidDebrief
from backend.models.estimating import ChecklistItem, EstimatingProject, ScopeGapItem
from backend.models.framework import ProcurementFramework
from backend.models.intel import BlogPost, CompanyIntel, ExecutiveProfile, NewsItem, UploadedPhoto
from backend.models.leadtime import LeadTimeItem
from backend.models.opportunity import Opportunity, QualificationScore
from backend.models.tender import CallIntelligence, TenderAward

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
    "BidDebrief",
    "EstimatingProject",
    "ScopeGapItem",
    "ChecklistItem",
    "ProcurementFramework",
    "LeadTimeItem",
    "CompanyIntel",
    "ExecutiveProfile",
    "NewsItem",
    "BlogPost",
    "UploadedPhoto",
    "TenderAward",
    "CallIntelligence",
]
