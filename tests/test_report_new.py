import json
from radar.report import emit
def test_report_is_schema_validated(tmp_path):
    path=emit(tmp_path,[{'source':'reddit'}],[])
    assert json.loads(path.read_text())['schema_version']=='1'
