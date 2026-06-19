import re                                    
import spacy                                 
from dateutil import parser as date_parser   
from dateutil.relativedelta import relativedelta  
from datetime import datetime                
from names_dataset import NameDataset

nlp = spacy.load("en_core_web_sm")          

_nd = None

def get_nd():
    global _nd
    if _nd is None:
        _nd = NameDataset()
    return _nd                 

# SECTION 1 — CLEAN THE TEXT

def clean_text(text: str) -> str:           # Line 13
    text = text.replace("\r\n", "\n")       # Line 14
    text = text.replace("\r", "\n")         # Line 15
    text = re.sub(r'[•●◆▪■►✓✔]', '', text) # Line 16
    text = re.sub(r' +', ' ', text)         # Line 17
    text = re.sub(r'\n{3,}', '\n\n', text)  # Line 18
    return text.strip()                     # Line 19


# SECTION 2 — SPLIT RESUME INTO SECTIONS

SECTION_HEADERS = {
    "experience": ["experience", "work experience", "employment",
                   "work history", "professional experience", "career history"],
    "education": ["education", "academic", "qualification",
                  "educational background", "academic background"],
    "skills": ["skills", "technical skills", "core competencies",
               "technologies", "expertise", "key skills", "competencies"],
    "certifications": ["certifications", "certificates", "courses",
                       "training", "professional development", "accreditations"],
    "projects": ["projects", "personal projects", "academic projects",
                 "key projects", "project experience", "notable projects"],
    "summary": ["summary", "objective", "profile", "about me",
                "professional summary", "career objective"],
}

def split_into_sections(text: str) -> dict:  # Line 33
    sections = {key: "" for key in SECTION_HEADERS}  # Line 34
    sections["header"] = ""                  # Line 35

    current_section = "header"              # Line 37
    lines = text.split("\n")               # Line 38

    for line in lines:                      # Line 40
        line_lower = line.lower().strip()   # Line 41

        matched = False                     # Line 43
        for section_name, keywords in SECTION_HEADERS.items():  # Line 44
            if any(line_lower == kw or line_lower.startswith(kw) for kw in keywords):  # Line 45
                current_section = section_name  # Line 46
                matched = True              # Line 47
                break                       # Line 48

        if not matched:                     # Line 50
            sections[current_section] += line + "\n"  # Line 51

    return sections                         # Line 53


# SECTION 3 — EXTRACT BASIC FIELDS

def extract_email(text: str) -> str:        # Line 59
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'  # Line 60
    match = re.search(pattern, text)        # Line 61
    return match.group() if match else None # Line 62


def extract_phone(text: str) -> str:
    pattern = r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}'
    for match in re.finditer(pattern, text):
        phone = match.group().strip()
        digits_only = re.sub(r'\D', '', phone)
        if 10 <= len(digits_only) <= 13:
            return phone
    return None


def extract_linkedin(text: str) -> str:     # Line 71
    pattern = r'linkedin\.com/in/[a-zA-Z0-9\-_%]+'  # Line 72
    match = re.search(pattern, text)        # Line 73
    return match.group() if match else None # Line 74


def extract_github(text: str) -> str:       # Line 77
    pattern = r'github\.com/[a-zA-Z0-9\-_]+'  # Line 78
    match = re.search(pattern, text)        # Line 79
    return match.group() if match else None # Line 80



# EXTRACT PORTFOLIO URL

def extract_portfolio(text: str) -> str:

    patterns = [
        r'portfolio[:\s]+([^\s]+)',
        r'website[:\s]+([^\s]+)',
        r'personal site[:\s]+([^\s]+)',
        r'((?:https?://)?(?:www\.)?(?!linkedin|github)[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            url = match.group(1).strip()
            # Must not be email, linkedin, github
            if ("@" not in url
                    and "linkedin" not in url.lower()
                    and "github" not in url.lower()
                    and "." in url
                    and len(url) > 8):
                return url
    return None


# EXTRACT CITY AND COUNTRY FROM LOCATION


# Common Indian cities
INDIAN_CITIES = {
    "mumbai", "delhi", "bangalore", "bengaluru", "hyderabad", "chennai",
    "kolkata", "pune", "ahmedabad", "jaipur", "lucknow", "kanpur",
    "nagpur", "indore", "bhopal", "surat", "vadodara", "coimbatore",
    "kochi", "trivandrum", "thiruvananthapuram", "madurai", "noida",
    "gurgaon", "gurugram", "chandigarh", "bhubaneswar", "patna",
    "agra", "varanasi", "mysore", "mysuru", "vizag", "visakhapatnam"
}

# Common countries
COUNTRIES = {
    "india", "united states", "uk", "united kingdom",
    "canada", "australia", "germany", "france", "singapore", "dubai",
    "uae", "netherlands", "sweden", "switzerland", "japan", "china",
    "new zealand", "ireland", "malaysia", "south africa"
}

def extract_city_country(text: str) -> tuple:
    """Extract city and country separately from resume text"""

    # Look for location patterns in first 20 lines
    lines = text.split("\n")[:20]

    city = None
    country = None

    for line in lines:
        line_lower = line.lower().strip()

        # Check for city match
        if not city:
            for c in INDIAN_CITIES:
                if re.search(r'\b' + re.escape(c) + r'\b', line_lower):
                    city = c.title()
                    break

        # Check for country match
        if not country:
            for co in COUNTRIES:
                if re.search(r'\b' + re.escape(co) + r'\b', line_lower):
                    country = co.title()
                    break


        if city and country:
            break

    # If only city found, assume India
    if city and not country:
        country = "India"

    # SpaCy for GPE entities as fallback
    if not city:
        first_block = "\n".join(lines)
        doc = nlp(first_block)
        for ent in doc.ents:
            if ent.label_ == "GPE":
                ent_lower = ent.text.lower().strip()
                if ent_lower in INDIAN_CITIES:
                    city = ent.text.title()
                    if not country:
                        country = "India"
                elif ent_lower in COUNTRIES:
                    country = ent.text.title()
                else:
                    if not city and len(ent.text) > 2:
                        city = ent.text.strip()

    return city, country



# EXTRACT PREVIOUS COMPANIES AND DESIGNATIONS


def extract_work_history(sections: dict) -> dict:
    """
    Extract full work history including:
    - current company + designation
    - previous companies
    - previous designations
    - all work experience entries
    """
    exp_text = sections.get("experience", "")
    lines = exp_text.split("\n")

    work_entries = []
    current_company = None
    current_designation = None
    previous_companies = []
    previous_designations = []

    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue

        # Skip bullet points
        if line.startswith(("-", "•", "●", "*", "◆")):
            continue

        # Detect lines with pipe separator → Company | Role | Duration
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            parts = [p for p in parts if p and len(p) > 1]

            company = None
            designation = None
            duration = None
            is_current = False

            for part in parts:
                part_lower = part.lower()
                # Duration detection
                if any(m in part_lower for m in ["jan", "feb", "mar", "apr",
                    "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
                    "present", "current", "now"]):
                    duration = part
                    if any(w in part_lower for w in ["present", "current", "now"]):
                        is_current = True
                # Company or designation
                elif not company:
                    company = part
                elif not designation:
                    designation = part

            if company:
                entry = {
                    "company": company,
                    "designation": designation,
                    "duration": duration,
                    "is_current": is_current
                }
                work_entries.append(entry)

                if is_current:
                    current_company = company
                    current_designation = designation
                else:
                    if company not in previous_companies:
                        previous_companies.append(company)
                    if designation and designation not in previous_designations:
                        previous_designations.append(designation)

        # Detect lines with comma separator or dash
        elif re.search(r'\b(19|20)\d{2}\b', line):
            # Line contains a year — likely a job entry
            years = re.findall(r'\b(19|20)\d{2}\b', line)
            is_current = any(w in line.lower() for w in ["present", "current", "now"])

            # Try to extract company/designation from this line
            clean = re.sub(r'[–\-–].*$', '', line).strip()
            clean = re.sub(r'\b(19|20)\d{2}\b', '', clean).strip()
            clean = re.sub(r'\s+', ' ', clean).strip()

            if clean and len(clean) > 2:
                entry = {
                    "company": clean,
                    "designation": None,
                    "duration": line,
                    "is_current": is_current
                }
                work_entries.append(entry)

                if is_current and not current_company:
                    current_company = clean
                elif not is_current and clean not in previous_companies:
                    previous_companies.append(clean)

    return {
        "current_company": current_company,
        "current_designation": current_designation,
        "previous_companies": previous_companies,
        "previous_designations": previous_designations,
        "work_experience": work_entries
    }


# EXTRACT EDUCATION — IMPROVED


DEGREE_KEYWORDS = [
    "b.tech", "m.tech", "btech", "mtech", "b.e", "m.e", "be", "me",
    "bachelor", "master", "mba", "bca", "mca", "b.sc", "m.sc", "bsc", "msc",
    "phd", "ph.d", "diploma", "b.com", "m.com", "bcom", "mcom",
    "b.a", "m.a", "ba", "ma", "12th", "10th", "hsc", "ssc",
    "b.arch", "llb", "mbbs", "b.pharma"
]

UNIVERSITY_KEYWORDS = [
    "university", "college", "institute", "iit", "nit", "bits", "vtu",
    "anna university", "mumbai university", "delhi university", "pu",
    "iim", "iisc", "school of", "faculty of", "academy"
]

SPECIALIZATION_KEYWORDS = [
    "computer science", "information technology", "electronics",
    "mechanical", "civil", "electrical", "chemical", "biotechnology",
    "data science", "artificial intelligence", "machine learning",
    "communication", "finance", "marketing", "human resources",
    "business administration", "commerce", "mathematics", "physics"
]

def extract_education_improved(sections: dict) -> list:
    """Extract degree, university, year AND specialization"""
    edu_text = sections.get("education", "")
    if not edu_text:
        edu_text = ""

    education_list = []
    lines = edu_text.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        line_lower = line.lower()

        # Check if line contains a degree keyword
        if any(kw in line_lower for kw in DEGREE_KEYWORDS):
            edu_entry = {
                "degree": None,
                "specialization": None,
                "university": None,
                "year": None
            }

            # Extract year from this line or next 2 lines
            combined = line
            if i + 1 < len(lines):
                combined += " " + lines[i + 1]
            if i + 2 < len(lines):
                combined += " " + lines[i + 2]

            years = re.findall(r'\b((19|20)\d{2})\b', combined)
            if years:
                edu_entry["year"] = years[-1][0]  # Get full 4-digit year

            # Extract degree
            edu_entry["degree"] = line.strip()

            # Extract specialization
            for spec in SPECIALIZATION_KEYWORDS:
                if spec in line_lower:
                    edu_entry["specialization"] = spec.title()
                    break
            # Check next line too
            if not edu_entry["specialization"] and i + 1 < len(lines):
                next_lower = lines[i + 1].lower()
                for spec in SPECIALIZATION_KEYWORDS:
                    if spec in next_lower:
                        edu_entry["specialization"] = spec.title()
                        break

            # Extract university from same line or nearby lines
            for j in range(max(0, i - 1), min(len(lines), i + 4)):
                check_line = lines[j].lower()
                if any(uk in check_line for uk in UNIVERSITY_KEYWORDS):
                    edu_entry["university"] = lines[j].strip()
                    break

            education_list.append(edu_entry)

        i += 1

    return education_list



# EXTRACT CERTIFICATIONS — IMPROVED


CERT_ISSUERS = [
    "aws", "amazon", "google", "microsoft", "oracle", "cisco", "comptia",
    "pmi", "scrum", "istqb", "salesforce", "ibm", "coursera", "udemy",
    "edx", "linkedin", "meta", "apple", "red hat", "mongodb", "databricks",
    "tableau", "sap", "adobe", "vmware", "kubernetes", "cncf", "isaca",
    "isc2", "ec-council", "offensive security", "hugging face", "nvidia"
]

def extract_certifications_improved(sections: dict) -> list:
    """Extract certification name, issuer, and year"""
    cert_text = sections.get("certifications", "")
    cert_list = []

    lines = cert_text.split("\n")

    for line in lines:
        line = line.strip()

        # Remove bullet characters
        line = re.sub(r'^[-•●◆▪■►✓✔\*]\s*', '', line).strip()

        if len(line) < 5:
            continue

        cert_entry = {
            "name": None,
            "issuer": None,
            "year": None
        }

        # Extract year
        year_match = re.search(r'\b(19|20)\d{2}\b', line)
        if year_match:
            cert_entry["year"] = year_match.group()
            # Remove year from name
            name_clean = re.sub(r'\b(19|20)\d{2}\b', '', line).strip()
            name_clean = re.sub(r'[-–,]\s*$', '', name_clean).strip()
        else:
            name_clean = line

        # Extract issuer
        line_lower = line.lower()
        for issuer in CERT_ISSUERS:
            if issuer in line_lower:
                cert_entry["issuer"] = issuer.upper() if len(issuer) <= 4 else issuer.title()
                break

        cert_entry["name"] = name_clean if name_clean else line
        cert_list.append(cert_entry)

    return cert_list



# EXTRACT PROJECTS

def extract_projects(sections: dict) -> list:
    """Extract project name, role, responsibilities, technologies"""
    proj_text = sections.get("projects", "")
    projects = []

    if not proj_text.strip():
        return projects

    lines = proj_text.split("\n")
    current_project = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Remove bullet characters
        is_bullet = bool(re.match(r'^[-•●◆▪■►✓✔\*]', line))
        line_clean = re.sub(r'^[-•●◆▪■►✓✔\*]\s*', '', line).strip()

        if not line_clean:
            continue

        line_lower = line_clean.lower()

        if is_bullet or len(line_clean) < 80:
            # Check if this looks like a project name
            # Project names are usually short, not sentences
            if (not is_bullet
                    and len(line_clean.split()) <= 8
                    and not line_clean.endswith(".")
                    and not any(w in line_lower for w in
                               ["developed", "built", "created", "implemented",
                                "designed", "worked", "used", "managed"])):

                # Save previous project
                if current_project and current_project.get("name"):
                    projects.append(current_project)

                current_project = {
                    "name": line_clean,
                    "role": None,
                    "responsibilities": "",
                    "technologies": None
                }

            else:
                # This is a responsibility/detail line
                if current_project is None:
                    current_project = {
                        "name": "Project",
                        "role": None,
                        "responsibilities": "",
                        "technologies": None
                    }

                # Check for role keywords
                if any(kw in line_lower for kw in
                       ["role:", "position:", "as a", "worked as"]):
                    current_project["role"] = line_clean

                # Check for technology keywords
                elif any(kw in line_lower for kw in
                         ["tech stack:", "technologies:", "built with",
                          "using:", "tools:"]):
                    current_project["technologies"] = line_clean

                else:
                    # Add to responsibilities
                    if current_project["responsibilities"]:
                        current_project["responsibilities"] += " | " + line_clean
                    else:
                        current_project["responsibilities"] = line_clean

    # Add last project
    if current_project and current_project.get("name"):
        projects.append(current_project)

    return projects


# SECTION 4 — EXTRACT NAME 

# JOB TITLE PATTERNS — used to reject false positives

JOB_TITLE_PATTERNS = [
    r'\b(senior|junior|lead|principal|chief|head)\b',
    r'\b(engineer|developer|programmer|architect|designer)\b',
    r'\b(manager|director|officer|president|ceo|cto|cfo)\b',
    r'\b(analyst|consultant|specialist|coordinator|advisor)\b',
    r'\b(intern|trainee|associate|executive|representative)\b',
    r'\b(scientist|researcher|professor|lecturer|teacher)\b',
    r'\b(cloud|software|hardware|network|security|data)\b',
    r'\b(computer|information|technology|digital|cyber)\b',
    r'\b(full.?stack|front.?end|back.?end|devops|mobile)\b',
    r'\b(summary|objective|profile|resume|curriculum|vitae)\b',
    r'\b(work|experience|employment|history|background)\b',
    r'\b(charles|section|header|page|updated)\b',
]

def is_job_title(text: str) -> bool:
    """Returns True if text looks like a job title or section header"""
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in JOB_TITLE_PATTERNS)


def normalize_name(name: str) -> str:
    """Fix casing issues in names"""
    if not name:
        return name
    # ALL CAPS → Title Case
    if name.isupper():
        return name.title()
    # all lowercase → Title Case
    if name.islower():
        return name.title()
    return name


def is_known_name(word: str) -> bool:
    """Check if a word is a known first name globally using names-dataset"""
    try:
        get_nd().search(word.capitalize())
        # result is a dict with 'first_name' and 'last_name' keys
        # each contains country data if the name exists
        return (result is not None and
                (result.get('first_name') or result.get('last_name')))
    except:
        return False


def derive_name_from_email(email: str) -> str:
    """Extract candidate name from email address"""
    if not email:
        return None
    try:
        # Get part before @
        local = email.split("@")[0]

        # Remove numbers
        local = re.sub(r'\d+', '', local)

        # Split on dots, underscores, hyphens
        parts = re.split(r'[._\-]', local)

        # Keep only parts with 2+ characters
        parts = [p.strip() for p in parts if len(p.strip()) >= 2]

        if len(parts) >= 2:
            # Capitalize each part
            name = " ".join(p.capitalize() for p in parts[:3])
            return name

        return None
    except:
        return None


def validate_name_with_email(name: str, email: str) -> bool:
    """Check if name matches email — cross validation"""
    if not name or not email:
        return False
    try:
        name_parts = [p.lower() for p in name.split() if len(p) > 1]
        email_local = email.split("@")[0].lower()
        email_local = re.sub(r'\d+', '', email_local)
        return any(part in email_local for part in name_parts)
    except:
        return False


def extract_name(text: str) -> str:
    """
    Multi-strategy name extractor combining:
    1. Email derivation
    2. names-dataset global name dictionary
    3. spaCy NER
    4. Position heuristic fallback
    All combined with cross-validation and job title rejection
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    first_lines = lines[:12]
    backup_name = None 

    # ── Pre-extract email (needed for cross-validation) ──
    email = extract_email(text)

    # STRATEGY 1 — Email Derivation
    email_name = derive_name_from_email(email)

    if email_name:
        email_words = email_name.split()

        # Check if at least first word is a known name
        if is_known_name(email_words[0]):

            # Try to find the full name in actual resume text
            for line in first_lines:
                line_clean = line.strip()

                # Skip lines that are clearly not names
                if is_job_title(line_clean):
                    continue
                if len(line_clean) > 50:
                    continue
                if any(c in line_clean for c in ['@', '/', '|', ':', '+', '(']):
                    continue

                # Check if email-derived name words appear in this line
                line_lower = line_clean.lower()
                matches = sum(
                    1 for w in email_words
                    if w.lower() in line_lower
                )

                if matches >= len(email_words) - 1:
                    # Found the name line — use actual text (better casing)
                    return normalize_name(line_clean)

            # Email name words not found in text — but email derivation
            # was confident (known first name) so use derived name
            if len(email_words) >= 2:
                return normalize_name(email_name)

    # STRATEGY 2 — names-dataset Line Scan
    for line in first_lines:
        line_clean = line.strip()

        # Basic filters
        if not line_clean:
            continue
        if is_job_title(line_clean):
            continue
        if len(line_clean) > 50:
            continue
        if any(c in line_clean for c in ['@', '/', '|', ':', '+', '(']):
            continue
        if any(char.isdigit() for char in line_clean):
            continue

        words = line_clean.split()
        if not (2 <= len(words) <= 4):
            continue

        # Check how many words are known names
        known_count = sum(1 for w in words if is_known_name(w))

        if known_count >= 2:
            # At least 2 words are known names — high confidence
            name = normalize_name(line_clean)

            # Cross validate with email
            if email:
                if validate_name_with_email(name, email):
                    return name  # Confirmed by email ✅
                else:
                    # Not confirmed but still looks like a name
                    # Store as backup, keep looking
                    backup_name = name
                    continue
            else:
                return name

        elif known_count == 1 and len(words) == 2:
            # One known name word, 2-word line — possible name
            if email and validate_name_with_email(line_clean, email):
                return normalize_name(line_clean)

    # Return backup if we found one
    backup_name = locals().get('backup_name', None)
    if backup_name:
        return backup_name

    # STRATEGY 3 — spaCy NER
    first_block = "\n".join(first_lines)
    doc = nlp(first_block)

    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text.strip()
            words = name.split()

            if not (2 <= len(words) <= 4):
                continue
            if is_job_title(name):
                continue
            if any(c.isdigit() for c in name):
                continue
            if any(c in name for c in ['@', '/', '|']):
                continue

            name = normalize_name(name)

            # Cross validate
            if email and validate_name_with_email(name, email):
                return name
            elif not email:
                return name

    # STRATEGY 4 — Position Heuristic (Last Resort)
    for line in first_lines[:6]:
        line_clean = line.strip()

        if not line_clean:
            continue
        if is_job_title(line_clean):
            continue
        if len(line_clean) > 45:
            continue
        if any(c in line_clean for c in ['@', '/', '|', ':', '+', '(']):
            continue
        if any(char.isdigit() for char in line_clean):
            continue

        words = line_clean.split()
        if not (2 <= len(words) <= 4):
            continue

        # All words start with capital
        if not all(w[0].isupper() for w in words if w):
            continue

        name = normalize_name(line_clean)

        if email and validate_name_with_email(name, email):
            return name

    return None


# SECTION 5 — EXTRACT LOCATION USING SPACY


def extract_location(text: str) -> str:     # Line 102
    first_lines = "\n".join(text.split("\n")[:15])  # Line 103
    doc = nlp(first_lines)                  # Line 104

    for ent in doc.ents:                    # Line 106
        if ent.label_ in ("GPE", "LOC"):   # Line 107
            return ent.text.strip()         # Line 108

    return None                             # Line 110


# SECTION 6 — EXTRACT SKILLS

SKILLS_DICTIONARY = {                       # Line 116
    "Python": ["python"],
    "Java": ["java"],
    "JavaScript": ["javascript", "js"],
    "TypeScript": ["typescript", "ts"],
    "C++": ["c++", "cpp"],
    "C#": ["c#", "csharp"],
    "React": ["react", "reactjs", "react.js"],
    "Node.js": ["node", "nodejs", "node.js"],
    "MongoDB": ["mongodb", "mongo"],
    "PostgreSQL": ["postgresql", "postgres"],
    "MySQL": ["mysql"],
    "FastAPI": ["fastapi"],
    "Django": ["django"],
    "Flask": ["flask"],
    "HTML": ["html", "html5"],
    "CSS": ["css", "css3"],
    "Git": ["git"],
    "Docker": ["docker"],
    "AWS": ["aws", "amazon web services"],
    "Machine Learning": ["machine learning", "ml"],
    "Deep Learning": ["deep learning", "dl"],
    "NLP": ["nlp", "natural language processing"],
    "spaCy": ["spacy"],
    "TensorFlow": ["tensorflow"],
    "PyTorch": ["pytorch"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "SQL": ["sql"],
    "REST API": ["rest api", "restful", "rest"],
    "GraphQL": ["graphql"],
    "Linux": ["linux"],
    "Agile": ["agile", "scrum"],
}

def extract_skills(text: str) -> list:      # Line 151
    text_lower = text.lower()               # Line 152
    found_skills = []                       # Line 153

    for skill_name, aliases in SKILLS_DICTIONARY.items():  # Line 155
        for alias in aliases:               # Line 156
            pattern = r'\b' + re.escape(alias) + r'\b'  # Line 157
            if re.search(pattern, text_lower):  # Line 158
                found_skills.append(skill_name)  # Line 159
                break                       # Line 160

    return found_skills                     # Line 162


# SECTION 7 — EXTRACT EXPERIENCE

def extract_experience(sections: dict) -> float:  # Line 168
    exp_text = sections.get("experience", "")     # Line 169

    # Try direct mention first
    direct = re.search(                     # Line 172
        r'(\d+\.?\d*)\s*\+?\s*years?\s*(of\s*)?(experience|exp)',
        exp_text, re.IGNORECASE
    )
    if direct:                              # Line 176
        return float(direct.group(1))      # Line 177

    # Calculate from date ranges
    date_pattern = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)[\s,]+(\d{4})\s*[-–to]+\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December|Present|Current|Now)[\s,]*(\d{4})?'  # Line 180

    matches = re.findall(date_pattern, exp_text, re.IGNORECASE)  # Line 182
    total_months = 0                        # Line 183

    for match in matches:                   # Line 185
        start_str = f"{match[0]} {match[1]}"  # Line 186
        try:
            start_date = date_parser.parse(start_str)  # Line 188
            end_word = match[2].lower()     # Line 189
            if end_word in ("present", "current", "now"):  # Line 190
                end_date = datetime.now()   # Line 191
            else:
                end_str = f"{match[2]} {match[3]}"  # Line 193
                end_date = date_parser.parse(end_str)  # Line 194

            diff = relativedelta(end_date, start_date)  # Line 196
            months = diff.years * 12 + diff.months  # Line 197
            total_months += months          # Line 198
        except:
            continue                        # Line 200

    return round(total_months / 12, 1) if total_months > 0 else None  # Line 202


# SECTION 8 — EXTRACT CURRENT JOB


def extract_current_job(sections: dict) -> tuple:  # Line 208
    exp_text = sections.get("experience", "")      # Line 209
    lines = exp_text.split("\n")                   # Line 210

    for line in lines:                      # Line 212
        if "present" in line.lower() or "current" in line.lower():  # Line 213
            parts = [p.strip() for p in re.split(r'[|,–-]', line)]  # Line 214
            parts = [p for p in parts if p and len(p) > 2]  # Line 215

            company = None                  # Line 217
            designation = None             # Line 218

            for part in parts:             # Line 220
                if any(word in part.lower() for word in ["present", "current", "now"]):  # Line 221
                    continue               # Line 222
                if not company:            # Line 223
                    company = part         # Line 224
                elif not designation:      # Line 225
                    designation = part     # Line 226

            return company, designation    # Line 228

    return None, None                      # Line 230


# SECTION 9 — EXTRACT EDUCATION


def extract_education(sections: dict) -> list:  # Line 236
    edu_text = sections.get("education", "")    # Line 237
    education_list = []                         # Line 238

    degree_keywords = ["b.tech", "m.tech", "btech", "mtech", "b.e", "m.e",  # Line 240
                       "bachelor", "master", "mba", "bca", "mca", "b.sc",
                       "m.sc", "phd", "diploma", "12th", "10th"]

    year_pattern = r'\b(19|20)\d{2}\b'          # Line 244

    lines = edu_text.split("\n")                # Line 246
    for line in lines:                          # Line 247
        line_lower = line.lower()               # Line 248
        if any(kw in line_lower for kw in degree_keywords):  # Line 249
            years = re.findall(year_pattern, line)  # Line 250 - BUG FIX
            years_full = re.findall(r'\b(19|20)\d{2}\b', line)  # Line 251
            edu_entry = {                       # Line 252
                "degree": line.strip(),
                "year": years_full[-1] if years_full else None,
                "university": None,
                "specialization": None
            }
            education_list.append(edu_entry)   # Line 258

    return education_list                       # Line 260




# SECTION 11 — BUILD PROFILE SUMMARY

def build_profile_summary(data: dict) -> str:
    """Build a professional summary from extracted data"""
    parts = []

    if data.get("name"):
        parts.append(f"{data['name']} is a professional")

    if data.get("total_experience"):
        parts.append(f"with {data['total_experience']} years of experience")

    if data.get("current_designation"):
        parts.append(f"currently working as {data['current_designation']}")

    if data.get("current_company"):
        parts.append(f"at {data['current_company']}")

    if data.get("city"):
        parts.append(f"based in {data['city']}")

    if data.get("skills"):
        top = ", ".join(data["skills"][:5])
        parts.append(f"Skilled in {top}.")

    if data.get("education"):
        edu = data["education"][0]
        degree = edu.get("degree", "")
        university = edu.get("university", "")
        year = edu.get("year", "")

        # Clean up degree — remove university and year if already in it
        if university and university in degree:
            degree = degree.replace(university, "").strip()
        if year and year in degree:
            degree = degree.replace(year, "").strip()
        degree = degree.strip("|, ")

        if degree:
            summary_edu = f"Holds {degree}"
            if university and university not in summary_edu:
                summary_edu += f" from {university}"
            parts.append(summary_edu + ".")

    return " ".join(parts) if parts else None



# SECTION 12 — CALCULATE PARSING STATUS

def calculate_parsing_status(data: dict) -> str:
    """
    Weighted scoring across all fields.
    Total possible = 100 points.
    """
    score = 0
    missing_fields = []

    # Basic fields (40 points)
    if data.get("name"):                    score += 15
    else:                                   missing_fields.append("Name")

    if data.get("email"):                   score += 15
    else:                                   missing_fields.append("Email")

    if data.get("phone"):                   score += 10
    else:                                   missing_fields.append("Phone")

    # Skills (15 points)
    skills = data.get("skills", [])
    if len(skills) >= 5:                    score += 15
    elif len(skills) >= 2:                  score += 8;  missing_fields.append("Skills (less than 5 found)")
    elif len(skills) >= 1:                  score += 3;  missing_fields.append("Skills (less than 5 found)")
    else:                                   missing_fields.append("Skills")

    # Experience (10 points)
    if data.get("total_experience"):        score += 10
    else:                                   missing_fields.append("Total Experience")

    # Education (10 points)
    if data.get("education"):               score += 10
    else:                                   missing_fields.append("Education")

    # Current job (10 points)
    if data.get("current_company"):         score += 5
    else:                                   missing_fields.append("Current Company")

    if data.get("current_designation"):     score += 5
    else:                                   missing_fields.append("Current Designation")

    # Location (5 points)
    if data.get("city"):                    score += 3
    else:                                   missing_fields.append("City")

    if data.get("country"):                 score += 2
    else:                                   missing_fields.append("Country")

    # Links (5 points)
    if data.get("linkedin"):                score += 3
    else:                                   missing_fields.append("LinkedIn")

    if data.get("github"):                  score += 2
    else:                                   missing_fields.append("GitHub")

    # Certifications (5 points)
    if data.get("certifications"):          score += 5
    else:                                   missing_fields.append("Certifications")

    # Store score and missing fields
    data["accuracy_score"] = score
    data["missing_fields"] = missing_fields     # ← only new line added to data

    # Determine status
    if score >= 75:
        return "Success"
    elif score >= 40:
        return "Partial"
    else:
        return "Failed"



# SECTION 13 — MAIN PARSE FUNCTION

def parse_resume(raw_text: str) -> dict:
    """Main parsing function — orchestrates all extractors"""
    try:
        # Step 1 — Clean and section the text
        text = clean_text(raw_text)
        sections = split_into_sections(text)

        # Step 2 — Extract all fields
        email = extract_email(text)
        phone = extract_phone(text)
        linkedin = extract_linkedin(text)
        github = extract_github(text)
        portfolio = extract_portfolio(text)
        name = extract_name(text)
        city, country = extract_city_country(text)

        # Rule-based skills first
        rule_based_skills = extract_skills(text)

        # LLM skills — only processes skills section
        from services.llm_service import extract_skills_with_llm
        skills = extract_skills_with_llm(text, rule_based_skills)

        experience = extract_experience(sections)
        work_history = extract_work_history(sections)
        education = extract_education_improved(sections)
        certifications = extract_certifications_improved(sections)
        projects = extract_projects(sections)

        # Step 3 — Build location string
        location_parts = [p for p in [city, country] if p]
        location = ", ".join(location_parts) if location_parts else None

        # Step 4 — Assemble data
        data = {
            "name": name,
            "email": email,
            "phone": phone,
            "location": location,
            "city": city,
            "country": country,
            "linkedin": linkedin,
            "github": github,
            "portfolio": portfolio,
            "skills": skills,
            "total_experience": experience,
            "current_company": work_history.get("current_company"),
            "current_designation": work_history.get("current_designation"),
            "previous_companies": work_history.get("previous_companies", []),
            "previous_designations": work_history.get("previous_designations", []),
            "work_experience": work_history.get("work_experience", []),
            "education": education,
            "certifications": certifications,
            "projects": projects,
            "profile_summary": None,
        }

        # Step 5 — Generate profile summary
        data["profile_summary"] = build_profile_summary(data)

        # Step 6 — Calculate parsing status
        data["parsing_status"] = calculate_parsing_status(data)

        return data

    except Exception as e:
        import traceback
        print(f"PARSE_RESUME CRASHED: {e}")
        traceback.print_exc()
        return None