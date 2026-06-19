from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Education(BaseModel):
    degree: Optional[str] = None
    specialization: Optional[str] = None
    university: Optional[str] = None
    year: Optional[str] = None


class WorkExperience(BaseModel):
    company: Optional[str] = None
    designation: Optional[str] = None
    duration: Optional[str] = None
    is_current: Optional[bool] = False


class Certification(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    year: Optional[str] = None


class Project(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    responsibilities: Optional[str] = None
    technologies: Optional[str] = None


class Candidate(BaseModel):
    # Basic Info
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    # Location — split
    location: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None

    # Links
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None

    # Skills
    skills: List[str] = []

    # Experience
    total_experience: Optional[float] = None
    current_company: Optional[str] = None
    current_designation: Optional[str] = None
    previous_companies: List[str] = []
    previous_designations: List[str] = []
    work_experience: List[WorkExperience] = []

    # Education
    education: List[Education] = []

    # Projects
    projects: List[Project] = []

    # Certifications
    certifications: List[Certification] = []

    # Summary
    profile_summary: Optional[str] = None

    # Metadata
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    parsing_status: str = "Pending"
    accuracy_score: Optional[int] = None
    missing_fields: List[str] = [] 
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)