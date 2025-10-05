import axios from 'axios';
import { getApiBaseUrl } from '../lib/api-config';

// Don't call getApiBaseUrl() at module load - call it per request
const getApiBase = () => getApiBaseUrl();

export interface InstitutionSignupData {
  name: string;
  institution_type: 'school' | 'university' | 'language_center' | 'corporate';
  admin_email: string;
  admin_password: string;
  admin_name: string;
  subscription_plan?: 'starter' | 'professional' | 'enterprise'; // Optional - managed by admin
}

export interface InstitutionLoginData {
  admin_email: string;
  password: string;
}

export interface InstitutionSignupResponse {
  institution_id: string;
  institution_code: string;
  admin_email: string;
  subscription_plan: string;
  message: string;
}

export interface InstitutionLoginResponse {
  access_token: string;
  token_type: string;
  institution_id: string;
  institution_name: string;
  admin_email: string;
}

export interface InstitutionStats {
  total_tutors: number;
  total_learners: number;
  max_tutors: number;
  max_learners: number;
  subscription_plan: string;
}

export interface Institution {
  id: string;
  name: string;
  institution_type: 'school' | 'university' | 'language_center' | 'corporate';
  admin_email: string;
  admin_name: string;
  contact_phone?: string;
  website?: string;
  subscription_plan: string;
  created_at: string;
}

export const institutionService = {
  async signup(data: InstitutionSignupData): Promise<InstitutionSignupResponse> {
    const response = await axios.post(
      `${getApiBase()}/institution/signup`,
      data
    );
    return response.data;
  },

  async login(data: InstitutionLoginData): Promise<InstitutionLoginResponse> {
    const response = await axios.post(
      `/api/institution/login`,
      data
    );
    return response.data;
  },

  async getInstitution(institutionId: string): Promise<Institution> {
    const token = localStorage.getItem('institution_token');
    const response = await axios.get(
      `${getApiBase()}/institution/${institutionId}`,
      {
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    );
    return response.data;
  },

  async getStats(institutionId: string): Promise<InstitutionStats> {
    const response = await axios.get(
      `${getApiBase()}/institution/stats/${institutionId}`
    );
    return response.data;
  }
};
