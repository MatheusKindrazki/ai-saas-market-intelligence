from radar.classify_llm import GLMClient
from radar.db import Database
from radar.mine import mine, mine_signal
from radar.models import RawSignal

def test_glm_skips_thinking_and_mine_rejects_bad_quotes(tmp_path):
    db=Database(tmp_path/"radar.db")
    signal=RawSignal("s","reddit","reddit","1","https://example.test","manual spreadsheet","This manual spreadsheet takes hours.",None,None,"2026-01-01","q","en","hash")
    db.upsert_signal(signal)
    good=GLMClient(api_key="fake",sleep=lambda _:None,transport=lambda *_: {"content":[{"type":"thinking","thinking":"ignore"},{"type":"text","text":"{\"is_complaint\":true,\"pain\":\"manual work\",\"observed\":[\"manual spreadsheet takes hours\"],\"inference\":[]}"}]})
    assert mine_signal(db,signal,good) is not None
    bad=GLMClient(api_key="fake",sleep=lambda _:None,transport=lambda *_: {"content":[{"type":"text","text":"{\"is_complaint\":true,\"observed\":[\"invented quote\"],\"inference\":[]}"}]})
    assert mine_signal(db,signal,bad) is None
    assert db.connection.execute("SELECT COUNT(*) FROM signal_errors").fetchone()[0] == 1


def test_mine_skips_classified_and_normalized_duplicate_bodies(tmp_path):
    db=Database(tmp_path/"radar.db")
    first=RawSignal("first","reddit","reddit","1","https://example.test/1","manual spreadsheet","Manual spreadsheet takes hours!",None,None,"2026-01-01","q","en","one")
    duplicate=RawSignal("duplicate","reddit","reddit","2","https://example.test/2","manual spreadsheet","manual   spreadsheet takes hours",None,None,"2026-01-01","q","en","two")
    db.upsert_signal(first); db.upsert_signal(duplicate)
    client=GLMClient(api_key="fake",sleep=lambda _:None,transport=lambda *_: {"content":[{"type":"text","text":"{\"is_complaint\":true,\"pain\":\"manual work\",\"observed\":[\"Manual spreadsheet takes hours\"],\"inference\":[]}"}]})
    assert len(mine(db,client)) == 1
    assert len(mine(db,client)) == 0
