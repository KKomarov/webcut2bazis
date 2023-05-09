import csv
import dataclasses
import os
import re
import sys
from pathlib import Path
from typing import List, Optional

# webcut
# position, root . name, count, material _ thickness, length, wide, orientation,  L1, L2, W1, W2
# each edge: texture _ thickness _ edge wide
# orientation: N - oriented, A - not oriented

# demos
# texture ; root . name ; L ; W; quantity; ano?; edge1; edge2; edge3; edge4;edge descr; edge descr;full path texture
# each edge: texture
# no texture thickness

# bazis
# position;name;length;width;count;noOrientation;thicknessL1;thicknessL2;thicknessW1;thicknessW2;remark


webcut_re = re.compile(
    r'\t\t(?P<position>\d+)\t(?P<root>.*)\.(?P<name>.*)\t(?P<count>\d+)\t(?P<material>.*)_(?P<thickness>\d+)\t'
    r'(?P<length>\d+)\t(?P<width>\d+)\t(?P<orientation>[NA])\t(?P<L1>.*)\t(?P<L2>.*)\t(?P<W1>.*)\t(?P<W2>.*)\n'
)


@dataclasses.dataclass
class Edge:
    material: str
    thickness: float
    width: float

    @staticmethod
    def from_webcut(s: str):
        if not s:
            return None
        m, t, w = s.rsplit('_', 2)
        return Edge(m, float(t.replace(',', '.')), float(w.replace(',', '.')))


@dataclasses.dataclass
class Item:
    position: int
    root: str
    name: str
    material: str
    thickness: int
    length: int
    width: int
    count: int
    oriented: bool
    L1: Optional[Edge]
    L2: Optional[Edge]
    W1: Optional[Edge]
    W2: Optional[Edge]

    @staticmethod
    def from_webcut(line: str):
        m = webcut_re.match(line)
        if not m:
            raise ValueError('Bad webcut format: ' + line)
        d = m.groupdict()
        item = Item(
            position=int(d['position']),
            root=d['root'],
            name=d['name'],
            material=d['material'],
            thickness=int(d['thickness']),
            count=int(d['count']),
            length=int(d['length']),
            width=int(d['width']),
            oriented=d['orientation'] == 'N',
            L1=Edge.from_webcut(d['L1']),
            L2=Edge.from_webcut(d['L2']),
            W1=Edge.from_webcut(d['W1']),
            W2=Edge.from_webcut(d['W2']),
        )
        return item


def parse_webcut(fn) -> List[Item]:
    res = []
    with open(fn, 'r') as f:
        for line in f.readlines():
            if not line:
                continue
            item = Item.from_webcut(line)
            res.append(item)
    return res


def to_bazis_cloud(items: List[Item], fn):
    field_names = (
        'position;name;length;width;count;noOrientation;'
        'thicknessL1;thicknessL2;thicknessW1;thicknessW2;remark'.split(';')
    )
    with open(fn, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=field_names, extrasaction='ignore', delimiter=';')
        writer.writeheader()
        for i in items:
            d = dataclasses.asdict(i)
            d['name'] = f'{i.name} # {i.root}'
            d['noOrientation'] = '' if i.oriented else 'Y'
            d['thicknessL1'] = i.L1.thickness if i.L1 else ''
            d['thicknessL2'] = i.L2.thickness if i.L2 else ''
            d['thicknessW1'] = i.W1.thickness if i.W1 else ''
            d['thicknessW2'] = i.W2.thickness if i.W2 else ''
            d['remark'] = ''
            writer.writerow(d)


def group_by(items, key):
    from itertools import groupby
    items = sorted(items, key=key)
    return [(k, list(v)) for k, v in groupby(items, key=key)]


def main():
    fn = Path(sys.argv[1])
    items = parse_webcut(fn)
    print(f'Parsed {len(items)} items')
    # group by material and thickness
    for k, v in group_by(items, key=lambda x: (x.material, x.thickness)):
        i = v[0]
        out_fn = fn.parent / f'{fn.name.rsplit(".", 1)[0]} # {i.material} # {i.thickness}mm.csv'
        print(f'Saved {len(v)} items to {out_fn}')
        to_bazis_cloud(v, out_fn)


if __name__ == '__main__':
    main()
