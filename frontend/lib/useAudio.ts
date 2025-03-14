import { useRef, useCallback, useEffect, useState } from 'react';

// Hook for playing audio effects
export function useAudio() {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isAudioSupported, setIsAudioSupported] = useState(true);
  
  // Initialize audio on client side only
  useEffect(() => {
    try {
      if (typeof window !== 'undefined') {
        // Check if Audio is supported
        if ('Audio' in window) {
          audioRef.current = new Audio();
          // Add an error listener to detect issues with audio loading
          audioRef.current.addEventListener('error', () => {
            console.warn('Audio playback not supported or audio file not found');
            setIsAudioSupported(false);
          });
        } else {
          setIsAudioSupported(false);
        }
      }
    } catch (error) {
      console.warn('Audio initialization error:', error);
      setIsAudioSupported(false);
    }
    
    // Cleanup
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.removeEventListener('error', () => {});
        audioRef.current = null;
      }
    };
  }, []);
  
  // Play selection sound
  const playSelectionSound = useCallback(() => {
    if (!isAudioSupported || !audioRef.current) return Promise.resolve();
    
    try {
      // Set the source to the selection sound
      audioRef.current.src = '/sounds/selection-click.mp3';
      audioRef.current.volume = 0.5; // Set volume to 50%
      
      // Play the sound and handle errors gracefully
      return audioRef.current.play()
        .catch(err => {
          console.warn('Selection sound playback error:', err);
          return Promise.resolve(); // Resolve anyway to prevent blocking
        });
    } catch (error) {
      console.warn('Selection sound error:', error);
      return Promise.resolve(); // Resolve anyway to prevent blocking
    }
  }, [isAudioSupported]);
  
  // Play success sound
  const playSuccessSound = useCallback(() => {
    if (!isAudioSupported || !audioRef.current) return Promise.resolve();
    
    try {
      // Set the source to the success sound
      audioRef.current.src = '/sounds/success-chime.mp3';
      audioRef.current.volume = 0.5; // Set volume to 50%
      
      // Play the sound and handle errors gracefully
      return audioRef.current.play()
        .catch(err => {
          console.warn('Success sound playback error:', err);
          return Promise.resolve(); // Resolve anyway to prevent blocking
        });
    } catch (error) {
      console.warn('Success sound error:', error);
      return Promise.resolve(); // Resolve anyway to prevent blocking
    }
  }, [isAudioSupported]);
  
  return {
    playSelectionSound,
    playSuccessSound,
    isAudioSupported
  };
}
