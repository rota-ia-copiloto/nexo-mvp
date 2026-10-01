class OutcomeService:
    def __init__(self,repo): self.repo=repo
    def evidence_for(self,outcome_id):
        df=self.repo.table("evidence"); return df[df.outcome_id==outcome_id].copy()
    def evaluate_retention90(self,outcome_id):
        out=self.repo.outcome(outcome_id); ev=self.evidence_for(outcome_id); a=(ev.strength=="A").sum(); b=(ev.strength=="B").sum(); evidence_ok=(a>=1 or b>=2); return {"days_ok":int(out.days_observed)>=90,"evidence_ok":bool(evidence_ok),"rule_version":out.rule_version,"result":bool(int(out.days_observed)>=90 and evidence_ok)}
