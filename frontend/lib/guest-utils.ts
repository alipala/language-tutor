// Constants
const GUEST_EXPIRATION_KEY = 'guestTimeExpired';
const GUEST_EXPIRATION_TIMESTAMP_KEY = 'guestTimeExpiredAt';
const GUEST_COOLDOWN_MINUTES = 30; // 30 minutes cooldown period

/**
 * Checks if the guest user's time limit has expired
 * @returns {boolean} True if the guest user's time limit has expired and is still within the cooldown period
 */
export const isGuestTimeExpired = (): boolean => {
  const expired = sessionStorage.getItem(GUEST_EXPIRATION_KEY) === 'true';
  
  if (!expired) {
    return false;
  }
  
  // Check if the cooldown period has passed
  const expiredAtStr = sessionStorage.getItem(GUEST_EXPIRATION_TIMESTAMP_KEY);
  if (!expiredAtStr) {
    return false; // No timestamp, treat as not expired
  }
  
  const expiredAt = parseInt(expiredAtStr, 10);
  const now = Date.now();
  const elapsedMinutes = (now - expiredAt) / (1000 * 60);
  
  // If more than GUEST_COOLDOWN_MINUTES have passed, reset the expiration
  if (elapsedMinutes >= GUEST_COOLDOWN_MINUTES) {
    resetGuestTimeExpiration();
    return false;
  }
  
  return true;
};

/**
 * Sets the guest user's time limit as expired
 */
export const setGuestTimeExpired = (): void => {
  sessionStorage.setItem(GUEST_EXPIRATION_KEY, 'true');
  sessionStorage.setItem(GUEST_EXPIRATION_TIMESTAMP_KEY, Date.now().toString());
};

/**
 * Resets the guest user's time limit expiration
 */
export const resetGuestTimeExpiration = (): void => {
  sessionStorage.removeItem(GUEST_EXPIRATION_KEY);
  sessionStorage.removeItem(GUEST_EXPIRATION_TIMESTAMP_KEY);
};

/**
 * Gets the remaining cooldown time in minutes for a guest user
 * @returns {number} The number of minutes remaining in the cooldown period, or 0 if not expired
 */
export const getRemainingCooldownMinutes = (): number => {
  const expired = sessionStorage.getItem(GUEST_EXPIRATION_KEY) === 'true';
  
  if (!expired) {
    return 0;
  }
  
  const expiredAtStr = sessionStorage.getItem(GUEST_EXPIRATION_TIMESTAMP_KEY);
  if (!expiredAtStr) {
    return 0;
  }
  
  const expiredAt = parseInt(expiredAtStr, 10);
  const now = Date.now();
  const elapsedMinutes = (now - expiredAt) / (1000 * 60);
  const remainingMinutes = GUEST_COOLDOWN_MINUTES - elapsedMinutes;
  
  return Math.max(0, Math.ceil(remainingMinutes));
};
