from __future__ import annotations
import random
import hashlib
from datetime import datetime, timedelta
import pandas as pd
from .catalog import *

def make_demo_data(seed: int = 42) -> dict[str, pd.DataFrame]:
    rng = random.Random(seed)
    skills=pd.DataFrame(SKILLS,columns=["skill_id","skill_name","skill_type"])
    occupations=pd.DataFrame(OCCUPATIONS,columns=["occupation_id","occupation_name"])
    companies=pd.DataFrame(COMPANIES,columns=["company_id","company_name","sector","employees"])
    jobs=[]; j=1; company_ids=[c[0] for c in COMPANIES]
    for occ_id,count in JOB_COUNTS.items():
        for _ in range(count):
            jobs.append((f"J{j:03d}",rng.choice(company_ids),occ_id,"Ativa",rng.choice(["Imediata","3 meses","6 meses"]))); j+=1
    jobs[0]=("J001","C001","O001","Ativa","Imediata")
    jobs=pd.DataFrame(jobs,columns=["job_id","company_id","occupation_id","status","horizon"])
    job_skills=[]
    for row in jobs.itertuples():
        for sid,level,weight in OCC_SKILLS[row.occupation_id]:
            job_skills.append((row.job_id,sid,level,weight,"Obrigatória"))
    job_skills=pd.DataFrame(job_skills,columns=["job_id","skill_id","required_level","weight","requirement_type"])
    participants=[("P001","Ana Souza",34,"Ensino Médio","Desempregado",8,"O001","Integral"),("P002","Carlos Mendes",29,"Ensino Médio","Empregado",0,"O002","Integral"),("P003","Júlia Rocha",31,"Técnico","Desempregado",4,"O001","Integral"),("P004","Paulo Ribeiro",38,"Técnico","Desempregado",10,"O003","Integral")]
    first=["Marina","Joana","Renata","Lucas","Bruno","Camila","Rafael","Fernanda","Diego","Patrícia","Beatriz","André","Carolina","Gustavo","Helena","Igor","Larissa","Marcelo","Natália","Otávio"]
    last=["Silva","Souza","Rocha","Ribeiro","Costa","Oliveira","Santos","Lima","Almeida","Pereira"]
    for i in range(5,201):
        emp=rng.choices(["Desempregado","Empregado","Informal"],weights=[.65,.20,.15])[0]
        participants.append((f"P{i:03d}",f"{rng.choice(first)} {rng.choice(last)}",rng.randint(19,55),rng.choices(["Ensino Fundamental","Ensino Médio","Técnico","Superior"],weights=[.15,.55,.20,.10])[0],emp,rng.randint(1,18) if emp=="Desempregado" else 0,rng.choice([o[0] for o in OCCUPATIONS]),rng.choice(["Integral","Diurno","Noturno"])))
    participants=pd.DataFrame(participants,columns=["participant_id","name","age","education","employment_status","unemployment_months","preferred_occupation","availability"])
    pskills=[]
    for sid,lvl in {"SK001":3,"SK014":3,"SK015":3,"SK002":1,"SK003":0,"SK005":0}.items(): pskills.append(("P001",sid,lvl,"baseline"))
    for pid,occ,base in [("P002","O002",.85),("P003","O001",.75),("P004","O003",.50)]:
        for sid,req,_ in OCC_SKILLS[occ]: pskills.append((pid,sid,max(0,min(4,round(req*base+rng.choice([-1,0,0,1])))),"baseline"))
    all_skill_ids=[s[0] for s in SKILLS]
    for row in participants.iloc[4:].itertuples():
        core=[x[0] for x in OCC_SKILLS[row.preferred_occupation]]; selected=set(rng.sample(core,min(len(core),rng.randint(2,min(5,len(core)))))); selected.update(rng.sample(all_skill_ids,rng.randint(1,4)))
        for sid in selected: pskills.append((row.participant_id,sid,rng.randint(1,3),"baseline"))
    participant_skills=pd.DataFrame(pskills,columns=["participant_id","skill_id","level","source"])
    courses=pd.DataFrame(COURSES,columns=["course_id","course_name","hours","target_occupation"])
    cskills=[(cid,sid,gain) for cid,pairs in COURSE_SKILLS.items() for sid,gain in pairs]
    course_skills=pd.DataFrame(cskills,columns=["course_id","skill_id","expected_gain"])
    employments=[("EMP001","P001","C001","O001","J001","2026-03-10",None,"active")]
    for idx,pid in enumerate(["P002","P003"]+[f"P{i:03d}" for i in range(5,40)],start=2):
        if len(employments)>=38: break
        prow=participants.loc[participants.participant_id==pid].iloc[0]; start=datetime(2026,1,1)+timedelta(days=rng.randint(1,180))
        employments.append((f"EMP{idx:03d}",pid,rng.choice(company_ids),prow.preferred_occupation,None,start.date().isoformat(),None,"active"))
    employments=pd.DataFrame(employments,columns=["employment_id","participant_id","company_id","occupation_id","job_id","start_date","end_date","status"])
    outcomes=[("OUT001","P001","EMP001","RETENTION_90","VALIDATED","RET90_V1.0",92,True)]
    evidence=[("EV001","OUT001","employer_confirmation","Empresa Alfa","B","VERIFIED","2026-03-10"),("EV002","OUT001","independent_employment_record","Registro independente","A","VERIFIED","2026-03-12"),("EV003","OUT001","retention_verification","Registro independente","A","VERIFIED","2026-06-10")]
    out_counter=2; ev_counter=4
    for e in employments.iloc[1:].itertuples():
        if len(outcomes)>=75: break
        oid=f"OUT{out_counter:03d}"; outcomes.append((oid,e.participant_id,e.employment_id,"HIRE_VERIFIED","VALIDATED","HIRE_V1.0",0,True)); evidence.append((f"EV{ev_counter:03d}",oid,"employer_confirmation","Empresa","B","VERIFIED",e.start_date)); out_counter+=1; ev_counter+=1
        if len(outcomes)<75 and rng.random()<.65:
            otype=rng.choice(["HIRE_ALIGNED","RETENTION_90","RETENTION_180"]); status="VALIDATED" if rng.random()<.8 else "UNDER_REVIEW"; days={"HIRE_ALIGNED":0,"RETENTION_90":120,"RETENTION_180":200}[otype]; oid=f"OUT{out_counter:03d}"; rule={"HIRE_ALIGNED":"HIRE_ALIGNED_V1.0","RETENTION_90":"RET90_V1.0","RETENTION_180":"RET180_V1.0"}[otype]
            outcomes.append((oid,e.participant_id,e.employment_id,otype,status,rule,days,status=="VALIDATED")); evidence.append((f"EV{ev_counter:03d}",oid,"independent_record","Registro independente","A","VERIFIED" if status=="VALIDATED" else "PENDING","2026-06-15")); out_counter+=1; ev_counter+=1
    while len(outcomes)<75:
        e=employments.iloc[(len(outcomes)-1)%len(employments)]; otype=["HIRE_ALIGNED","RETENTION_90","RETENTION_180"][len(outcomes)%3]; status="VALIDATED" if len(outcomes)%5 else "UNDER_REVIEW"; days={"HIRE_ALIGNED":0,"RETENTION_90":120,"RETENTION_180":200}[otype]; oid=f"OUT{len(outcomes)+1:03d}"; rule={"HIRE_ALIGNED":"HIRE_ALIGNED_V1.0","RETENTION_90":"RET90_V1.0","RETENTION_180":"RET180_V1.0"}[otype]
        outcomes.append((oid,e.participant_id,e.employment_id,otype,status,rule,days,status=="VALIDATED")); evidence.append((f"EV{ev_counter:03d}",oid,"independent_record","Registro independente","A","VERIFIED" if status=="VALIDATED" else "PENDING","2026-06-15")); ev_counter+=1
    outcomes=pd.DataFrame(outcomes[:75],columns=["outcome_id","participant_id","employment_id","definition","status","rule_version","days_observed","achieved"])
    valid=set(outcomes.outcome_id); evidence=[e for e in evidence if e[1] in valid]
    evidence=pd.DataFrame(evidence,columns=["evidence_id","outcome_id","evidence_type","source","strength","status","captured_at"])
    while len(evidence)<145:
        o=outcomes.iloc[len(evidence)%len(outcomes)]; evidence=pd.concat([evidence,pd.DataFrame([{"evidence_id":f"EV{len(evidence)+1:03d}","outcome_id":o.outcome_id,"evidence_type":"supplementary_record","source":"Registro complementar","strength":"B","status":"VERIFIED" if o.status=="VALIDATED" else "PENDING","captured_at":"2026-06-15"}])],ignore_index=True)
    journey=[("JE001","P001","participant_registered","2026-01-10","Cadastro concluído"),("JE002","P001","assessment_completed","2026-01-12","Diagnóstico concluído"),("JE003","P001","gap_identified","2026-01-13","Gap identificado"),("JE004","P001","course_recommended","2026-01-14","Operações Logísticas + ERP"),("JE005","P001","course_started","2026-01-20","Formação iniciada"),("JE006","P001","course_completed","2026-02-20","Formação concluída"),("JE007","P001","skill_profile_updated","2026-02-21","Perfil atualizado"),("JE008","P001","job_match_generated","2026-02-22","Match Empresa Alfa"),("JE009","P001","application_sent","2026-02-25","Candidatura enviada"),("JE010","P001","interview_completed","2026-03-05","Entrevista realizada"),("JE011","P001","employment_started","2026-03-10","Contratação iniciada"),("JE012","P001","retention_90_candidate","2026-06-08","Outcome candidato"),("JE013","P001","outcome_validated","2026-06-10","RETENTION_90 validado")]
    journey_events=pd.DataFrame(journey,columns=["event_id","participant_id","event_type","event_date","label"])
    experiments=pd.DataFrame([("EXP01","Extração de skills",100,.85,.87),("EXP02","Normalização semântica",100,.85,.89),("EXP03","Matching",100,.70,.76),("EXP04","Recomendação",60,.70,.74),("EXP05","Engajamento empresarial",18,.60,.72),("EXP06","Evidência suficiente",40,.90,.93),("EXP07","Reprodutibilidade auditor",30,.95,.967)],columns=["experiment_id","name","sample","target","result"])
    return {
        "skills": skills, "occupations": occupations, "companies": companies,
        "jobs": jobs, "job_skills": job_skills, "participants": participants,
        "participant_skills": participant_skills, "courses": courses,
        "course_skills": course_skills, "employments": employments,
        "outcomes": outcomes, "evidence": evidence,
        "journey_events": journey_events, "experiments": experiments,
    }
