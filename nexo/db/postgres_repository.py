from __future__ import annotations
import json
import pandas as pd
from sqlalchemy import create_engine, text
from nexo.config import settings
from .repository import Repository

class PostgresRepository(Repository):
    is_persistent = True

    def __init__(self, database_url: str | None = None):
        url=database_url or settings.database_url
        if not url:
            raise RuntimeError("DATABASE_URL não configurada. Use a connection string do Supabase em uma variável de ambiente do servidor Streamlit.")
        self.engine=create_engine(url, pool_pre_ping=True, future=True)

    def table(self,name:str)->pd.DataFrame:
        allowed={"skills","occupations","companies","jobs","job_skills","participants","participant_skills","courses","course_skills","employments","outcomes","evidence","journey_events","experiments","demands","demand_skills","demand_skill_candidates","skill_aliases","skill_embedding_documents","audit_log"}
        if name not in allowed: raise KeyError(name)
        with self.engine.connect() as conn:
            return pd.read_sql(text(f'SELECT * FROM public.{name}'),conn)

    def get_embedding_documents(self, embedding_model: str, only_missing: bool = True) -> pd.DataFrame:
        where = "WHERE embedding_model=:model"
        if only_missing:
            where += " AND embedding IS NULL"
        q=f"""SELECT embedding_id, skill_id, content, content_type, source_ref, embedding_model
              FROM public.skill_embedding_documents {where}
              ORDER BY skill_id, content_type, content"""
        with self.engine.connect() as conn:
            return pd.read_sql(text(q), conn, params={"model": embedding_model})

    def update_skill_embeddings(self, records: list[dict]):
        if not records:
            return
        with self.engine.begin() as conn:
            for item in records:
                vector_literal = "[" + ",".join(str(float(x)) for x in item["embedding"]) + "]"
                conn.execute(text("""UPDATE public.skill_embedding_documents
                                     SET embedding=CAST(:embedding AS extensions.vector),
                                         embedding_model=:model, updated_at=now()
                                     WHERE embedding_id=CAST(:id AS uuid)"""), {
                    "embedding": vector_literal, "model": item["embedding_model"], "id": item["embedding_id"]
                })

    def semantic_skill_search(self, embedding: list[float], threshold: float = 0.42, count: int = 3, embedding_model: str = "text-embedding-3-small") -> list[dict]:
        vector_literal = "[" + ",".join(str(float(x)) for x in embedding) + "]"
        q="""WITH ranked AS (
                SELECT d.skill_id, s.skill_name, d.content AS matched_text, d.content_type,
                       1 - (d.embedding <=> CAST(:embedding AS extensions.vector)) AS similarity,
                       row_number() over (partition by d.skill_id order by d.embedding <=> CAST(:embedding AS extensions.vector)) AS rn
                FROM public.skill_embedding_documents d
                JOIN public.skills s ON s.skill_id=d.skill_id
                WHERE d.embedding_model=:model AND d.embedding IS NOT NULL
              )
              SELECT skill_id, skill_name, matched_text, content_type, similarity
              FROM ranked
              WHERE rn=1 AND similarity >= :threshold
              ORDER BY similarity DESC
              LIMIT :count"""
        with self.engine.connect() as conn:
            rows=conn.execute(text(q), {"embedding":vector_literal,"model":embedding_model,"threshold":float(threshold),"count":int(count)}).mappings().all()
            return [dict(r) for r in rows]

    def get_demand(self, demand_id: str):
        with self.engine.connect() as conn:
            row=conn.execute(text('SELECT * FROM public.demands WHERE demand_id=:id'), {'id':demand_id}).mappings().first()
            return dict(row) if row else None

    def get_demand_skills(self, demand_id: str) -> pd.DataFrame:
        q="""SELECT ds.demand_id, ds.skill_id, s.skill_name, ds.requirement_type,
                    ds.confidence, ds.validation_status, ds.source,
                    ds.validated_by, ds.validated_at, ds.notes
             FROM public.demand_skills ds
             JOIN public.skills s ON s.skill_id=ds.skill_id
             WHERE ds.demand_id=:id ORDER BY ds.confidence DESC NULLS LAST"""
        with self.engine.connect() as conn:
            return pd.read_sql(text(q),conn,params={'id':demand_id})

    def _audit(self, conn, actor_id, action, entity_type, entity_id, old_value=None, new_value=None, reason=None):
        conn.execute(text("""INSERT INTO public.audit_log(actor_id,action,entity_type,entity_id,old_value,new_value,reason)
                             VALUES (:actor,:action,:etype,:eid,CAST(:old AS jsonb),CAST(:new AS jsonb),:reason)"""),{
            'actor':actor_id,'action':action,'etype':entity_type,'eid':entity_id,
            'old':json.dumps(old_value,ensure_ascii=False,default=str) if old_value is not None else None,
            'new':json.dumps(new_value,ensure_ascii=False,default=str) if new_value is not None else None,
            'reason':reason
        })

    def save_demand(self, *, demand_id: str, company_id: str, occupation_id: str | None,
                    quantity: int, horizon: str, description: str, status: str='draft',
                    actor_id: str='streamlit-demo'):
        with self.engine.begin() as conn:
            old=conn.execute(text('SELECT * FROM public.demands WHERE demand_id=:id'),{'id':demand_id}).mappings().first()
            conn.execute(text("""INSERT INTO public.demands(demand_id,company_id,occupation_id,quantity,horizon,description,status)
                                 VALUES (:id,:company,:occupation,:quantity,:horizon,:description,:status)
                                 ON CONFLICT (demand_id) DO UPDATE SET
                                   company_id=excluded.company_id, occupation_id=excluded.occupation_id,
                                   quantity=excluded.quantity, horizon=excluded.horizon,
                                   description=excluded.description, status=excluded.status, updated_at=now()"""),{
                'id':demand_id,'company':company_id,'occupation':occupation_id,'quantity':int(quantity),
                'horizon':horizon,'description':description,'status':status
            })
            new={'demand_id':demand_id,'company_id':company_id,'occupation_id':occupation_id,'quantity':int(quantity),'horizon':horizon,'description':description,'status':status}
            self._audit(conn,actor_id,'UPSERT','demand',demand_id,dict(old) if old else None,new,'Criação/atualização de demanda pela interface NEXO')
        return self.get_demand(demand_id)

    def save_demand_skills(self, demand_id: str, skills: list[dict], actor_id: str='streamlit-demo'):
        with self.engine.begin() as conn:
            for item in skills:
                conn.execute(text("""INSERT INTO public.demand_skills(demand_id,skill_id,requirement_type,confidence,validation_status,source)
                                     VALUES (:demand,:skill,:req,:confidence,'suggested',:source)
                                     ON CONFLICT (demand_id,skill_id) DO UPDATE SET
                                       requirement_type=excluded.requirement_type,
                                       confidence=excluded.confidence,
                                       source=excluded.source"""),{
                    'demand':demand_id,'skill':item['skill_id'],'req':item.get('requirement_type','suggested'),
                    'confidence':float(item.get('confidence',0)),'source':item.get('source','model')
                })
            conn.execute(text("UPDATE public.demands SET status='analyzed', updated_at=now() WHERE demand_id=:id"),{'id':demand_id})
            self._audit(conn,actor_id,'SKILL_EXTRACTION','demand',demand_id,None,{'skills':skills},'Competências sugeridas pelo motor de extração')
        return self.get_demand_skills(demand_id)

    def validate_demand_skills(self, demand_id: str, validations: list[dict], actor_id: str='streamlit-demo'):
        with self.engine.begin() as conn:
            for item in validations:
                old=conn.execute(text('SELECT * FROM public.demand_skills WHERE demand_id=:d AND skill_id=:s'),{'d':demand_id,'s':item['skill_id']}).mappings().first()
                conn.execute(text("""UPDATE public.demand_skills SET
                                      requirement_type=:req,
                                      validation_status=:status,
                                      validated_by=:actor,
                                      validated_at=now(),
                                      notes=:notes
                                     WHERE demand_id=:demand AND skill_id=:skill"""),{
                    'req':item.get('requirement_type','suggested'),'status':item.get('validation_status','validated'),
                    'actor':actor_id,'notes':item.get('notes'),'demand':demand_id,'skill':item['skill_id']
                })
                self._audit(conn,actor_id,'VALIDATE_SKILL','demand_skill',f"{demand_id}:{item['skill_id']}",dict(old) if old else None,item,'Validação humana de competência')
            remaining=conn.execute(text("SELECT count(*) FROM public.demand_skills WHERE demand_id=:id AND validation_status='suggested'"),{'id':demand_id}).scalar_one()
            status='validated' if remaining==0 else 'analyzed'
            conn.execute(text('UPDATE public.demands SET status=:status, updated_at=now() WHERE demand_id=:id'),{'status':status,'id':demand_id})
        return self.get_demand_skills(demand_id)

    def get_skill_candidates(self, demand_id: str) -> pd.DataFrame:
        q="""SELECT c.candidate_id, c.demand_id, c.raw_term, c.proposed_skill_id,
                    c.proposed_label, c.requirement_type, c.confidence,
                    c.evidence_excerpt, c.rationale, c.extraction_model,
                    c.prompt_version, c.normalization_method, c.normalization_score, c.semantic_candidates, c.review_status, c.final_skill_id,
                    c.reviewed_by, c.reviewed_at, c.created_at
             FROM public.demand_skill_candidates c
             WHERE c.demand_id=:id
             ORDER BY c.created_at DESC, c.confidence DESC"""
        with self.engine.connect() as conn:
            return pd.read_sql(text(q),conn,params={'id':demand_id})

    def save_skill_candidates(self, demand_id: str, candidates: list[dict], actor_id: str='streamlit-demo'):
        with self.engine.begin() as conn:
            # Pending suggestions from a prior extraction run can be replaced safely;
            # already-reviewed candidates remain part of the audit trail.
            conn.execute(text("DELETE FROM public.demand_skill_candidates WHERE demand_id=:id AND review_status='pending'"), {'id':demand_id})
            for item in candidates:
                conn.execute(text("""INSERT INTO public.demand_skill_candidates(
                                        demand_id, raw_term, proposed_skill_id, proposed_label,
                                        requirement_type, confidence, evidence_excerpt, rationale,
                                        extraction_model, prompt_version, normalization_method, normalization_score, semantic_candidates, review_status)
                                     VALUES (:demand,:raw,:skill,:label,:req,:confidence,:excerpt,:rationale,
                                             :model,:prompt,:norm_method,:norm_score,CAST(:semantic AS jsonb),'pending')"""), {
                    'demand':demand_id,
                    'raw':item['raw_term'],
                    'skill':item.get('proposed_skill_id'),
                    'label':item.get('proposed_label'),
                    'req':item.get('requirement_type','suggested'),
                    'confidence':float(item.get('confidence',0)),
                    'excerpt':item.get('evidence_excerpt'),
                    'rationale':item.get('rationale'),
                    'model':item.get('extraction_model'),
                    'prompt':item.get('prompt_version','skills_v1'),
                    'norm_method':item.get('normalization_method'),
                    'norm_score':float(item.get('normalization_score',0)),
                    'semantic':json.dumps(item.get('semantic_candidates',[]),ensure_ascii=False,default=str),
                })
            conn.execute(text("UPDATE public.demands SET status='analyzed', updated_at=now() WHERE demand_id=:id"), {'id':demand_id})
            self._audit(conn,actor_id,'LLM_SKILL_EXTRACTION','demand',demand_id,None,{
                'candidate_count':len(candidates),
                'skills':[{'raw_term':c.get('raw_term'),'proposed_skill_id':c.get('proposed_skill_id'),'confidence':c.get('confidence')} for c in candidates],
            },'Extração LLM + normalização contra taxonomia NEXO; requer validação humana')
        return self.get_skill_candidates(demand_id)

    def review_skill_candidates(self, demand_id: str, reviews: list[dict], actor_id: str='streamlit-demo'):
        with self.engine.begin() as conn:
            for item in reviews:
                cid=item['candidate_id']
                old=conn.execute(text('SELECT * FROM public.demand_skill_candidates WHERE candidate_id=:id'),{'id':cid}).mappings().first()
                if not old:
                    continue
                decision=item.get('review_status','pending')
                final_skill_id=item.get('final_skill_id') or old.get('proposed_skill_id')
                req=item.get('requirement_type') or old.get('requirement_type') or 'suggested'

                if decision == 'validated' and not final_skill_id:
                    raise ValueError('Uma competência validada precisa estar mapeada para uma skill da taxonomia NEXO.')

                conn.execute(text("""UPDATE public.demand_skill_candidates SET
                                      review_status=:status,
                                      final_skill_id=:final_skill,
                                      requirement_type=:req,
                                      reviewed_by=:actor,
                                      reviewed_at=now()
                                    WHERE candidate_id=:cid"""), {
                    'status':decision,'final_skill':final_skill_id if decision=='validated' else None,
                    'req':req,'actor':actor_id,'cid':cid
                })

                if decision == 'validated':
                    conn.execute(text("""INSERT INTO public.demand_skills(
                                            demand_id, skill_id, requirement_type, confidence,
                                            validation_status, source, validated_by, validated_at,
                                            notes, source_candidate_id)
                                         VALUES (:demand,:skill,:req,:confidence,'validated','llm_human_validated',
                                                 :actor,now(),:notes,:candidate)
                                         ON CONFLICT (demand_id,skill_id) DO UPDATE SET
                                           requirement_type=excluded.requirement_type,
                                           confidence=excluded.confidence,
                                           validation_status='validated',
                                           source='llm_human_validated',
                                           validated_by=excluded.validated_by,
                                           validated_at=excluded.validated_at,
                                           notes=excluded.notes,
                                           source_candidate_id=excluded.source_candidate_id"""), {
                        'demand':demand_id,'skill':final_skill_id,'req':req,
                        'confidence':float(old.get('confidence') or 0), 'actor':actor_id,
                        'notes':f"Validado a partir do termo extraído: {old.get('raw_term')}", 'candidate':cid
                    })
                elif decision == 'rejected':
                    conn.execute(text("DELETE FROM public.demand_skills WHERE demand_id=:d AND source_candidate_id=:c"), {'d':demand_id,'c':cid})

                new={'candidate_id':str(cid),'review_status':decision,'final_skill_id':final_skill_id if decision=='validated' else None,'requirement_type':req}
                self._audit(conn,actor_id,'REVIEW_SKILL_CANDIDATE','demand_skill_candidate',str(cid),dict(old),new,'Decisão humana da empresa sobre competência sugerida pela IA')

            pending=conn.execute(text("SELECT count(*) FROM public.demand_skill_candidates WHERE demand_id=:id AND review_status='pending'"),{'id':demand_id}).scalar_one()
            validated=conn.execute(text("SELECT count(*) FROM public.demand_skills WHERE demand_id=:id AND validation_status='validated'"),{'id':demand_id}).scalar_one()
            status='validated' if pending==0 and validated>0 else 'analyzed'
            conn.execute(text('UPDATE public.demands SET status=:status, updated_at=now() WHERE demand_id=:id'),{'status':status,'id':demand_id})
        return self.get_skill_candidates(demand_id)

