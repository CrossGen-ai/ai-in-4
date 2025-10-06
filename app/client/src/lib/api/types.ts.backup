// API type definitions
export interface HealthCheckResponse {
  status: string;
  timestamp?: string;
}

// User types
export interface User {
  id: number;
  email: string;
  created_at: string;
  last_login?: string;
}

export interface UserExperience {
  id: number;
  user_id: number;
  experience_level: string;
  background?: string;
  goals?: string;
  created_at: string;
}

export interface UserCreate {
  email: string;
  experience_level: string;
  background?: string;
  goals?: string;
}

// Auth types
export interface MagicLinkRequest {
  email: string;
}

export interface AuthResponse {
  access_token: string;
  user: User;
}

// Course types
export interface Course {
  id: number;
  title: string;
  description?: string;
  schedule?: string;
  materials_url?: string;
}
