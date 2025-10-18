"""Replace hardcoded colors with CSS variables."""
import re
from pathlib import Path

templates_dir = Path("app/templates")

# Color mappings
COLOR_MAP = {
    '#667eea': 'var(--accent-dark)',
    '#764ba2': 'var(--accent-dark)',
    '#f8f9fa': 'var(--accent-light)',
    '#e9ecef': 'var(--border-color)',
    '#dee2e6': 'var(--border-color)',
    '#495057': 'var(--text-secondary)',
    '#6c757d': 'var(--text-secondary)',
    '#333': 'var(--text-primary)',
    '#666': 'var(--text-secondary)',
    'white': 'var(--card-bg)',
    '#fff': 'var(--card-bg)',
    '#000': 'var(--text-primary)',
}

def replace_colors(content):
    """Replace hardcoded colors with CSS variables."""
    for old_color, new_var in COLOR_MAP.items():
        # Replace in various contexts
        content = re.sub(
            f'(color|background|border-color|fill):\\s*{re.escape(old_color)}',
            f'\\1: {new_var}',
            content,
            flags=re.IGNORECASE
        )
    return content

def process_template(filepath):
    """Process a single template file."""
    print(f"Processing {filepath.name}...")
    
    try:
        content = filepath.read_text(encoding='utf-8')
        original = content
        
        # Replace colors
        content = replace_colors(content)
        
        if content != original:
            filepath.write_text(content, encoding='utf-8')
            print(f"  ✓ Updated colors in {filepath.name}")
        else:
            print(f"  - No color changes for {filepath.name}")
            
    except Exception as e:
        print(f"  ✗ Error: {e}")

def main():
    """Process all templates."""
    print("Replacing colors with CSS variables...\n")
    
    for html_file in templates_dir.glob("*.html"):
        process_template(html_file)
    
    print("\n✓ Done!")

if __name__ == "__main__":
    main()
