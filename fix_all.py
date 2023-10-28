from pathlib import Path
from typing import List

import yaml

from core import entrance


def find_newest(files: List[Path]) -> Path:
    newest_file, newest_ctime = None, 0
    for file in files:
        if (ctime:= file.lstat().st_ctime )> newest_ctime:
            newest_file, newest_ctime = file, ctime
    return file


if __name__ == '__main__':
    with open('secret.yaml', 'r') as f:
        secret = yaml.load(f, yaml.Loader)

    global_prefix = secret['global_prefix']
    for d in secret['tasks']:
        nickname, account_id = d['nickname'], d['account_id']

        directory = f'{global_prefix}/{nickname}'
        qfx_files = list(Path(directory).glob('*.QFX'))
        if len(qfx_files) == 0:
            print(f'Error: no QFX files found in directory {directory}!')
            continue

        entrance(str(find_newest(qfx_files)), account_id)
