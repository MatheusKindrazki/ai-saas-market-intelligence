from types import SimpleNamespace
from radar.mine import is_candidate, validate_observed
from radar.cluster import cluster_pains
from radar.score import score
def test_candidate_and_quote_gate():
    assert is_candidate('', 'This manual spreadsheet takes hours')
    assert validate_observed('This takes   hours', ['takes hours'])
    assert not validate_observed('This takes hours', ['fabricated claim'])
def test_clustering_and_score_caps_wtp():
    pains=[SimpleNamespace(id='a',pain='manual invoice work takes hours',icp='small business'),SimpleNamespace(id='b',pain='manual invoice work takes hours',icp='small business'),SimpleNamespace(id='c',pain='different words',icp='other')]
    assert cluster_pains(pains)==[('a','b'),('c',)]
    result=score({'severity':5,'recurrence':5,'willingness_to_pay':5,'market_access':5,'speed_to_value':5},['evidence'],[])
    assert result['dimensions']['willingness_to_pay']==2 and result['verdict']=='include'
