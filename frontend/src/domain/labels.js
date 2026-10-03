// The names shown for the kinds of customer and for regular payments.

const PERSONAS = {
  rider: "Rider",
  garment: "Garment worker",
  student: "Student",
  shopkeeper: "Shop owner",
  freelancer: "Freelancer",
};

// A short name for a chip. An unknown kind falls back to the name the API gives.
export const personaName = (user) => PERSONAS[user.persona] ?? user.persona_label;

const PAYMENTS = {
  house_rent: "House rent",
  mess_rent: "Mess rent",
  shop_rent: "Shop rent",
  send_home: "Money sent home",
  savings_samity: "Savings group (samity)",
  bike_installment: "Bike installment",
  electricity: "Electricity bill",
  internet: "Internet bill",
  subscriptions: "Subscriptions",
  supplier: "Supplier",
  grocery: "Grocery shop",
  food: "Food",
  pharmacy: "Pharmacy",
  shopping: "Shopping",
  transport: "Transport",
};

const ACTIONS = {
  keep_to_safe_spend: "Keep to the safe amount",
  move_payment: "Move a payment",
  pay_directly: "Pay shops directly",
};

// A short name for a suggested action. The API's own sentence says the rest.
export const actionName = (id) => ACTIONS[id] ?? "Suggested action";

// "house_rent" -> "House rent". An unknown label is shown as it is, with spaces.
export function paymentName(label) {
  if (PAYMENTS[label]) return PAYMENTS[label];
  const words = label.replaceAll("_", " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}
