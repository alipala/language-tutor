'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  Shuffle,
  Filter,
  Download,
  X,
  CheckCircle,
  XCircle,
  Eye,
  EyeOff,
  Star,
  StarOff
} from 'lucide-react';

export interface Flashcard {
  id: string;
  session_id: string;
  user_id: string;
  language: string;
  level: string;
  topic?: string;
  front: string;
  back: string;
  category: string;
  difficulty: string;
  tags: string[];
  created_at: string;
  last_reviewed?: string;
  review_count: number;
  correct_count: number;
  incorrect_count: number;
  mastery_level: number;
  next_review_date?: string;
  is_active: boolean;
}

export interface FlashcardSet {
  id: string;
  session_id: string;
  user_id: string;
  language: string;
  level: string;
  topic?: string;
  title: string;
  description: string;
  flashcards: Flashcard[];
  total_cards: number;
  created_at: string;
  is_completed: boolean;
  completed_at?: string;
}

interface FlashcardViewerProps {
  flashcards: Flashcard[];
  flashcardSet?: FlashcardSet;
  onReview?: (flashcardId: string, correct: boolean) => void;
  onClose?: () => void;
  showProgress?: boolean;
  showFilters?: boolean;
  showDownload?: boolean;
  autoAdvance?: boolean;
  className?: string;
}

type FilterType = 'all' | 'due' | 'new' | 'difficult' | 'mastered';
type CategoryFilter = 'all' | 'grammar' | 'vocabulary' | 'pronunciation' | 'fluency' | 'comprehension';
type DifficultyFilter = 'all' | 'easy' | 'medium' | 'hard';

export const FlashcardViewer: React.FC<FlashcardViewerProps> = ({
  flashcards,
  flashcardSet,
  onReview,
  onClose,
  showProgress = true,
  showFilters = true,
  showDownload = true,
  autoAdvance = false,
  className = ''
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [showAnswer, setShowAnswer] = useState(false);
  const [filter, setFilter] = useState<FilterType>('all');
  const [categoryFilter, setCategoryFilter] = useState<CategoryFilter>('all');
  const [difficultyFilter, setDifficultyFilter] = useState<DifficultyFilter>('all');
  const [filteredCards, setFilteredCards] = useState<Flashcard[]>(flashcards);
  const [reviewMode, setReviewMode] = useState(false);
  const [reviewedCards, setReviewedCards] = useState<Set<string>>(new Set());

  // Filter flashcards based on current filters
  useEffect(() => {
    let filtered = [...flashcards];

    // Apply filter
    switch (filter) {
      case 'due':
        const now = new Date();
        filtered = filtered.filter(card =>
          !card.next_review_date || new Date(card.next_review_date) <= now
        );
        break;
      case 'new':
        filtered = filtered.filter(card => card.review_count === 0);
        break;
      case 'difficult':
        filtered = filtered.filter(card => card.mastery_level < 0.5);
        break;
      case 'mastered':
        filtered = filtered.filter(card => card.mastery_level >= 0.8);
        break;
    }

    // Apply category filter
    if (categoryFilter !== 'all') {
      filtered = filtered.filter(card => card.category === categoryFilter);
    }

    // Apply difficulty filter
    if (difficultyFilter !== 'all') {
      filtered = filtered.filter(card => card.difficulty === difficultyFilter);
    }

    setFilteredCards(filtered);
    setCurrentIndex(0);
    setIsFlipped(false);
    setShowAnswer(false);
  }, [flashcards, filter, categoryFilter, difficultyFilter]);

  const currentCard = filteredCards[currentIndex];
  const progress = filteredCards.length > 0 ? ((currentIndex + 1) / filteredCards.length) * 100 : 0;

  const handleFlip = () => {
    setIsFlipped(!isFlipped);
    if (!isFlipped) {
      setShowAnswer(true);
    }
  };

  const handleNext = () => {
    if (currentIndex < filteredCards.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setIsFlipped(false);
      setShowAnswer(false);
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
      setIsFlipped(false);
      setShowAnswer(false);
    }
  };

  const handleReview = async (correct: boolean) => {
    if (currentCard && onReview) {
      await onReview(currentCard.id, correct);
      setReviewedCards(prev => new Set(prev).add(currentCard.id));

      if (autoAdvance && currentIndex < filteredCards.length - 1) {
        setTimeout(() => {
          handleNext();
        }, 500);
      }
    }
  };

  const handleShuffle = () => {
    const shuffled = [...filteredCards].sort(() => Math.random() - 0.5);
    setFilteredCards(shuffled);
    setCurrentIndex(0);
    setIsFlipped(false);
    setShowAnswer(false);
  };

  const handleDownload = () => {
    if (!flashcardSet) return;

    const dataStr = JSON.stringify({
      title: flashcardSet.title,
      description: flashcardSet.description,
      flashcards: filteredCards.map(card => ({
        front: card.front,
        back: card.back,
        category: card.category,
        difficulty: card.difficulty,
        tags: card.tags
      })),
      created_at: flashcardSet.created_at
    }, null, 2);

    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    const exportFileDefaultName = `${flashcardSet.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_flashcards.json`;

    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return 'bg-green-100 text-green-700 border-green-200';
      case 'medium': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'hard': return 'bg-red-100 text-red-700 border-red-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'grammar': return 'bg-blue-100 text-blue-700';
      case 'vocabulary': return 'bg-purple-100 text-purple-700';
      case 'pronunciation': return 'bg-orange-100 text-orange-700';
      case 'fluency': return 'bg-teal-100 text-teal-700';
      case 'comprehension': return 'bg-indigo-100 text-indigo-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const renderStars = (masteryLevel: number) => {
    const stars = [];
    const filledStars = Math.round(masteryLevel * 5);

    for (let i = 0; i < 5; i++) {
      stars.push(
        i < filledStars ?
          <Star key={i} className="h-3 w-3 fill-yellow-400 text-yellow-400" /> :
          <StarOff key={i} className="h-3 w-3 text-gray-300" />
      );
    }

    return stars;
  };

  if (!currentCard) {
    return (
      <div className={`flex flex-col items-center justify-center p-8 text-center ${className}`}>
        <div className="text-6xl mb-4">🎴</div>
        <h3 className="text-xl font-semibold text-gray-800 mb-2">No flashcards found</h3>
        <p className="text-gray-600 mb-4">
          {flashcards.length === 0
            ? "No flashcards have been generated for this session yet."
            : "No flashcards match the current filters."
          }
        </p>
        {flashcards.length > 0 && (
          <Button onClick={() => {
            setFilter('all');
            setCategoryFilter('all');
            setDifficultyFilter('all');
          }} className="text-black border-gray-300 hover:bg-gray-100">
            Clear Filters
          </Button>
        )}
      </div>
    );
  }

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-4">
          {flashcardSet && (
            <div>
              <h2 className="text-lg font-semibold text-black">{flashcardSet.title}</h2>
              <p className="text-sm text-gray-600">{flashcardSet.description}</p>
            </div>
          )}
          <div className="flex items-center space-x-2">
            <span className={`inline-block text-xs px-2 py-1 rounded-full font-medium border ${getDifficultyColor(currentCard.difficulty)}`}>
              {currentCard.difficulty}
            </span>
            <span className={`inline-block text-xs px-2 py-1 rounded-full font-medium ${getCategoryColor(currentCard.category)}`}>
              {currentCard.category}
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {showFilters && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setReviewMode(!reviewMode)}
              className={`text-black border-gray-300 hover:bg-gray-100 ${reviewMode ? 'bg-blue-50 border-blue-200' : ''}`}
            >
              {reviewMode ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              {reviewMode ? 'Study Mode' : 'Review Mode'}
            </Button>
          )}

          {showDownload && flashcardSet && (
            <Button variant="outline" size="sm" onClick={handleDownload} className="text-black border-gray-300 hover:bg-gray-100">
              <Download className="h-4 w-4 mr-1" />
              Export
            </Button>
          )}

          {onClose && (
            <Button variant="outline" size="sm" onClick={onClose} className="text-black border-gray-300 hover:bg-gray-100">
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="flex flex-wrap items-center gap-2 p-4 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4 text-gray-500" />
            <span className="text-sm font-medium text-black">Filter:</span>
          </div>

          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as FilterType)}
            className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500 text-black bg-white"
          >
            <option value="all" className="text-black">All Cards</option>
            <option value="due" className="text-black">Due for Review</option>
            <option value="new" className="text-black">New Cards</option>
            <option value="difficult" className="text-black">Difficult</option>
            <option value="mastered" className="text-black">Mastered</option>
          </select>

          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value as CategoryFilter)}
            className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500 text-black bg-white"
          >
            <option value="all" className="text-black">All Categories</option>
            <option value="grammar" className="text-black">Grammar</option>
            <option value="vocabulary" className="text-black">Vocabulary</option>
            <option value="pronunciation" className="text-black">Pronunciation</option>
            <option value="fluency" className="text-black">Fluency</option>
            <option value="comprehension" className="text-black">Comprehension</option>
          </select>

          <select
            value={difficultyFilter}
            onChange={(e) => setDifficultyFilter(e.target.value as DifficultyFilter)}
            className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500 text-black bg-white"
          >
            <option value="all" className="text-black">All Difficulties</option>
            <option value="easy" className="text-black">Easy</option>
            <option value="medium" className="text-black">Medium</option>
            <option value="hard" className="text-black">Hard</option>
          </select>

          <Button variant="outline" size="sm" onClick={handleShuffle} className="text-black border-gray-300 hover:bg-gray-100">
            <Shuffle className="h-4 w-4 mr-1" />
            Shuffle
          </Button>
        </div>
      )}

      {/* Progress */}
      {showProgress && (
        <div className="px-4 py-2 border-b border-gray-200">
          <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
            <span>Card {currentIndex + 1} of {filteredCards.length}</span>
            <span>{Math.round(progress)}% complete</span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>
      )}

      {/* Flashcard */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-2xl">
          <div
            className={`relative w-full h-96 cursor-pointer transition-transform duration-500 transform-style-preserve-3d ${
              isFlipped ? 'rotate-y-180' : ''
            }`}
            onClick={handleFlip}
            style={{
              transformStyle: 'preserve-3d',
              transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)'
            }}
          >
            {/* Front of card */}
            <div
              className="absolute inset-0 w-full h-full backface-hidden"
              style={{ backfaceVisibility: 'hidden' }}
            >
              <div className="w-full h-full bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl shadow-xl p-8 flex flex-col items-center justify-center text-white">
                <div className="text-center">
                  <div className="text-2xl mb-4">💭</div>
                  <h3 className="text-xl font-semibold mb-4">Question</h3>
                  <p className="text-lg leading-relaxed">{currentCard.front}</p>
                </div>
                <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2">
                  <div className="text-sm opacity-75">Click to reveal answer</div>
                </div>
              </div>
            </div>

            {/* Back of card */}
            <div
              className="absolute inset-0 w-full h-full backface-hidden rotate-y-180"
              style={{
                backfaceVisibility: 'hidden',
                transform: 'rotateY(180deg)'
              }}
            >
              <div className="w-full h-full bg-gradient-to-br from-green-500 to-teal-600 rounded-2xl shadow-xl p-8 flex flex-col items-center justify-center text-white">
                <div className="text-center">
                  <div className="text-2xl mb-4">💡</div>
                  <h3 className="text-xl font-semibold mb-4">Answer</h3>
                  <p className="text-lg leading-relaxed">{currentCard.back}</p>
                </div>

                {/* Mastery stars */}
                <div className="absolute top-4 right-4 flex items-center space-x-1">
                  {renderStars(currentCard.mastery_level)}
                </div>

                {/* Tags */}
                {currentCard.tags.length > 0 && (
                  <div className="absolute bottom-4 left-4 flex flex-wrap gap-1">
                    {currentCard.tags.slice(0, 3).map((tag, index) => (
                      <span key={index} className="text-xs bg-white bg-opacity-20 px-2 py-1 rounded-full">
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Review buttons (only show when flipped and in review mode) */}
          {isFlipped && reviewMode && onReview && (
            <div className="flex justify-center space-x-4 mt-6">
              <Button
                onClick={(e) => {
                  e.stopPropagation();
                  handleReview(false);
                }}
                variant="outline"
                className="border-red-300 text-red-600 hover:bg-red-50"
                disabled={reviewedCards.has(currentCard.id)}
              >
                <XCircle className="h-4 w-4 mr-2" />
                Incorrect
              </Button>
              <Button
                onClick={(e) => {
                  e.stopPropagation();
                  handleReview(true);
                }}
                className="bg-green-600 hover:bg-green-700"
                disabled={reviewedCards.has(currentCard.id)}
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Correct
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between p-4 border-t border-gray-200">
        <Button
          variant="outline"
          onClick={handlePrevious}
          disabled={currentIndex === 0}
          className="text-black border-gray-300 hover:bg-gray-100"
        >
          <ChevronLeft className="h-4 w-4 mr-1" />
          Previous
        </Button>

        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm" onClick={() => setIsFlipped(false)} className="text-black border-gray-300 hover:bg-gray-100">
            <RotateCcw className="h-4 w-4 mr-1" />
            Reset
          </Button>

          {!isFlipped && (
            <Button onClick={handleFlip} className="text-black bg-blue-600 hover:bg-blue-700">
              <Eye className="h-4 w-4 mr-1" />
              Show Answer
            </Button>
          )}
        </div>

        <Button
          variant="outline"
          onClick={handleNext}
          disabled={currentIndex === filteredCards.length - 1}
          className="text-black border-gray-300 hover:bg-gray-100"
        >
          Next
          <ChevronRight className="h-4 w-4 ml-1" />
        </Button>
      </div>

      {/* Card Statistics */}
      <div className="px-4 py-2 border-t border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <div className="flex items-center space-x-4">
            <span>Reviews: {currentCard.review_count}</span>
            <span>Correct: {currentCard.correct_count}</span>
            <span>Incorrect: {currentCard.incorrect_count}</span>
            <span>Mastery: {Math.round(currentCard.mastery_level * 100)}%</span>
          </div>
          <div>
            Created: {new Date(currentCard.created_at).toLocaleDateString()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FlashcardViewer;
