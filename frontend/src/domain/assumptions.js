// What the synthetic data assumes, in short. The full list is in docs/SYNTHETIC_DATA.md.
// These are written here by hand: if the generator changes, change them too.

export const DATA_NOTES_URL = "https://github.com/Tamim2276/DIU_HACKATHON/blob/main/docs/SYNTHETIC_DATA.md";

export const PERSONAS = [
  { name: "Ride-share rider", income: "A payout of about ৳900 on a working day. Works on 87% of days." },
  { name: "Garment worker", income: "One salary of about ৳16,500 around the 8th, late in a quarter of months." },
  { name: "University student", income: "An allowance of about ৳11,000 around the 3rd. Some also earn from tutoring." },
  { name: "Small shop owner", income: "Sales of about ৳3,400 on a working day, as several customer payments." },
  { name: "Freelancer", income: "About two payments a month of roughly ৳15,000 each, on random days." },
];

export const ASSUMPTIONS = [
  "300 customers, 60 of each kind, from 1 October 2025 to 30 September 2026. A program generated every transaction; no real customer data was used.",
  "Each customer has their own income size, spending habits and payment dates, drawn at random once.",
  "Regular payments are made before daily spending. A payment the wallet cannot cover is paid late, or in part.",
  "People spend more right after income arrives, on Fridays and Saturdays, and in the ten days before Eid.",
  "Each day carries a small chance of an unplanned expense of ৳1,500 to ৳6,000. Nobody, including the model, can predict these.",
  "The cash-out fee is assumed to be 1.4%. It is not upay's official charge.",
];

export const LIMITS = [
  "The amounts and probabilities are guesses chosen to look plausible. They were not fitted to real data.",
  "Real customers are more varied than five kinds with equal numbers.",
  "A model that works on this data has only been shown to recover patterns that were put in. It still has to be tested on real, governed data.",
  "The warning looks only at the forecast balance. A customer who pays a bill late keeps a higher balance, so a missed payment does not always raise a warning.",
];
