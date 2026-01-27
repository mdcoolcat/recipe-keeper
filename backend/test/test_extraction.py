"""Test recipe extraction against test_urls.csv"""
import csv
import requests
import json
import time
import sys
import os

# Add parent directory to path so we can import backend modules if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

API_URL = "http://localhost:8000/api/extract-recipe"

def compare_ingredients(expected, extracted):
    """Compare ingredient lists"""
    expected_clean = [i.strip() for i in expected if i.strip()]
    extracted_clean = [i.strip() for i in extracted if i.strip()]

    matches = 0
    for exp in expected_clean:
        # Check if any extracted ingredient contains the expected one (flexible matching)
        if any(exp.lower() in ext.lower() or ext.lower() in exp.lower() for ext in extracted_clean):
            matches += 1

    return matches, len(expected_clean), expected_clean, extracted_clean

def compare_steps(expected, extracted):
    """Compare instruction steps"""
    expected_clean = [s.strip() for s in expected if s.strip()]
    extracted_clean = [s.strip() for s in extracted if s.strip()]

    return len(expected_clean), len(extracted_clean), expected_clean, extracted_clean

def test_url(title, url, expected_ingredients, expected_steps, expected_method):
    """Test a single URL"""
    print(f"\n{'='*80}")
    print(f"Testing: {title}")
    print(f"URL: {url}")
    print(f"Expected Extraction Method: {expected_method.upper() if expected_method else 'N/A'}")
    print(f"{'='*80}")

    try:
        response = requests.post(API_URL, json={"url": url}, timeout=90)
        data = response.json()

        if not data.get("success"):
            print(f"❌ FAILED: {data.get('error')}")
            return False, None

        recipe = data.get("recipe", {})
        extraction_method = data.get("extraction_method", "unknown")
        print(f"\n✅ Extraction succeeded!")
        print(f"Platform: {data.get('platform', 'unknown').upper()}")
        print(f"Extraction Method: {extraction_method.upper()}")

        # Verify extraction method matches expected
        if expected_method and extraction_method.lower() != expected_method.lower():
            print(f"⚠️  WARNING: Expected method '{expected_method}' but got '{extraction_method}'")
        elif expected_method:
            print(f"✅ Extraction method matches expected: {expected_method}")

        print(f"Extracted Title: {recipe.get('title')}")
        print(f"Thumbnail: {recipe.get('thumbnail_url', 'None')[:80]}...")

        # Display extracted ingredients (always)
        ext_ingredients = recipe.get('ingredients', [])
        print(f"\n📝 Ingredients: {len(ext_ingredients)} extracted")
        if ext_ingredients:
            for idx, ing in enumerate(ext_ingredients[:10], 1):  # Show first 10
                print(f"   {idx}. {ing}")
            if len(ext_ingredients) > 10:
                print(f"   ... and {len(ext_ingredients) - 10} more")
        else:
            print("   (none)")

        # Compare with expected if provided
        if expected_ingredients:
            matches, total, exp_list, ext_list = compare_ingredients(expected_ingredients, ext_ingredients)
            print(f"Comparison: {matches}/{total} matched with expected")
            if matches == total:
                print("✅ All ingredients matched!")
            elif matches > total * 0.7:
                print("⚠️  Most ingredients matched (>70%)")
            else:
                print("❌ Poor ingredient match (<70%)")

        # Display extracted steps (always)
        ext_steps = recipe.get('steps', [])
        print(f"\n👨‍🍳 Instructions: {len(ext_steps)} steps extracted")
        if ext_steps:
            for idx, step in enumerate(ext_steps[:5], 1):  # Show first 5
                step_preview = step[:100] + "..." if len(step) > 100 else step
                print(f"   {idx}. {step_preview}")
            if len(ext_steps) > 5:
                print(f"   ... and {len(ext_steps) - 5} more steps")
        else:
            print("   (none)")

        # Compare with expected if provided
        if expected_steps:
            exp_count, ext_count, exp_list, ext_list = compare_steps(expected_steps, ext_steps)
            print(f"Comparison: {ext_count} steps (expected {exp_count})")
            if ext_count == 0 and exp_count > 0:
                print("⚠️  No steps extracted (but expected some)")
            elif ext_count > 0:
                print("✅ Steps extracted successfully")

        return True, extraction_method

    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT: Request took longer than 90 seconds")
        return False, None
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False, None

def main():
    """Run all tests from test_urls.csv"""
    print("Starting Recipe Extraction Tests")

    # Clear cache before running tests
    print("Clearing cache...")
    try:
        response = requests.delete(f"{API_URL.replace('/extract-recipe', '/cache')}")
        if response.status_code == 200:
            print("✓ Cache cleared successfully\n")
        else:
            print(f"⚠ Cache clear returned status {response.status_code}\n")
    except Exception as e:
        print(f"⚠ Could not clear cache: {e}\n")

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
        ingredients = (test.get('Ingredients') or '').split('\n')
        instructions = (test.get('Instructions') or '').split('\n')
        expected_method = test.get('ExtractedMethod', '').strip()

        if not url:
            continue

        print(f"\nTest {i}/{len(tests)}")
        success, extraction_method = test_url(title, url, ingredients, instructions, expected_method)
        results.append({
            'title': title,
            'url': url,
            'success': success,
            'extraction_method': extraction_method or 'N/A',
            'expected_method': expected_method or 'N/A',
            'method_match': extraction_method == expected_method if expected_method else None
        })

        # Wait a bit between requests to avoid rate limiting
        if i < len(tests):
            print("\nWaiting 20 seconds before next test...")
            time.sleep(20)

    # Summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")

    passed = sum(1 for r in results if r['success'])
    total = len(results)

    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    # Count method matches
    method_matches = sum(1 for r in results if r.get('method_match') == True)
    method_total = sum(1 for r in results if r.get('method_match') is not None)
    if method_total > 0:
        print(f"Extraction Method Match: {method_matches}/{method_total} ({method_matches/method_total*100:.1f}%)")

    print("\nResults:")
    print(f"{'Status':<10} {'Expected':<12} {'Actual':<12} {'Match':<7} {'Title':<45}")
    print(f"{'-'*10} {'-'*12} {'-'*12} {'-'*7} {'-'*45}")
    for r in results:
        status = "✅ PASS" if r['success'] else "❌ FAIL"
        expected = r['expected_method'][:11] if r['expected_method'] else 'N/A'
        actual = r['extraction_method'][:11] if r['extraction_method'] else 'N/A'
        match = "✅" if r.get('method_match') == True else ("❌" if r.get('method_match') == False else "N/A")
        title = r['title'][:44] if len(r['title']) > 44 else r['title']
        print(f"{status:<10} {expected:<12} {actual:<12} {match:<7} {title:<45}")

if __name__ == "__main__":
    main()
