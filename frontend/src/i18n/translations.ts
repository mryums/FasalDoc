export type Language = 'en' | 'ur' | 'rom'

export interface Translation {
  appName: string
  tagline: string

  nav: {
    newDiagnosis: string
    logout: string
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
    symptomsTitle: string
    treatmentTitle: string
    preventionTitle: string
    unknown: string
    moreInfo: string
    noMoreInfo: string
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

  auth: {
    loginTitle: string
    signupTitle: string
    email: string
    name: string
    password: string
    confirmPassword: string
    loginButton: string
    signupButton: string
    loggingIn: string
    signingUp: string
    noAccount: string
    hasAccount: string
    goSignup: string
    goLogin: string
    errors: {
      emailRequired: string
      nameRequired: string
      passwordRequired: string
      passwordShort: string
      passwordMismatch: string
      invalidEmail: string
      loginFailed: string
      signupFailed: string
    }
  }

  dashboard: {
    greeting: string
    subtitle: string
    uploadPhoto: string
    uploadDesc: string
    useCamera: string
    cameraDesc: string
    askQuestion: string
    askDesc: string
    voiceInput: string
    voiceDesc: string
    recentActivity: string
    noRecent: string
    startDiagnosis: string
  }

  camera: {
    title: string
    capture: string
    retake: string
    usePhoto: string
    cancel: string
    permissionDenied: string
    unsupported: string
    loading: string
  }

  voice: {
    listening: string
    stop: string
    speak: string
    transcript: string
    confirm: string
    cancel: string
    unsupported: string
    editHint: string
  }

  privacy: {
    notice: string
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

    nav: { newDiagnosis: 'New Diagnosis', logout: 'Logout' },

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
      languagesNote: 'You can write your question in English, Urdu, or Roman Urdu.',
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
      symptomsTitle: 'Symptoms',
      treatmentTitle: 'Treatment',
      preventionTitle: 'Prevention',
      unknown: 'Unknown',
      moreInfo: 'More Information from Crop Knowledge Base',
      noMoreInfo: 'No additional information available for this diagnosis.',
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

    auth: {
      loginTitle: 'Welcome Back',
      signupTitle: 'Create Account',
      email: 'Email',
      name: 'Full Name',
      password: 'Password',
      confirmPassword: 'Confirm Password',
      loginButton: 'Log In',
      signupButton: 'Sign Up',
      loggingIn: 'Logging in...',
      signingUp: 'Creating account...',
      noAccount: "Don't have an account?",
      hasAccount: 'Already have an account?',
      goSignup: 'Sign Up',
      goLogin: 'Log In',
      errors: {
        emailRequired: 'Please enter your email.',
        nameRequired: 'Please enter your name.',
        passwordRequired: 'Please enter your password.',
        passwordShort: 'Password must be at least 6 characters.',
        passwordMismatch: 'Passwords do not match.',
        invalidEmail: 'Please enter a valid email address.',
        loginFailed: 'Login failed. Please check your credentials.',
        signupFailed: 'Signup failed. Please try again.',
      },
    },

    dashboard: {
      greeting: 'Welcome back, {name}!',
      subtitle: 'What would you like to do today?',
      uploadPhoto: 'Upload Photo',
      uploadDesc: 'Choose a crop photo from your device for diagnosis.',
      useCamera: 'Use Camera',
      cameraDesc: 'Take a live photo of your crop for instant analysis.',
      askQuestion: 'Ask a Question',
      askDesc: 'Type or speak your agriculture question.',
      voiceInput: 'Voice Input',
      voiceDesc: 'Speak your question instead of typing.',
      recentActivity: 'Recent Activity',
      noRecent: 'No recent diagnoses. Start a new one!',
      startDiagnosis: 'Start New Diagnosis',
    },

    camera: {
      title: 'Camera',
      capture: 'Capture',
      retake: 'Retake',
      usePhoto: 'Use Photo',
      cancel: 'Cancel',
      permissionDenied: 'Camera permission was denied. Please allow camera access in your browser settings.',
      unsupported: 'Your browser does not support live camera. Please use the photo upload option instead.',
      loading: 'Starting camera...',
    },

    voice: {
      listening: 'Listening...',
      stop: 'Stop',
      speak: 'Tap the microphone and speak',
      transcript: 'What we heard:',
      confirm: 'Use This Text',
      cancel: 'Cancel',
      unsupported: 'Voice input is not supported in this browser. Please type your question instead.',
      editHint: 'You can edit the text above before confirming.',
    },

    privacy: {
      notice: 'Your uploaded images, voice input, and questions are processed by FasalDoc\'s AI service to provide crop diagnosis and recommendations.',
    },
  },

  ur: {
    appName: 'فصل ڈاکٹر',
    tagline: 'اپنی فصل کو پہچانیں، اپنی پیداوار بچائیں۔',

    nav: { newDiagnosis: 'نئی جانچ', logout: 'لاگ آؤٹ' },

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
      symptomsTitle: 'علامات',
      treatmentTitle: 'علاج',
      preventionTitle: 'بچاؤ',
      unknown: 'نامعلوم',
      moreInfo: 'فصل علم کے ذخیرے سے مزید معلومات',
      noMoreInfo: 'اس تشخیص کے لیے مزید معلومات دستیاب نہیں ہیں۔',
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

    auth: {
      loginTitle: 'خوش آمدید',
      signupTitle: 'اکاؤنٹ بنائیں',
      email: 'ای میل',
      name: 'پورا نام',
      password: 'پاس ورڈ',
      confirmPassword: 'پاس ورڈ کی تصدیق',
      loginButton: 'لاگ ان',
      signupButton: 'سائن اپ',
      loggingIn: 'لاگ ان ہو رہا ہے...',
      signingUp: 'اکاؤنٹ بنایا جا رہا ہے...',
      noAccount: 'اکاؤنٹ نہیں ہے؟',
      hasAccount: 'پہلے سے اکاؤنٹ ہے؟',
      goSignup: 'سائن اپ کریں',
      goLogin: 'لاگ ان کریں',
      errors: {
        emailRequired: 'براہ کرم اپنا ای میل درج کریں۔',
        nameRequired: 'براہ کرم اپنا نام درج کریں۔',
        passwordRequired: 'براہ کرم اپنا پاس ورڈ درج کریں۔',
        passwordShort: 'پاس ورڈ کم از کم 6 حروف کا ہونا چاہیے۔',
        passwordMismatch: 'پاس ورڈ میچ نہیں کرتے۔',
        invalidEmail: 'براہ کرم درست ای میل ایڈریس درج کریں۔',
        loginFailed: 'لاگ ان ناکام۔ براہ کرم اپنی تفصیلات چیک کریں۔',
        signupFailed: 'سائن اپ ناکام۔ براہ کرم دوبارہ کوشش کریں۔',
      },
    },

    dashboard: {
      greeting: 'خوش آمدید، {name}!',
      subtitle: 'آج آپ کیا کرنا چاہیں گے؟',
      uploadPhoto: 'تصویر اپ لوڈ کریں',
      uploadDesc: 'تشخیص کے لیے اپنے آلے سے فصل کی تصویر منتخب کریں۔',
      useCamera: 'کیمرہ استعمال کریں',
      cameraDesc: 'فوری تجزیے کے لیے اپنی فصل کی براہ راست تصویر لیں۔',
      askQuestion: 'سوال پوچھیں',
      askDesc: 'اپنا زرعی سوال ٹائپ کریں یا بولیں۔',
      voiceInput: 'آواز سے ان پٹ',
      voiceDesc: 'ٹائپ کرنے کے بجائے اپنا سوال بولیں۔',
      recentActivity: 'حالیہ سرگرمی',
      noRecent: 'کوئی حالیہ تشخیص نہیں۔ نئی شروع کریں!',
      startDiagnosis: 'نئی تشخیص شروع کریں',
    },

    camera: {
      title: 'کیمرہ',
      capture: 'تصویر لیں',
      retake: 'دوبارہ لیں',
      usePhoto: 'یہ تصویر استعمال کریں',
      cancel: 'منسوخ کریں',
      permissionDenied: 'کیمرے کی اجازت نہیں دی گئی۔ براہ کرم اپنے براؤزر کی سیٹنگز میں کیمرے کی رسائی کی اجازت دیں۔',
      unsupported: 'آپ کا براؤزر لائیو کیمرے کو سپورٹ نہیں کرتا۔ براہ کرم تصویر اپ لوڈ کا آپشن استعمال کریں۔',
      loading: 'کیمرہ شروع ہو رہا ہے...',
    },

    voice: {
      listening: 'سن رہا ہے...',
      stop: 'رکیں',
      speak: 'مائیکروفون ٹیپ کریں اور بولیں',
      transcript: 'جو ہم نے سنا:',
      confirm: 'یہ متن استعمال کریں',
      cancel: 'منسوخ کریں',
      unsupported: 'اس براؤزر میں آواز سے ان پٹ سپورٹ نہیں ہے۔ براہ کرم اپنا سوال ٹائپ کریں۔',
      editHint: 'تصدیق سے پہلے آپ اوپر کا متن تبدیل کر سکتے ہیں۔',
    },

    privacy: {
      notice: 'آپ کی اپ لوڈ کردہ تصاویر، آواز کا ان پٹ اور سوالات فصل ڈاکٹر کی اے آئی سروس کے ذریعے فصل کی تشخیص اور سفارشات فراہم کرنے کے لیے پروسیس کیے جاتے ہیں۔',
    },
  },

  rom: {
    appName: 'FasalDoc',
    tagline: 'Apni fasal ko pehchanain, apni paidawar bachayen.',

    nav: { newDiagnosis: 'Nayi Jaanch', logout: 'Logout' },

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
      symptomsTitle: 'Alamaat',
      treatmentTitle: 'Ilaj',
      preventionTitle: 'Bachao',
      unknown: 'Naamum',
      moreInfo: 'Fasal ilm ke zakhire se mazeed maloomat',
      noMoreInfo: 'Is tashkhees ke liye mazeed maloomat dastiyab nahi hain.',
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

    auth: {
      loginTitle: 'Khush Aamdeed',
      signupTitle: 'Account Banayen',
      email: 'Email',
      name: 'Pura Naam',
      password: 'Password',
      confirmPassword: 'Password Ki Tasdeeq',
      loginButton: 'Log In',
      signupButton: 'Sign Up',
      loggingIn: 'Log in ho raha hai...',
      signingUp: 'Account banaya ja raha hai...',
      noAccount: 'Account nahi hai?',
      hasAccount: 'Pehle se account hai?',
      goSignup: 'Sign Up Karein',
      goLogin: 'Log In Karein',
      errors: {
        emailRequired: 'Barah-e-karam apna email darj karein.',
        nameRequired: 'Barah-e-karam apna naam darj karein.',
        passwordRequired: 'Barah-e-karam apna password darj karein.',
        passwordShort: 'Password kam az kam 6 haroof ka hona chahiye.',
        passwordMismatch: 'Password match nahi karte.',
        invalidEmail: 'Barah-e-karam durust email address darj karein.',
        loginFailed: 'Login nakaam. Barah-e-karam apni tafseelat check karein.',
        signupFailed: 'Sign up nakaam. Barah-e-karam dobara koshish karein.',
      },
    },

    dashboard: {
      greeting: 'Khush aamdeed, {name}!',
      subtitle: 'Aaj aap kya karna chahein ge?',
      uploadPhoto: 'Tasveer Upload Karein',
      uploadDesc: 'Tashkhees ke liye apne aalay se fasal ki tasveer select karein.',
      useCamera: 'Camera Istemal Karein',
      cameraDesc: 'Fori tajziye ke liye apni fasal ki live tasveer lein.',
      askQuestion: 'Sawal Poochein',
      askDesc: 'Apna zarai sawal type karein ya boleyn.',
      voiceInput: 'Aawaz Se Input',
      voiceDesc: 'Type karne ke bajaye apna sawal boleyn.',
      recentActivity: 'Haaliya Sargarmi',
      noRecent: 'Koi haaliya tashkhees nahi. Nayi shuru karein!',
      startDiagnosis: 'Nayi Tashkhees Shuru Karein',
    },

    camera: {
      title: 'Camera',
      capture: 'Tasveer Lein',
      retake: 'Dobara Lein',
      usePhoto: 'Yeh Tasveer Istemal Karein',
      cancel: 'Mansoogh Karein',
      permissionDenied: 'Camera ki ijazat nahi di gayi. Barah-e-karam apne browser ki settings mein camera ki rasai ki ijazat dain.',
      unsupported: 'Aap ka browser live camera ko support nahi karta. Barah-e-karam tasveer upload ka option istemal karein.',
      loading: 'Camera shuru ho raha hai...',
    },

    voice: {
      listening: 'Sun raha hai...',
      stop: 'Rukein',
      speak: 'Microphone tap karein aur boleyn',
      transcript: 'Jo hum ne suna:',
      confirm: 'Yeh Matn Istemal Karein',
      cancel: 'Mansoogh Karein',
      unsupported: 'Is browser mein aawaz se input support nahi hai. Barah-e-karam apna sawal type karein.',
      editHint: 'Tasdeeq se pehle aap oopar ka matn tabdeel kar sakte hain.',
    },

    privacy: {
      notice: 'Aap ki upload ki gayi tasweerein, aawaz ka input aur sawalaat FasalDoc ki AI service ke zariye fasal ki tashkhees aur tajaweez faraham karne ke liye process kiye jate hain.',
    },
  },
}
