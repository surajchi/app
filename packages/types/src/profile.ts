/** Profile domain types — mirror apps/profiles ProfileSerializer. */

export type ExperienceLevel = 'beginner' | 'intermediate' | 'pro';
export type RiskAppetite = 'low' | 'medium' | 'high';

export interface Profile {
  avatar_url: string;
  country: string;
  timezone: string;
  base_currency: string;
  language: string;
  bio: string;
  experience_level: ExperienceLevel;
  risk_appetite: RiskAppetite;
  updated_at: string;
}

export type ProfileUpdate = Partial<Omit<Profile, 'updated_at'>>;
