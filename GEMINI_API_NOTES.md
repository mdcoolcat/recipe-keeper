# Gemini API Free Tier - Important Findings

## Actual Free Tier Limits (Discovered Through Testing)

### Reality Check ❌
The free tier is **NOT as generous as initially thought**:

| Model | Daily Limit | Status |
|-------|-------------|--------|
| `gemini-2.5-flash` | 20 requests/day | ❌ Very Limited |
| `gemini-2.0-flash` | ~15-20 requests/day | ❌ Also Limited |
| **Shared Quota** | All models share the same pool | ❌ Critical Issue |

### Key Discoveries:

1. **Quota is Shared**: All Gemini models (2.0, 2.5) share the same daily quota
2. **Low Daily Limits**: Around 15-20 total requests per day across all models
3. **Requests Per Minute**: Also limited (hit during testing)
4. **Token Limits**: Input token limits also apply

## What This Means for the Project:

### For POC/Testing:
- ✅ Good for: Light testing (5-10 extractions per day)
- ❌ Bad for: Extensive testing, multiple users, demos

### For Production:
**You will need to upgrade to pay-as-you-go pricing:**
- Input: $0.075 per 1M tokens
- Output: $0.30 per 1M tokens
- Very affordable for recipe extraction use case

### Cost Estimate (Pay-as-you-go):

**Per Recipe Extraction:**
- Text extraction (description/comment): ~500 tokens input → $0.0000375
- Video extraction (fallback): ~1000-5000 tokens input → $0.00075
- **Average cost: Less than $0.001 per recipe**

**For 1000 users extracting 10 recipes each:**
- 10,000 extractions × $0.001 = **~$10/month**

## Successful Tests (Before Hitting Quota):

### Test: Gut Brownies (YouTube)
- ✅ Successfully extracted from comment
- ✅ Thumbnail captured: `https://i.ytimg.com/vi/xe6gvF2nYoI/maxresdefault.jpg`
- ✅ Platform: YouTube
- ✅ Extraction method: Comment text (author)

**Result:**
```json
{
  "title": "Gut Brownies",
  "ingredients": [
    "1 medium Sweet potato",
    "2 medium eggs",
    "70-80mL Honey",
    "8 Tbsp of flour",
    "3 Tbsp Psyllium Husk",
    "4 Tbsp Cacao Powder",
    "1 tsp Baking soda",
    "1 tsp Vanilla Extract",
    "Dark Chocolate Chips",
    "3-4 Tbsp milk of choice",
    "Walnuts"
  ],
  "steps": [
    "Mix Dry Ingredients",
    "Add in Wet Ingredients",
    "Add in 180C or 350F oven for 40 minutes",
    "Enjoy your delicious Treat!"
  ]
}
```

## Recommendations:

### For Immediate Development:
1. **Use Mock Data**: Create cached responses for testing the frontend
2. **Rate Limiting**: Add daily quota tracking to warn users
3. **Wait for Reset**: Quota resets at midnight Pacific Time

### For Launch:
1. **Upgrade to Pay-as-you-go**: Enable billing in Google AI Studio
2. **Add Usage Tracking**: Monitor costs per user/extraction
3. **Consider Caching**: Don't re-extract the same video twice
4. **Error Handling**: Gracefully handle quota exceeded errors

### Alternative Approaches:
1. **Multiple API Keys**: Use key rotation (technically allowed but not scalable)
2. **User-Provided Keys**: Let users bring their own Gemini API key
3. **OpenAI GPT-4**: Alternative API with different pricing (~$0.03/1K tokens)

## Current Model Configuration:

**File:** `backend/recipe_extractor.py`
```python
self.model_id = 'models/gemini-2.0-flash'
```

**Available Models:**
- `models/gemini-2.5-flash` - Latest but lowest free tier
- `models/gemini-2.0-flash` - Slightly better but still limited
- `models/gemini-flash-latest` - Alias to latest flash model

## Testing Strategy Going Forward:

1. **Tomorrow**: Run full test suite after quota resets
2. **Use Judiciously**: Save API calls for important tests
3. **Cache Results**: Store successful extractions for UI testing
4. **Consider Upgrade**: $10-20/month is reasonable for active development

## Quota Reset Schedule:

- **Reset Time**: Midnight Pacific Time (PT)
- **Check Usage**: https://aistudio.google.com/usage
- **Rate Limits Docs**: https://ai.google.dev/gemini-api/docs/rate-limits
