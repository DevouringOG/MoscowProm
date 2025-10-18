"""Script to completely rebuild templates with new design system."""
from pathlib import Path

# Base template with new design
BASE_STYLES = """
    <style>
        .page-wrapper {
            min-height: 100vh;
        }
        
        .page-header {
            background: var(--card-bg);
            border-bottom: 2px solid var(--border-color);
            padding: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }

        .page-title {
            font-size: 24px;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: -0.02em;
        }

        .header-actions {
            display: flex;
            gap: 12px;
        }

        .content-section {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            padding: 24px;
            margin-bottom: 24px;
        }

        .search-bar {
            display: flex;
            gap: 12px;
            margin-bottom: 24px;
        }

        .search-input {
            flex: 1;
            padding: 10px 16px;
            border: 1px solid var(--border-dark);
            font-size: 14px;
            font-family: 'Inter', sans-serif;
        }

        .search-input:focus {
            outline: none;
            border-color: var(--text-primary);
        }

        .org-table {
            width: 100%;
            border-collapse: collapse;
        }

        .org-table thead {
            background: var(--accent-light);
            border-bottom: 2px solid var(--border-color);
        }

        .org-table th {
            padding: 12px 16px;
            text-align: left;
            font-size: 11px;
            font-weight: 700;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .org-table td {
            padding: 16px;
            border-bottom: 1px solid var(--border-color);
            font-size: 14px;
        }

        .org-table tbody tr {
            transition: background 0.15s ease;
        }

        .org-table tbody tr:hover {
            background: var(--accent-light);
        }

        .org-link {
            color: var(--text-primary);
            font-weight: 600;
            text-decoration: none;
        }

        .org-link:hover {
            text-decoration: underline;
        }

        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .filters-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }

        .filter-item {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .filter-label {
            font-size: 11px;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .filter-select {
            padding: 8px 12px;
            border: 1px solid var(--border-dark);
            font-family: 'Inter', sans-serif;
            font-size: 14px;
        }

        .filter-select:focus {
            outline: none;
            border-color: var(--text-primary);
        }

        .stats-summary {
            display: flex;
            gap: 16px;
            padding: 16px;
            background: var(--accent-light);
            border: 1px solid var(--border-color);
            margin-bottom: 24px;
        }

        .stat-item {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .stat-label {
            font-size: 11px;
            color: var(--text-secondary);
            font-weight: 600;
            text-transform: uppercase;
        }

        .stat-value {
            font-size: 18px;
            font-weight: 700;
            color: var(--text-primary);
        }

        .upload-zone {
            border: 2px solid var(--border-dark);
            padding: 60px 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.15s ease;
            background: var(--card-bg);
        }

        .upload-zone:hover {
            border-color: var(--text-primary);
            background: var(--accent-light);
        }

        .upload-zone.dragover {
            border-color: var(--text-primary);
            background: var(--accent-light);
        }

        .upload-icon {
            font-size: 48px;
            margin-bottom: 16px;
            color: var(--text-tertiary);
        }

        .upload-text {
            font-size: 16px;
            color: var(--text-primary);
            font-weight: 600;
            margin-bottom: 8px;
        }

        .upload-hint {
            font-size: 13px;
            color: var(--text-secondary);
        }

        .progress-bar {
            width: 100%;
            height: 4px;
            background: var(--border-color);
            margin-top: 16px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: var(--accent-dark);
            width: 0%;
            transition: width 0.3s ease;
        }

        .result-box {
            padding: 16px;
            margin-top: 16px;
            border: 2px solid var(--border-color);
        }

        .result-box.success {
            border-color: var(--success);
            background: #D1FAE5;
            color: #065F46;
        }

        .result-box.error {
            border-color: var(--danger);
            background: #FEE2E2;
            color: #991B1B;
        }
    </style>
"""

print("Design styles ready. Use this in templates.")
print("\nKey changes:")
print("- Removed all border-radius")
print("- Removed all gradients")
print("- Using Inter font variables")
print("- Sharp rectangular design")
print("- Monochrome palette")
