# Each topic exists in ONE language only.
# A cross-lingual question therefore has exactly one valid answer.
DOCS = {
    "leave_en":    "Employees are entitled to 21 days of paid annual leave per year. Unused leave may carry over for up to 6 months.",
    "probation_en":"New employees serve a probation period of 90 days, during which either party may terminate with 7 days notice.",
    "expense_en":  "Expense claims must be submitted within 30 days. Receipts are required for any amount above 100 SAR.",
    "laptop_en":   "All company laptops must use full disk encryption. Lost devices must be reported to IT within 2 hours.",
    "travel_en":   "Business travel requires manager approval 10 days in advance. Economy class is standard for flights under 6 hours.",
    "training_en": "Each employee receives an annual training budget of 8000 SAR, which does not carry over between years.",

    "remote_ar":   "يسمح بالعمل عن بعد بحد أقصى يومين أسبوعياً بعد موافقة المدير المباشر، ويقدم الطلب قبل ثمان وأربعين ساعة.",
    "eos_ar":      "تصرف مكافأة نهاية الخدمة بعد إتمام سنة كاملة في الشركة، وتحسب على أساس الراتب الأساسي الأخير.",
    "2fa_ar":      "التحقق بخطوتين إلزامي على جميع حسابات الشركة، ويمنع منعاً باتاً مشاركة كلمات المرور أو رموز التحقق.",
    "sick_ar":     "الإجازة المرضية مدفوعة الأجر لمدة ثلاثين يوماً، ويشترط تقديم تقرير طبي معتمد خلال ثلاثة أيام.",
    "overtime_ar": "يحتسب العمل الإضافي بمعدل ساعة ونصف عن كل ساعة، ويتطلب موافقة مسبقة من المدير المباشر.",
    "parking_ar":  "مواقف السيارات مخصصة للموظفين الدائمين فقط، ويصدر تصريح الموقف من إدارة المرافق خلال أسبوع.",
}

# Arabic questions -> English documents, and vice versa.
QUESTIONS = [
    ("كم عدد أيام الإجازة السنوية؟", "leave_en"),
    ("هل يمكن ترحيل رصيد الإجازة؟", "leave_en"),
    ("ما هي مدة فترة التجربة؟", "probation_en"),
    ("كم يوم إشعار مطلوب أثناء فترة التجربة؟", "probation_en"),
    ("متى يجب تقديم مطالبات المصاريف؟", "expense_en"),
    ("هل الفاتورة مطلوبة للمبالغ الصغيرة؟", "expense_en"),
    ("هل تشفير القرص إلزامي على الأجهزة؟", "laptop_en"),
    ("ماذا أفعل إذا فقدت جهاز العمل؟", "laptop_en"),
    ("كم يوم قبل السفر يجب أخذ الموافقة؟", "travel_en"),
    ("ما هي درجة السفر المعتمدة؟", "travel_en"),
    ("كم ميزانية التدريب السنوية؟", "training_en"),
    ("هل ترحل ميزانية التدريب للسنة القادمة؟", "training_en"),

    ("How many days can I work from home?", "remote_ar"),
    ("Do I need approval to work remotely?", "remote_ar"),
    ("When are end of service benefits paid?", "eos_ar"),
    ("How is end of service calculated?", "eos_ar"),
    ("Is two-factor authentication mandatory?", "2fa_ar"),
    ("Can I share my password with a colleague?", "2fa_ar"),
    ("How many paid sick days are there?", "sick_ar"),
    ("Do I need a medical report for sick leave?", "sick_ar"),
    ("How is overtime calculated?", "overtime_ar"),
    ("Do I need approval before working overtime?", "overtime_ar"),
    ("Who can use the parking spaces?", "parking_ar"),
    ("How long does a parking permit take?", "parking_ar"),
]
