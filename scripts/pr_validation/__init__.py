"""
PR Validation Module

Modular components for PR size validation:
- loc_counter: Line counting functionality
- file_categorizer: File categorization logic
- pr_validator: Validation against limits
- pr_reporter: Report generation
"""

from .file_categorizer import FileCategory, categorize_file, categorize_files, compile_patterns
from .loc_counter import count_file_changes, get_changed_files, get_effective_loc
from .pr_reporter import (
    format_header,
    generate_failure_report,
    generate_success_report,
    print_analysis,
)
from .pr_validator import check_category_limit, get_category_status, validate_pr

__all__ = [
    # From loc_counter
    "get_changed_files",
    "count_file_changes",
    "get_effective_loc",
    # From file_categorizer
    "FileCategory",
    "categorize_file",
    "categorize_files",
    "compile_patterns",
    # From pr_validator
    "validate_pr",
    "check_category_limit",
    "get_category_status",
    # From pr_reporter
    "print_analysis",
    "generate_success_report",
    "generate_failure_report",
    "format_header",
]
