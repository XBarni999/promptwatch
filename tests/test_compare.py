import json
import tempfile
from pathlib import Path
from promptwatch.cli import main

def test_compare_cli_command():
    # Write two temporary answer files
    with tempfile.TemporaryDirectory() as tmpdir:
        old_path = Path(tmpdir) / "old.json"
        new_path = Path(tmpdir) / "new.json"
        html_path = Path(tmpdir) / "diff.html"
        
        old_data = {
            "answers": [
                {"case_id": "c1", "output": "Hello World"},
                {"case_id": "c2", "output": "Old output"},
                {"case_id": "c3", "output": "To be deleted"}
            ]
        }
        new_data = {
            "answers": [
                {"case_id": "c1", "output": "Hello World"}, # Identical
                {"case_id": "c2", "output": "New output"},   # Changed
                {"case_id": "c4", "output": "Added output"}   # Added
            ]
        }
        
        old_path.write_text(json.dumps(old_data), encoding="utf-8")
        new_path.write_text(json.dumps(new_data), encoding="utf-8")
        
        # Run comparison cli command
        exit_code = main(["compare", str(old_path), str(new_path), "--html", str(html_path)])
        
        # Exit code should be 1 because there are changes
        assert exit_code == 1
        
        # Verify HTML report was generated
        assert html_path.exists()
        html_content = html_path.read_text(encoding="utf-8")
        assert "Run Comparison" in html_content
        assert "Hello World" in html_content
        assert "New output" in html_content
        assert "Old output" in html_content
