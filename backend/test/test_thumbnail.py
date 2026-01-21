"""Test thumbnail extraction for all URLs in test_urls.csv"""
import sys
import os
import csv

# Add parent directory to path so we can import backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from video_processor import video_processor


def test_thumbnail(title, url):
    """Test thumbnail extraction for a single URL"""
    print(f"\n{'='*80}")
    print(f"Testing: {title}")
    print(f"URL: {url}")
    print(f"{'='*80}")

    try:
        metadata = video_processor.get_video_info(url)

        if metadata:
            video_title = metadata.get('title', 'N/A')
            thumbnail_url = metadata.get('thumbnail', '')

            print(f"✅ Metadata extracted successfully!")
            print(f"Title: {video_title}")
            print(f"Thumbnail URL: {thumbnail_url[:80]}..." if len(thumbnail_url) > 80 else f"Thumbnail URL: {thumbnail_url}")
            print(f"Thumbnail length: {len(thumbnail_url)} chars")

            if thumbnail_url:
                print("✅ Thumbnail URL found!")
                return True
            else:
                print("⚠️  No thumbnail URL found")
                return False
        else:
            print("❌ Failed to get metadata")
            return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def main():
    """Run thumbnail tests for all URLs in test_urls.csv"""
    print("Starting Thumbnail Extraction Tests")
    print("Reading test_urls.csv...")

    # test_urls.csv is in the same directory as this test file
    csv_path = os.path.join(os.path.dirname(__file__), 'test_urls.csv')

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        tests = list(reader)

    print(f"Found {len(tests)} test cases\n")

    results = []
    for i, test in enumerate(tests, 1):
        title = test.get('Title', '').strip()
        url = test.get('URL', '').strip()

        if not url:
            continue

        print(f"\nTest {i}/{len(tests)}")
        success = test_thumbnail(title, url)
        results.append({
            'title': title,
            'url': url,
            'success': success
        })

    # Summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")

    passed = sum(1 for r in results if r['success'])
    total = len(results)

    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("\nResults:")
    for r in results:
        status = "✅ PASS" if r['success'] else "❌ FAIL"
        print(f"  {status}: {r['title']}")


if __name__ == "__main__":
    main()
