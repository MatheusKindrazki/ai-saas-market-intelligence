import pytest

from radar.classify_llm import ClassificationError, GLMClient
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


def test_glm_parses_fenced_json_response_and_mines_verbatim_quote(tmp_path):
    db=Database(tmp_path/"radar.db")
    signal=RawSignal("fenced","reddit","reddit","1","https://example.test","manual spreadsheet","This manual spreadsheet takes hours.",None,None,"2026-01-01","q","en","hash")
    db.upsert_signal(signal)
    client=GLMClient(api_key="fake",sleep=lambda _:None,transport=lambda *_: {"content":[{"type":"text","text":"```json\n{\"is_complaint\":true,\"pain\":\"manual work\",\"observed\":[\"manual spreadsheet takes hours\"],\"inference\":[]}\n```"}]})
    assert mine_signal(db,signal,client) is not None


def test_mine_unescapes_html_entities_before_prompt_and_verbatim_gate(tmp_path):
    db=Database(tmp_path/"radar.db")
    signal=RawSignal("entities","github","github","1","https://example.test","manual spreadsheet","I&#x27;m using a manual spreadsheet &amp; it takes hours &gt; every week.",None,None,"2026-01-01","q","en","hash")
    db.upsert_signal(signal)
    client=GLMClient(api_key="fake",sleep=lambda _:None,transport=lambda *_: {"content":[{"type":"text","text":"{\"is_complaint\":true,\"pain\":\"manual work\",\"observed\":[\"I'm using a manual spreadsheet & it takes hours > every week.\"],\"inference\":[]}"}]})
    assert mine_signal(db,signal,client) is not None
    assert db.connection.execute("SELECT body FROM signals WHERE id='entities'").fetchone()[0] == signal.body


def test_glm_payload_allows_text_after_thinking_budget():
    payloads=[]
    client=GLMClient(api_key="fake",sleep=lambda _:None,transport=lambda _,__,payload: (payloads.append(payload) or {"content":[{"type":"text","text":"{}"}]}))
    assert client.classify("BODY:\\nexample") == {}
    assert payloads[0]["max_tokens"] >= 4000


def test_glm_retries_when_thinking_leaves_the_text_block_empty():
    responses=[{"content":[{"type":"thinking","thinking":"long deliberation"}]},{"content":[{"type":"text","text":"   "}]},{"content":[{"type":"text","text":"{\"ok\":true}"}]}]
    calls=[]
    client=GLMClient(api_key="fake",sleep=lambda _:None,transport=lambda *_: (calls.append(1) or responses[len(calls)-1]))
    assert client.classify("BODY") == {"ok":True}
    assert len(calls) == 3


def test_glm_reports_empty_text_and_honours_max_tokens_argument():
    payloads=[]
    client=GLMClient(api_key="fake",sleep=lambda _:None,max_tokens=12000,transport=lambda _,__,payload: (payloads.append(payload) or {"content":[{"type":"thinking","thinking":"no answer"}]}))
    with pytest.raises(ClassificationError,match="empty text"): client.classify("BODY")
    assert len(payloads) == 3 and payloads[0]["max_tokens"] == 12000


def test_glm_per_call_max_tokens_overrides_only_that_request():
    """The thesis call needs a bigger budget than the client default; the default must survive it."""
    payloads=[]
    client=GLMClient(api_key="fake",sleep=lambda _:None,transport=lambda _,__,payload: (payloads.append(payload) or {"content":[{"type":"text","text":"{}"}]}))
    assert client.classify("BODY",max_tokens=16000) == {}
    assert client.classify("BODY") == {}
    assert [payload["max_tokens"] for payload in payloads] == [16000,4000]


def test_glm_raises_on_max_tokens_stop_reason_instead_of_truncated_json():
    """A JSON object cut mid-string parses as 'Unterminated string': fail loudly, not cryptically."""
    client=GLMClient(api_key="fake",sleep=lambda _:None,transport=lambda *_: {"stop_reason":"max_tokens","content":[{"type":"text","text":"{\"recommendation\":\"half a sen"}]})
    with pytest.raises(ClassificationError,match="truncated at max_tokens"): client.classify("BODY")


def test_glm_truncation_counts_toward_the_three_attempts():
    calls=[]
    responses=[{"stop_reason":"max_tokens","content":[{"type":"text","text":"{\"a\":\"cut"}]},{"stop_reason":"max_tokens","content":[{"type":"text","text":"{\"a\":\"cut"}]},{"stop_reason":"end_turn","content":[{"type":"text","text":"{\"ok\":true}"}]}]
    client=GLMClient(api_key="fake",sleep=lambda _:None,transport=lambda *_: (calls.append(1) or responses[len(calls)-1]))
    assert client.classify("BODY") == {"ok":True}
    assert len(calls) == 3
    always=GLMClient(api_key="fake",sleep=lambda _:None,transport=lambda *_: (calls.append(1) or responses[0]))
    with pytest.raises(ClassificationError,match="after 3 attempts"): always.classify("BODY")
    assert len(calls) == 6


def test_mine_skips_classified_and_normalized_duplicate_bodies(tmp_path):
    db=Database(tmp_path/"radar.db")
    first=RawSignal("first","reddit","reddit","1","https://example.test/1","manual spreadsheet","Manual spreadsheet takes hours!",None,None,"2026-01-01","q","en","one")
    duplicate=RawSignal("duplicate","reddit","reddit","2","https://example.test/2","manual spreadsheet","manual   spreadsheet takes hours",None,None,"2026-01-01","q","en","two")
    db.upsert_signal(first); db.upsert_signal(duplicate)
    client=GLMClient(api_key="fake",sleep=lambda _:None,transport=lambda *_: {"content":[{"type":"text","text":"{\"is_complaint\":true,\"pain\":\"manual work\",\"observed\":[\"Manual spreadsheet takes hours\"],\"inference\":[]}"}]})
    assert len(mine(db,client)) == 1
    assert len(mine(db,client)) == 0
