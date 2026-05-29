import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from pyberry.cli import init, build, dev, check

def test_cli_init():
    args = MagicMock()
    args.app = "test_project"
    
    with patch("os.makedirs") as mock_makedirs, patch("builtins.open", new_callable=MagicMock) as mock_open:
        init(args)
        
        mock_makedirs.assert_called_with(os.path.join(os.getcwd(), "test_project"), exist_ok=True)
        assert mock_open.call_count == 4  # main.py, user_app.py, security.py, berrypy.log

def test_cli_build():
    args = MagicMock()
    args.app = "user_app.py"
    
    with patch("pyberry.compiler.transpile.transpile_file") as mock_transpile, \
         patch("subprocess.run") as mock_run, \
         patch("builtins.open", new_callable=MagicMock) as mock_open, \
         patch("os.makedirs"):
         
        build(args)
        # Verify setup.py build was called
        mock_run.assert_called()

def test_cli_dev():
    args = MagicMock()
    args.app = "user_app.py"
    
    with patch("subprocess.run") as mock_run, \
         patch("builtins.open", new_callable=MagicMock), \
         patch("os.makedirs"):
         
        dev(args)
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
