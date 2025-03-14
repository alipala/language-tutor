import { FC } from 'react';

interface SpeechClientProps {
  language: string;
  level: string;
}

declare const SpeechClient: FC<SpeechClientProps>;
export default SpeechClient;
