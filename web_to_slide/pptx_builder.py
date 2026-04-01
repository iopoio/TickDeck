from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
import io
import base64
from PIL import Image
import colorsys

def _hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def _tinted_dark(primary_hex):
    rgb = _hex_to_rgb(primary_hex)
    h, s, l = colorsys.rgb_to_hls(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
    # Target: L=0.08, S=0.25 (Very dark, slightly saturated with primary hue)
    r, g, b = colorsys.hls_to_rgb(h, 0.08, 0.25)
    return RGBColor(int(r*255), int(g*255), int(b*255))

def _tinted_gray(primary_hex):
    rgb = _hex_to_rgb(primary_hex)
    h, s, l = colorsys.rgb_to_hls(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
    # Target: L=0.55, S=0.08 (Subtle gray with primary tint)
    r, g, b = colorsys.hls_to_rgb(h, 0.55, 0.08)
    return RGBColor(int(r*255), int(g*255), int(b*255))

def _headline_font_size(text):
    length = len(text)
    if length > 28: return Pt(52)
    elif length > 18: return Pt(64)
    else: return Pt(80)

def build_cover(brand, headline, sub, logo_b64=None):
    """
    Build a premium cover slide using python-pptx from a template.
    Returns: bytes (PPTX file content)
    """
    template_path = 'static/templates/cover_default.pptx'
    try:
        prs = Presentation(template_path)
    except Exception as e:
        # Fallback to creating a new presentation if template is missing
        prs = Presentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)
        prs.slides.add_slide(prs.slide_layouts[6])
        
    slide = prs.slides[0]
    
    primary_hex = brand.get('primaryColor', '#1C3D5A')
    p_rgb = _hex_to_rgb(primary_hex)
    primary_color = RGBColor(*p_rgb)
    
    bg_color = _tinted_dark(primary_hex)
    gray_color = _tinted_gray(primary_hex)
    
    # Iterate over shapes and update placeholders/styles
    for shape in list(slide.shapes):
        # Background rect (Full screen)
        if shape.left == 0 and shape.top == 0 and abs(shape.width - prs.slide_width) < 0.1:
            shape.fill.solid()
            shape.fill.fore_color.rgb = bg_color
            continue
            
        # Bottom Bar
        if shape.top >= Inches(7.0) and abs(shape.width - prs.slide_width) < 0.1:
            shape.fill.solid()
            shape.fill.fore_color.rgb = primary_color
            continue

        # Text Frames
        if shape.has_text_frame:
            text = shape.text.upper()
            if "HEADLINE PLACEHOLDER" in text:
                shape.text = headline or ""
                p = shape.text_frame.paragraphs[0]
                p.font.size = _headline_font_size(headline or "")
                p.font.color.rgb = RGBColor(255, 255, 255)
                p.font.bold = True
            elif "SUBHEADLINE PLACEHOLDER" in text:
                shape.text = sub or ""
                p = shape.text_frame.paragraphs[0]
                p.font.size = Pt(18)
                p.font.color.rgb = gray_color
            elif "COMPANY NAME" in text:
                shape.text = brand.get('name', 'Company').upper()
                shape.fill.solid()
                shape.fill.fore_color.rgb = primary_color
                for p in shape.text_frame.paragraphs:
                    p.font.color.rgb = RGBColor(255, 255, 255)
                    p.font.bold = True
            elif "LOGO AREA" in text and not logo_b64:
                # If no logo, just remove the marker
                shape._element.getparent().remove(shape._element)

        # Accent Line (identified by y-pos)
        if not shape.has_text_frame and Inches(5.24) <= shape.top <= Inches(5.26):
            shape.fill.solid()
            shape.fill.fore_color.rgb = primary_color

    # Add Logo if available
    if logo_b64:
        try:
            # Strip data prefix if present
            if ',' in logo_b64:
                logo_b64 = logo_b64.split(',')[1]
                
            image_data = base64.b64decode(logo_b64)
            image_stream = io.BytesIO(image_data)
            
            with Image.open(image_stream) as img:
                w, h = img.size
                aspect = w / float(h or 1)
                max_w = Inches(1.8)
                max_h = Inches(0.5)
                
                if aspect >= max_w / max_h:
                    l_w = max_w
                    l_h = max_w / aspect
                else:
                    l_h = max_h
                    l_w = max_h * aspect
                
                # Position near right-bottom
                l_x = prs.slide_width - l_w - Inches(0.5)
                l_y = Inches(7.05) - l_h - Inches(0.1)
                
                image_stream.seek(0)
                slide.shapes.add_picture(image_stream, l_x, l_y, width=l_w, height=l_h)
                
            # Clean up marker
            for shape in list(slide.shapes):
                if shape.has_text_frame and "LOGO AREA" in shape.text:
                    shape._element.getparent().remove(shape._element)
        except Exception:
            pass

    # Save to memory
    output = io.BytesIO()
    prs.save(output)
    return output.getvalue()


def merge_cover(pptx_bytes, brand, headline, sub, logo_b64=None):
    """
    Phase 1.5: PptxGenJS가 만든 PPTX에서 slide[0]을 python-pptx 커버로 교체.
    Returns: bytes (병합된 PPTX)
    """
    from pptx.opc.constants import RELATIONSHIP_TYPE as RT
    from copy import deepcopy
    from lxml import etree

    # 1. PptxGenJS PPTX 열기
    src_stream = io.BytesIO(pptx_bytes)
    prs = Presentation(src_stream)

    # 2. python-pptx로 커버 PPTX 생성
    cover_bytes = build_cover(brand, headline, sub, logo_b64)
    cover_stream = io.BytesIO(cover_bytes)
    cover_prs = Presentation(cover_stream)
    cover_slide = cover_prs.slides[0]

    # 3. 기존 slide[0] 삭제
    if len(prs.slides) > 0:
        first_slide = prs.slides[0]
        rId = None
        for rel in prs.part.rels.values():
            if rel.target_part == first_slide.part:
                rId = rel.rId
                break
        if rId:
            # XML에서 슬라이드 참조 제거
            sldIdLst = prs.presentation.sldIdLst
            for sldId in sldIdLst:
                if sldId.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id') == rId:
                    sldIdLst.remove(sldId)
                    break
            # relationship 제거
            del prs.part.rels[rId]

    # 4. 커버 슬라이드의 XML과 리소스를 복사해서 새 슬라이드로 추가
    # 간단한 방식: 빈 슬라이드 추가 → XML 교체
    slide_layout = prs.slide_layouts[6]  # blank layout
    new_slide = prs.slides.add_slide(slide_layout)

    # 새 슬라이드의 XML을 커버 슬라이드 XML로 교체
    new_slide_elem = new_slide._element
    cover_elem = cover_slide._element

    # 기존 spTree 제거 → 커버의 spTree 복사
    ns = '{http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing}'
    sp_tree_tag = '{http://schemas.openxmlformats.org/presentationml/2006/main}cSld'

    old_cSld = new_slide_elem.find(sp_tree_tag)
    new_cSld = deepcopy(cover_elem.find(sp_tree_tag))
    if old_cSld is not None and new_cSld is not None:
        parent = new_slide_elem
        parent.replace(old_cSld, new_cSld)

    # 5. 새 슬라이드를 맨 앞으로 이동
    sldIdLst = prs.presentation.sldIdLst
    sldId_elements = list(sldIdLst)
    if len(sldId_elements) >= 2:
        last = sldId_elements[-1]  # 방금 추가한 슬라이드
        sldIdLst.remove(last)
        sldIdLst.insert(0, last)

    # 6. 저장
    output = io.BytesIO()
    prs.save(output)
    return output.getvalue()
