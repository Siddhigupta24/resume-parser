import re
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
from datetime import datetime

# Lazy spaCy loading
_nlp = None

def get_nlp():
    global _nlp
    if _nlp is None:
        import spacy
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


# SECTION 1 — CLEAN THE TEXT

def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    text = re.sub(r'[•●◆▪■►✓✔]', '', text)
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


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

def split_into_sections(text: str) -> dict:
    sections = {key: "" for key in SECTION_HEADERS}
    sections["header"] = ""
    current_section = "header"
    lines = text.split("\n")

    for line in lines:
        line_lower = line.lower().strip()
        matched = False
        for section_name, keywords in SECTION_HEADERS.items():
            if any(line_lower == kw or line_lower.startswith(kw) for kw in keywords):
                current_section = section_name
                matched = True
                break
        if not matched:
            sections[current_section] += line + "\n"

    return sections


# SECTION 3 — EXTRACT BASIC FIELDS

def extract_email(text: str) -> str:
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(pattern, text)
    return match.group() if match else None


def extract_phone(text: str) -> str:
    pattern = r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}'
    for match in re.finditer(pattern, text):
        phone = match.group().strip()
        digits_only = re.sub(r'\D', '', phone)
        if 10 <= len(digits_only) <= 13:
            return phone
    return None


def extract_linkedin(text: str) -> str:
    pattern = r'linkedin\.com/in/[a-zA-Z0-9\-_%]+'
    match = re.search(pattern, text)
    return match.group() if match else None


def extract_github(text: str) -> str:
    pattern = r'github\.com/[a-zA-Z0-9\-_]+'
    match = re.search(pattern, text)
    return match.group() if match else None


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
            if ("@" not in url
                    and "linkedin" not in url.lower()
                    and "github" not in url.lower()
                    and "." in url
                    and len(url) > 8):
                return url
    return None


# EXTRACT CITY AND COUNTRY

INDIAN_CITIES = {
    "mumbai", "delhi", "bangalore", "bengaluru", "hyderabad", "chennai",
    "kolkata", "pune", "ahmedabad", "jaipur", "lucknow", "kanpur",
    "nagpur", "indore", "bhopal", "surat", "vadodara", "coimbatore",
    "kochi", "trivandrum", "thiruvananthapuram", "madurai", "noida",
    "gurgaon", "gurugram", "chandigarh", "bhubaneswar", "patna",
    "agra", "varanasi", "mysore", "mysuru", "vizag", "visakhapatnam"
}

COUNTRIES = {
    "india", "united states", "uk", "united kingdom",
    "canada", "australia", "germany", "france", "singapore", "dubai",
    "uae", "netherlands", "sweden", "switzerland", "japan", "china",
    "new zealand", "ireland", "malaysia", "south africa"
}

def extract_city_country(text: str) -> tuple:
    lines = text.split("\n")[:20]
    city = None
    country = None

    for line in lines:
        line_lower = line.lower().strip()
        if not city:
            for c in INDIAN_CITIES:
                if re.search(r'\b' + re.escape(c) + r'\b', line_lower):
                    city = c.title()
                    break
        if not country:
            for co in COUNTRIES:
                if re.search(r'\b' + re.escape(co) + r'\b', line_lower):
                    country = co.title()
                    break
        if city and country:
            break

    if city and not country:
        country = "India"

    if not city:
        first_block = "\n".join(lines)
        doc = get_nlp()(first_block)
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


# EXTRACT WORK HISTORY

def extract_work_history(sections: dict) -> dict:
    exp_text = sections.get("experience", "")
    lines = [l.strip() for l in exp_text.split("\n") if l.strip()]

    work_entries = []
    current_company = None
    current_designation = None
    previous_companies = []
    previous_designations = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Skip bullet points
        if line.startswith(("-", "•", "●", "*", "◆")):
            i += 1
            continue

        # PIPE FORMAT: Operations Manager | Amazon | May 2019 - Present
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            parts = [p for p in parts if p and len(p) > 1]
            company = None
            designation = None
            duration = None
            is_current = False

            for part in parts:
                part_lower = part.lower()
                if any(m in part_lower for m in ["jan","feb","mar","apr","may","jun",
                    "jul","aug","sep","oct","nov","dec","present","current","now"]):
                    duration = part
                    if any(w in part_lower for w in ["present","current","now"]):
                        is_current = True
                elif not company:
                    company = part
                elif not designation:
                    designation = part

            if company:
                entry = {"company": company, "designation": designation,
                         "duration": duration, "is_current": is_current}
                work_entries.append(entry)
                if is_current:
                    current_company = company
                    current_designation = designation
                else:
                    if company not in previous_companies:
                        previous_companies.append(company)
                    if designation and designation not in previous_designations:
                        previous_designations.append(designation)
            i += 1
            continue

        # MULTI-LINE BLOCK FORMAT:
        # Line 0: Designation
        # Line 1: Company — Location
        # Line 2: May 2019 – Present
        if (i + 2 < len(lines)):
            next_line = lines[i + 1]
            date_line = lines[i + 2]

            has_date = re.search(
                r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|'
                r'January|February|March|April|June|July|August|'
                r'September|October|November|December|Present|Current)'
                r'.*(19|20)\d{2}|(19|20)\d{2}.*'
                r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Present|Current)',
                date_line, re.IGNORECASE
            )

            is_company_line = (
                not re.search(r'\b(19|20)\d{2}\b', next_line)
                and not next_line.startswith(("-", "•"))
                and len(next_line) > 3
            )

            if has_date and is_company_line:
                designation = line
                # Strip location after — or ,
                company = re.split(r'[—–,]', next_line)[0].strip()
                duration = date_line
                is_current = bool(re.search(
                    r'present|current|now', date_line, re.IGNORECASE))

                entry = {"company": company, "designation": designation,
                         "duration": duration, "is_current": is_current}
                work_entries.append(entry)

                if is_current:
                    current_company = company
                    current_designation = designation
                else:
                    if company not in previous_companies:
                        previous_companies.append(company)
                    if designation and designation not in previous_designations:
                        previous_designations.append(designation)
                i += 3
                continue

        i += 1

    return {
        "current_company": current_company,
        "current_designation": current_designation,
        "previous_companies": previous_companies,
        "previous_designations": previous_designations,
        "work_experience": work_entries
    }


# EXTRACT EDUCATION

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
    edu_text = sections.get("education", "") or ""
    education_list = []
    lines = edu_text.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        line_lower = line.lower()
        if any(kw in line_lower for kw in DEGREE_KEYWORDS):
            edu_entry = {"degree": None, "specialization": None,
                         "university": None, "year": None}

            combined = line
            if i + 1 < len(lines): combined += " " + lines[i + 1]
            if i + 2 < len(lines): combined += " " + lines[i + 2]

            years = re.findall(r'\b((19|20)\d{2})\b', combined)
            if years:
                edu_entry["year"] = years[-1][0]

            edu_entry["degree"] = line.strip()

            for spec in SPECIALIZATION_KEYWORDS:
                if spec in line_lower:
                    edu_entry["specialization"] = spec.title()
                    break
            if not edu_entry["specialization"] and i + 1 < len(lines):
                next_lower = lines[i + 1].lower()
                for spec in SPECIALIZATION_KEYWORDS:
                    if spec in next_lower:
                        edu_entry["specialization"] = spec.title()
                        break

            for j in range(max(0, i - 1), min(len(lines), i + 4)):
                check_line = lines[j].lower()
                if any(uk in check_line for uk in UNIVERSITY_KEYWORDS):
                    edu_entry["university"] = lines[j].strip()
                    break

            education_list.append(edu_entry)
        i += 1

    return education_list


# EXTRACT CERTIFICATIONS

CERT_ISSUERS = [
    "aws", "amazon", "google", "microsoft", "oracle", "cisco", "comptia",
    "pmi", "scrum", "istqb", "salesforce", "ibm", "coursera", "udemy",
    "edx", "linkedin", "meta", "apple", "red hat", "mongodb", "databricks",
    "tableau", "sap", "adobe", "vmware", "kubernetes", "cncf", "isaca",
    "isc2", "ec-council", "offensive security", "hugging face", "nvidia"
]

def extract_certifications_improved(sections: dict) -> list:
    cert_text = sections.get("certifications", "")
    cert_list = []
    lines = cert_text.split("\n")

    for line in lines:
        line = line.strip()
        line = re.sub(r'^[-•●◆▪■►✓✔\*]\s*', '', line).strip()
        if len(line) < 5:
            continue

        cert_entry = {"name": None, "issuer": None, "year": None}
        year_match = re.search(r'\b(19|20)\d{2}\b', line)
        if year_match:
            cert_entry["year"] = year_match.group()
            name_clean = re.sub(r'\b(19|20)\d{2}\b', '', line).strip()
            name_clean = re.sub(r'[-–,]\s*$', '', name_clean).strip()
        else:
            name_clean = line

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

        is_bullet = bool(re.match(r'^[-•●◆▪■►✓✔\*]', line))
        line_clean = re.sub(r'^[-•●◆▪■►✓✔\*]\s*', '', line).strip()
        if not line_clean:
            continue

        line_lower = line_clean.lower()

        if is_bullet or len(line_clean) < 80:
            if (not is_bullet
                    and len(line_clean.split()) <= 8
                    and not line_clean.endswith(".")
                    and not any(w in line_lower for w in
                               ["developed", "built", "created", "implemented",
                                "designed", "worked", "used", "managed"])):
                if current_project and current_project.get("name"):
                    projects.append(current_project)
                current_project = {"name": line_clean, "role": None,
                                   "responsibilities": "", "technologies": None}
            else:
                if current_project is None:
                    current_project = {"name": "Project", "role": None,
                                       "responsibilities": "", "technologies": None}
                if any(kw in line_lower for kw in ["role:", "position:", "as a", "worked as"]):
                    current_project["role"] = line_clean
                elif any(kw in line_lower for kw in ["tech stack:", "technologies:",
                                                       "built with", "using:", "tools:"]):
                    current_project["technologies"] = line_clean
                else:
                    if current_project["responsibilities"]:
                        current_project["responsibilities"] += " | " + line_clean
                    else:
                        current_project["responsibilities"] = line_clean

    if current_project and current_project.get("name"):
        projects.append(current_project)

    return projects


# SECTION 4 — EXTRACT NAME

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
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in JOB_TITLE_PATTERNS)


def normalize_name(name: str) -> str:
    if not name:
        return name
    if name.isupper():
        return name.title()
    if name.islower():
        return name.title()
    return name


def derive_name_from_email(email: str) -> str:
    if not email:
        return None
    try:
        local = email.split("@")[0]
        local = re.sub(r'\d+', '', local)
        parts = re.split(r'[._\-]', local)
        parts = [p.strip() for p in parts if len(p.strip()) >= 2]
        if len(parts) >= 2:
            return " ".join(p.capitalize() for p in parts[:3])
        return None
    except:
        return None


def validate_name_with_email(name: str, email: str) -> bool:
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
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    first_lines = lines[:12]
    backup_name = None

    email = extract_email(text)

    # STRATEGY 1 — Email Derivation
    email_name = derive_name_from_email(email)
    if email_name:
        email_words = email_name.split()
        for line in first_lines:
            line_clean = line.strip()
            if is_job_title(line_clean): continue
            if len(line_clean) > 50: continue
            if any(c in line_clean for c in ['@', '/', '|', ':', '+', '(']): continue
            line_lower = line_clean.lower()
            matches = sum(1 for w in email_words if w.lower() in line_lower)
            if matches >= len(email_words) - 1:
                return normalize_name(line_clean)
        if len(email_words) >= 2:
            return normalize_name(email_name)

    # STRATEGY 2 — Capital words line scan
    for line in first_lines:
        line_clean = line.strip()
        if not line_clean: continue
        if is_job_title(line_clean): continue
        if len(line_clean) > 50: continue
        if any(c in line_clean for c in ['@', '/', '|', ':', '+', '(']): continue
        if any(char.isdigit() for char in line_clean): continue
        words = line_clean.split()
        if not (2 <= len(words) <= 4): continue
        if not all(w[0].isupper() for w in words if w): continue
        name = normalize_name(line_clean)
        if email and validate_name_with_email(name, email):
            return name
        else:
            backup_name = name

    # STRATEGY 3 — spaCy NER
    first_block = "\n".join(first_lines)
    doc = get_nlp()(first_block)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text.strip()
            words = name.split()
            if not (2 <= len(words) <= 4): continue
            if is_job_title(name): continue
            if any(c.isdigit() for c in name): continue
            if any(c in name for c in ['@', '/', '|']): continue
            name = normalize_name(name)
            if email and validate_name_with_email(name, email):
                return name
            elif not email:
                return name

    if backup_name:
        return backup_name

    # STRATEGY 4 — Position Heuristic
    for line in first_lines[:6]:
        line_clean = line.strip()
        if not line_clean: continue
        if is_job_title(line_clean): continue
        if len(line_clean) > 45: continue
        if any(c in line_clean for c in ['@', '/', '|', ':', '+', '(']): continue
        if any(char.isdigit() for char in line_clean): continue
        words = line_clean.split()
        if not (2 <= len(words) <= 4): continue
        if not all(w[0].isupper() for w in words if w): continue
        return normalize_name(line_clean)

    return None


# SECTION 5 — EXTRACT LOCATION

def extract_location(text: str) -> str:
    first_lines = "\n".join(text.split("\n")[:15])
    doc = get_nlp()(first_lines)
    for ent in doc.ents:
        if ent.label_ in ("GPE", "LOC"):
            return ent.text.strip()
    return None


# SECTION 6 — EXTRACT SKILLS

SKILLS_DICTIONARY = {
    "Python": ["python"], "Java": ["java"],
    "JavaScript": ["javascript", "js"], "TypeScript": ["typescript", "ts"],
    "C++": ["c++", "cpp"], "C#": ["c#", "csharp"],
    "React": ["react", "reactjs", "react.js"],
    "Node.js": ["node", "nodejs", "node.js"],
    "MongoDB": ["mongodb", "mongo"], "PostgreSQL": ["postgresql", "postgres"],
    "MySQL": ["mysql"], "FastAPI": ["fastapi"], "Django": ["django"],
    "Flask": ["flask"], "HTML": ["html", "html5"], "CSS": ["css", "css3"],
    "Git": ["git"], "Docker": ["docker"], "AWS": ["aws", "amazon web services"],
    "Machine Learning": ["machine learning", "ml"],
    "Deep Learning": ["deep learning", "dl"],
    "NLP": ["nlp", "natural language processing"], "spaCy": ["spacy"],
    "TensorFlow": ["tensorflow"], "PyTorch": ["pytorch"],
    "Pandas": ["pandas"], "NumPy": ["numpy"], "SQL": ["sql"],
    "REST API": ["rest api", "restful", "rest"], "GraphQL": ["graphql"],
    "Linux": ["linux"], "Agile": ["agile", "scrum"],
}

def extract_skills(text: str) -> list:
    text_lower = text.lower()
    found_skills = []
    for skill_name, aliases in SKILLS_DICTIONARY.items():
        for alias in aliases:
            pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.append(skill_name)
                break
    return found_skills


# SECTION 7 — EXTRACT EXPERIENCE

def extract_experience(sections: dict) -> float:
    exp_text = sections.get("experience", "")
    direct = re.search(
        r'(\d+\.?\d*)\s*\+?\s*years?\s*(of\s*)?(experience|exp)',
        exp_text, re.IGNORECASE
    )
    if direct:
        return float(direct.group(1))

    date_pattern = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)[\s,]+(\d{4})\s*[-–to]+\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December|Present|Current|Now)[\s,]*(\d{4})?'
    matches = re.findall(date_pattern, exp_text, re.IGNORECASE)
    total_months = 0

    for match in matches:
        start_str = f"{match[0]} {match[1]}"
        try:
            start_date = date_parser.parse(start_str)
            end_word = match[2].lower()
            if end_word in ("present", "current", "now"):
                end_date = datetime.now()
            else:
                end_str = f"{match[2]} {match[3]}"
                end_date = date_parser.parse(end_str)
            diff = relativedelta(end_date, start_date)
            total_months += diff.years * 12 + diff.months
        except:
            continue

    return round(total_months / 12, 1) if total_months > 0 else None


# SECTION 8 — EXTRACT CURRENT JOB

def extract_current_job(sections: dict) -> tuple:
    exp_text = sections.get("experience", "")
    lines = exp_text.split("\n")

    for line in lines:
        if "present" in line.lower() or "current" in line.lower():
            parts = [p.strip() for p in re.split(r'[|,–-]', line)]
            parts = [p for p in parts if p and len(p) > 2]
            company = None
            designation = None
            for part in parts:
                if any(word in part.lower() for word in ["present", "current", "now"]):
                    continue
                if not company:
                    company = part
                elif not designation:
                    designation = part
            return company, designation

    return None, None


# SECTION 11 — BUILD PROFILE SUMMARY

def build_profile_summary(data: dict) -> str:
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
    score = 0
    missing_fields = []

    if data.get("name"):         score += 15
    else:                        missing_fields.append("Name")
    if data.get("email"):        score += 15
    else:                        missing_fields.append("Email")
    if data.get("phone"):        score += 10
    else:                        missing_fields.append("Phone")

    skills = data.get("skills", [])
    if len(skills) >= 5:         score += 15
    elif len(skills) >= 2:       score += 8;  missing_fields.append("Skills (less than 5 found)")
    elif len(skills) >= 1:       score += 3;  missing_fields.append("Skills (less than 5 found)")
    else:                        missing_fields.append("Skills")

    if data.get("total_experience"):    score += 10
    else:                               missing_fields.append("Total Experience")
    if data.get("education"):           score += 10
    else:                               missing_fields.append("Education")
    if data.get("current_company"):     score += 5
    else:                               missing_fields.append("Current Company")
    if data.get("current_designation"): score += 5
    else:                               missing_fields.append("Current Designation")
    if data.get("city"):                score += 3
    else:                               missing_fields.append("City")
    if data.get("country"):             score += 2
    else:                               missing_fields.append("Country")
    if data.get("linkedin"):            score += 3
    else:                               missing_fields.append("LinkedIn")
    if data.get("github"):              score += 2
    else:                               missing_fields.append("GitHub")
    if data.get("certifications"):      score += 5
    else:                               missing_fields.append("Certifications")

    data["accuracy_score"] = score
    data["missing_fields"] = missing_fields

    if score >= 75:   return "Success"
    elif score >= 40: return "Partial"
    else:             return "Failed"


# SECTION 13 — MAIN PARSE FUNCTION

def parse_resume(raw_text: str) -> dict:
    try:
        text = clean_text(raw_text)
        sections = split_into_sections(text)

        email = extract_email(text)
        phone = extract_phone(text)
        linkedin = extract_linkedin(text)
        github = extract_github(text)
        portfolio = extract_portfolio(text)
        name = extract_name(text)
        city, country = extract_city_country(text)

        rule_based_skills = extract_skills(text)
        from services.llm_service import extract_skills_with_llm
        skills = extract_skills_with_llm(text, rule_based_skills)

        experience = extract_experience(sections)
        work_history = extract_work_history(sections)
        education = extract_education_improved(sections)
        certifications = extract_certifications_improved(sections)
        projects = extract_projects(sections)

        location_parts = [p for p in [city, country] if p]
        location = ", ".join(location_parts) if location_parts else None

        data = {
            "name": name, "email": email, "phone": phone,
            "location": location, "city": city, "country": country,
            "linkedin": linkedin, "github": github, "portfolio": portfolio,
            "skills": skills, "total_experience": experience,
            "current_company": work_history.get("current_company"),
            "current_designation": work_history.get("current_designation"),
            "previous_companies": work_history.get("previous_companies", []),
            "previous_designations": work_history.get("previous_designations", []),
            "work_experience": work_history.get("work_experience", []),
            "education": education, "certifications": certifications,
            "projects": projects, "profile_summary": None,
        }

        data["profile_summary"] = build_profile_summary(data)
        data["parsing_status"] = calculate_parsing_status(data)

        return data

    except Exception as e:
        import traceback
        print(f"PARSE_RESUME CRASHED: {e}")
        traceback.print_exc()
        return None