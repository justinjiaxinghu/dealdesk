"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import type {
  Assumption,
  AssumptionSet,
  Deal,
  Document,
  ExtractedField,
} from "@/interfaces/api";
import { assumptionService } from "@/services/assumption.service";
import { dealService } from "@/services/deal.service";
import { documentService } from "@/services/document.service";

// ---------------------------------------------------------------------------
// useDeals – fetches the deal list
// ---------------------------------------------------------------------------

export function useDeals() {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await dealService.list();
      setDeals(data);
    } catch (err) {
      console.error("Failed to fetch deals", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { deals, loading, refresh };
}

// ---------------------------------------------------------------------------
// useDeal – fetches a single deal with its documents, assumptions, and model
// ---------------------------------------------------------------------------

export function useDeal(id: string) {
  const [deal, setDeal] = useState<Deal | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [fields, setFields] = useState<ExtractedField[]>([]);
  const [assumptionSets, setAssumptionSets] = useState<AssumptionSet[]>([]);
  const [assumptions, setAssumptions] = useState<Assumption[]>([]);
  const [loading, setLoading] = useState(true);
  const initialLoadDone = useRef(false);

  const refresh = useCallback(async () => {
    // Only show full loading spinner on initial load, not during pipeline refreshes
    if (!initialLoadDone.current) {
      setLoading(true);
    }
    try {
      const [dealData, docs, sets] = await Promise.all([
        dealService.get(id),
        documentService.list(id),
        assumptionService.listSets(id),
      ]);

      setDeal(dealData);
      setDocuments(docs);
      setAssumptionSets(sets);

      // Fetch extracted fields for the first document (if any)
      if (docs.length > 0) {
        const firstDoc = docs[0];
        const f = await documentService.getFields(id, firstDoc.id);
        setFields(f);
      }

      // Fetch assumptions for the first assumption set
      if (sets.length > 0) {
        const firstSet = sets[0];
        const a = await assumptionService.listAssumptions(firstSet.id);
        setAssumptions(a);
      }
    } catch (err) {
      console.error("Failed to fetch deal data", err);
    } finally {
      setLoading(false);
      initialLoadDone.current = true;
    }
  }, [id]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return {
    deal,
    documents,
    fields,
    assumptionSets,
    assumptions,
    loading,
    refresh,
  };
}
