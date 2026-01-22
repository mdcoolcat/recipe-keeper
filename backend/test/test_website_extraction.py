"""
Test Website Recipe Extraction

Tests recipe extraction from recipe websites using multi-layer approach.
Uses test_websites.csv for test cases with expected outputs.

Usage:
    python test/test_website_extraction.py
    python test/test_website_extraction.py --url https://example.com/recipe
"""

import sys
import os
import asyncio
import csv
from pathlib import Path
from typing import List, Dict

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from web_scraper import WebScraper
from models import Recipe


class WebsiteExtractionTester:
    """Test website recipe extraction with validation"""

    def __init__(self):
        self.web_scraper = WebScraper()
        self.results = []

    def normalize_ingredient(self, ingredient: str) -> str:
        """
        Normalize ingredient for comparison

        Args:
            ingredient: Raw ingredient string

        Returns:
            Normalized ingredient string
        """
        # Remove extra whitespace
        ingredient = ' '.join(ingredient.split())
        # Convert to lowercase for comparison
        return ingredient.lower().strip()

    def extract_quantity(self, ingredient: str) -> str:
        """
        Extract quantity/measurement from ingredient

        Args:
            ingredient: Ingredient string

        Returns:
            Quantity portion of ingredient
        """
        import re
        # Match common patterns: "1 cup", "2 tbsp", "1/2 tsp", "3-4 cloves", etc.
        quantity_pattern = r'^([\d\s/\-½¼¾⅓⅔⅛⅜⅝⅞]+\s*(?:cup|cups|tbsp|tablespoon|tablespoons|tsp|teaspoon|teaspoons|oz|ounces|lb|lbs|pound|pounds|g|grams|ml|l|kg)?)'
        match = re.match(quantity_pattern, ingredient.lower())
        if match:
            return match.group(1).strip()
        return ''

    def compare_ingredients(self, extracted: List[str], expected: List[str]) -> Dict:
        """
        Compare extracted ingredients with expected

        Args:
            extracted: List of extracted ingredients
            expected: List of expected ingredients

        Returns:
            Comparison results dictionary
        """
        result = {
            'total_expected': len(expected),
            'total_extracted': len(extracted),
            'matched': 0,
            'missing': [],
            'extra': [],
            'quantity_mismatches': []
        }

        # Normalize ingredients
        extracted_norm = [self.normalize_ingredient(i) for i in extracted]
        expected_norm = [self.normalize_ingredient(i) for i in expected]

        # Check each expected ingredient
        for exp in expected:
            exp_norm = self.normalize_ingredient(exp)
            exp_quantity = self.extract_quantity(exp_norm)

            found = False
            for ext in extracted:
                ext_norm = self.normalize_ingredient(ext)
                ext_quantity = self.extract_quantity(ext_norm)

                # Check if ingredient name matches (fuzzy)
                # Remove quantities for comparison
                exp_name = exp_norm.replace(exp_quantity, '').strip()
                ext_name = ext_norm.replace(ext_quantity, '').strip()

                if exp_name in ext_name or ext_name in exp_name:
                    found = True
                    result['matched'] += 1

                    # Check if quantities match
                    if exp_quantity and ext_quantity:
                        if exp_quantity != ext_quantity:
                            result['quantity_mismatches'].append({
                                'expected': exp,
                                'extracted': ext,
                                'expected_qty': exp_quantity,
                                'extracted_qty': ext_quantity
                            })
                    break

            if not found:
                result['missing'].append(exp)

        # Check for extra ingredients
        for ext in extracted:
            ext_norm = self.normalize_ingredient(ext)
            ext_quantity = self.extract_quantity(ext_norm)
            ext_name = ext_norm.replace(ext_quantity, '').strip()

            found = False
            for exp in expected:
                exp_norm = self.normalize_ingredient(exp)
                exp_quantity = self.extract_quantity(exp_norm)
                exp_name = exp_norm.replace(exp_quantity, '').strip()

                if exp_name in ext_name or ext_name in exp_name:
                    found = True
                    break

            if not found:
                result['extra'].append(ext)

        return result

    async def test_url(self, url: str, expected_title: str = None,
                      expected_ingredients: List[str] = None,
                      expected_instructions: List[str] = None,
                      expect_llm: bool = False) -> dict:
        """
        Test extraction from a single URL

        Args:
            url: Recipe website URL
            expected_title: Expected recipe title
            expected_ingredients: Expected ingredients list
            expected_instructions: Expected instructions list
            expect_llm: Whether LLM (Gemini) usage is expected

        Returns:
            Test result dictionary
        """
        print(f"\n{'='*80}")
        print(f"Testing: {url}")
        print(f"Expected LLM usage: {expect_llm}")
        print(f"{'='*80}")

        result = {
            'url': url,
            'expected_title': expected_title,
            'expect_llm': expect_llm,
            'success': False,
            'actual_title': None,
            'used_llm': False,
            'error': None,
            'ingredients_count': 0,
            'steps_count': 0,
            'ingredient_comparison': None
        }

        try:
            # Capture console output to detect which layer was used
            import io
            from contextlib import redirect_stdout, redirect_stderr

            captured_output = io.StringIO()

            with redirect_stdout(captured_output), redirect_stderr(captured_output):
                recipe = await self.web_scraper.extract_recipe(url)

            output = captured_output.getvalue()

            # Detect if Gemini was used
            if 'Gemini AI' in output or 'QUOTA_EXCEEDED' in output:
                result['used_llm'] = True

            if recipe:
                result['success'] = True
                result['actual_title'] = recipe.title
                result['ingredients_count'] = len(recipe.ingredients)
                result['steps_count'] = len(recipe.steps)

                print(f"\n✅ SUCCESS!")
                print(f"Title: {recipe.title}")
                print(f"Ingredients: {len(recipe.ingredients)} items")
                print(f"Steps: {len(recipe.steps)} steps")
                print(f"Used LLM: {result['used_llm']}")

                # Validate LLM usage expectation
                if result['used_llm'] and not expect_llm:
                    print(f"\n⚠️  WARNING: Used LLM when not expected!")
                    print(f"Extraction should have succeeded with Schema.org/WordPress/heuristics")
                elif not result['used_llm'] and expect_llm:
                    print(f"\n✅ Great! Extracted without LLM (better than expected)")

                # Compare ingredients if expected provided
                if expected_ingredients:
                    comparison = self.compare_ingredients(recipe.ingredients, expected_ingredients)
                    result['ingredient_comparison'] = comparison

                    print(f"\n📝 Ingredient Validation:")
                    print(f"  Expected: {comparison['total_expected']} items")
                    print(f"  Extracted: {comparison['total_extracted']} items")
                    print(f"  Matched: {comparison['matched']} items")

                    if comparison['missing']:
                        print(f"\n  ❌ Missing ingredients ({len(comparison['missing'])}):")
                        for ing in comparison['missing'][:3]:
                            print(f"    - {ing}")
                        if len(comparison['missing']) > 3:
                            print(f"    ... and {len(comparison['missing']) - 3} more")

                    if comparison['quantity_mismatches']:
                        print(f"\n  ⚠️  Quantity mismatches ({len(comparison['quantity_mismatches'])}):")
                        for mismatch in comparison['quantity_mismatches'][:3]:
                            print(f"    Expected: {mismatch['expected']}")
                            print(f"    Got:      {mismatch['extracted']}")
                        if len(comparison['quantity_mismatches']) > 3:
                            print(f"    ... and {len(comparison['quantity_mismatches']) - 3} more")

                    if comparison['extra']:
                        print(f"\n  ℹ️  Extra ingredients ({len(comparison['extra'])}):")
                        for ing in comparison['extra'][:3]:
                            print(f"    + {ing}")
                        if len(comparison['extra']) > 3:
                            print(f"    ... and {len(comparison['extra']) - 3} more")

                    # Overall success
                    match_rate = comparison['matched'] / comparison['total_expected'] if comparison['total_expected'] > 0 else 0
                    if match_rate >= 0.8:
                        print(f"\n  ✅ Ingredient match rate: {match_rate*100:.1f}% (Good!)")
                    elif match_rate >= 0.6:
                        print(f"\n  ⚠️  Ingredient match rate: {match_rate*100:.1f}% (Acceptable)")
                    else:
                        print(f"\n  ❌ Ingredient match rate: {match_rate*100:.1f}% (Poor)")

                print(f"\nFirst 3 ingredients:")
                for i, ingredient in enumerate(recipe.ingredients[:3], 1):
                    print(f"  {i}. {ingredient}")

                if recipe.steps:
                    print(f"\nFirst 2 steps:")
                    for i, step in enumerate(recipe.steps[:2], 1):
                        print(f"  {i}. {step[:100]}{'...' if len(step) > 100 else ''}")
            else:
                result['error'] = "Extraction failed - no recipe found"
                print(f"\n❌ FAILED: No recipe extracted")

        except Exception as e:
            result['error'] = str(e)
            result['used_llm'] = 'QUOTA_EXCEEDED' in str(e)
            print(f"\n❌ ERROR: {e}")

        self.results.append(result)
        return result

    async def test_csv_file(self, csv_path: str):
        """
        Test extraction from URLs in CSV file

        CSV format: Title,URL,Ingredients,Instructions,LLM

        Args:
            csv_path: Path to CSV file
        """
        print(f"\n{'='*80}")
        print(f"Testing URLs from: {csv_path}")
        print(f"{'='*80}")

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            for row in rows:
                url = row['URL']
                title = row['Title']

                # Parse ingredients (split by newline)
                ingredients_str = row.get('Ingredients', '')
                expected_ingredients = [i.strip() for i in ingredients_str.split('\n') if i.strip()] if ingredients_str else None

                # Parse instructions (split by newline)
                instructions_str = row.get('Instructions', '')
                expected_instructions = [i.strip() for i in instructions_str.split('\n') if i.strip()] if instructions_str else None

                # Parse LLM expectation
                expect_llm = row.get('LLM', 'False').strip().lower() == 'true'

                await self.test_url(url, title, expected_ingredients, expected_instructions, expect_llm)
                await asyncio.sleep(1)  # Be nice to servers

        except FileNotFoundError:
            print(f"❌ ERROR: File not found: {csv_path}")
        except Exception as e:
            print(f"❌ ERROR reading CSV: {e}")
            import traceback
            traceback.print_exc()

    def print_summary(self):
        """Print test summary"""
        print(f"\n\n{'='*80}")
        print("TEST SUMMARY")
        print(f"{'='*80}")

        total = len(self.results)
        successful = sum(1 for r in self.results if r['success'])
        failed = total - successful

        # Check LLM usage violations
        llm_violations = sum(1 for r in self.results if r['success'] and r['used_llm'] and not r['expect_llm'])

        print(f"Total tests: {total}")
        print(f"Successful: {successful} ({successful/total*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100:.1f}%)")

        if llm_violations > 0:
            print(f"\n⚠️  LLM usage violations: {llm_violations}")
            print(f"   (Used LLM when Schema.org/WordPress/heuristics should have worked)")

        if failed > 0:
            print(f"\nFailed URLs:")
            for result in self.results:
                if not result['success']:
                    print(f"  ❌ {result['url']}")
                    print(f"     Error: {result['error']}")

        if llm_violations > 0:
            print(f"\nLLM Usage Violations:")
            for result in self.results:
                if result['success'] and result['used_llm'] and not result['expect_llm']:
                    print(f"  ⚠️  {result['url']}")
                    print(f"     Expected: No LLM, Actual: Used LLM")

        print(f"\n{'='*80}")


async def main():
    """Main test runner"""
    tester = WebsiteExtractionTester()

    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--url' and len(sys.argv) > 2:
            # Test single URL
            url = sys.argv[2]
            await tester.test_url(url)
        else:
            print("Usage:")
            print("  python test/test_website_extraction.py")
            print("  python test/test_website_extraction.py --url https://example.com/recipe")
            sys.exit(1)
    else:
        # Default: test URLs from CSV file
        csv_path = os.path.join(os.path.dirname(__file__), 'test_websites.csv')
        await tester.test_csv_file(csv_path)

    # Print summary
    tester.print_summary()


if __name__ == '__main__':
    asyncio.run(main())
