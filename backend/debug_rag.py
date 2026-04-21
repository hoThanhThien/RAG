from app.services.rag_service import _collect_hybrid_candidates, _filter_results_by_intent, _pick_best_chunk_per_tour, load_vector_store
from app.services.rag.intents import extract_query_intents, source_match_text, BEACH_TERMS, INTERNATIONAL_TERMS

cache = load_vector_store()
q = "di bien"
intents = extract_query_intents(q)
print("intents:", intents)

candidates = _collect_hybrid_candidates(q, cache, top_k=8)
print("candidates:", len(candidates))
for c in candidates[:6]:
    print(" ", c.get("tour_id"), c.get("title"), "type=", c.get("chunk_type"), "score=", c.get("score"))

# Check filter step
from app.services.rag_service import _intent_score_adjustment
rescored = []
for item in candidates:
    enriched = dict(item)
    enriched["score"] = _intent_score_adjustment(q, enriched)
    rescored.append(enriched)
rescored.sort(key=lambda x: float(x.get("score") or 0), reverse=True)
deduped = _pick_best_chunk_per_tour(rescored)
print("\ndeduped after scoring:", len(deduped))
for d in deduped[:5]:
    txt = source_match_text(d)
    has_intl = any(t in txt for t in INTERNATIONAL_TERMS)
    has_beach = any(t in txt for t in BEACH_TERMS)
    print(" ", d.get("tour_id"), d.get("title"), d.get("location"), "intl=", has_intl, "beach=", has_beach, "s=", d.get("score"))

final = _filter_results_by_intent(deduped, query=q, top_k=4)
print("\nfinal after filter:", len(final))
for f in final:
    print(" ", f.get("tour_id"), f.get("title"), f.get("location"))
