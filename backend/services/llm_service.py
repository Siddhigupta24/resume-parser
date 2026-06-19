from groq import Groq
import json
import re
from config import GROQ_API_KEY

# Initialize Groq client once at module level
client = Groq(api_key=GROQ_API_KEY)


# MAIN FUNCTION — Extract skills using Groq

def extract_skills_with_llm(resume_text: str, fallback_skills: list) -> list:
    """
    Uses Groq API to extract skills from resume.
    ONLY processes the dedicated skills section.
    If no skills section found — returns rule-based skills directly.
    Never sends irrelevant resume text to the API.
    """

    # If no API key configured — return fallback only
    if not GROQ_API_KEY:
        print("No Groq API key found. Using rule-based skills only.")
        return fallback_skills

    # Extract ONLY the skills section
    skills_text, section_found = extract_skills_section(resume_text)

    # If no skills section detected — skip LLM entirely
    # Rule-based parser already handles this case
    if not section_found:
        print("No skills section found in resume. Using rule-based skills only.")
        return fallback_skills

    # Skills section found — send to Groq
    print(f"Skills section found ({len(skills_text)} chars). Sending to Groq...")

    # Skills section found — clean before sending to Groq
    # Remove PDF artifacts like (cid:127) which are bullet characters
    skills_text = re.sub(r'\(cid:\d+\)', '·', skills_text)   # Replace (cid:XXX) with dot
    skills_text = re.sub(r'[·•●◆▪■►]', ',', skills_text)     # Replace bullets with comma
    skills_text = re.sub(r'\s+', ' ', skills_text).strip()    # Clean whitespace


    prompt = build_skills_prompt(skills_text)

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=500,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "You are a resume parser. Always respond with valid JSON only. No explanation. No markdown."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        response_text = response.choices[0].message.content.strip()
        print(f"Groq raw response: {response_text[:200]}")

        llm_skills = parse_skills_response(response_text)
        combined = merge_skills(llm_skills, fallback_skills)

        print(f"Groq extracted {len(llm_skills)} skills. Rule-based: {len(fallback_skills)}. Combined: {len(combined)}")
        return combined

    except Exception as e:
        print(f"Groq API error: {e}. Using rule-based skills.")
        return fallback_skills



# HELPER — Extract ONLY the skills section


def extract_skills_section(text: str) -> tuple:
    """
    Extracts ONLY the dedicated skills section from resume.

    Returns:
        tuple: (skills_text, section_found)
        - skills_text: text content of skills section
        - section_found: True if a skills section was detected

    STRICT RULE:
        If no skills section header is found → return ("", False)
        We never send other resume sections to the LLM.
    """

    lines = text.split("\n")
    skill_lines = []
    in_skills_section = False

    # Exact and partial keywords that indicate START of skills section
    # Ordered from most specific to least specific
    start_keywords = [
        "technical skills",
        "core competencies",
        "key skills",
        "programming languages",
        "tech stack",
        "technologies used",
        "tools and technologies",
        "skills & expertise",
        "skills and expertise",
        "areas of expertise",
        "technical expertise",
        "competencies",
        "technologies",
        "expertise",
        "skills",          # most generic — checked last
        "tools",
    ]

    # Keywords that indicate END of skills section
    # When we see these — stop collecting skill lines
    end_keywords = [
        "experience",
        "employment",
        "work history",
        "work experience",
        "professional experience",
        "career history",
        "education",
        "academic",
        "qualification",
        "projects",
        "certifications",
        "certificates",
        "achievements",
        "awards",
        "publications",
        "references",
        "declaration",
        "languages spoken",
        "hobbies",
        "interests",
        "personal",
        "objective",
        "summary",
        "profile",
    ]

    for line in lines:
        line_stripped = line.strip()
        line_lower = line_stripped.lower()

        # Skip empty lines while not in section
        if not line_stripped:
            if in_skills_section:
                # Allow one blank line inside skills section
                # (some resumes have blank lines between skill categories)
                skill_lines.append("")
            continue

        # ── Detect START of skills section ──
        if not in_skills_section:
            for kw in start_keywords:
                # Match if line IS the keyword or STARTS with it
                # e.g. "Skills:" or "Technical Skills" or "SKILLS"
                if (line_lower == kw
                        or line_lower == kw + ":"
                        or line_lower == kw + "s"
                        or line_lower.startswith(kw + ":")
                        or line_lower.startswith(kw + " ")):
                    in_skills_section = True
                    break
            continue  # Don't add the header line itself

        # ── Detect END of skills section ──
        if in_skills_section:
            for kw in end_keywords:
                if (line_lower == kw
                        or line_lower == kw + ":"
                        or line_lower.startswith(kw + ":")
                        or line_lower.startswith(kw + " ")
                        or kw in line_lower):
                    # Skills section ended
                    in_skills_section = False
                    break

            # If still in skills section — collect this line
            if in_skills_section:
                skill_lines.append(line_stripped)

    # Remove trailing blank lines
    while skill_lines and not skill_lines[-1]:
        skill_lines.pop()

    # No skills section found
    if not skill_lines:
        return ("", False)

    skills_text = "\n".join(skill_lines)
    return (skills_text, True)


# HELPER — Build prompt for Groq

def build_skills_prompt(skills_text: str) -> str:
    """
    Precise prompt for Llama 3 via Groq.
    Only skills section text is passed — nothing else.
    """

    prompt = f"""Extract all technical skills from this resume skills section.

STRICT RULES:
- Include ALL of these:
  * Programming languages (Python, Java, JavaScript)
  * Frameworks and libraries (React, Django, TensorFlow)
  * Tools and platforms (Figma, JIRA, Docker, AWS)
  * Databases (SQL, MongoDB, PostgreSQL)
  * Methodologies (Agile, Scrum, Kanban)
  * Domain skills (Product Strategy, Roadmapping, A/B Testing, OKRs, User Research)
  * Cloud and DevOps (AWS, Azure, Kubernetes, CI/CD)
  * Any professional competency listed in a skills section
- Normalize names: "JS" → "JavaScript", "ReactJS" → "React", "ML" → "Machine Learning"
- Exclude ONLY: vague personality traits like "hardworking", "passionate", "team player"
- Exclude: job titles (developer, engineer, manager)
- Return ONLY a valid JSON array of strings
- No explanation, no markdown, no extra text

EXAMPLE OUTPUT:
["Python", "React", "Product Strategy", "A/B Testing", "JIRA", "SQL", "Agile", "OKRs"]

SKILLS SECTION TEXT:
{skills_text}

JSON array:"""

    return prompt



# HELPER — Parse JSON response

def parse_skills_response(response_text: str) -> list:
    """
    Parse JSON array from Groq response.
    Three layers of fallback parsing.
    """

    # Layer 1 — Direct JSON parse (ideal case)
    try:
        skills = json.loads(response_text)
        if isinstance(skills, list):
            return [str(s).strip() for s in skills if s and str(s).strip()]
    except json.JSONDecodeError:
        pass

    # Layer 2 — Extract JSON array from response text
    # Handles case where model adds explanation before/after
    try:
        match = re.search(r'\[.*?\]', response_text, re.DOTALL)
        if match:
            skills = json.loads(match.group())
            if isinstance(skills, list):
                return [str(s).strip() for s in skills if s and str(s).strip()]
    except:
        pass

    # Layer 3 — Extract quoted strings
    try:
        skills = re.findall(r'"([^"]+)"', response_text)
        cleaned = [s.strip() for s in skills if s.strip()]
        if cleaned:
            return cleaned
    except:
        pass

    print("Could not parse Groq response as JSON.")
    return []


# HELPER — Merge LLM + rule-based skills

def merge_skills(llm_skills: list, rule_skills: list) -> list:
    """
    Combine Groq LLM skills with rule-based skills.

    Priority: LLM skills first (better normalized).
    Rule-based skills added only if not already covered.
    Handles partial duplicates: "ReactJS" vs "React".
    """

    # Start with LLM results — better quality normalization
    combined = list(llm_skills)
    combined_lower = [s.lower() for s in combined]

    for skill in rule_skills:
        skill_lower = skill.lower()

        # Skip exact duplicates
        if skill_lower in combined_lower:
            continue

        # Skip partial duplicates
        # e.g. "ReactJS" already covered by "React"
        already_covered = False
        for existing in combined_lower:
            if skill_lower in existing or existing in skill_lower:
                already_covered = True
                break

        if not already_covered:
            combined.append(skill)
            combined_lower.append(skill_lower)

    return combined