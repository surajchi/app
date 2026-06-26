/** User domain types — mirror apps/users serializers. */

export type UserStatus = 'active' | 'suspended' | 'pending' | 'deleted';

export interface User {
  id: string;
  email: string;
  full_name: string;
  phone: string | null;
  status: UserStatus;
  is_2fa_enabled: boolean;
  email_verified: boolean;
  is_staff: boolean;
  roles: string[];
  created_at: string;
}

export interface UserUpdate {
  full_name?: string;
  phone?: string | null;
}
