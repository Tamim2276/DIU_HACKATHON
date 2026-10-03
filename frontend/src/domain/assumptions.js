// What the synthetic data assumes, in short, in both languages. The full list is in docs/SYNTHETIC_DATA.md.
// These are written here by hand: if the generator changes, change them too.

export const DATA_NOTES_URL = "https://github.com/Tamim2276/DIU_HACKATHON/blob/main/docs/SYNTHETIC_DATA.md";

// How each kind of customer earns in the data. The key is the persona's id in the API.
export const INCOME = {
  en: {
    rider: "A payout of about ৳900 on a working day. Works on 87% of days.",
    garment: "One salary of about ৳16,500 around the 8th, late in a quarter of months.",
    student: "An allowance of about ৳11,000 around the 3rd. Some also earn from tutoring.",
    shopkeeper: "Sales of about ৳3,400 on a working day, as several customer payments.",
    freelancer: "About two payments a month of roughly ৳15,000 each, on random days.",
  },
  bn: {
    rider: "কাজের দিনে প্রায় ৳৯০০ আয়। ৮৭% দিনে কাজ করেন।",
    garment: "মাসের ৮ তারিখের দিকে প্রায় ৳১৬,৫০০ বেতন; চার মাসে এক মাস দেরিতে আসে।",
    student: "মাসের ৩ তারিখের দিকে প্রায় ৳১১,০০০ হাতখরচ। কেউ কেউ টিউশনি থেকেও আয় করেন।",
    shopkeeper: "কাজের দিনে প্রায় ৳৩,৪০০ বিক্রি, কয়েকজন ক্রেতার পেমেন্ট মিলিয়ে।",
    freelancer: "মাসে প্রায় দুটি পেমেন্ট, প্রতিটি কমবেশি ৳১৫,০০০, যেকোনো দিনে।",
  },
};

export const ASSUMPTIONS = {
  en: [
    "300 customers, 60 of each kind, from 1 October 2025 to 30 September 2026. A program generated every transaction; no real customer data was used.",
    "Each customer has their own income size, spending habits and payment dates, drawn at random once.",
    "Regular payments are made before daily spending. A payment the wallet cannot cover is paid late, or in part.",
    "People spend more right after income arrives, on Fridays and Saturdays, and in the ten days before Eid.",
    "Each day carries a small chance of an unplanned expense of ৳1,500 to ৳6,000. Nobody, including the model, can predict these.",
    "The cash-out fee is assumed to be 1.4%. It is not upay's official charge.",
  ],
  bn: [
    "৩০০ জন গ্রাহক, প্রতি ধরনের ৬০ জন করে, ১ অক্টোবর ২০২৫ থেকে ৩০ সেপ্টেম্বর ২০২৬ পর্যন্ত। প্রতিটি লেনদেন একটি প্রোগ্রাম তৈরি করেছে; কোনো আসল গ্রাহকের ডেটা ব্যবহার করা হয়নি।",
    "প্রত্যেক গ্রাহকের আয়ের পরিমাণ, খরচের অভ্যাস ও পেমেন্টের তারিখ আলাদা, যা একবারই দৈবভাবে ঠিক করা।",
    "নিয়মিত পেমেন্ট দৈনন্দিন খরচের আগে দেওয়া হয়। ওয়ালেটে টাকা না থাকলে পেমেন্ট দেরিতে বা আংশিক দেওয়া হয়।",
    "আয় আসার ঠিক পরে, শুক্র ও শনিবারে, আর ঈদের আগের দশ দিনে মানুষ বেশি খরচ করে।",
    "প্রতিদিন সামান্য সম্ভাবনা থাকে ৳১,৫০০ থেকে ৳৬,০০০-এর একটি অপ্রত্যাশিত খরচের। মডেলসহ কেউই এটি আগে থেকে জানতে পারে না।",
    "ক্যাশ আউটের চার্জ ১.৪% ধরা হয়েছে। এটি upay-এর অফিসিয়াল চার্জ নয়।",
  ],
};

export const LIMITS = {
  en: [
    "The amounts and probabilities are guesses chosen to look plausible. They were not fitted to real data.",
    "Real customers are more varied than five kinds with equal numbers.",
    "A model that works on this data has only been shown to recover patterns that were put in. It still has to be tested on real, governed data.",
    "The warning looks only at the forecast balance. A customer who pays a bill late keeps a higher balance, so a missed payment does not always raise a warning.",
  ],
  bn: [
    "পরিমাণ ও সম্ভাবনাগুলো অনুমান করে বসানো, যাতে বাস্তবসম্মত দেখায়। আসল ডেটার সঙ্গে মিলিয়ে ঠিক করা হয়নি।",
    "আসল গ্রাহকেরা সমান সংখ্যার পাঁচ ধরনের চেয়ে অনেক বেশি বৈচিত্র্যময়।",
    "এই ডেটায় কাজ করা মডেল শুধু এটুকু দেখায় যে, যে ধরনগুলো আমরা রেখেছি সেগুলো সে ধরতে পারে। আসল, নিয়ন্ত্রিত ডেটায় একে এখনো পরীক্ষা করতে হবে।",
    "সতর্কতা শুধু পূর্বাভাসের ব্যালেন্স দেখে। যে গ্রাহক বিল দেরিতে দেন তার ব্যালেন্স বেশি থাকে, তাই পেমেন্ট বাদ পড়লেও সব সময় সতর্কতা আসে না।",
  ],
};
