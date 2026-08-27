"""Container smoke test: requires a docker daemon and an image built with `just docker-build`."""

import os
import shutil
import subprocess

import pytest

pytestmark = pytest.mark.container
IMAGE = os.environ.get("ANNOTOOLS_IMAGE", "annotools:dev")


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker not available")
def test_image_prints_help():
    result = subprocess.run(["docker", "run", "--rm", IMAGE, "--help"], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert "--http" in result.stdout
