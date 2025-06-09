import subprocess

import pytest

import extractor_api


@pytest.mark.asyncio
async def test_run_cmd_raises_with_output():
    cmd = [
        "python",
        "-c",
        "import sys; print('err', file=sys.stderr); sys.exit(1)",
    ]
    with pytest.raises(subprocess.CalledProcessError) as exc:
        await extractor_api.run_cmd(cmd)

    assert exc.value.returncode == 1
    assert exc.value.cmd == cmd
    assert exc.value.output == b""
    assert exc.value.stderr == b"err\n"
