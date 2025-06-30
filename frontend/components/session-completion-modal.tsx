'use client';

import React, { useEffect, useState } from 'react';
import { CheckCircle, Home, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';

interface SessionCompletionModalProps {
  isOpen: boolean;
  onGoHome: () => void;
  onStartNew: () => void;
  sessionDuration: string;
  messageCount: number;
  language: string;
  level: string;
}

// Helper function to determine if we should show bilingual UI based on level
const shouldShowBilingual = (level: string): boolean => {
  const levelUpper = level.toUpperCase();
  return ['A1', 'A2', 'B1'].includes(levelUpper);
};

// Helper function to get text based on language and level
const getText = (language: string, level: string, englishText: string, translations: Record<string, string>): string => {
  const isBilingual = shouldShowBilingual(level);
  const targetText = translations[language.toLowerCase()] || englishText;
  
  if (isBilingual && language.toLowerCase() !== 'english') {
    return `${englishText} / ${targetText}`;
  }
  
  return targetText;
};

// Translation mappings
const translations = {
  sessionComplete: {
    english: 'Session Complete!',
    dutch: 'Sessie Voltooid!',
    spanish: '¡Sesión Completada!',
    german: 'Sitzung Abgeschlossen!',
    french: 'Session Terminée!',
    portuguese: 'Sessão Concluída!'
  },
  conversationSaved: {
    english: 'Your conversation has been saved successfully',
    dutch: 'Je gesprek is succesvol opgeslagen',
    spanish: 'Tu conversación se ha guardado exitosamente',
    german: 'Dein Gespräch wurde erfolgreich gespeichert',
    french: 'Votre conversation a été sauvegardée avec succès',
    portuguese: 'Sua conversa foi salva com sucesso'
  },
  sessionSummary: {
    english: 'Session Summary',
    dutch: 'Sessie Samenvatting',
    spanish: 'Resumen de Sesión',
    german: 'Sitzungszusammenfassung',
    french: 'Résumé de Session',
    portuguese: 'Resumo da Sessão'
  },
  duration: {
    english: 'Duration',
    dutch: 'Duur',
    spanish: 'Duración',
    german: 'Dauer',
    french: 'Durée',
    portuguese: 'Duração'
  },
  messages: {
    english: 'Messages',
    dutch: 'Berichten',
    spanish: 'Mensajes',
    german: 'Nachrichten',
    french: 'Messages',
    portuguese: 'Mensagens'
  },
  language: {
    english: 'Language',
    dutch: 'Taal',
    spanish: 'Idioma',
    german: 'Sprache',
    french: 'Langue',
    portuguese: 'Idioma'
  },
  level: {
    english: 'Level',
    dutch: 'Niveau',
    spanish: 'Nivel',
    german: 'Niveau',
    french: 'Niveau',
    portuguese: 'Nível'
  },
  greatJob: {
    english: 'Great job! Your progress has been saved to your learning plan.',
    dutch: 'Geweldig gedaan! Je voortgang is opgeslagen in je leerplan.',
    spanish: '¡Excelente trabajo! Tu progreso se ha guardado en tu plan de aprendizaje.',
    german: 'Großartige Arbeit! Dein Fortschritt wurde in deinem Lernplan gespeichert.',
    french: 'Excellent travail! Vos progrès ont été sauvegardés dans votre plan d\'apprentissage.',
    portuguese: 'Ótimo trabalho! Seu progresso foi salvo no seu plano de aprendizagem.'
  },
  chooseNext: {
    english: 'Choose what you\'d like to do next:',
    dutch: 'Kies wat je hierna wilt doen:',
    spanish: 'Elige qué te gustaría hacer a continuación:',
    german: 'Wähle, was du als nächstes tun möchtest:',
    french: 'Choisissez ce que vous aimeriez faire ensuite:',
    portuguese: 'Escolha o que você gostaria de fazer a seguir:'
  },
  viewProgress: {
    english: 'View Progress & Dashboard',
    dutch: 'Bekijk Voortgang & Dashboard',
    spanish: 'Ver Progreso y Panel',
    german: 'Fortschritt & Dashboard anzeigen',
    french: 'Voir Progrès et Tableau de Bord',
    portuguese: 'Ver Progresso e Painel'
  },
  startNew: {
    english: 'Start New Session',
    dutch: 'Start Nieuwe Sessie',
    spanish: 'Iniciar Nueva Sesión',
    german: 'Neue Sitzung starten',
    french: 'Commencer Nouvelle Session',
    portuguese: 'Iniciar Nova Sessão'
  },
  learningPlanProgress: {
    english: 'Your learning plan progress has been updated successfully',
    dutch: 'Je leerplan voortgang is succesvol bijgewerkt',
    spanish: 'Tu progreso del plan de aprendizaje se ha actualizado exitosamente',
    german: 'Dein Lernplan-Fortschritt wurde erfolgreich aktualisiert',
    french: 'Vos progrès du plan d\'apprentissage ont été mis à jour avec succès',
    portuguese: 'Seu progresso do plano de aprendizagem foi atualizado com sucesso'
  },
  practiceConversationSaved: {
    english: 'Your practice conversation has been saved to your history',
    dutch: 'Je oefengesprek is opgeslagen in je geschiedenis',
    spanish: 'Tu conversación de práctica se ha guardado en tu historial',
    german: 'Dein Übungsgespräch wurde in deiner Historie gespeichert',
    french: 'Votre conversation de pratique a été sauvegardée dans votre historique',
    portuguese: 'Sua conversa de prática foi salva no seu histórico'
  },
  learningPlanGreatJob: {
    english: 'Excellent work! Your learning plan progress has been updated.',
    dutch: 'Uitstekend werk! Je leerplan voortgang is bijgewerkt.',
    spanish: '¡Excelente trabajo! Tu progreso del plan de aprendizaje ha sido actualizado.',
    german: 'Ausgezeichnete Arbeit! Dein Lernplan-Fortschritt wurde aktualisiert.',
    french: 'Excellent travail! Vos progrès du plan d\'apprentissage ont été mis à jour.',
    portuguese: 'Excelente trabalho! Seu progresso do plano de aprendizagem foi atualizado.'
  },
  practiceGreatJob: {
    english: 'Great job! Your conversation has been saved to your practice history.',
    dutch: 'Geweldig gedaan! Je gesprek is opgeslagen in je oefengeschiedenis.',
    spanish: '¡Excelente trabajo! Tu conversación se ha guardado en tu historial de práctica.',
    german: 'Großartige Arbeit! Dein Gespräch wurde in deiner Übungshistorie gespeichert.',
    french: 'Excellent travail! Votre conversation a été sauvegardée dans votre historique de pratique.',
    portuguese: 'Ótimo trabalho! Sua conversa foi salva no seu histórico de prática.'
  }
};

export default function SessionCompletionModal({
  isOpen,
  onGoHome,
  onStartNew,
  sessionDuration,
  messageCount,
  language,
  level
}: SessionCompletionModalProps) {
  const router = useRouter();

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop overlay */}
      <div className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm" />
      
      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div 
          className="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden animate-in fade-in zoom-in duration-500"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Success Header */}
          <div className="bg-gradient-to-r from-green-500 to-emerald-500 px-6 py-8 text-center">
            <div className="w-20 h-20 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="h-12 w-12 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">
              {getText(language, level, 'Session Complete!', translations.sessionComplete)}
            </h2>
            <p className="text-green-100">
              {getText(language, level, 'Your conversation has been saved successfully', translations.conversationSaved)}
            </p>
          </div>
          
          {/* Content */}
          <div className="px-6 py-6">
            {/* Session Stats */}
            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <h3 className="font-semibold text-gray-900 mb-3 text-center">
                {getText(language, level, 'Session Summary', translations.sessionSummary)}
              </h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{sessionDuration}</div>
                  <div className="text-gray-600">
                    {getText(language, level, 'Duration', translations.duration)}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{messageCount}</div>
                  <div className="text-gray-600">
                    {getText(language, level, 'Messages', translations.messages)}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold text-purple-600 capitalize">{language}</div>
                  <div className="text-gray-600">
                    {getText(language, level, 'Language', translations.language)}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold text-orange-600">{level.toUpperCase()}</div>
                  <div className="text-gray-600">
                    {getText(language, level, 'Level', translations.level)}
                  </div>
                </div>
              </div>
            </div>

            {/* Progress Message */}
            <div className="text-center mb-6">
              <p className="text-gray-700 mb-2">
                🎉 {getText(language, level, 'Great job! Your progress has been saved to your learning plan.', translations.greatJob)}
              </p>
              <p className="text-sm text-gray-600">
                {getText(language, level, 'Choose what you\'d like to do next:', translations.chooseNext)}
              </p>
            </div>
            
            {/* Action Buttons */}
            <div className="space-y-3">
              <Button 
                className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-3 rounded-lg shadow-sm transition-all hover:shadow-md flex items-center justify-center gap-2"
                onClick={onGoHome}
              >
                <Home className="h-4 w-4" />
                {getText(language, level, 'View Progress & Dashboard', translations.viewProgress)}
              </Button>
              
              <Button 
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 rounded-lg shadow-sm transition-all hover:shadow-md flex items-center justify-center gap-2"
                onClick={onStartNew}
              >
                <RotateCcw className="h-4 w-4" />
                {getText(language, level, 'Start New Session', translations.startNew)}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
