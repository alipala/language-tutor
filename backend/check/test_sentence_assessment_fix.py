#!/usr/bin/env python3
"""
Test script to verify the sentence assessment fix
"""
import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append('backend')

from sentence_assessment import analyze_sentence

async def test_sentence_assessment():
    """Test that analyze_sentence returns the required recognized_text field"""
    
    print("🧪 Testing sentence assessment fix...")
    
    # Test data
    test_text = "I really like the Turkish cuisine, which is really rich about the different kinds of foods."
    language = "english"
    level = "B1"
    exercise_type = "free"
    
    try:
        # Call the analyze_sentence function
        result = await analyze_sentence(
            text=test_text,
            language=language,
            level=level,
            exercise_type=exercise_type
        )
        
        print(f"✅ Analysis completed successfully")
        print(f"📝 Input text: {test_text}")
        
        # Check if recognized_text field is present
        if "recognized_text" in result:
            print(f"✅ recognized_text field is present: '{result['recognized_text']}'")
            
            # Verify it matches the input
            if result["recognized_text"] == test_text:
                print(f"✅ recognized_text matches input text")
            else:
                print(f"❌ recognized_text doesn't match input text")
                print(f"   Expected: {test_text}")
                print(f"   Got: {result['recognized_text']}")
        else:
            print(f"❌ recognized_text field is missing from response")
            return False
        
        # Check other required fields
        required_fields = [
            "grammatical_score", "vocabulary_score", "complexity_score", 
            "appropriateness_score", "overall_score", "grammar_issues", 
            "improvement_suggestions", "corrected_text", "level_appropriate_alternatives"
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in result:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
        else:
            print(f"✅ All required fields are present")
        
        # Print some sample results
        print(f"\n📊 Assessment Results:")
        print(f"   Overall Score: {result.get('overall_score', 'N/A')}")
        print(f"   Grammar Score: {result.get('grammatical_score', 'N/A')}")
        print(f"   Vocabulary Score: {result.get('vocabulary_score', 'N/A')}")
        print(f"   Corrected Text: {result.get('corrected_text', 'N/A')}")
        
        print(f"\n🎉 TEST PASSED: Sentence assessment fix is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    # Set up environment
    os.environ.setdefault("OPENAI_API_KEY", "test-key")  # Placeholder for test
    
    # Run the test
    success = asyncio.run(test_sentence_assessment())
    
    if success:
        print(f"\n✅ CONCLUSION: The fix is working correctly!")
        print(f"   - The analyze_sentence function now includes the recognized_text field")
        print(f"   - This should resolve the 422 validation error in production")
        print(f"   - The 'Analyze Sentence' button should work properly now")
    else:
        print(f"\n❌ CONCLUSION: The test failed - there may be additional issues")
    
    sys.exit(0 if success else 1)
