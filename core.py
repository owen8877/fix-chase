import base64
from hashlib import md5
from pathlib import Path
from typing import List, Union


def read_file(path: str) -> List[str]:
    with open(path, 'r') as f:
        return f.readlines()


def write_file(path: str, lines: List[str]):
    with open(path, 'w', newline='\n') as f:
        f.writelines(l + '\n' for l in lines)
        f.write('')


class Open:
    def __init__(self, label):
        self.label = label

    def __str__(self):
        return f'Open({self.label})'


class Oneliner:
    def __init__(self, label, content):
        self.label = label
        self.content = content

    def __str__(self):
        return f'Oneliner({self.label}, {self.content})'


class Close:
    def __init__(self, label):
        self.label = label

    def __str__(self):
        return f'Close({self.label})'

    def __eq__(self, other):
        return self.label == other.label


Label = Union[Open, Oneliner, Close]


def parse_label(line: str) -> Label:
    """
    :param line:
    :return: (label, content)
    """
    if line[1] == '/':
        return Close(line[2:-1])

    r = line.find('>')
    label = line[1:r]
    if r == len(line) - 1:
        return Open(label)
    else:
        return Oneliner(label, line[r + 1:])


class AST:
    def __init__(self, lines: List[Label]):
        self.__dict__['label'] = lines[0]
        if not isinstance(self.label, Open):
            raise Exception('The oneliner and close tag should be handled earlier!')

        remaining_lines = lines[1:-1]
        self.__dict__['children'] = []

        while len(remaining_lines) > 0:
            if isinstance(anchor := remaining_lines[0], Oneliner):
                self.children.append(anchor)
                remaining_lines = remaining_lines[1:]
            else:
                for i in range(1, len(remaining_lines)):
                    if remaining_lines[i] == Close(anchor.label):
                        self.children.append(AST(remaining_lines[:i + 1]))
                        remaining_lines = remaining_lines[i + 1:]
                        break
                else:
                    raise Exception('cannot go here')

    def __getattr__(self, item):
        for child in self.__dict__['children']:
            if isinstance(child, Oneliner):
                if child.label == item:
                    return child
            else:
                if child.__dict__['label'].label == item:
                    return child
        return None

    def __setattr__(self, key, value):
        for child in self.__dict__['children']:
            if isinstance(child, Oneliner):
                if child.label == key:
                    child.content = value
                    return
            else:
                if child.__dict__['label'].label == key:
                    raise Exception('Cannot set value on AST!')
        raise Exception(f'Key {key} not found!')

    def __str__(self):
        children = ', '.join([str(_) for _ in self.children])
        return f'{self.label.label}({children})'

    def dump(self) -> List[str]:
        chunks = [f'<{self.label.label}>']
        for child in self.children:
            if isinstance(child, Oneliner):
                chunks.append(f'<{child.label}>{child.content}')
            else:
                chunks.extend(child.dump())
        chunks.append(f'</{self.label.label}>')
        return chunks


class QFXHolder:
    def __init__(self, lines: List[str]):
        lines = [l.strip() for l in lines]
        self.headers = [l for l in lines if not l.startswith('<')]
        self.tree = AST([parse_label(l) for l in lines if l.startswith('<')])

    def dump(self):
        return self.headers + self.tree.dump()

    def update(self, account_id: str):
        """
        Modify the tree so that it has updated account and FITID information.

        :param account_id:
        :return:
        """
        common = self.tree.CREDITCARDMSGSRSV1.CCSTMTTRNRS.CCSTMTRS
        common.CCACCTFROM.children.append(Oneliner('ACCTID', account_id))

        for item in common.BANKTRANLIST.children:
            if isinstance(item, Oneliner) or item.label.label != 'STMTTRN':
                continue

            t, dp, a, n = item.TRNTYPE, item.DTPOSTED, item.TRNAMT, item.NAME
            s: str = t.content + dp.content + a.content + n.content
            b = bytes(s, 'utf-8')
            e = base64.b64encode(b)
            item.FITID = dp.content[:8] + md5(e).hexdigest()


def entrance(path: str, account_id: str):
    """
    Primary entrance of the working function.

    :param path:
    :param account_id:
    :return:
    """
    path_obj = Path(path)
    directory, base_name, ext_name = path_obj.parent, path_obj.stem, path_obj.suffix

    holder = QFXHolder(read_file(path))
    holder.update(account_id)

    output_path = directory.joinpath(f'{base_name}.pat{ext_name}')
    write_file(output_path, holder.dump())
