import { useRef, useCallback, useEffect } from 'react';

// Hook for playing audio effects
export function useAudio() {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  
  // Initialize audio on client side only
  useEffect(() => {
    if (typeof window !== 'undefined' && !audioRef.current) {
      audioRef.current = new Audio();
    }
    
    // Cleanup
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);
  
  // Play selection sound
  const playSelectionSound = useCallback(() => {
    if (!audioRef.current) return;
    
    // Set the source to the selection sound
    audioRef.current.src = '/sounds/selection-click.mp3';
    audioRef.current.volume = 0.5; // Set volume to 50%
    
    // Play the sound
    audioRef.current.play().catch(err => {
      console.error('Error playing selection sound:', err);
    });
  }, []);
  
  // Play success sound
  const playSuccessSound = useCallback(() => {
    if (!audioRef.current) return;
    
    // Set the source to the success sound
    audioRef.current.src = '/sounds/success-chime.mp3';
    audioRef.current.volume = 0.5; // Set volume to 50%
    
    // Play the sound
    audioRef.current.play().catch(err => {
      console.error('Error playing success sound:', err);
    });
  }, []);
  
  return {
    playSelectionSound,
    playSuccessSound
  };
}
