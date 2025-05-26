import os
import importlib.util

def test_interactive_server_directory_exists():
    assert os.path.isdir('d:/Projects/AIWhisperer/interactive_server')

def test_main_entrypoint_exists():
    main_path = 'd:/Projects/AIWhisperer/interactive_server/main.py'
    assert os.path.isfile(main_path)

def test_main_entrypoint_importable():
    main_path = 'd:/Projects/AIWhisperer/interactive_server/main.py'
    if not os.path.isfile(main_path):
        import pytest
        pytest.skip('main.py does not exist yet')
    spec = importlib.util.spec_from_file_location('interactive_server.main', main_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        assert False, f"main.py is not importable: {e}"
