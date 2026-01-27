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

def test_url(title, url, expected_ingredients, expected_steps):
    """Test a single URL"""
    print(f"\n{'='*80}")
    print(f"Testing: {title}")
    print(f"URL: {url}")
    print(f"{'='*80}")

    try:
        response = requests.post(API_URL, json={"url": url}, timeout=90)
        data = response.json()

        if not data.get("success"):
            print(f"❌ FAILED: {data.get('error')}")
            return False

        recipe = data.get("recipe", {})
        print(f"\n✅ Extraction succeeded!")
        print(f"Platform: {data.get('platform', 'unknown').upper()}")
        print(f"Extracted Title: {recipe.get('title')}")
        print(f"Thumbnail: {recipe.get('thumbnail_url', 'None')[:80]}...")

        # Compare ingredients
        if expected_ingredients:
            matches, total, exp_list, ext_list = compare_ingredients(expected_ingredients, recipe.get('ingredients', []))
            print(f"\n📝 Ingredients: {matches}/{total} matched")
            print(f"Expected ({total}): {exp_list[:3]}..." if len(exp_list) > 3 else f"Expected: {exp_list}")
            print(f"Extracted ({len(ext_list)}): {ext_list[:3]}..." if len(ext_list) > 3 else f"Extracted: {ext_list}")

            if matches == total:
                print("✅ All ingredients matched!")
            elif matches > total * 0.7:
                print("⚠️  Most ingredients matched (>70%)")
            else:
                print("❌ Poor ingredient match (<70%)")

        # Compare steps
        if expected_steps:
            exp_count, ext_count, exp_list, ext_list = compare_steps(expected_steps, recipe.get('steps', []))
            print(f"\n👨‍🍳 Instructions: {ext_count} steps extracted (expected {exp_count})")
            if ext_count > 0:
                print(f"First step: {ext_list[0][:100]}..." if len(ext_list[0]) > 100 else f"First step: {ext_list[0]}")

            if ext_count == 0 and exp_count > 0:
                print("⚠️  No steps extracted (but expected some)")
            elif ext_count > 0:
                print("✅ Steps extracted successfully")

        return True

    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT: Request took longer than 90 seconds")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    """Run all tests from test_urls.csv"""
    print("Starting Recipe Extraction Tests")
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

        if not url:
            continue

        print(f"\nTest {i}/{len(tests)}")
        success = test_url(title, url, ingredients, instructions)
        results.append({
            'title': title,
            'url': url,
            'success': success
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
    print("\nResults:")
    for r in results:
        status = "✅ PASS" if r['success'] else "❌ FAIL"
        print(f"  {status}: {r['title']}")

if __name__ == "__main__":
    main()
