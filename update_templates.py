"""Script to update all HTML templates with new design."""
import re
from pathlib import Path

# Template directory
templates_dir = Path("app/templates")

# Emoji replacements (remove all emoji)
emoji_replacements = {
    "📊 ": "",
    "📤 ": "",
    "📋 ": "",
    "🏠 ": "",
    "✏️ ": "",
    "🏭 ": "",
    "✅ ": "",
    "❌ ": "",
    "📁 ": "",
    "💼 ": "",
    "📈 ": "",
    "💰 ": "",
    "👥 ": "",
    "🌟 ": "",
}

# Style replacements (remove inline styles with gradients and border-radius)
style_patterns = [
    (r'border-radius:\s*\d+px;?', ''),
    (r'background:\s*linear-gradient\([^)]+\);?', 'background: var(--accent-dark);'),
]

def update_template(filepath: Path):
    """Update a single template file."""
    print(f"Updating {filepath.name}...")
    
    content = filepath.read_text(encoding='utf-8')
    original_content = content
    
    # Remove emoji
    for emoji, replacement in emoji_replacements.items():
        content = content.replace(emoji, replacement)
    
    # Add CSS link if not present and has <head> tag
    if '<head>' in content and '/static/css/main.css' not in content:
        content = content.replace(
            '</title>',
            '</title>\n    <link rel="stylesheet" href="/static/css/main.css">'
        )
    
    # Only save if content changed
    if content != original_content:
        filepath.write_text(content, encoding='utf-8')
        print(f"  ✓ Updated {filepath.name}")
    else:
        print(f"  - No changes needed for {filepath.name}")

def main():
    """Update all templates."""
    print("Updating all templates...\n")
    
    for html_file in templates_dir.glob("*.html"):
        try:
            update_template(html_file)
        except Exception as e:
            print(f"  ✗ Error updating {html_file.name}: {e}")
    
    print("\n✓ Done!")

if __name__ == "__main__":
    main()
