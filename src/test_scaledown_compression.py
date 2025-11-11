"""
Test ScaleDown compression to debug the issue without hitting OpenAI API limits.
This script tests ONLY the compression step, showing you what's being compressed
and what ScaleDown returns.
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_compression(context, prompt, compression_rate="auto", model="gpt-4o"):
    """
    Test ScaleDown compression and show detailed results.
    
    Args:
        context: The context to compress (user prefs + channel data)
        prompt: The question/instruction
        compression_rate: Compression rate ("auto", 0.3, 0.5, 0.7, etc.)
        model: Target model
    """
    
    scaledown_api_key = os.getenv('SCALEDOWN_API_KEY')
    if not scaledown_api_key:
        print("❌ ERROR: SCALEDOWN_API_KEY not found in .env file")
        return
    
    print("=" * 80)
    print(f"TESTING SCALEDOWN COMPRESSION (rate: {compression_rate})")
    print("=" * 80)
    
    # Show what we're sending
    print("\n📤 INPUT TO SCALEDOWN:")
    print(f"\n--- CONTEXT (length: {len(context)} chars) ---")
    print(context)
    print(f"\n--- PROMPT (length: {len(prompt)} chars) ---")
    print(prompt)
    
    # Prepare request
    url = "https://api.scaledown.xyz/compress/raw/"
    headers = {
        'x-api-key': scaledown_api_key,
        'Content-Type': 'application/json'
    }
    
    payload = {
        "context": context,
        "prompt": prompt,
        "model": model,
        "scaledown": {
            "rate": compression_rate
        }
    }
    
    # Debug: Show the exact payload being sent
    print(f"\n🔍 DEBUG - Payload being sent:")
    print(f"   Context length: {len(context)}")
    print(f"   Prompt length: {len(prompt)}")
    print(f"   Payload keys: {list(payload.keys())}")
    print(f"   Scaledown config: {payload['scaledown']}")
    
    # Make request
    print(f"\n🔄 Calling ScaleDown API...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        # Debug: Show raw response
        print(f"\n🔍 DEBUG - Raw API response:")
        print(json.dumps(result, indent=2))
        
        # Show results
        print("\n✅ SCALEDOWN RESPONSE:")
        
        # Extract from nested 'results' object
        results_data = result.get('results', {})
        
        print(f"\nStatus: {result.get('successful', 'Unknown')}")
        print(f"Model: {result.get('model_used', 'Unknown')}")
        print(f"Original Tokens: {results_data.get('original_prompt_tokens', 0)}")
        print(f"Compressed Tokens: {results_data.get('compressed_prompt_tokens', 0)}")
        
        if results_data.get('original_prompt_tokens', 0) > 0:
            compression_pct = (1 - results_data.get('compressed_prompt_tokens', 0) / results_data.get('original_prompt_tokens', 1)) * 100
            print(f"Compression: {compression_pct:.1f}%")
        
        print(f"\n--- COMPRESSED PROMPT (length: {len(results_data.get('compressed_prompt', ''))} chars) ---")
        print(results_data.get('compressed_prompt', ''))
        
        # Show metadata
        if 'request_metadata' in result:
            print(f"\n📊 METADATA:")
            metadata = result['request_metadata']
            print(f"  Compression Time: {metadata.get('compression_time_ms', 0)}ms")
            print(f"  Compression Rate: {metadata.get('compression_rate', 'N/A')}")
            print(f"  Original Length: {metadata.get('prompt_length', 0)} chars")
            print(f"  Compressed Length: {metadata.get('compressed_prompt_length', 0)} chars")
        
        # Return result for further analysis
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ ERROR calling ScaleDown API:")
        print(f"   {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"\n   Response Status: {e.response.status_code}")
            print(f"   Response Body: {e.response.text}")
        return None


def test_different_rates():
    """Test different compression rates to find the sweet spot."""
    
    # Sample context and prompt (similar to what your agent uses)
    context = """You are analyzing whether a Discord channel matches a user's preferences.

User Preferences:
- Interests: python, data science, machine learning, data analysis, pandas, numpy
- Role: student
- Experience Level: beginner
- Goals: learning fundamentals, building projects, getting job-ready

Channel Information:
- Name: python-beginners
- Description: A friendly space for Python beginners to ask questions and learn together
- Topics: python, programming, learning, beginners, tutorials
- Activity Level: high
- Target Audience: beginners
- Best for Roles: student, career switcher, hobbyist
- Best for Goals: learning fundamentals, building first projects, getting help

Matching Criteria (from metadata):
- Interests: 40% weight (matches topics)
- Experience Level: 30% weight (matches target_audience)
- Role: 20% weight (matches best_for_roles)
- Goals: 10% weight (matches best_for_goals)"""

    prompt = """Analyze how well this channel matches the user's preferences. Return ONLY a JSON object:
{
    "match_score": 0.0-1.0,
    "reasoning": "brief explanation of the score",
    "key_matches": ["list", "of", "matching", "aspects"],
    "potential_concerns": ["list", "of", "potential", "issues"]
}

Be objective and consider all factors. Use the weighting criteria provided."""

    # Test different compression rates
    rates_to_test = ["auto", 0.3, 0.5, 0.7]
    
    results = {}
    
    for rate in rates_to_test:
        result = test_compression(context, prompt, compression_rate=rate)
        if result:
            results[rate] = result
        print("\n" + "=" * 80 + "\n")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY OF COMPRESSION RATES")
    print("=" * 80)
    print(f"\n{'Rate':<10} {'Original':<12} {'Compressed':<12} {'Reduction':<12} {'Compressed Length'}")
    print("-" * 70)
    
    for rate, result in results.items():
        results_data = result.get('results', {})
        orig = results_data.get('original_prompt_tokens', 0)
        comp = results_data.get('compressed_prompt_tokens', 0)
        reduction = f"{(1 - comp/orig)*100:.1f}%" if orig > 0 else "N/A"
        comp_len = len(results_data.get('compressed_prompt', ''))
        print(f"{str(rate):<10} {orig:<12} {comp:<12} {reduction:<12} {comp_len} chars")
    
    print("\n💡 RECOMMENDATION:")
    print("   If compressed_prompt is empty or very short, the compression is too aggressive.")
    print("   Try a lower compression rate (0.3 = light compression, 0.7 = heavy compression)")
    print("   'auto' lets ScaleDown decide, but might be too aggressive for small inputs.")


def main():
    """Main entry point."""
    
    print("\n" + "=" * 80)
    print("SCALEDOWN COMPRESSION TESTER")
    print("=" * 80)
    print("\nThis script tests ScaleDown compression WITHOUT calling OpenAI.")
    print("It helps you debug compression issues and find the right compression rate.")
    print("\n")
    
    # Check if API key exists
    scaledown_api_key = os.getenv('SCALEDOWN_API_KEY')
    if not scaledown_api_key:
        print("❌ ERROR: SCALEDOWN_API_KEY not found in .env file")
        print("   Please add your ScaleDown API key to the .env file")
        sys.exit(1)
    
    print("✅ ScaleDown API key found")
    print("\nTesting different compression rates...\n")
    
    # Run tests
    test_different_rates()
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
