export interface Deal {
  id: string;
  name: string;
  address: string;
  city: string;
  state: string;
  property_type: string;
  latitude: number | null;
  longitude: number | null;
  square_feet: number | null;
  created_at: string;
  updated_at: string;
}

export interface CreateDealInput {
  name: string;
  address: string;
  city: string;
  state: string;
  property_type: string;
  latitude?: number | null;
  longitude?: number | null;
  square_feet?: number | null;
}

export interface ProcessingStep {
  name: string;
  status: string;
  detail: string;
}

export interface Document {
  id: string;
  deal_id: string;
  document_type: string;
  original_filename: string;
  processing_status: string;
  processing_steps: ProcessingStep[];
  error_message: string | null;
  page_count: number | null;
  created_at: string;
}

export interface ExtractedField {
  id: string;
  document_id: string;
  field_key: string;
  value_text: string | null;
  value_number: number | null;
  unit: string | null;
  confidence: number;
  source_page: number | null;
}

export interface MarketTable {
  id: string;
  document_id: string;
  table_type: string;
  headers: string[];
  rows: string[][];
  source_page: number | null;
  confidence: number;
}

export interface AssumptionSet {
  id: string;
  deal_id: string;
  name: string;
  created_at: string;
}

export interface Assumption {
  id: string;
  set_id: string;
  key: string;
  value_number: number | null;
  unit: string | null;
  range_min: number | null;
  range_max: number | null;
  source_type: string;
  source_ref: string | null;
  notes: string | null;
  updated_at: string;
}

export interface ExportRecord {
  id: string;
  deal_id: string;
  set_id: string;
  file_path: string;
  export_type: string;
  created_at: string;
}

export interface QuickExtractResult {
  name: string | null;
  address: string | null;
  city: string | null;
  state: string | null;
  property_type: string | null;
  square_feet: number | null;
}

export interface Benchmark {
  key: string;
  value: number;
  unit: string;
  range_min: number;
  range_max: number;
  source: string;
  confidence: number;
}

export interface ValidationSource {
  url: string;
  title: string;
  snippet: string;
}

export interface SearchStepResult {
  url: string;
  title: string;
  snippet: string;
}

export interface SearchStep {
  phase: string;
  query: string;
  results: SearchStepResult[];
}

export interface FieldValidation {
  id: string;
  deal_id: string;
  field_key: string;
  om_value: number | null;
  market_value: number | null;
  status: string;
  explanation: string;
  sources: ValidationSource[];
  confidence: number;
  search_steps: SearchStep[];
  created_at: string;
}
