import easyocr

def check_language(lang_code):
    """Test if a language code is supported."""
    try:
        # Quick test with minimal download
        reader = easyocr.Reader([lang_code], gpu=False, download_enabled=False)
        return True
    except:
        return False

# Test Amharic variations
for code in ['am', 'amh', 'amharic']:
    print(f"{code}: {'Supported' if check_language(code) else ' Not supported'}")