"""CLI 진입점"""
import sys
from .pipeline import run_pipeline


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.yulsight.com"
    company = sys.argv[2] if len(sys.argv) > 2 else None
    result = run_pipeline(url, company)
    print(f"\n[완료] {len(result.get('slides', []))}개 슬라이드")
    print(f"  JSON : slide_{result['meta']['company_name']}.json")


if __name__ == "__main__":
    main()
