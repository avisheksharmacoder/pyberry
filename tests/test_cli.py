import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from pyberry.cli import create_app, build, run, check

def test_cli_create_app():
    args = MagicMock()
    args.app = "test_project"
    
    with patch("os.makedirs") as mock_makedirs, patch("builtins.open", new_callable=MagicMock) as mock_open:
        create_app(args)
        
        mock_makedirs.assert_any_call(os.path.join(os.getcwd(), "test_project"), exist_ok=True)
        mock_makedirs.assert_any_call(os.path.join(os.getcwd(), "test_project", "db"), exist_ok=True)
        assert mock_open.call_count == 5  # main.py, security.py, db/initial_schema.sql, docs.md, berrypy.log

def test_cli_build():
    args = MagicMock()
    args.app = "user_app.py"
    args.audit = True
    
    with patch("pyberry.compiler.transpile.transpile_file") as mock_transpile, \
         patch("subprocess.run") as mock_run, \
         patch("builtins.open", new_callable=MagicMock) as mock_open, \
         patch("os.makedirs"):
         
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        build(args)
        # Verify setup.py build was called
        mock_run.assert_called()

def test_cli_run():
    args = MagicMock()
    args.app = "user_app.py"
    args.dev = True
    
    with patch("subprocess.run") as mock_run, \
         patch("builtins.open", new_callable=MagicMock), \
         patch("os.makedirs"):
         
        run(args)
        mock_run.assert_called()
        cmd = mock_run.call_args[0][0]
        assert "granian" in cmd
        assert "dev_wrapper:app" in cmd

def test_cli_check(capsys):
    args = MagicMock()
    
    with patch("shutil.which") as mock_which, \
         patch("sysconfig.get_config_var", return_value=True):
         
        mock_which.return_value = "/bin/mock_path"
        check(args)
        
    captured = capsys.readouterr()
    assert "All systems go!" in captured.out or "Checking system requirements" in captured.out
