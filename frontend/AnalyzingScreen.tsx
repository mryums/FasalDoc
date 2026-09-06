/**
 * Integration point for Member 4's agriculture research dataset.
 *
 * Member 4 owns the source of truth for: supported crops, common problems,
 * symptoms, treatments, Urdu terminology, and Pakistani agricultural context.
 * Their dataset was NOT present in the repository when this frontend was
 * built, so nothing agricultural is hardcoded into the UI.
 *
 * When Member 4 delivers the data (JSON / CSV / TS), fill `agricultureData`
 * here — the UI reads from this module only, so no component changes needed.
 */

export interface CropTerm {
  english: string
  urdu?: string
  romanUrdu?: string
}

export interface AgricultureDataset {
  /** Crops FasalDoc is known to work well with (from Member 4). */
  supportedCrops: CropTerm[]
  /** Seasonal / preventive tips shown on the home screen (from Member 4). */
  tips: string[]
}

export const agricultureData: AgricultureDataset = {
  supportedCrops: [],
  tips: [],
}
