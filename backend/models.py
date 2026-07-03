from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class EmployeeData(BaseModel):
    """Employee compensation record"""
    employee_id: str
    job_title: str
    job_level: str
    department: Optional[str] = None
    location: Optional[str] = None
    base_salary: float
    bonus: Optional[float] = None
    equity: Optional[float] = None
    tenure_years: float
    gender: str  # 'Male' or 'Female'
    hire_date: Optional[datetime] = None
    performance_rating: Optional[float] = None


class AnalysisRequest(BaseModel):
    """Request to run analysis"""
    employees: List[Dict[str, Any]]
    median_table: Optional[List[Dict[str, Any]]] = None
    company_name: Optional[str] = "Company"


class ChatRequest(BaseModel):
    """A question for the pay-equity assistant, plus compact analysis context."""
    question: str
    context: Optional[Dict[str, Any]] = None
    history: Optional[List[Dict[str, Any]]] = None  # previous turns for follow-up resolution


class TeachRequest(BaseModel):
    """User teaches the assistant a better answer for a question."""
    question: str
    answer: str


class Step1Output(BaseModel):
    """Step 1: Data Preparation results"""
    total_employees: int
    duplicates_found: int
    missing_values: Dict[str, int]
    outliers_found: int
    salary_stats: Dict[str, float]
    data_ready: bool


class Step2Output(BaseModel):
    """Step 2: Descriptive Analysis results"""
    overall_unadjusted_gap_pct: float
    gender_pct_by_role: Dict[str, Dict[str, Any]]
    occupational_segregation: Dict[str, Any]


class Step3Output(BaseModel):
    """Step 3: Controlled Gaps results"""
    controlled_gaps: Dict[str, Any]
    gaps_flagged_count: int
    gaps_needing_investigation: List[Dict[str, Any]]


class RemediationAction(BaseModel):
    """Single remediation action"""
    role_level: str
    gap_pct: float
    affected_employees: int
    estimated_cost: int
    timeline: str
    action: str


class Step5Output(BaseModel):
    """Step 5: Remediation Plan"""
    immediate: List[Dict[str, Any]]
    medium_term: List[Dict[str, Any]]
    monitoring: List[Dict[str, Any]]
    total_cost: int
    affected_employees: int


class AnalysisResponse(BaseModel):
    """Complete analysis response"""
    step1_data_quality: Dict[str, Any]
    step2_descriptive: Dict[str, Any]
    step3_controlled_gaps: Dict[str, Any]
    step4_root_causes: Dict[str, Any]
    step5_remediation: Dict[str, Any]
    summary: Dict[str, Any]
    timestamp: datetime = datetime.now()
