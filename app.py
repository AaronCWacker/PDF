import os
import io
import re
import streamlit as st

# Must be the very first Streamlit command.
st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

from PIL import Image
import fitz  # PyMuPDF

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ---------------------------------------------------------------
# Define available NotoEmoji fonts (all in the base directory now)
available_fonts = {
    "NotoEmoji Variable": "NotoEmoji-VariableFont_wght.ttf",
    "NotoEmoji Bold": "NotoEmoji-Bold.ttf",
    "NotoEmoji Light": "NotoEmoji-Light.ttf",
    "NotoEmoji Medium": "NotoEmoji-Medium.ttf",
    "NotoEmoji Regular": "NotoEmoji-Regular.ttf",
    "NotoEmoji SemiBold": "NotoEmoji-SemiBold.ttf"
}

# Sidebar: Let the user choose the desired NotoEmoji font.
selected_font_name = st.sidebar.selectbox(
    "Select NotoEmoji Font",
    options=list(available_fonts.keys())
)
selected_font_path = available_fonts[selected_font_name]

# Register the chosen emoji font with ReportLab.
pdfmetrics.registerFont(TTFont(selected_font_name, selected_font_path))

# ---------------------------------------------------------------
# Helper function to wrap emoji characters with a font tag.
def apply_emoji_font(text, emoji_font):
    # This regex attempts to capture many common emoji ranges.
    emoji_pattern = re.compile(
        r"([\U0001F300-\U0001F5FF"
        r"\U0001F600-\U0001F64F"
        r"\U0001F680-\U0001F6FF"
        r"\U0001F700-\U0001F77F"
        r"\U0001F780-\U0001F7FF"
        r"\U0001F800-\U0001F8FF"
        r"\U0001F900-\U0001F9FF"
        r"\U0001FA00-\U0001FA6F"
        r"\U0001FA70-\U0001FAFF"
        r"\u2600-\u26FF"
        r"\u2700-\u27BF]+)"
    )
    # Wrap found emoji with a font tag using the selected emoji font.
    return emoji_pattern.sub(r'<font face="{}">\1</font>'.format(emoji_font), text)

# ---------------------------------------------------------------
# Default markdown content with emojis.
default_markdown = """# Pillow-PyMuPDF-ReportLab - Markdown to PDF One Pager

## Core ML Techniques
1. 🌟 **Mixture of Experts (MoE)**
   - Conditional computation techniques
   - Sparse gating mechanisms
   - Training specialized sub-models

2. 🔥 **Supervised Fine-Tuning (SFT) using PyTorch**
   - Loss function customization
   - Gradient accumulation strategies
   - Learning rate schedulers

3. 🤖 **Large Language Models (LLM) using Transformers**
   - Attention mechanisms
   - Tokenization strategies
   - Position encodings

## Training Methods
4. 📊 **Self-Rewarding Learning using NPS 0-10 and Verbatims**
   - Custom reward functions
   - Feedback categorization
   - Signal extraction from text

5. 👍 **Reinforcement Learning from Human Feedback (RLHF)**
   - Preference datasets
   - PPO implementation
   - KL divergence constraints

6. 🔗 **MergeKit: Merging Models to Same Embedding Space**
   - TIES merging
   - Task arithmetic
   - SLERP interpolation

## Optimization & Deployment
7. 📏 **DistillKit: Model Size Reduction with Spectrum Analysis**
   - Knowledge distillation
   - Quantization techniques
   - Model pruning strategies

8. 🧠 **Agentic RAG Agents using Document Inputs**
   - Vector database integration
   - Query planning
   - Self-reflection mechanisms

9. ⏳ **Longitudinal Data Summarization from Multiple Docs**
   - Multi-document compression
   - Timeline extraction
   - Entity tracking

## Knowledge Representation
10. 📑 **Knowledge Extraction using Markdown Knowledge Graphs**
    - Entity recognition
    - Relationship mapping
    - Hierarchical structuring

11. 🗺️ **Knowledge Mapping with Mermaid Diagrams**
    - Flowchart generation
    - Sequence diagram creation
    - State diagrams

12. 💻 **ML Code Generation with Streamlit/Gradio/HTML5+JS**
    - Code completion
    - Unit test generation
    - Documentation synthesis
"""

# ---------------------------------------------------------------
# Process markdown into a two-column layout for the PDF.
def markdown_to_pdf_content(markdown_text):
    lines = markdown_text.strip().split('\n')
    pdf_content = []
    in_list_item = False
    current_item = None
    sub_items = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('# '):
            # Optionally skip the main title.
            pass
        elif line.startswith('## '):
            if current_item and sub_items:
                pdf_content.append([current_item, sub_items])
                sub_items = []
                current_item = None
            section = line.replace('## ', '').strip()
            pdf_content.append(f"<b>{section}</b>")
            in_list_item = False
        elif re.match(r'^\d+\.', line):
            if current_item and sub_items:
                pdf_content.append([current_item, sub_items])
                sub_items = []
            current_item = line.strip()
            in_list_item = True
        elif line.startswith('- ') and in_list_item:
            sub_items.append(line.strip())
        else:
            if not in_list_item:
                pdf_content.append(line.strip())
    
    if current_item and sub_items:
        pdf_content.append([current_item, sub_items])
    
    mid_point = len(pdf_content) // 2
    left_column = pdf_content[:mid_point]
    right_column = pdf_content[mid_point:]
    
    return left_column, right_column

# ---------------------------------------------------------------
# Create the PDF using ReportLab.
def create_main_pdf(markdown_text, base_font_size=10, auto_size=False):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=(A4[1], A4[0]),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    story = []
    spacer_height = 10
    left_column, right_column = markdown_to_pdf_content(markdown_text)
    
    total_items = 0
    for col in (left_column, right_column):
        for item in col:
            if isinstance(item, list):
                main_item, sub_items = item
                total_items += 1 + len(sub_items)
            else:
                total_items += 1
    
    if auto_size:
        base_font_size = max(6, min(12, 200 / total_items))
    
    item_font_size = base_font_size
    subitem_font_size = base_font_size * 0.9
    section_font_size = base_font_size * 1.2
    title_font_size = min(16, base_font_size * 1.5)
    
    # Define ParagraphStyles using Helvetica for normal text.
    title_style = ParagraphStyle(
        'Heading1',
        parent=styles['Heading1'],
        fontName="Helvetica-Bold",
        textColor=colors.darkblue,
        alignment=1,
        fontSize=title_font_size
    )
    
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Heading2'],
        fontName="Helvetica-Bold",
        textColor=colors.darkblue,
        fontSize=section_font_size,
        leading=section_font_size * 1.2,
        spaceAfter=2
    )
    
    item_style = ParagraphStyle(
        'ItemStyle',
        parent=styles['Normal'],
        fontName="Helvetica",
        fontSize=item_font_size,
        leading=item_font_size * 1.2,
        spaceAfter=1
    )
    
    subitem_style = ParagraphStyle(
        'SubItemStyle',
        parent=styles['Normal'],
        fontName="Helvetica",
        fontSize=subitem_font_size,
        leading=subitem_font_size * 1.2,
        leftIndent=10,
        spaceAfter=1
    )
    
    story.append(Paragraph(apply_emoji_font("Cutting-Edge ML Outline (ReportLab)", selected_font_name), title_style))
    story.append(Spacer(1, spacer_height))
    
    left_cells = []
    for item in left_column:
        if isinstance(item, str) and item.startswith('<b>'):
            # Process section headings.
            text = item.replace('<b>', '').replace('</b>', '')
            left_cells.append(Paragraph(apply_emoji_font(text, selected_font_name), section_style))
        elif isinstance(item, list):
            main_item, sub_items = item
            left_cells.append(Paragraph(apply_emoji_font(main_item, selected_font_name), item_style))
            for sub_item in sub_items:
                left_cells.append(Paragraph(apply_emoji_font(sub_item, selected_font_name), subitem_style))
        else:
            left_cells.append(Paragraph(apply_emoji_font(item, selected_font_name), item_style))
    
    right_cells = []
    for item in right_column:
        if isinstance(item, str) and item.startswith('<b>'):
            text = item.replace('<b>', '').replace('</b>', '')
            right_cells.append(Paragraph(apply_emoji_font(text, selected_font_name), section_style))
        elif isinstance(item, list):
            main_item, sub_items = item
            right_cells.append(Paragraph(apply_emoji_font(main_item, selected_font_name), item_style))
            for sub_item in sub_items:
                right_cells.append(Paragraph(apply_emoji_font(sub_item, selected_font_name), subitem_style))
        else:
            right_cells.append(Paragraph(apply_emoji_font(item, selected_font_name), item_style))
    
    max_cells = max(len(left_cells), len(right_cells))
    left_cells.extend([""] * (max_cells - len(left_cells)))
    right_cells.extend([""] * (max_cells - len(right_cells)))
    
    table_data = list(zip(left_cells, right_cells))
    col_width = (A4[1] - 72) / 2.0
    table = Table(table_data, colWidths=[col_width, col_width], hAlign='CENTER')
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0, colors.white),
        ('LINEAFTER', (0, 0), (0, -1), 0.5, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))
    
    story.append(table)
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ---------------------------------------------------------------
# Convert PDF bytes to an image for preview using PyMuPDF.
def pdf_to_image(pdf_bytes):
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()
        return img
    except Exception as e:
        st.error(f"Failed to render PDF preview: {e}")
        return None

# ---------------------------------------------------------------
# Sidebar options for text size.
with st.sidebar:
    auto_size = st.checkbox("Auto-size text", value=True)
    if not auto_size:
        base_font_size = st.slider("Base Font Size (points)", min_value=6, max_value=16, value=10, step=1)
    else:
        base_font_size = 10
        st.info("Font size will auto-adjust between 6-12 points based on content length.")

# Persist markdown content in session state.
if 'markdown_content' not in st.session_state:
    st.session_state.markdown_content = default_markdown

# ---------------------------------------------------------------
# Generate the PDF.
with st.spinner("Generating PDF..."):
    pdf_bytes = create_main_pdf(st.session_state.markdown_content, base_font_size, auto_size)

# Display PDF preview.
with st.container():
    pdf_image = pdf_to_image(pdf_bytes)
    if pdf_image:
        st.image(pdf_image, use_container_width=True)
    else:
        st.info("Download the PDF to view it locally.")

# PDF Download button.
st.download_button(
    label="Download PDF",
    data=pdf_bytes,
    file_name="ml_outline.pdf",
    mime="application/pdf"
)

# Markdown editor.
edited_markdown = st.text_area(
    "Modify the markdown content below:",
    value=st.session_state.markdown_content,
    height=300
)

# Update PDF on button click.
if st.button("Update PDF"):
    st.session_state.markdown_content = edited_markdown
    st.experimental_rerun()

# Markdown Download button.
st.download_button(
    label="Save Markdown",
    data=st.session_state.markdown_content,
    file_name="ml_outline.md",
    mime="text/markdown"
)
