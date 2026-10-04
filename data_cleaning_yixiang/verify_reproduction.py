import json
from pathlib import Path
from clean_data import digest

root=Path(__file__).resolve().parent/'outputs'
first=json.loads((root/'evidence/output_hashes.json').read_text())
second=json.loads((root/'repeat/evidence/output_hashes.json').read_text())
assert first.keys()==second.keys(),'Output file sets differ'
for path,expected in first.items():
    assert digest(root/path)==expected,(path,'first output changed')
    assert digest(root/'repeat'/path)==second[path],(path,'repeat output changed')
    assert expected==second[path],(path,'outputs differ')
print(f'Identical file hashes: {len(first)}')
