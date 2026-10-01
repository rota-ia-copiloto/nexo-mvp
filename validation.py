def validate_demo(repo):
    assert len(repo.table("participants"))==200
    assert len(repo.table("companies"))==18
    assert len(repo.table("jobs"))==112
    assert len(repo.table("skills"))==47
    assert len(repo.table("outcomes"))==75
    assert len(repo.table("employments"))==38
    out=repo.outcome("OUT001")
    assert out.definition=="RETENTION_90" and int(out.days_observed)==92
    assert len(repo.table("evidence")[repo.table("evidence").outcome_id=="OUT001"])==3
