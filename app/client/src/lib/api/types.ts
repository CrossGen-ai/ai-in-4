// API type definitions
export type HealthCheckResponse = {
  status: string;
  timestamp?: string;
}

// User types
export type User = {
  id: number;
  email: string;
  created_at: string;
  last_login?: string;
}

export type UserExperience = {
  id: number;
  user_id: number;
  experience_level: string;
  background?: string;
  goals?: string;
  created_at: string;
}

export type UserCreate = {
  // Contact Information
  email: string;

  // Basic Info
  name: string;
  employment_status: string;
  employment_status_other?: string;
  industry?: string;
  role?: string;

  // Primary Use Context
  primary_use_context: string;

  // AI Experience
  tried_ai_before: boolean;
  ai_tools_used?: string[];
  usage_frequency: string;
  comfort_level: number; // 1-5

  // Goals & Applications
  goals: string[]; // Exactly 3 items

  // Biggest Challenges
  challenges?: string[];

  // Learning Preference
  learning_preference: string;

  // Additional Comments
  additional_comments?: string;

  // Legacy fields (optional for backward compatibility)
  experience_level?: string;
  background?: string;
}

// Auth types
export type MagicLinkRequest = {
  email: string;
}

export type AuthResponse = {
  access_token: string;
  user: User;
}

// Course types
export type Course = {
  id: number;
  title: string;
  description?: string;
  schedule?: string;
  materials_url?: string;
}
