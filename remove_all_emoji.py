"""Complete emoji removal from all templates."""
import re
from pathlib import Path

templates_dir = Path("app/templates")

# Comprehensive emoji patterns
EMOJI_PATTERNS = [
    # All emoji characters
    r'[\U0001F300-\U0001F9FF]',  # Emoticons
    r'[\U0001F600-\U0001F64F]',  # Emoticons
    r'[\U0001F680-\U0001F6FF]',  # Transport & Map
    r'[\U0001F1E0-\U0001F1FF]',  # Flags
    r'[\U00002600-\U000027BF]',  # Misc symbols
    r'[\U0001F900-\U0001F9FF]',  # Supplemental Symbols
    r'[\U0001FA00-\U0001FA6F]',  # Chess Symbols
    r'[\U00002700-\U000027BF]',  # Dingbats
]

# Specific emoji to remove (including arrows and symbols)
SPECIFIC_EMOJI = {
    '📊': '',
    '📤': '',
    '📋': '',
    '🏠': '',
    '✏️': '',
    '🏭': '',
    '✅': '',
    '❌': '',
    '📁': '',
    '💼': '',
    '📈': '',
    '💰': '',
    '👥': '',
    '🌟': '',
    '🔍': '',
    '📍': '',
    '🗺️': '',
    '✕': '×',  # Replace with regular multiplication sign
    '▼': '▾',  # Replace with down arrow
    '▲': '▴',  # Replace with up arrow
    '📭': '',
    '🗑️': '',
    '🏢': '',
    '📦': '',
    '📞': '',
    '💾': '',
    '➕': '+',  # Replace with plus
    '👤': '',
    '📝': '',
    '💵': '',
    '🏆': '',
    '📅': '',
    '🌍': '',
}

def remove_all_emoji(content):
    """Remove all emoji from content."""
    # First, remove specific emoji
    for emoji, replacement in SPECIFIC_EMOJI.items():
        content = content.replace(emoji, replacement)
    
    # Then remove any remaining emoji using patterns
    for pattern in EMOJI_PATTERNS:
        content = re.sub(pattern, '', content)
    
    # Clean up double spaces
    content = re.sub(r'  +', ' ', content)
    
    # Clean up space before closing tags
    content = re.sub(r' +</', '</', content)
    
    return content

def process_template(filepath):
    """Process a single template file."""
    print(f"Processing {filepath.name}...")
    
    try:
        content = filepath.read_text(encoding='utf-8')
        original = content
        
        # Remove all emoji
        content = remove_all_emoji(content)
        
        if content != original:
            filepath.write_text(content, encoding='utf-8')
            print(f"  ✓ Removed emoji from {filepath.name}")
            
            # Count changes
            changes = sum(1 for a, b in zip(original, content) if a != b)
            print(f"    Changed {changes} characters")
        else:
            print(f"  - No emoji found in {filepath.name}")
            
    except Exception as e:
        print(f"  ✗ Error: {e}")

def main():
    """Process all templates."""
    print("Removing ALL emoji from templates...\n")
    
    html_files = list(templates_dir.glob("*.html"))
    print(f"Found {len(html_files)} template files\n")
    
    for html_file in html_files:
        process_template(html_file)
    
    print("\n✓ Complete! All emoji removed.")

if __name__ == "__main__":
    main()
