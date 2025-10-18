"""Remove all border-radius and gradients from templates."""
import re
from pathlib import Path

templates_dir = Path("app/templates")

def clean_styles(content):
    """Remove border-radius and linear-gradient from styles."""
    # Remove border-radius lines
    content = re.sub(r'\s*border-radius:\s*[^;]+;?\s*\n?', '', content)
    
    # Replace linear-gradient with solid colors
    content = re.sub(
        r'background:\s*linear-gradient\([^)]+\);?',
        'background: var(--accent-dark);',
        content
    )
    
    # Remove transform: translateY
    content = re.sub(r'\s*transform:\s*translateY[^;]+;?\s*\n?', '', content)
    
    # Remove box-shadow (keep minimal or remove)
    content = re.sub(
        r'box-shadow:\s*0\s+\d+px\s+\d+px[^;]+;',
        'box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);',
        content
    )
    
    return content

def process_template(filepath):
    """Process a single template file."""
    print(f"Processing {filepath.name}...")
    
    try:
        content = filepath.read_text(encoding='utf-8')
        original = content
        
        # Clean styles
        content = clean_styles(content)
        
        if content != original:
            filepath.write_text(content, encoding='utf-8')
            print(f"  ✓ Cleaned {filepath.name}")
        else:
            print(f"  - No changes for {filepath.name}")
            
    except Exception as e:
        print(f"  ✗ Error: {e}")

def main():
    """Process all templates."""
    print("Cleaning all templates...\n")
    
    for html_file in templates_dir.glob("*.html"):
        if html_file.name != "index.html":  # Skip index, it's already clean
            process_template(html_file)
    
    print("\n✓ Done! All border-radius and gradients removed.")

if __name__ == "__main__":
    main()
