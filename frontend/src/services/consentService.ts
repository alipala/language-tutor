/**
 * Service for consent-related API calls
 */
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface ConsentStatus {
  has_consent: boolean;
  consent_given_date?: string;
  consent_revoked: boolean;
  institution_name: string;
  tutor_name: string;
  data_shared: string[];
}

export interface ConsentGrantData {
  learner_id: string;
  institution_id: string;
  tutor_id: string;
}

export const consentService = {
  /**
   * Get consent status for a learner
   */
  async getConsentStatus(
    learnerId: string,
    institutionId: string
  ): Promise<ConsentStatus> {
    const response = await axios.get(
      `${API_BASE}/api/v1/consent/status/${learnerId}/${institutionId}`
    );
    return response.data;
  },

  /**
   * Grant consent
   */
  async grantConsent(data: ConsentGrantData): Promise<any> {
    const response = await axios.post(
      `${API_BASE}/api/v1/consent/grant`,
      data
    );
    return response.data;
  },

  /**
   * Revoke consent
   */
  async revokeConsent(
    learnerId: string,
    institutionId: string
  ): Promise<any> {
    const response = await axios.post(
      `${API_BASE}/api/v1/consent/revoke`,
      {
        learner_id: learnerId,
        institution_id: institutionId
      }
    );
    return response.data;
  }
};
