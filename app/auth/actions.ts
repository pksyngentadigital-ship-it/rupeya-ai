// Rupeya.ai — Auth server actions used outside the sign-in page
// -----------------------------------------------------------
// Currently just sign-out. As we add account management (delete account,
// change email, change password), those server actions land here too.
// -----------------------------------------------------------

"use server";

import { redirect } from "next/navigation";
import { createSupabaseServerClient } from "@/lib/supabase/server";

export async function signOut() {
  const supabase = createSupabaseServerClient();
  await supabase.auth.signOut();
  redirect("/");
}
