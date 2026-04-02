import os
import json
import requests
import logging
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import Image as RLImage
from io import BytesIO

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

OUTPUT_DIR = Path("generated_cvs")
OUTPUT_DIR.mkdir(exist_ok=True)

ROLES = [
    "Software Engineer", "Data Scientist", "AI Engineer", "Backend Developer",
    "Frontend Developer", "DevOps Engineer", "Machine Learning Engineer",
    "Product Manager", "UX Designer", "Full Stack Developer",
    "Data Analyst", "Cloud Architect", "Cybersecurity Analyst",
    "Mobile Developer", "QA Engineer"
]

NATIONALITIES = [
    "Spanish", "French", "German", "Italian", "British",
    "American", "Brazilian", "Mexican", "Argentine", "Colombian"
]


def generate_cv_data(role: str, nationality: str) -> dict:
    prompt = f"""
    Generate realistic fake CV data for a {role} with {nationality} nationality.

    Return ONLY a JSON object with this exact structure, no markdown, no extra text:
    {{
        "name": "Full Name",
        "email": "email@example.com",
        "phone": "690123456",
        "location": "City, Country",
        "linkedin": "linkedin.com/in/username",
        "current_role": "Current Job Title",
        "summary": "3-4 sentence professional summary with specific achievements and numbers",
        "experience": [
            {{
                "title": "Job Title",
                "company": "Company Name",
                "period": "Jan 2022 - Present",
                "description": "4-5 bullet points with metrics separated by |"
            }}
        ],
        "education": [
            {{
                "degree": "Degree Name",
                "institution": "University Name",
                "year": "2019"
            }}
        ],
        "skills": ["skill1", "skill2", "skill3", "skill4", "skill5", "skill6", "skill7", "skill8"],
        "languages": ["Spanish (Native)", "English (C1)"],
        "certifications": ["Certification 1 (2022)", "Certification 2 (2023)"],
        "years_experience": 4
    }}

    Requirements:
    - 3 work experiences, each with 4-5 bullet points with specific metrics
    - 2 education entries
    - 8-10 relevant technical skills
    - 2 certifications relevant to the role
    - Summary must be 3-4 sentences with specific achievements
    - Name should match the nationality
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9
    )
    content = response.choices[0].message.content.strip()
    content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(content)


def get_avatar(name: str, index: int) -> BytesIO:
    styles = ["avataaars", "personas", "micah"]
    style = styles[index % len(styles)]
    seed = name.replace(" ", "")
    url = f"https://api.dicebear.com/7.x/{style}/png?seed={seed}&size=120&backgroundColor=b6e3f4,c0aede,d1d4f9"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return BytesIO(response.content)
    except Exception as e:
        logger.warning(f"No avatar for {name}: {e}")
    return None


def create_cv_pdf(data: dict, index: int, avatar_img: BytesIO = None):
    filename = OUTPUT_DIR / f"cv_{index:02d}_{data['name'].replace(' ', '_')}.pdf"

    doc = SimpleDocTemplate(
        str(filename),
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    PRIMARY = colors.HexColor("#2C3E50")
    ACCENT = colors.HexColor("#3498DB")
    LIGHT_GRAY = colors.HexColor("#EEEEEE")
    MID_GRAY = colors.HexColor("#7F8C8D")

    name_style = ParagraphStyle("Name",
        fontSize=22, textColor=PRIMARY, fontName="Helvetica-Bold",
        spaceAfter=18, alignment=TA_LEFT)

    role_style = ParagraphStyle("Role",
        fontSize=12, textColor=ACCENT, fontName="Helvetica",
        spaceAfter=4)

    section_style = ParagraphStyle("Section",
        fontSize=11, textColor=PRIMARY, fontName="Helvetica-Bold",
        spaceBefore=8, spaceAfter=4)

    body_style = ParagraphStyle("Body",
        fontSize=9, textColor=PRIMARY,
        fontName="Helvetica", spaceAfter=2, leading=14)

    small_style = ParagraphStyle("Small",
        fontSize=8, textColor=MID_GRAY,
        fontName="Helvetica", spaceAfter=2)

    exp_title_style = ParagraphStyle("ExpTitle",
        fontSize=10, textColor=PRIMARY, fontName="Helvetica-Bold", spaceAfter=1)

    story = []

    # --- HEADER ---
    current_role = data.get("current_role", "")
    contact_info = f'{data["location"]}  |  {data["email"]}  |  {data["phone"]}'
    linkedin = data.get("linkedin", "")

    left_paragraphs = [
        Paragraph(data["name"], name_style),
        Paragraph(current_role, role_style),
        Paragraph(contact_info, small_style),
        Paragraph(linkedin, small_style),
    ]

    if avatar_img:
        try:
            img = RLImage(avatar_img, width=2.8*cm, height=2.8*cm)
            header_table = Table(
                [[left_paragraphs, img]],
                colWidths=[13.5*cm, 3*cm]
            )
            header_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (0, 0), "TOP"),
                ("VALIGN", (1, 0), (1, 0), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            story.append(header_table)
        except Exception as e:
            logger.warning(f"Avatar error: {e}")
            for p in left_paragraphs:
                story.append(p)
    else:
        for p in left_paragraphs:
            story.append(p)

    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=8, spaceBefore=4))

    # --- SUMMARY ---
    story.append(Paragraph("Professional Summary", section_style))
    story.append(Paragraph(data["summary"], body_style))

    # --- EXPERIENCE ---
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_GRAY, spaceAfter=4, spaceBefore=8))
    story.append(Paragraph("Work Experience", section_style))

    for exp in data["experience"]:
        story.append(Paragraph(f"{exp['title']} -- {exp['company']}", exp_title_style))
        story.append(Paragraph(exp["period"], small_style))
        for bullet in exp["description"].split("|"):
            bullet = bullet.strip()
            if bullet:
                story.append(Paragraph(f"- {bullet}", body_style))
        story.append(Spacer(1, 5))

    # --- EDUCATION ---
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_GRAY, spaceAfter=4, spaceBefore=4))
    story.append(Paragraph("Education", section_style))

    for edu in data["education"]:
        edu_title_style = ParagraphStyle("EduTitle",
            fontSize=10, textColor=PRIMARY, fontName="Helvetica-Bold", spaceAfter=1)
        story.append(Paragraph(edu["degree"], edu_title_style))
        story.append(Paragraph(f"{edu['institution']} -- {edu['year']}", small_style))
        story.append(Spacer(1, 4))

    # --- SKILLS ---
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_GRAY, spaceAfter=4, spaceBefore=4))
    story.append(Paragraph("Skills", section_style))
    skills_text = " | ".join(data["skills"])
    story.append(Paragraph(skills_text, body_style))

    # --- CERTIFICATIONS ---
    if data.get("certifications"):
        story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_GRAY, spaceAfter=4, spaceBefore=4))
        story.append(Paragraph("Certifications", section_style))
        for cert in data["certifications"]:
            story.append(Paragraph(f"- {cert}", body_style))

    # --- LANGUAGES ---
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_GRAY, spaceAfter=4, spaceBefore=4))
    story.append(Paragraph("Languages", section_style))
    langs_text = " | ".join(data["languages"])
    story.append(Paragraph(langs_text, body_style))

    doc.build(story)
    return filename


def main():
    NUM_CVS = 30

    logger.info(f"Generating {NUM_CVS} CVs...")
    all_data = []

    for i in range(NUM_CVS):
        role = ROLES[i % len(ROLES)]
        nationality = NATIONALITIES[i % len(NATIONALITIES)]

        logger.info(f"[{i+1}/{NUM_CVS}] Generating CV: {role} ({nationality})")

        try:
            cv_data = generate_cv_data(role, nationality)
            logger.info(f"   Data generated: {cv_data['name']}")

            avatar = get_avatar(cv_data["name"], i)
            pdf_path = create_cv_pdf(cv_data, i + 1, avatar)
            logger.info(f"   PDF created: {pdf_path.name}")

            all_data.append(cv_data)

        except Exception as e:
            logger.error(f"   Error on CV {i+1}: {e}")
            continue
    # For later use in RAG
    with open(OUTPUT_DIR / "candidates_metadata.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    logger.info(f"Done! {len(all_data)} CVs in '{OUTPUT_DIR}'")


if __name__ == "__main__":
    main()
