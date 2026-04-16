import io
import logging
from pptx import Presentation
from pptx.util import Inches, Pt, Cm
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

logger = logging.getLogger(__name__)


def _hex_to_rgb(hex_str: str) -> RGBColor:
    """hex 색상 문자열을 RGBColor로 변환"""
    try:
        hex_str = hex_str.lstrip('#')
        if len(hex_str) == 3:
            hex_str = ''.join([c * 2 for c in hex_str])
        return RGBColor(int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))
    except Exception as e:
        logger.error(f"Hex to RGB conversion failed for {hex_str}: {e}")
        raise


def _set_text_style(run, size_pt: int, color: RGBColor, is_bold: bool = False):
    """텍스트 런에 폰트 크기/색상/굵기 적용"""
    run.font.size = Pt(size_pt)
    run.font.name = "Malgun Gothic"
    run.font.color.rgb = color
    run.font.bold = is_bold


def _add_background_fill(slide, color: RGBColor):
    """슬라이드 전체 배경 사각형 추가"""
    width = Cm(33.87)
    height = Cm(19.05)
    rect = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, width, height)
    rect.fill.solid()
    rect.fill.fore_color.rgb = color
    rect.line.fill.background()


def build_pptx(slide_data: dict) -> bytes:
    """SlideData dict를 받아 pptx 파일의 bytes 반환"""
    prs = Presentation()
    prs.slide_width = Cm(33.87)
    prs.slide_height = Cm(19.05)

    brand = slide_data.get("brand", {})
    primary_color_hex = brand.get("primaryColor", "#2563EB")
    primary_color = _hex_to_rgb(primary_color_hex)
    company_name = brand.get("companyName", "TickDeck")

    white = RGBColor(255, 255, 255)
    black = RGBColor(0, 0, 0)
    light_gray = RGBColor(242, 242, 242)

    for slide_info in slide_data.get("slides", []):
        stype = slide_info.get("type", "content")
        slide = prs.slides.add_slide(prs.slide_layouts[6])

        headline = slide_info.get("headline", "")
        subheadline = slide_info.get("subheadline", "")
        body = slide_info.get("body", [])
        eyebrow = slide_info.get("eyebrow", "")

        if stype == "cover":
            _add_background_fill(slide, primary_color)

            tx_hl = slide.shapes.add_textbox(Inches(0.8), Inches(2.5), Inches(11.7), Inches(2.0))
            tf_hl = tx_hl.text_frame
            tf_hl.word_wrap = True
            run_hl = tf_hl.paragraphs[0].add_run()
            run_hl.text = headline
            _set_text_style(run_hl, 54, white, True)

            if subheadline:
                run_sub = tf_hl.add_paragraph().add_run()
                run_sub.text = subheadline
                _set_text_style(run_sub, 24, white)

            tx_co = slide.shapes.add_textbox(Inches(0.8), Inches(6.5), Inches(5), Inches(0.5))
            run_co = tx_co.text_frame.paragraphs[0].add_run()
            run_co.text = company_name
            _set_text_style(run_co, 16, white)

        elif stype == "section_intro":
            _add_background_fill(slide, light_gray)

            if eyebrow:
                tx_eb = slide.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(11.7), Inches(0.5))
                run_eb = tx_eb.text_frame.paragraphs[0].add_run()
                run_eb.text = eyebrow
                _set_text_style(run_eb, 18, primary_color)

            tx_hl = slide.shapes.add_textbox(Inches(0.8), Inches(3.0), Inches(11.7), Inches(1.5))
            run_hl = tx_hl.text_frame.paragraphs[0].add_run()
            run_hl.text = headline
            _set_text_style(run_hl, 48, black, True)

        elif stype == "key_metrics":
            tx_hl = slide.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(11.7), Inches(1.0))
            run_hl = tx_hl.text_frame.paragraphs[0].add_run()
            run_hl.text = headline
            _set_text_style(run_hl, 36, black, True)

            if body:
                n = len(body)
                avail_width = 13.333 - 1.6
                col_width = avail_width / n
                for i, item in enumerate(body):
                    left = Inches(0.8 + (i * col_width))
                    tx_m = slide.shapes.add_textbox(left, Inches(3.0), Inches(col_width - 0.2), Inches(3.0))
                    tf_m = tx_m.text_frame
                    tf_m.word_wrap = True

                    if ":" in item:
                        label, val = item.split(":", 1)
                        p_val = tf_m.paragraphs[0]
                        p_val.alignment = PP_ALIGN.CENTER
                        run_v = p_val.add_run()
                        run_v.text = val.strip()
                        _set_text_style(run_v, 42, primary_color, True)

                        p_lab = tf_m.add_paragraph()
                        p_lab.alignment = PP_ALIGN.CENTER
                        run_l = p_lab.add_run()
                        run_l.text = label.strip()
                        _set_text_style(run_l, 18, black)
                    else:
                        p = tf_m.paragraphs[0]
                        p.alignment = PP_ALIGN.CENTER
                        run_m = p.add_run()
                        run_m.text = item
                        _set_text_style(run_m, 24, black)

        elif stype == "cta":
            _add_background_fill(slide, primary_color)

            tx_box = slide.shapes.add_textbox(Inches(0.8), Inches(3.0), Inches(11.7), Inches(2.5))
            tf = tx_box.text_frame
            tf.word_wrap = True

            run_hl = tf.paragraphs[0].add_run()
            run_hl.text = headline
            _set_text_style(run_hl, 48, white, True)

            if subheadline:
                run_sub = tf.add_paragraph().add_run()
                run_sub.text = subheadline
                _set_text_style(run_sub, 22, white)

        else:  # content 또는 알 수 없는 타입
            tx_hl = slide.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(11.7), Inches(1.0))
            run_hl = tx_hl.text_frame.paragraphs[0].add_run()
            run_hl.text = headline
            _set_text_style(run_hl, 36, black, True)

            if body:
                tx_body = slide.shapes.add_textbox(Inches(0.8), Inches(2.0), Inches(11.7), Inches(5.0))
                tf_body = tx_body.text_frame
                tf_body.word_wrap = True
                for i, bullet in enumerate(body):
                    p = tf_body.paragraphs[0] if i == 0 else tf_body.add_paragraph()
                    run_b = p.add_run()
                    run_b.text = f"• {bullet}"
                    _set_text_style(run_b, 18, black)

    pptx_io = io.BytesIO()
    prs.save(pptx_io)
    return pptx_io.getvalue()
