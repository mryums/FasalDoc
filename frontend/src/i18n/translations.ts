export type Language = 'en' | 'ur' | 'rom'

export interface Translation {
  appName: string
  tagline: string

  nav: {
    newDiagnosis: string
  }

  home: {
    headline: string
    subtext: string
    step1Title: string
    step1Text: string
    step2Title: string
    step2Text: string
    step3Title: string
    step3Text: string
    cta: string
    languagesNote: string
  }

  upload: {
    title: string
    subtitle: string
    dropPhoto: string
    choosePhoto: string
    useCamera: string
    changePhoto: string
    removePhoto: string
    formatsNote: string
    questionLabel: string
    questionPlaceholder: string
    questionHelp: string
    diagnose: string
    diagnosing: string
    micComingSoon: string
    errors: {
      noImage: string
      invalidType: string
      tooLarge: string
    }
  }

  analyzing: {
    title: string
    messages: [string, string, string]
    note: string
  }

  result: {
    title: string
    possibleProblem: string
    confidenceLabel: string
    confidenceHigh: string
    confidenceMedium: string
    confidenceLow: string
    lowConfidenceAdvice: string
    adviceTitle: string
    needsExpert: string
    followupCta: string
    newDiagnosis: string
    imageLabel: string
  }

  followup: {
    title: string
    aboutLabel: string
    placeholder: string
    send: string
    sending: string
    greeting: string
  }

  errors: {
    network: string
    server: string
    validationPrefix: string
    retry: string
  }

  footer: {
    disclaimer: string
    builtFor: string
  }
}

export const translations: Record<Language, Translation> = {
  en: {
    appName: 'FasalDoc',
    tagline: 'Understand Your Crop. Protect Your Harvest.',

    nav: { newDiagnosis: 'New Diagnosis' },

    home: {
      headline: 'Understand Your Crop. Protect Your Harvest.',
      subtext:
        'Upload a photo of your plant and FasalDoc will help identify visible crop problems and suggest the next step.',
      step1Title: 'Upload a photo',
      step1Text: 'Take or choose a clear photo of the affected plant.',
      step2Title: 'Get AI diagnosis',
      step2Text: 'FasalDoc checks the photo for visible symptoms.',
      step3Title: 'Receive advice',
      step3Text: 'Get an understandable result and a recommended action.',
      cta: 'Check My Crop',
      languagesNote: 'You can write your question in English, اردو, or Roman Urdu.',
    },

    upload: {
      title: 'Photo of Your Crop',
      subtitle: 'A clear, close photo of the affected part works best.',
      dropPhoto: 'Tap to choose a crop photo',
      choosePhoto: 'Choose Photo',
      useCamera: 'Use Camera',
      changePhoto: 'Change',
      removePhoto: 'Remove',
      formatsNote: 'JPEG, PNG or WEBP — up to 10 MB',
      questionLabel: 'Describe the problem (optional)',
      questionPlaceholder: 'Describe what you noticed about your crop...',
      questionHelp: 'English, Urdu, or Roman Urdu — all are fine.',
      diagnose: 'Diagnose Crop',
      diagnosing: 'Diagnosing...',
      micComingSoon: 'Voice input (coming soon)',
      errors: {
        noImage: 'Please upload a crop image first.',
        invalidType: 'Only JPEG, PNG, and WEBP images are allowed.',
        tooLarge: 'Image must be smaller than 10 MB.',
      },
    },

    analyzing: {
      title: 'Analyzing your crop...',
      messages: [
        'Analyzing your crop photo...',
        'Checking visible symptoms...',
        'Preparing recommendations...',
      ],
      note: 'This usually takes only a few seconds.',
    },

    result: {
      title: 'Diagnosis Result',
      possibleProblem: 'Possible Problem',
      confidenceLabel: 'Confidence',
      confidenceHigh: 'FasalDoc is fairly confident based on the uploaded image.',
      confidenceMedium: 'FasalDoc is somewhat sure, but not fully certain.',
      confidenceLow: 'AI is not fully confident. Consider providing a clearer image or additional information.',
      lowConfidenceAdvice:
        'A closer, well-lit photo of the affected leaves or stems can improve the result.',
      adviceTitle: 'Recommended Action',
      needsExpert:
        'This problem may need expert attention. Please also contact your local agriculture office or extension worker.',
      followupCta: 'Ask FasalDoc a Question',
      newDiagnosis: 'New Diagnosis',
      imageLabel: 'Your crop photo',
    },

    followup: {
      title: 'Ask FasalDoc',
      aboutLabel: 'About this diagnosis',
      placeholder: 'Ask about this problem... e.g. "Is this dangerous for my crop?"',
      send: 'Send',
      sending: 'Sending...',
      greeting:
        'Ask anything about the diagnosis above — what it means, what to do next, or how to protect the rest of your crop.',
    },

    errors: {
      network: 'Unable to connect to FasalDoc. Please check your internet connection and try again.',
      server: 'Something went wrong while analyzing your crop. Please try again.',
      validationPrefix: 'FasalDoc could not accept the request:',
      retry: 'Try Again',
    },

    footer: {
      disclaimer:
        'FasalDoc gives guidance based on the photo you share. For serious crop problems, always consult your local agriculture office.',
      builtFor: 'Built for farmers of Pakistan',
    },
  },

  ur: {
    appName: 'فصل ڈاکٹر',
    tagline: 'اپنی فصل کو پہچانیں، اپنی پیداوار بچائیں۔',

    nav: { newDiagnosis: 'نئی جانچ' },

    home: {
      headline: 'اپنی فصل کو پہچانیں، اپنی پیداوار بچائیں۔',
      subtext:
        'اپنے پودے کی تصویر اپ لوڈ کریں اور فصل ڈاکٹر مرئی مسائل کی شناخت اور اگلا قدم بتانے میں مدد کرے گا۔',
      step1Title: 'تصویر اپ لوڈ کریں',
      step1Text: 'متاثرہ پودے کی صاف تصویر لیں یا منتخب کریں۔',
      step2Title: 'اے آئی جائزہ',
      step2Text: 'فصل ڈاکٹر تصویر میں نظر آنے والی علامات چیک کرتا ہے۔',
      step3Title: 'مشورہ پائیں',
      step3Text: 'آسان زبان میں نتیجہ اور تجویز شدہ اقدام حاصل کریں۔',
      cta: 'میری فصل کی جانچ کریں',
      languagesNote: 'آپ اپنا سوال انگریزی، اردو یا رومن اردو میں لکھ سکتے ہیں۔',
    },

    upload: {
      title: 'اپنی فصل کی تصویر',
      subtitle: 'متاثرہ حصے کی قریب سے صاف تصویر سب سے بہتر ہے۔',
      dropPhoto: 'فصل کی تصویر منتخب کرنے کے لیے ٹچ کریں',
      choosePhoto: 'تصویر منتخب کریں',
      useCamera: 'کیمرہ استعمال کریں',
      changePhoto: 'تبدیل کریں',
      removePhoto: 'ہٹائیں',
      formatsNote: 'JPEG، PNG یا WEBP — زیادہ سے زیادہ 10 MB',
      questionLabel: 'مسئلے کی تفصیل لکھیں (اختیاری)',
      questionPlaceholder: 'بتائیں کہ آپ نے اپنی فصل میں کیا دیکھا...',
      questionHelp: 'انگریزی، اردو یا رومن اردو — سب چلے گا۔',
      diagnose: 'فصل کی جانچ کریں',
      diagnosing: 'جانچ ہو رہی ہے...',
      micComingSoon: 'آواز سے سوال (جلد آ رہا ہے)',
      errors: {
        noImage: 'براہ کرم پہلے فصل کی تصویر اپ لوڈ کریں۔',
        invalidType: 'صرف JPEG، PNG اور WEBP تصاویر قبول کی جاتی ہیں۔',
        tooLarge: 'تصویر 10 MB سے چھوٹی ہونی چاہیے۔',
      },
    },

    analyzing: {
      title: 'آپ کی فصل کا جائزہ لیا جا رہا ہے...',
      messages: [
        'آپ کی فصل کی تصویر کا جائزہ لیا جا رہا ہے...',
        'نظر آنے والی علامات چیک کی جا رہی ہیں...',
        'ہدایات تیار کی جا رہی ہیں...',
      ],
      note: 'اس میں عام طور پر صرف چند سیکنڈ لگتے ہیں۔',
    },

    result: {
      title: 'جانچ کا نتیجہ',
      possibleProblem: 'ممکنہ مسئلہ',
      confidenceLabel: 'یقین کی سطح',
      confidenceHigh: 'فصل ڈاکٹر اپ لوڈ کردہ تصویر کی بنیاد پر کافی پراعتماد ہے۔',
      confidenceMedium: 'فصل ڈاکٹر کچھ حد تک پراعتماد ہے، مگر مکمل طور پر یقینی نہیں۔',
      confidenceLow: 'اے آئی مکمل طور پر پراعتماد نہیں ہے۔ بہتر ہے کہ واضح تصویر یا مزید معلومات دیں۔',
      lowConfidenceAdvice:
        'متاثرہ پتوں یا تنوں کی قریب سے، روشنی میں لی گئی تصویر نتیجہ بہتر کر سکتی ہے۔',
      adviceTitle: 'تجویز کردہ اقدام',
      needsExpert:
        'یہ مسئلہ ماہرانہ توجہ کا متقاضا ہو سکتا ہے۔ براہ کرم اپنے قریبی زراعت کے دفتر سے بھی رابطہ کریں۔',
      followupCta: 'فصل ڈاکٹر سے سوال پوچھیں',
      newDiagnosis: 'نئی جانچ',
      imageLabel: 'آپ کی فصل کی تصویر',
    },

    followup: {
      title: 'فصل ڈاکٹر سے پوچھیں',
      aboutLabel: 'اس جانچ کے بارے میں',
      placeholder: 'اس مسئلے کے بارے میں پوچھیں... مثلاً "کیا یہ میری فصل کے لیے خطرناک ہے؟"',
      send: 'بھیجیں',
      sending: 'بھیجا جا رہا ہے...',
      greeting:
        'اوپر دیے گئے نتیجے کے بارے میں کچھ بھی پوچھیں — اس کا مطلب، اگلا قدم، یا باقی فصل کی حفاظت۔',
    },

    errors: {
      network: 'فصل ڈاکٹر سے رابطہ نہیں ہو سکا۔ براہ کرم اپنا انٹرنیٹ کنکشن چیک کریں اور دوبارہ کوشش کریں۔',
      server: 'آپ کی فصل کا جائزہ لیتے ہوئے کچھ غلط ہو گیا۔ براہ کرم دوبارہ کوشش کریں۔',
      validationPrefix: 'فصل ڈاکٹر درخواست قبول نہیں کر سکا:',
      retry: 'دوبارہ کوشش کریں',
    },

    footer: {
      disclaimer:
        'فصل ڈاکٹر آپ کی بھیجی گئی تصویر کی بنیاد پر رہنمائی دیتا ہے۔ سنگین مسائل کے لیے ہمیشہ اپنے قریبی زراعت کے دفتر سے مشورہ کریں۔',
      builtFor: 'پاکستان کے کسانوں کے لیے بنایا گیا',
    },
  },

  rom: {
    appName: 'FasalDoc',
    tagline: 'Apni fasal ko pehchanain, apni paidawar bachayen.',

    nav: { newDiagnosis: 'Nayi Jaanch' },

    home: {
      headline: 'Apni fasal ko pehchanain, apni paidawar bachayen.',
      subtext:
        'Apne pauday ki tasveer upload karein — FasalDoc nazar aanay walay masail ki pehchan aur agla qadam batanay mein madad karega.',
      step1Title: 'Tasveer upload karein',
      step1Text: 'Mutassira pauday ki saaf tasveer lein ya select karein.',
      step2Title: 'AI jaanch',
      step2Text: 'FasalDoc tasveer mein nazar aanay wali alaamat check karta hai.',
      step3Title: 'Mashwara payen',
      step3Text: 'Aasan zaban mein nateeja aur tajveez milegi.',
      cta: 'Meri Fasal Ki Jaanch Karein',
      languagesNote: 'Aap apna sawal English, Urdu ya Roman Urdu mein likh saktay hain.',
    },

    upload: {
      title: 'Apni Fasal Ki Tasveer',
      subtitle: 'Mutassira hissay ki qareeb se saaf tasveer sab se behtar hai.',
      dropPhoto: 'Fasal ki tasveer select karnay ke liye tap karein',
      choosePhoto: 'Tasveer Select Karein',
      useCamera: 'Camera Istemal Karein',
      changePhoto: 'Tabdeel Karein',
      removePhoto: 'Hatayen',
      formatsNote: 'JPEG, PNG ya WEBP — zyada se zyada 10 MB',
      questionLabel: 'Maslay ki tafseel likhain (ikhtiyari)',
      questionPlaceholder: 'Batayen ke aap ne apni fasal mein kya dekha...',
      questionHelp: 'English, Urdu ya Roman Urdu — sab chalay ga.',
      diagnose: 'Fasal Ki Jaanch Karein',
      diagnosing: 'Jaanch ho rahi hai...',
      micComingSoon: 'Awaaz se sawal (jald aa raha hai)',
      errors: {
        noImage: 'Barah-e-karam pehle fasal ki tasveer upload karein.',
        invalidType: 'Sirf JPEG, PNG aur WEBP tasweerein qabool ki jati hain.',
        tooLarge: 'Tasveer 10 MB se chhoti honi chahiye.',
      },
    },

    analyzing: {
      title: 'Aap ki fasal ka jaiza liya ja raha hai...',
      messages: [
        'Aap ki fasal ki tasveer ka jaiza liya ja raha hai...',
        'Nazar aanay wali alaamat check ki ja rahi hain...',
        'Hidayaat tayyar ki ja rahi hain...',
      ],
      note: 'Is mein aam tor par sirf chand second lagte hain.',
    },

    result: {
      title: 'Jaanch Ka Nateeja',
      possibleProblem: 'Mumkina Masla',
      confidenceLabel: 'Yaqeen Ki Satah',
      confidenceHigh: 'FasalDoc upload ki gayi tasveer ki bunyad par kafi pur-aitmaad hai.',
      confidenceMedium: 'FasalDoc kuch had tak pur-aitmaad hai, magar mukammal tor par yaqini nahi.',
      confidenceLow: 'AI mukammal tor par pur-aitmaad nahi hai. Behtar tasveer ya mazeed maloomat dain.',
      lowConfidenceAdvice:
        'Mutassira patton ya tanon ki qareeb se, roshni mein li gayi tasveer nateeja behtar kar sakti hai.',
      adviceTitle: 'Tajveez Karda Qadam',
      needsExpert:
        'Yeh masla mahiranah tawajjuh ka mutaqazi ho sakta hai. Barah-e-karam apne qareebi zarayat ke daftar se bhi rabta karein.',
      followupCta: 'FasalDoc Se Sawal Poochein',
      newDiagnosis: 'Nayi Jaanch',
      imageLabel: 'Aap ki fasal ki tasveer',
    },

    followup: {
      title: 'FasalDoc Se Poochein',
      aboutLabel: 'Is jaanch ke baray mein',
      placeholder: 'Is maslay ke baray mein poochein... masalan "Kya yeh meri fasal ke liye khatarnak hai?"',
      send: 'Bhejain',
      sending: 'Bheja ja raha hai...',
      greeting:
        'Oopar diye gaye natijay ke baray mein kuch bhi poochein — us ka matlab, agla qadam, ya baqi fasal ki hifazat.',
    },

    errors: {
      network: 'FasalDoc se rabta nahi ho saka. Barah-e-karam apna internet connection check karein aur dobara koshish karein.',
      server: 'Aap ki fasal ka jaiza letay hue kuch ghalat ho gaya. Barah-e-karam dobara koshish karein.',
      validationPrefix: 'FasalDoc darkhwast qabool nahi kar saka:',
      retry: 'Dobara Koshish Karein',
    },

    footer: {
      disclaimer:
        'FasalDoc aap ki bheji gayi tasveer ki bunyad par rehnumai deta hai. Sanjeeda masail ke liye hamesha apne qareebi zarayat ke daftar se mashwara karein.',
      builtFor: 'Pakistan ke kisanon ke liye banaya gaya',
    },
  },
}
