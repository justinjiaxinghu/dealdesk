"use client";

import { useCallback, useEffect, useState } from "react";

import type {
  Assumption,
  AssumptionSet,
  Deal,
  Document,
  ExtractedField,
  MarketTable,
  ModelResult,
} from "@/interfaces/api";
import { assumptionService } from "@/services/assumption.service";
import { dealService } from "@/services/deal.service";
import { documentService } from "@/services/document.service";
import { modelService } from "@/services/model.service";

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
  const [tables, setTables] = useState<MarketTable[]>([]);
  const [assumptionSets, setAssumptionSets] = useState<AssumptionSet[]>([]);
  const [assumptions, setAssumptions] = useState<Assumption[]>([]);
  const [modelResult, setModelResult] = useState<ModelResult | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [dealData, docs, sets] = await Promise.all([
        dealService.get(id),
        documentService.list(id),
        assumptionService.listSets(id),
      ]);

      setDeal(dealData);
      setDocuments(docs);
      setAssumptionSets(sets);

      // Fetch extracted fields & tables for the first document (if any)
      if (docs.length > 0) {
        const firstDoc = docs[0];
        const [f, t] = await Promise.all([
          documentService.getFields(id, firstDoc.id),
          documentService.getTables(id, firstDoc.id),
        ]);
        setFields(f);
        setTables(t);
      }

      // Fetch assumptions & model result for the first assumption set
      if (sets.length > 0) {
        const firstSet = sets[0];
        const a = await assumptionService.listAssumptions(firstSet.id);
        setAssumptions(a);

        try {
          const result = await modelService.getResult(firstSet.id);
          setModelResult(result);
        } catch {
          // No model result yet — that's fine
          setModelResult(null);
        }
      }
    } catch (err) {
      console.error("Failed to fetch deal data", err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return {
    deal,
    documents,
    fields,
    tables,
    assumptionSets,
    assumptions,
    modelResult,
    loading,
    refresh,
  };
}
