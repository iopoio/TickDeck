from web_to_slide.pptx_builder import build_cover
import os

def test_pptx_generation():
    brand = {
        'name': 'Antigravity Inc',
        'primaryColor': '#5A9E86' # Sage
    }
    headline = "The Future of AI Coding"
    sub = "Powered by antigravity and expert agents."
    
    # Try generating without logo first
    print("Generating PPTX without logo...")
    pptx_bytes = build_cover(brand, headline, sub)
    
    os.makedirs('tmp', exist_ok=True)
    with open('tmp/test_cover.pptx', 'wb') as f:
        f.write(pptx_bytes)
    print("Saved to tmp/test_cover.pptx")
    
    # Check if file size is reasonable
    size = os.path.getsize('tmp/test_cover.pptx')
    print(f"File size: {size} bytes")
    if size > 1000:
        print("Test PASSED: File generated.")
    else:
        print("Test FAILED: File too small.")

if __name__ == "__main__":
    test_pptx_generation()
