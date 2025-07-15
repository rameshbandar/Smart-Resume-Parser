import fitz  # PyMuPDF
from docx import Document
import spacy
import re
import streamlit as st
import pandas as pd
from io import BytesIO

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using PyMuPDF"""
    doc = fitz.open(stream=pdf_path.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_text_from_docx(docx_path):
    """Extract text from DOCX using python-docx"""
    doc = Document(BytesIO(docx_path.read()))
    return "\n".join([para.text for para in doc.paragraphs])

def clean_text(text):
    """Clean and normalize text"""
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_skills(text):
    """Extract skills using spaCy and keyword matching"""
    doc = nlp(text)
    skills = []
    skill_keywords = ["python", "machine learning", "sql", "java", "c++", "aws"]
    
    for token in doc:
        if token.text.lower() in skill_keywords:
            skills.append(token.text)
    
    # Also check noun chunks
    for chunk in doc.noun_chunks:
        if chunk.text.lower() in skill_keywords:
            skills.append(chunk.text)
    
    return list(set(skills))  # Remove duplicates

def extract_experience(text):
    """Extract work experience using regex"""
    experience = []
    # Matches patterns like "Job Title at Company (Date)"
    pattern = r"(.+?)\s+at\s+(.+?)\s*\((\d{4}\s*-\s*\d{4}|present)\)"
    matches = re.finditer(pattern, text, re.IGNORECASE)
    
    for match in matches:
        experience.append({
            "role": match.group(1),
            "company": match.group(2),
            "duration": match.group(3)
        })
    return experience

def extract_education(text):
    """Extract education using regex"""
    education = []
    # Matches patterns like "Degree at University (Year)"
    pattern = r"(Bachelor|Master|PhD|B\.?Tech|M\.?Tech|B\.?Sc|M\.?Sc).*?\s+at\s+(.+?)\s*\((\d{4})\)"
    matches = re.finditer(pattern, text, re.IGNORECASE)
    
    for match in matches:
        education.append({
            "degree": match.group(1),
            "institution": match.group(2),
            "year": match.group(3)
        })
    return education

def extract_contact_info(text):
    """Extract email and phone number"""
    email = re.search(r'[\w\.-]+@[\w\.-]+', text)
    phone = re.search(r'(\+\d{1,3}\s?)?(\(\d{3}\)|\d{3})[\s-]?\d{3}[\s-]?\d{4}', text)
    return {
        "email": email.group(0) if email else None,
        "phone": phone.group(0) if phone else None
    }

def parse_resume(file):
    """Main parsing function"""
    if file.name.endswith('.pdf'):
        text = extract_text_from_pdf(file)
    elif file.name.endswith('.docx'):
        text = extract_text_from_docx(file)
    else:
        raise ValueError("Unsupported file format")
    
    cleaned_text = clean_text(text)
    
    return {
        "contact_info": extract_contact_info(cleaned_text),
        "skills": extract_skills(cleaned_text),
        "experience": extract_experience(cleaned_text),
        "education": extract_education(cleaned_text)
    }

# Streamlit UI
st.title("📄 Smart Resume Parser")
st.markdown("Upload a resume (PDF or DOCX) to extract structured information")

uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx"])

if uploaded_file:
    try:
        resume_data = parse_resume(uploaded_file)
        
        st.subheader("Extracted Information")
        st.json(resume_data)
        
        # Create downloadable files
        json_data = pd.DataFrame.from_dict(resume_data, orient='index').to_json()
        csv_data = pd.json_normalize(resume_data).to_csv(index=False)
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="Download as JSON",
                data=json_data,
                file_name="resume_data.json"
            )
        with col2:
            st.download_button(
                label="Download as CSV",
                data=csv_data,
                file_name="resume_data.csv"
            )
    
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")

st.markdown("---")
st.markdown("### How it works:")
st.markdown("""
1. Upload a resume (PDF or DOCX)
2. The system extracts:
   - Contact information (email, phone)
   - Skills
   - Work experience
   - Education
3. View results in JSON format
4. Download as CSV or JSON
""")