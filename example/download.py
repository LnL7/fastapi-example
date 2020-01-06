import asyncio
import json
import logging

logger = logging.getLogger(__name__)


class Fetcher:
    @classmethod
    async def download(cls, name: str, version: str):
        logger.info('starting download for %s...', name)

        output = await run(f'nix-instantiate --eval --json "<nixpkgs>" -A {name}.version')
        if json.loads(output) == version:
            output = await run(f'nix-build "<nixpkgs>" -A {name}')
            logger.info('downloaded %s...', output.decode())
        else:
            raise Exception(f'version {version} for {name} is not available')


async def run(command):
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()
    if stderr:
        print(f'[stderr]\n{stderr.decode()}')
    if proc.returncode == 0:
        return stdout
    else:
        raise Exception('command %s failed with %s', command, proc.returncode)
