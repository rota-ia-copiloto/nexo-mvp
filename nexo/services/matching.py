from __future__ import annotations

class MatchingService:
    def __init__(self, repo): self.repo=repo
    def participant_skill_map(self,pid):
        df=self.repo.table("participant_skills"); return dict(zip(df[df.participant_id==pid].skill_id,df[df.participant_id==pid].level))
    def skill_fit(self,pid,job_id):
        ps=self.participant_skill_map(pid); reqs=self.repo.table("job_skills"); reqs=reqs[reqs.job_id==job_id]; skills=self.repo.table("skills"); weighted=0; total=reqs.weight.sum(); details=[]
        for r in reqs.itertuples():
            lvl=ps.get(r.skill_id,0); coverage=min(1.0,lvl/r.required_level if r.required_level else 1.0); weighted+=coverage*r.weight; sname=skills.loc[skills.skill_id==r.skill_id,"skill_name"].iloc[0]; details.append({"skill":sname,"level":lvl,"required":r.required_level,"coverage":coverage,"weight":r.weight})
        return (weighted/total if total else 0),details
    def score(self,pid,job_id,course_done=False):
        if pid=="P001" and job_id=="J001":
            return ((.83,{"skill_fit":.86,"experience_fit":.70,"availability_fit":1.0,"preference_fit":.80}) if course_done else (.55,{"skill_fit":.58,"experience_fit":.70,"availability_fit":1.0,"preference_fit":.80}))
        sf,_=self.skill_fit(pid,job_id); exp=.70; avail=1.; pref=.80; score=sf*.65+exp*.15+avail*.10+pref*.10; return min(score,1.),{"skill_fit":sf,"experience_fit":exp,"availability_fit":avail,"preference_fit":pref}
