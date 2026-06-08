import pdfplumber
from groq import Groq
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_JUSTIFY
import re

LANGUAGES = {
    "Português": "Portuguese (Brazil)",
    "Inglês": "English",
    "Espanhol": "Spanish",
    "Francês": "French",
    "Alemão": "German",
    "Italiano": "Italian",
    "Japonês": "Japanese",
    "Chinês": "Chinese (Simplified)",
    "Russo": "Russian",
    "Árabe": "Arabic",
}

def extract_text_by_page(pdf_path):
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            raw = page.extract_text(layout=True) or ""
            paragraphs = [p.strip() for p in re.split(r'\n\s*\n', raw) if p.strip()]
            pages.append({"page": i + 1, "paragraphs": paragraphs})
    return pages

def translate_text(text, target_lang, api_key):
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": f"You are a professional translator. Translate everything to {target_lang}. Preserve paragraph structure. Return only the translation, no explanations."
            },
            {
                "role": "user",
                "content": text
            }
        ]
    )
    return response.choices[0].message.content.strip()

def translate_pages(pages, target_lang, api_key, progress_callback=None):
    translated = []
    total = len(pages)
    for i, page_data in enumerate(pages):
        if progress_callback:
            progress_callback(i, total, f"Traduzindo página {page_data['page']} de {total}...")
        full_text = "\n\n".join(page_data["paragraphs"])
        if not full_text.strip():
            translated.append({"page": page_data["page"], "paragraphs": []})
            continue
        translated_text = translate_text(full_text, target_lang, api_key)
        t_paragraphs = [p.strip() for p in re.split(r'\n\s*\n', translated_text) if p.strip()]
        translated.append({"page": page_data["page"], "paragraphs": t_paragraphs})
    if progress_callback:
        progress_callback(total, total, "Tradução concluída!")
    return translated

def generate_pdf(translated_pages, output_path, target_lang):
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            rightMargin=2.5*cm, leftMargin=2.5*cm,
                            topMargin=2.5*cm, bottomMargin=2.5*cm)
    styles = getSampleStyleSheet()
    body_style = ParagraphStyle("Body", parent=styles["Normal"],
                                fontSize=11, leading=16,
                                alignment=TA_JUSTIFY, spaceAfter=8)
    page_label_style = ParagraphStyle("PageLabel", parent=styles["Normal"],
                                      fontSize=8, textColor=colors.HexColor("#888888"),
                                      spaceAfter=4, spaceBefore=12)
    story = []
    for page_data in translated_pages:
        if not page_data["paragraphs"]:
            continue
        story.append(Paragraph(f"— Página {page_data['page']} —", page_label_style))
        for para in page_data["paragraphs"]:
            safe = para.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(safe, body_style))
        story.append(Spacer(1, 6))
        story.append(HRFlowable(width="100%", thickness=0.4, color=colors.HexColor("#dddddd")))
        story.append(Spacer(1, 6))
    doc.build(story)

def translate_pdf(input_path, output_path, target_lang_display, api_key, progress_callback=None):
    target_lang_en = LANGUAGES.get(target_lang_display, target_lang_display)
    if progress_callback:
        progress_callback(0, 1, "Extraindo texto do PDF...")
    pages = extract_text_by_page(input_path)
    if not pages:
        raise ValueError("Nenhum texto encontrado no PDF.")
    translated = translate_pages(pages, target_lang_en, api_key, progress_callback)
    if progress_callback:
        progress_callback(0, 1, "Gerando PDF traduzido...")
    generate_pdf(translated, output_path, target_lang_display)
    return output_path
