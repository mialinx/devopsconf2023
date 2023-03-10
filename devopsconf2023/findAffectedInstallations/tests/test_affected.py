import argparse

import pytest

import contextlib
import os
import tempfile
import textwrap
import re
from typing import List, Tuple


from ..validation.check import get_stands_for_changed_templates

_SINGLE_FILE_MASTER = textwrap.dedent("""\
    key1: value1
    key2:
        subkey1: subvalue1
        subkey2: subvalue2
""")


_MULTI_FILE_PARENT_MASTER = textwrap.dedent("""\
include:
    - file2.yaml

key1: kkk1
key2: kkk2
""")


_MULTI_FILE_CHILD_MASTER = textwrap.dedent("""\
key1: orig_kkk1
key3: kkk3
""")


_SINGLE_FILE_BRANCH = textwrap.dedent("""\
    key1: value1
    key2:
        subkey2: changed_subvalue
    key3: value3
""")

_MULTI_FILE_PARENT_BRANCH = textwrap.dedent("""\
include:
    - file2.yaml

key2: kkk2
key4: kkk4
""")

_MULTI_FILE_CHILD_BRANCH = textwrap.dedent("""\
key3: kkk3
""")

_STAND_FILE_1 = textwrap.dedent("""\
    include:
    - shared/shared_file.yaml
""")

_STAND_FILE_2 = textwrap.dedent("""\
    include:
    - shared/shared_file.yaml
""")

_SHARED_FILE1 = textwrap.dedent("""\
    key: some_value
""")

_SHARED_FILE_WITH_CYCLE = textwrap.dedent("""\
    include:
    - ../stand1.yaml
""")

_WORKFLOW_1 = textwrap.dedent("""\
    include: 
    - ../stand1.yaml
    - ../workflows/common/workflows_shared.yaml
""")
_WORKFLOW_WITH_COMMON_FILE = textwrap.dedent("""\
    include: 
    - ../stand2.yaml
    - ../workflows/common/workflows_shared.yaml
""")
_WORKFLOW_COMMON_FILE = textwrap.dedent("""\
    key: some_value
""")

_WORKFLOW_TO_STAND_INTERNALS = textwrap.dedent("""\
    include: 
    - ../shared/shared_file.yaml
""")

@contextlib.contextmanager
def _construct_templates_dir(data: List[Tuple[str, str]]):
    """Create temporary directory and put templates"""
    with tempfile.TemporaryDirectory(prefix="yc-test-bb-templates") as temp_dir:
        for template_name, template_content in data:
            dir_name = os.path.dirname(template_name)
            file_full_name = os.path.join(temp_dir, template_name)
            if dir_name:
                full_path = os.path.join(temp_dir, dir_name)
                os.makedirs(full_path, exist_ok=True)
            with open(file_full_name, "w") as f:
                f.write(template_content)
        yield temp_dir

@pytest.mark.parametrize("template_data,diffs_paths,expected_changed_stands", [
    (
        [("stand1.yaml", _STAND_FILE_1), ("stand2.yaml", _STAND_FILE_2), ("shared/shared_file.yaml", _SHARED_FILE1)],
        {"stand2.yaml"},
        {"stand2.yaml"},
    ),
    (
        [("stand1.yaml", _STAND_FILE_1), ("stand2.yaml", _STAND_FILE_2), ("shared/shared_file.yaml", _SHARED_FILE1)],
        {"stand1.yaml", "stand2.yaml"},
        {"stand1.yaml", "stand2.yaml"},
    ),
    (
        [("stand1.yaml", _STAND_FILE_1), ("stand2.yaml", _STAND_FILE_2), ("shared/shared_file.yaml", _SHARED_FILE1)],
        {"shared/shared_file.yaml"},
        {"stand1.yaml", "stand2.yaml"},
    ),
])
def test_get_templates_paths_for_check(template_data, diffs_paths, expected_changed_stands):
    with _construct_templates_dir(template_data) as templates_dir:
        diff_full_paths = {os.path.join(templates_dir, p) for p in diffs_paths}
        expected_full_paths = {os.path.join(templates_dir, p) for p in expected_changed_stands}
        assert expected_full_paths == get_stands_for_changed_templates(diff_full_paths, templates_dir)