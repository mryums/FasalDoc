/**
 * Integration point for Member 4's agriculture research dataset.
 *
 * Member 4 owns the source of truth for: supported crops, common problems,
 * symptoms, treatments, Urdu terminology, and Pakistani agricultural context.
 *
 * Data extracted from `data/plant_disease_dataset/crop_knowledge.json`.
 * Member 4's original files are NOT modified — this is a read-only summary.
 *
 * Roman Urdu coverage: the upstream JSON carries `en` + `ur` only. Roman
 * Urdu (Latin-script Urdu) is added here as a NON-FABRICATED transliteration
 * layer for the diagnoses the MobileNetV2 classifier can actually return
 * (see `ROMAN_URDU` below). The agricultural meaning, treatment steps and any
 * "confirm the dose locally" caveats are preserved verbatim — only the script
 * changes. Diseases outside the classifier's label set keep falling back to
 * English and are never shown in Roman Urdu mode.
 */

import cropKnowledge from '../../../data/plant_disease_dataset/crop_knowledge.json'

export type LocalizedText = { en: string; ur?: string; rom?: string }
export type LocalizedList = { en: string[]; ur?: string[]; rom?: string[] }

export interface CropTerm {
  english: string
  urdu?: string
  romanUrdu?: string
}

export interface DiseaseInfo {
  diseaseId: string
  name: LocalizedText
  description: LocalizedText
  symptoms: LocalizedList
  treatment: LocalizedList
  prevention: LocalizedList
  type: string
  causalAgent: string
}

export interface PlantInfo {
  plantId: string
  name: LocalizedText
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
 * Roman Urdu transliterations of the model-reachable diseases. Keyed by the
 * upstream `disease_id`. Sentences mirror the `en`/`ur` source exactly; the
 * standard English disease/chemical name is kept inside the Roman Urdu
 * sentence where that is the clearer, safer wording.
 */
const ROMAN_URDU: Record<
  string,
  { name: string; symptoms: string[]; treatment: string[]; prevention: string[] }
> = {
  DS001: {
    name: 'Ibtidaai Jhalasua (Early Blight)',
    symptoms: [
      'Sab se pehle nichlay puranay paton par ghelay bhooray dhabay bante hain jin mein gol gol chalay hon, jaise kisi nishanay ka board ho.',
      'Har dhabay ke gird aksar peela halka banta hai aur qareebi patta ahista ahista peela hone lagta hai.',
      'Mutassir patte sookh kar mur jate hain aur aakhirkaar gir jate hain, khaas tor par poday ke nichlay hissay se.',
      'Shadeed soorat-e-haal mein tanon aur phalon par bhi ghelay, dhansay hue dhabay ban sakte hain.',
    ],
    treatment: [
      'Jaise hi mutassir patte nazar aayen unhein tor kar tabah kar dein — unhein khet mein para na chhoren.',
      'Tambay (copper) par mabni fungicide ka spray karein aur product ke label aur maqami zaraai mashveron ki hidayat par poora amal karein.',
      'Patton ko bhigone ke bajaye poday ki jaron ke qareeb paani dein.',
    ],
    prevention: [
      'Qabil-e-aitmaad zariye se beemari se paak beej ya napenain (transplants) istemal karein.',
      'Podon ke beech munasib faasla rakhein aur unhein saharein (stake) taake hawa azaadana guzar sake.',
      'Mitti par mulch bichhayen taake baarish ya paani ke chintay mitti se fungus ko paton tak na pohnchain.',
      'Fasal kaatne ke baad purani baqiyat hata dein ya mitti mein dal dein, aur agli bahaar tamatar ke muqablay koi aur fasal boyen (rotation).',
    ],
  },
  DS002: {
    name: 'Deemeen Jhalasua (Late Blight)',
    symptoms: [
      'Paton par baray, be-tarteeb, paani mein doobe hue se grey-green dhabay bante hain jo tezi se bhooray ya kaalay ho jate hain.',
      'Narm-o-tr (humid) mausam mein mutassir patton ke peethay par safed rooi jaisi fungai ugati hai.',
      'Phalon par bhooray sakht dhabay bante hain aur tanon par charhamile ghelay dhabay/dhaariyan nazar aa sakti hain.',
      'Munasib (thanday aur gile) mausam mein poora poda chand dinon mein sookh kar gir sakta hai.',
    ],
    treatment: [
      'Mutassir poday foran hata kar tabah kar dein taake beemari tandrust podon tak na pheelay.',
      'Gile ya barish ke mausam se pehle aur doran protectant fungicide ka spray karein aur product ke label aur maqami zaraai mashveron ki hidayat par amal karein.',
      'Jab patte gelay hon to khet mein kaam karne se guraez karein kyunke is se pathogen pheelta hai.',
    ],
    prevention: [
      'Fasal ka baqaida jaiza lein, khaas tor par barish ya dhund ke baad, aur pehli nishan par hi qadam uthayen.',
      'Podon ki jaron ke qareeb paani dein aur oopar se (overhead) sidhwai se guraez karein.',
      'Podon ke beech acha faasla rakhein taake barish ke baad patte jaldi sookh jayen.',
      'Khud-ro (volunteer) tamatar aur aloo ke poday tabah kar dein kyunke ye mausamon ke darmiyan beemari bacha kar rakhte hain.',
    ],
  },
  DS003: {
    name: 'Zard Patta Curl Virus (TYLCV)',
    symptoms: [
      'Patte oopar ki taraf murtay hain aur ragon ke beech sikudan ya lehr-dar ho jate hain.',
      'Patte peela pad jate hain, khaas kar naujawan wale, aur mamool se chhotay ho sakte hain.',
      'Poday ki nauwai ruk jati hai (stunted) aur shaakhawan kam ho jati hai.',
      'Phool aur phal kam lagta hai, aur shadeed infection mein paidawar tezi se girti hai.',
    ],
    treatment: [
      'Mutassir podon ka koi ilaaj nahi — unhein hata kar tabah kar dein taake wo virus ka zariya na banein.',
      'Whitefly (safed macchi) ke wasila ko peelay chippakne wale khazane (yellow sticky traps) ya neem-oil spray se control karein, label ki hidayat ke mutabiq.',
    ],
    prevention: [
      'Jahan mumkin ho wahan TYLCV-resistant tamatar ki kisman istemal karein.',
      'Certified nursery se virus-free napenain lagayen aur lagane se pehle paudon ka jaiza lein.',
      'Jahan amli ho paudon ko keeda-roof jaal (netting) se dhaken aur khet ke gird ghaas-phoos saaf rakhein.',
      'Pure mausam mein mutassir podon ko nazar aate hi hata kar tabah karte jayen.',
    ],
  },
  DS004: {
    name: 'Septoria Patten Ke Dhabay',
    symptoms: [
      'Nichlay paton par pehle kayi chhotay gol dhabay (2-3 mm) bante hain jin ke kinare ghelay aur markaz grey ya bhoora hota hai.',
      'Ghor se dekhein to dhabon ke markaz mein chhotay kaalay nuqte (fruiting bodies) nazar aate hain.',
      'Zyada dhabon wale patte peela, phir bhooray ho kar waqt se pehle gir jate hain.',
      'Gile mausam mein beemari ahista ahista poday par oopar ki taraf chadhti hai.',
    ],
    treatment: [
      'Phailao kam karne ke liye mutassir nichlay patte hata kar tabah kar dein.',
      'Septoria leaf spot ke liye munasib fungicide ka spray karein aur product ke label aur maqami zaraai mashveron ki hidayat par amal karein.',
      'Podon ke gird mulch bichhayen taake paani ke chintay mitti se spores ko paton tak na le jayen.',
    ],
    prevention: [
      'Podon ko saharein (stake/cage) aur acha faasla rakhein taake patte jaldi sookh jayen.',
      'Patta nahi balkay zameen paani dein, aur behtar hai subah ke waqt.',
      'Kataai ke baad tamatar ki baqiyat hata kar mitti mein dal dein aur kisi door ki fasal se rotation karein.',
      'Khet ke gird solanaceous ghaas-phoos (jaise nightshade) saaf karein, kyunke wo fungus ko bacha kar rakhti hai.',
    ],
  },
  DS005: {
    name: 'Bacterial Dhabay (Bacterial Spot)',
    symptoms: [
      'Paton par chhotay, ghelay, paani mein doobe hue se dhabay bante hain, aksar har dhabay ke gird peela halka hota hai.',
      'Phalon par dhabay thore ubhre hue, khurdre aur ghelay bhooray hote hain, aur darar bhi aa sakti hai.',
      'Beemari barhne par patton ke dhabay mil kar baray sookhay (bhooray) ilaqay bana lete hain.',
      'Zyada mutassir patte peela pad kar gir sakte hain aur poda kamzor ho jata hai.',
    ],
    treatment: [
      'Tambay (copper) par mabni bactericide ka spray karein aur product ke label aur maqami zaraai mashveron ki hidayat par amal karein (copper zyada tar phailao ko roakta hai, mutassir utarne ko theek nahi karta).',
      'Podon gile hon to un ke darmiyan kaam karne se guraez karein.',
      'Bacteria ka zariya kam karne ke liye zyada mutassir patte ya poday hata dein.',
    ],
    prevention: [
      'Certified, beemari se paak beej ya treatment-shuda napenain istemal karein.',
      'Podon ki jaron ke qareeb paani dein aur overhead sidhwai se guraez karein.',
      'Tamatar ki rotation kisi door ki fasal se karein — tamatar ke baad tamatar ya aloo na lagayen.',
      'Mausamon ke darmiyan auzaar aur sanware (stakes) disinfect karein aur kataai ke baad baqiyat hata dein.',
    ],
  },
  DS051: {
    name: 'Tandrust (Koi Beemari Nahi)',
    symptoms: ['Is tasveer mein poday par kisi beemari ki koi alaamat nazar nahi aa rahin.'],
    treatment: ['Koi ilaaj zaroori nahi. Achi ziraat-i-dekh bhaal jari rakhein.'],
    prevention: ['Har hafte fasal ka jaiza lein taake koi beemari shuruaati marhale mein pakri jaye.'],
  },
  DS006: {
    name: 'Ibtidaai Jhalasua (Early Blight)',
    symptoms: [
      'Nichlay puranay paton par pehle ghelay bhooray se kaalay, gol gol chalay wale (target-jaise) dhabay bante hain.',
      'Dhabon ke gird ka patta peela padta hai, aur bohat mutassir patte sookh kar mar jate hain.',
      'Munasib halaat mein beemari poday par oopar ki taraf barhti hai.',
      'Kandhon (tubers) ko paton ke zariye kam nuqsaan hota hai, magar patton ki kami se paidawar girti hai.',
    ],
    treatment: [
      'Mutassir patte/pattadar hissa hata kar tabah kar dein.',
      'Tambay (copper) par mabni fungicide ka spray karein aur product ke label aur maqami zaraai mashveron ki hidayat par amal karein.',
      'Podon ka acha faasla rakhein taake patte jaldi sookh jayen.',
    ],
    prevention: [
      'Aloo ki rotation kisi door ki fasal se karein; fungus purani baqiyat mein zinda rehta hai.',
      'Paani aur ghiza ki kami (water stress/deficiency) se bachain, is se poday zyada shikar hote hain.',
      'Jaron ke qareeb paani dein aur paton par lamba gilaapan na hone dein.',
      'Kataai ke baad fasal ki baqiyat hata dein ya mitti mein daba dein.',
    ],
  },
  DS007: {
    name: 'Deemeen Jhalasua (Late Blight)',
    symptoms: [
      'Paton par paani mein doobe hue se ghelay dhabay bante hain, aksar zakhm ke kinare par halka border hota hai.',
      'Gile halaat mein mutassir patton ke peethay par safed fungai ki ring nazar aati hai.',
      'Pattadar hissa tezi se gir/sookh jata hai; tanon par ghelay dhabay aa sakte hain.',
      'Kandhon (tubers) ki jild ke neeche surkh-bhoori sookhi saran (dry rot) banti hai, aur wo zameen mein ya godam mein sarrh sakte hain.',
    ],
    treatment: [
      'Mutassir podon ko foran tabah kar dein — unhein khaad (compost) mein na dalein.',
      'Gile ya barish ke mausam se pehle protectant fungicide ka spray karein aur product ke label aur maqami zaraai mashveron ki hidayat par amal karein.',
      'Mutassir podon se kandhe na katien aur na godam mein rakhein.',
    ],
    prevention: [
      'Certified, beemari-se-paak seed aloo istemal karein.',
      'Khud-ro (volunteer) aloo ke poday aur chhanan ke baad bachi huyi keerein tabah kar dein.',
      'Jaw (drainage) behtar karein aur aisa ghanaghana pattadar saaya na hone dein jo der tak gila rahe.',
      'Mutassir khet mein sirf tab kataaien jab pattadar hissa mukammal sookh gir chuka ho.',
    ],
  },
  DS052: {
    name: 'Tandrust (Koi Beemari Nahi)',
    symptoms: ['Is tasveer mein poday par kisi beemari ki koi alaamat nazar nahi aa rahin.'],
    treatment: ['Koi ilaaj zaroori nahi. Achi ziraat-i-dekh bhaal jari rakhein.'],
    prevention: ['Har hafte fasal ka jaiza lein taake koi beemari shuruaati marhale mein pakri jaye.'],
  },
  DS010: {
    name: 'Shumali Patta Jhalasua (Northern Leaf Blight)',
    symptoms: [
      'Paton par lambay (2-15 cm), sigar jaise grey-green se bhooray dhabay/zakhm bante hain.',
      'Zakhm patton ki ragon ke samantar chalte hain aur ahista ahista halkay bhooray ho jate hain.',
      'Gile mausam mein zakhmon ki satah par ghelay grey fungai aa sakti hai.',
      'Shadeed infection mein patte siray se sookhne lagte hain aur bhosla (ear) kam bharata hai.',
    ],
    treatment: [
      'Agar beemari shadeed ho aur phool-ke-baal (tasselling) se pehle aa rahi ho to fungicide ka spray karein aur product ke label aur maqami zaraai mashveron ki hidayat par amal karein.',
      'Jahan amli ho zyada mutassir nichlay patte hata dein.',
    ],
    prevention: [
      'Aap ke ilaqa ke liye munasib resistant hybrid kismen lagayen.',
      'Rotation karein aur purani makai ki baqiyat mitti mein dal dein ya hata dein, kyunke fungus wahin sara karne rehta hai (overwinter).',
      'Bohat zyada ghanai se pachai karne se bachain; saye mein hawa ki raah rakhein.',
      'Whorl (gonth) ki marhale se, khaas kar gile mausam ke baad, khet ki nadrist jari rakhein.',
    ],
  },
  DS011: {
    name: 'Aam Zang (Common Rust)',
    symptoms: [
      'Patton ki dono satahon par bikhre hue chhotay, gol se lambe surkh-bhooray phuhare (pustules/blisters) bante hain.',
      'Phuhare phat kar zang-rang ka powder (spores) chhorte hain jo haathon par lag jata hai.',
      'Zyada mutassir patte peela pad kar waqt se pehle sookh jate hain.',
      'Naujawan podon par shadeed infection tanay ki taqat aur bhoslay ka size kam kar sakta hai.',
    ],
    treatment: [
      'Fungicide ka spray sirf tab karein agar infection bohat ho aur poday naujawan hon (tasselling se pehle), product ke label aur maqami zaraai mashveron ki hidayat ke mutabiq.',
      'Pakode poday aam tor par zang bardasht kar lete hain aur paidawar kam girti hai — ho sakta hai spray safa-i-mahal sabit ho.',
    ],
    prevention: [
      'Rust-resistant hybrid kismen istemal karein.',
      'Munasib waqt par pachai karein taake naujawani ka marhala zang ke shadeed mausam se na milay.',
      'Zaroorat se zyada nitrogen (urvar) se bachain, is se naram aur shikar patta banta hai.',
      'Qareeb khud-ro makai ke poday aur ghaas-phoos hata dein.',
    ],
  },
  DS012: {
    name: 'Khakistari Patta Dhabay (Gray Leaf Spot)',
    symptoms: [
      'Nichlay paton par pehle chhotay bhooray dhabay aate hain, jo barh ay rectangular, bhooray se grey zakhm ban jate hain.',
      'Zakhm mukhya ragon se saaf kinare tak mehdood rete hain, jis se ek seedhi/ciocch (blocky) shakal banti hai.',
      'Aghar marhale mein zakhm mil kar patte ka bara hissa khatam kar sakte hain.',
      'Gile mausam mein beemari nichlay paton se oopar ki taraf barhti hai.',
    ],
    treatment: [
      'Agar zakhm bhoslay wale patte (ear leaf) ya us se oopar tasselling se pehle aa jayen to fungicide ka spray karein, product ke label aur maqami zaraai mashveron ki hidayat ke mutabiq.',
      'Waqt ahem hai — ek mawqe-o-muhall (well-timed) spray aam tor par der ke baar baar spray se zyada mufeed hota hai.',
    ],
    prevention: [
      'Resistant hybrid lagayen — yeh sab se qabil-e-aitmaad control hai.',
      'Makai ki aur fasalon se rotation karein aur kataai ke baad purani makai ki keeer mitti mein dal dein ya hata dein.',
      'Bohat zyada ghanaghana pachai se bachain jo nami ko rook le.',
      'Aisi sidhwai ki rukh-ba-rukh kam karein jo patton ko raat bhar gila rakhe.',
    ],
  },
  DS053: {
    name: 'Tandrust (Koi Beemari Nahi)',
    symptoms: ['Is tasveer mein poday par kisi beemari ki koi alaamat nazar nahi aa rahin.'],
    treatment: ['Koi ilaaj zaroori nahi. Achi ziraat-i-dekh bhaal jari rakhein.'],
    prevention: ['Har hafte fasal ka jaiza lein taake koi beemari shuruaati marhale mein pakri jaye.'],
  },
  DS039: {
    name: 'Citrus Greening (HLB)',
    symptoms: [
      'Paton par be-tarteeb, daag-daar peela pan (blotchy mottling) — rong-ood (midrib) ke dono taraf pattern mukhtalif hota hai.',
      'Peeli naujawan kaliyan aur kam, thuri huyi pattadar shaakhawan.',
      'Phal chhotay, tedhay-medhay, kadwe hote hain aur kuch haray hi rehte hain.',
      'Beej na-shuda ho jate hain, aur darakht chand saal tak bar-bar kamzor hota jata hai.',
    ],
    treatment: [
      'Is ka koi ilaaj nahi — bohat shadeed mutassir darakht hata kar tabah kar dein taake baqi baghcha mehfooz rahe.',
      'Psyllid (chhota keeda) ke wasila ko malzoos pesticide/oil spray se control karein, product ke label aur maqami zaraai mashveron ki hidayat ke mutabiq.',
      'Bare (mature) darakht hatane se pehle shakhti kas ke apne maqami zaraai extension office se tasdeeq karwayen.',
    ],
    prevention: [
      'Sirf certified, beemari-se-paak nursery ke paudon khareedain — kisi n-maaloom darakht se budwood na lein.',
      'Saal bhar naujawano (new flush) par psyllid control jari rakhein.',
      'Mutassir darakhton ko foran hata dein, kyunke wo baqi baghche ke liye zariya hain.',
      'Peelay sticky traps aur psyllid nadrist se nigrani karein.',
    ],
  },
  DS063: {
    name: 'Makri ka Tela (Two-Spotted Spider Mite)',
    symptoms: [
      'Paton par bohat barik peelay dhabay (stippling) nazar aate hain, jo pehle nichlay puranay paton par sab saaf zahir hotay hain.',
      'Paton ke peethay aur patta-tanon ke joaron par barik resham jaise jalay dikhai dete hain, khaas tor par shadeed hamlay mein.',
      'Zyada nuqsaan wale patte dhamsay bhooray ya grey-green ho jate hain, sukhey se lagte hain aur hare hi rehte hue gir jate hain.',
      'Garam, khuskh aur dhool bharay mausam mein nuqsaan sab tezi se phailta hai; telaay paton ke peethay guchhon mein baithte hain.',
    ],
    treatment: [
      'Mutassir paton ke peethay par zor daar paani ki dhaar marien taake telaay toot kar kam ho jayen; ye kuch din ke waqfay se dohrayen.',
      'Neem ke tel ya insecticidal soap ka spray subah ya sham ke waqt paton ki nicheeli satah par mukammal karein, product ke label ke mutabiq.',
      'Shadeed hamlay mein two-spotted spider mite ke liye tajweez karda miticide istemal karein aur miqdar kisi maqami zaraai mashwer ya dealer se zaroor tay karein; resistance se bachne ke liye adwiya badal badal kar lagayen.',
      'Podon ke gird jadibootiyan saaf rakhein kyunke wo telaayon ka panah-gah hain aur ilaaj ke baad dobara phailne ka zariya banti hain.',
    ],
    prevention: [
      'Fasal ko paani ki munasib farahami se tandrust rakhein; pyase aur dabao wale podon par hamla sab pehle aur sab zyada hota hai.',
      'Be-maqsad aur aam tor par istemal hone wale broad-spectrum keeday mar spray se guraez karein jo shikari keeron aur qudrati dushmanon ko mar dete hain.',
      'Garam khuskh mausam mein paton ke peethay baqaida check karein aur pehli phunk ya jaala nazar aate hi qadam uthayen.',
      'Khet ke gird kuch saaya aur nami paida rakhein; dhool bharay khulay maqamaton par telaayon ka phailaon asaan hota hai.',
    ],
  },
}

/**
 * Roman Urdu plant/crop names used to build the localized diagnosis heading
 * (kept separate from the disease name so the crop context is preserved).
 * Urdu crop names already ship in the upstream JSON (`p.name.ur`).
 */
const PLANT_ROM: Record<string, string> = {
  Tomato: 'Tamatar',
  Potato: 'Aloo',
  Maize: 'Makai',
  Citrus: 'Santra',
  Wheat: 'Gandum',
  Rice: 'Chawal',
  Cotton: 'Kapas',
  Chili: 'Mirch',
  Onion: 'Pyaaz',
  Mango: 'Aam',
  Guava: 'Amrood',
  Chickpea: 'Chana',
}

/** Crops the classifier labels use vs. Member 4's crop naming (Corn→Maize, Orange→Citrus). */
const PLANT_ALIASES: Record<string, string[]> = {
  Maize: ['corn', 'maize'],
  Citrus: ['citrus', 'orange'],
  Tomato: ['tomato'],
  Potato: ['potato', 'aloo'],
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

  const plant = cropKnowledgeData.plants.find(
    (p) =>
      p.name.en.toLowerCase() === cropLower ||
      p.name.en.toLowerCase().includes(cropLower) ||
      cropLower.includes(p.name.en.toLowerCase()),
  )
  if (!plant) return null

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
  const plants: PlantInfo[] = (cropKnowledge as any).plants.map((p: any) => {
    const cropEn = String(p.name?.en ?? '')
    return {
      plantId: p.plant_id,
      name: {
        en: cropEn,
        ur: p.name?.ur,
        rom: PLANT_ROM[cropEn],
      },
      diseases: (p.diseases || []).map((d: any) => {
        const id = d.disease_id as string
        const rom = ROMAN_URDU[id]
        return {
          diseaseId: id,
          name: { en: d.name?.en ?? '', ur: d.name?.ur, rom: rom?.name },
          description: { en: d.description?.en ?? '', ur: d.description?.ur },
          symptoms: { en: d.symptoms?.en ?? [], ur: d.symptoms?.ur, rom: rom?.symptoms },
          treatment: { en: d.treatment?.en ?? [], ur: d.treatment?.ur, rom: rom?.treatment },
          prevention: { en: d.prevention?.en ?? [], ur: d.prevention?.ur, rom: rom?.prevention },
          type: d.type ?? '',
          causalAgent: d.causal_agent ?? '',
        }
      }),
    }
  })

  const supportedCrops: CropTerm[] = plants.map((p) => ({
    english: p.name.en,
    urdu: p.name.ur,
    romanUrdu: p.name.rom,
  }))

  return {
    supportedCrops,
    tips: [],
    plants,
  }
}

const cropKnowledgeData = buildDataset()

export const agricultureData: AgricultureDataset = cropKnowledgeData

/** A localized diagnosis heading + its Symptoms/Treatment/Prevention bullets. */
export interface LocalizedDiseaseInfo {
  displayName: string
  symptoms: string[]
  treatment: string[]
  prevention: string[]
}

const NON_ALNUM = /[^a-z0-9 ]+/g

function tokenize(text: string): string[] {
  return text
    .replace(NON_ALNUM, ' ')
    .split(' ')
    .map((w) => w.trim())
    .filter(Boolean)
}

/** Disease label without a trailing parenthetical, lowercased, e.g. "citrus greening". */
function primaryLabel(name: string): string {
  return name
    .toLowerCase()
    .replace(/\(.*?\)/g, ' ')
    .replace(NON_ALNUM, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

/**
 * Score how well `disease` explains `diagLower` for `plant`.
 * Returns 0 when there is no meaningful match. Prefers crop-correct, more
 * specific matches so "Potato Early Blight" never resolves to Tomato's entry.
 */
function matchScore(
  plant: PlantInfo,
  disease: DiseaseInfo,
  diagLower: string,
): number {
  const diagTokens = new Set(tokenize(diagLower))

  // Crop match — the classifier label always names the crop ("Tomato ...").
  const cropTokens = PLANT_ALIASES[plant.name.en] ?? [plant.name.en.toLowerCase()]
  const cropHit = cropTokens.some((c) => diagLower.includes(c))

  // Disease match: exact substring, then full-token containment (handles word
  // reordering like "Corn Northern Leaf Blight" vs "Northern Corn Leaf Blight"),
  // then aliases. A "Healthy" diagnosis matches via the `healthy` alias token.
  const label = primaryLabel(disease.name.en).toLowerCase()
  const labelTokens = tokenize(label)
  const isHealthy = labelTokens.includes('healthy')

  let diseaseHit = 0
  if (label && diagLower.includes(label)) {
    diseaseHit = label.length
  } else if (labelTokens.length && labelTokens.every((t) => diagTokens.has(t))) {
    diseaseHit = labelTokens.join(' ').length
  }
  if (!diseaseHit) {
    for (const alias of ((disease as any).aliases ?? []) as string[]) {
      const a = String(alias).toLowerCase()
      if (a && diagLower.includes(a)) {
        diseaseHit = a.length
        break
      }
    }
  }
  // Healthy entries only match when the diagnosis itself says healthy.
  if (isHealthy && !diagTokens.has('healthy')) diseaseHit = 0

  if (!diseaseHit) return 0

  // Crop-correct, more-specific matches win; crop weight dominates.
  return diseaseHit + (cropHit ? 1000 : 0)
}

/**
 * Resolve a backend diagnosis label (e.g. "Tomato Late Blight") to Member 4's
 * localized Symptoms/Treatment/Prevention + a language-correct display name.
 *
 * `language` selects the arrays shown to the user:
 *   en → English · ur → Urdu script · rom → Roman Urdu.
 * When a translation is genuinely absent for a non-model disease, `rom` falls
 * back to English rather than fabricating Urdu text. Returns null when no
 * disease entry matches (never invents data).
 */
export function localizedDiseaseForDiagnosis(
  diagnosisText: string,
  language: string,
): LocalizedDiseaseInfo | null {
  const diagLower = (diagnosisText || '').toLowerCase().trim()
  if (!diagLower) return null

  let best: { plant: PlantInfo; disease: DiseaseInfo; score: number } | null = null
  for (const plant of cropKnowledgeData.plants) {
    for (const disease of plant.diseases) {
      const score = matchScore(plant, disease, diagLower)
      if (score > 0 && (!best || score > best.score)) {
        best = { plant, disease, score }
      }
    }
  }
  if (!best) return null

  const { plant, disease } = best

  const pickText = (t: LocalizedText): string => {
    if (language === 'ur') return t.ur || t.en
    if (language === 'rom') return t.rom || t.en
    return t.en
  }
  const pickList = (l: LocalizedList): string[] => {
    if (language === 'ur') return l.ur && l.ur.length ? l.ur : l.en
    if (language === 'rom') return l.rom && l.rom.length ? l.rom : l.en
    return l.en
  }

  // Localized diagnosis heading = crop + disease, in the selected language.
  // Skip the crop prefix when the localized disease name already starts with
  // it (avoids "مکئی مکئی کا ..." / "Citrus Citrus Greening").
  const diseaseName = pickText(disease.name)
  const plantName = pickText(plant.name)
  let displayName: string
  if (language === 'en') {
    displayName = diagnosisText
  } else {
    const plantFirst = plantName.split(/[\s(]/)[0]
    const needCrop = !plantFirst || !diseaseName.startsWith(plantFirst)
    displayName = (needCrop ? `${plantName} ` : '') + diseaseName
  }

  return {
    displayName,
    symptoms: pickList(disease.symptoms),
    treatment: pickList(disease.treatment),
    prevention: pickList(disease.prevention),
  }
}
