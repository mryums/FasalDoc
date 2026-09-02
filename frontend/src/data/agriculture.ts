/**
 * Integration point for Member 4's agriculture research dataset.
 *
 * Member 4 owns the source of truth for: supported crops, common problems,
 * symptoms, treatments, Urdu terminology, and Pakistani agricultural context.
 *
 * Data extracted from `data/plant_disease_dataset/crop_knowledge.json`.
 * Member 4's original files are NOT modified — this is a read-only summary.
 */

import cropKnowledge from '../../../data/plant_disease_dataset/crop_knowledge.json'

export interface CropTerm {
  english: string
  urdu?: string
  romanUrdu?: string
}

export interface DiseaseInfo {
  diseaseId: string
  name: { en: string; ur?: string }
  description: { en: string; ur?: string }
  symptoms: { en: string[]; ur?: string[] }
  treatment: { en: string[]; ur?: string[] }
  prevention: { en: string[]; ur?: string[] }
  type: string
  causalAgent: string
}

export interface PlantInfo {
  plantId: string
  name: { en: string; ur?: string }
  diseases: DiseaseInfo[]
}

export interface AgricultureDataset {
  /** Crops FasalDoc is known to work well with (from Member 4). */
  supportedCrops: CropTerm[]
  /** Seasonal / preventive tips shown on the home screen (from Member 4). */
  tips: string[]
  /** Full plant + disease knowledge base for lookup. */
  plants: PlantInfo[]
}

/**
 * Look up disease information by crop name and disease name.
 * Performs case-insensitive matching against English names and aliases.
 * Returns null if no match is found — the frontend should NOT fabricate data.
 */
export function diseaseLookup(
  cropName: string,
  diseaseName: string,
): DiseaseInfo | null {
  if (!cropName || !diseaseName) return null

  const cropLower = cropName.toLowerCase().trim()
  const diseaseLower = diseaseName.toLowerCase().trim()

  // Find the plant
  const plant = cropKnowledgeData.plants.find(
    (p) =>
      p.name.en.toLowerCase() === cropLower ||
      p.name.en.toLowerCase().includes(cropLower) ||
      cropLower.includes(p.name.en.toLowerCase()),
  )
  if (!plant) return null

  // Find the disease
  const disease = plant.diseases.find(
    (d) =>
      d.name.en.toLowerCase() === diseaseLower ||
      d.name.en.toLowerCase().includes(diseaseLower) ||
      diseaseLower.includes(d.name.en.toLowerCase()),
  )

  return disease ?? null
}

// Build the dataset from the imported JSON
function buildDataset(): AgricultureDataset {
  const plants: PlantInfo[] = (cropKnowledge as any).plants.map((p: any) => ({
    plantId: p.plant_id,
    name: { en: p.name.en, ur: p.name.ur },
    diseases: (p.diseases || []).map((d: any) => ({
      diseaseId: d.disease_id,
      name: { en: d.name.en, ur: d.name.ur },
      description: { en: d.description?.en ?? '', ur: d.description?.ur },
      symptoms: { en: d.symptoms?.en ?? [], ur: d.symptoms?.ur },
      treatment: { en: d.treatment?.en ?? [], ur: d.treatment?.ur },
      prevention: { en: d.prevention?.en ?? [], ur: d.prevention?.ur },
      type: d.type ?? '',
      causalAgent: d.causal_agent ?? '',
    })),
  }))

  const supportedCrops: CropTerm[] = plants.map((p) => ({
    english: p.name.en,
    urdu: p.name.ur,
  }))

  return {
    supportedCrops,
    tips: [],
    plants,
  }
}

const cropKnowledgeData = buildDataset()

export const agricultureData: AgricultureDataset = cropKnowledgeData
